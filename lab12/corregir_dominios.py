"""Migración incremental sobre copia; no repite la lectura/ETL de los CSV fuente."""

import argparse
import csv
import hashlib
import io
import json
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import duckdb
from pipeline import ROOT, snapshot


def migrate(con, gender_zip):
    if con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='clinical_lineage'"
    ).fetchone()[0]:
        raise ValueError("La migración ya fue aplicada")
    before = snapshot(con)
    con.execute("BEGIN")
    try:
        with zipfile.ZipFile(gender_zip) as z:
            rows = [
                {k.lower(): v or None for k, v in r.items()}
                for r in csv.DictReader(
                    io.StringIO(z.read("GiBleed_5.3/CONCEPT.csv").decode())
                )
            ]
            genders = {
                int(r["concept_id"]): r
                for r in rows
                if r["concept_id"] in ["8507", "8532"]
            }
            for cid, code in [(8507, "M"), (8532, "F")]:
                r = genders[cid]
                if (
                    r["concept_code"],
                    r["domain_id"],
                    r["vocabulary_id"],
                    r["standard_concept"],
                    r["invalid_reason"],
                ) != (code, "Gender", "Gender", "S", None):
                    raise ValueError("El suplemento Gender no cumple las condiciones")
                existing = con.execute(
                    "SELECT concept_code,domain_id,standard_concept FROM concept WHERE concept_id=?",
                    [cid],
                ).fetchone()
                if existing and existing != (code, "Gender", "S"):
                    raise ValueError("Conflicto de concepto Gender")
                if not existing:
                    con.execute(
                        "INSERT INTO concept VALUES (?,?,?,?,?,?,?,?,?,?)",
                        list(r.values()),
                    )
            # Metadatos canónicos disponibles en el suplemento, sin copiar pacientes.
            if con.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_name='vocabulary'"
            ).fetchone()[0]:
                vr = next(
                    {k.lower(): v or None for k, v in r.items()}
                    for r in csv.DictReader(
                        io.StringIO(z.read("GiBleed_5.3/VOCABULARY.csv").decode())
                    )
                    if r["VOCABULARY_ID"] == "Gender"
                )
                meta_id = vr["vocabulary_concept_id"]
                if not con.execute(
                    "SELECT count(*) FROM concept WHERE concept_id=?", [meta_id]
                ).fetchone()[0]:
                    meta = [r for r in rows if r["concept_id"] == meta_id]
                    if meta:
                        con.execute(
                            "INSERT INTO concept VALUES (?,?,?,?,?,?,?,?,?,?)",
                            list(meta[0].values()),
                        )
                if con.execute(
                    "SELECT count(*) FROM concept WHERE concept_id=?", [meta_id]
                ).fetchone()[0]:
                    con.execute(
                        "INSERT INTO vocabulary SELECT ?,?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM vocabulary WHERE vocabulary_id='Gender')",
                        list(vr.values()),
                    )
        con.execute(
            "UPDATE person SET gender_concept_id=CASE gender_source_value WHEN 'M' THEN 8507 WHEN 'F' THEN 8532 ELSE 0 END"
        )
        con.execute((ROOT / "sql/dominos_clinicos.sql").read_text())
        con.execute(
            "CREATE TABLE clinical_lineage (source_row BIGINT,event_table VARCHAR,event_id BIGINT,target_concept_id BIGINT)"
        )
        con.execute(
            "INSERT INTO clinical_lineage SELECT l.source_row,'condition_occurrence',l.condition_occurrence_id,c.condition_concept_id FROM condition_lineage l JOIN condition_occurrence c USING(condition_occurrence_id)"
        )
        for domain, table, pk in [
            ("Observation", "observation", "observation_id"),
            ("Measurement", "measurement", "measurement_id"),
        ]:
            con.execute(
                f"CREATE TEMP TABLE integrate_{table} AS SELECT row_number() OVER(ORDER BY source_row,target_id)::INTEGER event_id,* FROM rejected_domain WHERE domain_id='{domain}'"
            )
            # El concepto describe el hallazgo/situación; no se inventan valores ni unidades.
            con.execute(
                f"INSERT INTO {table} ({pk},person_id,{table}_concept_id,{table}_date,{table}_datetime,{table}_type_concept_id,visit_occurrence_id,{table}_source_value,{table}_source_concept_id) SELECT event_id,person_id,target_id,CAST(START AS DATE),CAST(START AS TIMESTAMP),0,visit_occurrence_id,CODE,source_id FROM integrate_{table}"
            )
            con.execute(
                f"INSERT INTO clinical_lineage SELECT source_row,'{table}',event_id,target_id FROM integrate_{table}"
            )
        check = validate_migration(con)
        if any(check.values()):
            raise ValueError(check)
        metadata = json.loads(
            con.execute("SELECT metadata FROM lab12_run").fetchone()[0]
        )
        metadata["parent_run_id"] = metadata["run_id"]
        metadata["run_id"] = str(uuid.uuid4())
        metadata["migrated_at"] = datetime.now(timezone.utc).isoformat()
        metadata["estado"] = (
            "athena_dominios_integrados_pendiente_validacion_cientifica"
        )
        metadata["migration"] = {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "gender_reference_url": "https://github.com/OHDSI/EunomiaDatasets/blob/main/datasets/GiBleed/GiBleed_5.3.zip",
            "gender_reference_sha256": hashlib.sha256(
                gender_zip.read_bytes()
            ).hexdigest(),
            "before": {"counts": before["counts"], "ceros": before["queries"]["ceros"]},
            "checks": check,
        }
        con.execute("UPDATE lab12_run SET metadata=?", [json.dumps(metadata)])
        con.execute("COMMIT")
        return metadata
    except Exception:
        con.execute("ROLLBACK")
        raise


def validate_migration(con):
    checks = {}
    relocated = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='migration_relocated'"
    ).fetchone()[0]
    for table, pk in [
        ("observation", "observation_id"),
        ("measurement", "measurement_id"),
    ]:
        checks[table + "_pk"] = con.execute(
            f"SELECT count(*)-count(DISTINCT {pk}) FROM {table}"
        ).fetchone()[0]
        checks[table + "_person_fk"] = con.execute(
            f"SELECT count(*) FROM {table} e WHERE NOT EXISTS (SELECT 1 FROM person p WHERE p.person_id=e.person_id)"
        ).fetchone()[0]
        checks[table + "_visit_fk"] = con.execute(
            f"SELECT count(*) FROM {table} e WHERE visit_occurrence_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM visit_occurrence v WHERE v.visit_occurrence_id=e.visit_occurrence_id AND v.person_id=e.person_id)"
        ).fetchone()[0]
        checks[table + "_domain"] = con.execute(
            f"SELECT count(*) FROM {table} e WHERE e.{table}_concept_id<>0 AND NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=e.{table}_concept_id AND c.domain_id='{table.title()}' AND c.standard_concept='S' AND c.invalid_reason IS NULL)"
        ).fetchone()[0]
        extra = (
            con.execute(
                "SELECT count(*) FROM migration_relocated WHERE domain_id=?",
                [table.title()],
            ).fetchone()[0]
            if relocated
            else 0
        )
        checks[table + "_source_count"] = abs(
            con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            - con.execute(
                "SELECT count(*) FROM rejected_domain WHERE domain_id=?",
                [table.title()],
            ).fetchone()[0]
            - extra
        )
        checks[table + "_lineage"] = con.execute(
            f"SELECT count(*) FROM clinical_lineage l WHERE l.event_table='{table}' AND NOT EXISTS (SELECT 1 FROM {table} e WHERE e.{pk}=l.event_id AND e.{table}_concept_id=l.target_concept_id)"
        ).fetchone()[0]
        checks[table + "_maps_to"] = con.execute(
            f"SELECT count(*) FROM {table} e WHERE e.{table}_concept_id<>0 AND NOT EXISTS (SELECT 1 FROM concept_relationship r WHERE r.concept_id_1=e.{table}_source_concept_id AND r.concept_id_2=e.{table}_concept_id AND r.relationship_id='Maps to' AND r.invalid_reason IS NULL)"
        ).fetchone()[0]
    checks["source_without_clinical_trace"] = con.execute(
        "SELECT count(*) FROM src_conditions s WHERE NOT EXISTS (SELECT 1 FROM clinical_lineage l WHERE l.source_row=s.source_row)"
    ).fetchone()[0]
    checks["lineage_without_source"] = con.execute(
        "SELECT count(*) FROM clinical_lineage l WHERE NOT EXISTS (SELECT 1 FROM src_conditions s WHERE s.source_row=l.source_row)"
    ).fetchone()[0]
    checks["duplicate_lineage"] = con.execute(
        "SELECT count(*) FROM (SELECT source_row,event_table,target_concept_id FROM clinical_lineage GROUP BY ALL HAVING count(*)>1)"
    ).fetchone()[0]
    checks["gender_mapping"] = con.execute(
        "SELECT count(*) FROM person p WHERE (gender_source_value='F' AND gender_concept_id<>8532) OR (gender_source_value='M' AND gender_concept_id<>8507)"
    ).fetchone()[0]
    checks["gender_standard"] = con.execute(
        "SELECT count(*) FROM person p WHERE gender_concept_id<>0 AND NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=p.gender_concept_id AND c.domain_id='Gender' AND c.standard_concept='S' AND c.invalid_reason IS NULL)"
    ).fetchone()[0]
    checks["measurement_without_numeric_invention"] = con.execute(
        "SELECT count(*) FROM measurement WHERE value_as_number IS NOT NULL OR unit_concept_id IS NOT NULL OR unit_source_value IS NOT NULL"
    ).fetchone()[0]
    return checks


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--gender-reference", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Use una salida nueva para conservar el antes")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    # Exige una base consistente y cerrada; checkpoint antes de copiar si hubiera WAL.
    with duckdb.connect(str(a.source), read_only=True) as c:
        snapshot(c)
    if Path(str(a.source) + ".wal").exists():
        raise ValueError("Cerrar/checkpoint de la base origen antes de copiar")
    shutil.copy2(a.source, a.output)
    with duckdb.connect(str(a.output)) as c:
        print(json.dumps(migrate(c, a.gender_reference), indent=2))
