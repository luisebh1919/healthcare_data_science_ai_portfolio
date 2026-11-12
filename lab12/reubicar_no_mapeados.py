"""Reubica códigos de dominio conocido sin inventar un concepto estándar."""

import argparse
import hashlib
import json
import uuid
from pathlib import Path

import duckdb
from corregir_dominios import validate_migration


def relocate(con):
    if con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='migration_relocated'"
    ).fetchone()[0]:
        raise ValueError("Reubicación ya aplicada")
    con.execute("BEGIN")
    try:
        con.execute(
            "CREATE TABLE migration_relocated AS SELECT l.source_row,d.condition_occurrence_id,c.domain_id,c.concept_id AS source_concept_id FROM condition_lineage l JOIN condition_occurrence d USING(condition_occurrence_id) JOIN src_conditions s USING(source_row) JOIN concept c ON c.vocabulary_id='SNOMED' AND c.concept_code=s.CODE WHERE d.condition_concept_id=0 AND c.domain_id IN ('Observation','Measurement') AND c.invalid_reason IS NULL"
        )
        for table in ["observation", "measurement"]:
            pk = table + "_id"
            maximum = con.execute(
                f"SELECT coalesce(max({pk}),0) FROM {table}"
            ).fetchone()[0]
            con.execute(
                f"CREATE TEMP TABLE relocate_{table} AS SELECT row_number() OVER(ORDER BY r.source_row)+{maximum} AS new_id,r.*,d.person_id,d.visit_occurrence_id,s.START,s.CODE FROM migration_relocated r JOIN condition_occurrence d USING(condition_occurrence_id) JOIN src_conditions s USING(source_row) WHERE r.domain_id='{table.title()}'"
            )
            con.execute(
                f"INSERT INTO {table} ({pk},person_id,{table}_concept_id,{table}_date,{table}_datetime,{table}_type_concept_id,visit_occurrence_id,{table}_source_value,{table}_source_concept_id) SELECT new_id,person_id,0,CAST(START AS DATE),CAST(START AS TIMESTAMP),0,visit_occurrence_id,CODE,source_concept_id FROM relocate_{table}"
            )
            con.execute(
                f"INSERT INTO clinical_lineage SELECT source_row,'{table}',new_id,0 FROM relocate_{table}"
            )
        con.execute(
            "DELETE FROM clinical_lineage WHERE event_table='condition_occurrence' AND source_row IN (SELECT source_row FROM migration_relocated)"
        )
        con.execute(
            "DELETE FROM condition_occurrence WHERE condition_occurrence_id IN (SELECT condition_occurrence_id FROM migration_relocated)"
        )
        con.execute(
            "DELETE FROM condition_lineage WHERE source_row IN (SELECT source_row FROM migration_relocated)"
        )
        checks = validate_migration(con)
        if any(checks.values()):
            raise ValueError(checks)
        meta = json.loads(con.execute("SELECT metadata FROM lab12_run").fetchone()[0])
        meta["parent_run_id"] = meta["run_id"]
        meta["run_id"] = str(uuid.uuid4())
        meta["migration"]["relocation"] = {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "rows": con.execute("SELECT count(*) FROM migration_relocated").fetchone()[
                0
            ],
        }
        meta["migration"]["checks"] = checks
        con.execute("UPDATE lab12_run SET metadata=?", [json.dumps(meta)])
        con.execute("COMMIT")
        return checks
    except Exception:
        con.execute("ROLLBACK")
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    a = p.parse_args()
    with duckdb.connect(str(a.db)) as c:
        print(json.dumps(relocate(c), indent=2))
