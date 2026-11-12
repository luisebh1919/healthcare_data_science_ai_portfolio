"""Corrección incremental de clases Visit con evidencia y sin alterar fechas."""

import argparse
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb
from pipeline import snapshot

RULES = [
    (
        "home",
        "OMOP4822459",
        "Correspondencia explícita: atención en domicilio / Home Visit",
    ),
    (
        "virtual",
        "OMOP5556618",
        "Correspondencia explícita: visita virtual / Telehealth",
    ),
    (
        "snf",
        "LTCP",
        "SNF es institución de cuidados no hospitalaria; agregación a tipo más amplio",
    ),
    (
        "urgentcare",
        "ER",
        "Convención de OHDSI ETL-Synthea v5.4; no equivale a urgencias hospitalarias exclusivamente",
    ),
]


def validate_visits(con):
    checks = {}
    checks["visit_standard_domain"] = con.execute(
        "SELECT count(*) FROM visit_occurrence v WHERE visit_concept_id<>0 AND NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=v.visit_concept_id AND c.domain_id='Visit' AND c.standard_concept='S' AND c.invalid_reason IS NULL)"
    ).fetchone()[0]
    if con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='visit_mapping_audit'"
    ).fetchone()[0]:
        checks["visit_rule_concordance"] = con.execute(
            "SELECT count(*) FROM visit_mapping_audit a JOIN src_encounters s ON s.ENCOUNTERCLASS=a.source_class JOIN visit_occurrence v ON v.visit_source_value=s.Id WHERE v.visit_concept_id<>a.target_concept_id"
        ).fetchone()[0]
    return checks


def finalize(con):
    if con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='visit_mapping_audit'"
    ).fetchone()[0]:
        raise ValueError("Migración Visit ya aplicada")
    before = snapshot(con)
    con.execute("BEGIN")
    try:
        con.execute(
            "CREATE TABLE visit_mapping_audit (source_class VARCHAR,target_concept_id BIGINT,target_concept_name VARCHAR,target_concept_code VARCHAR,evidence VARCHAR,changed_rows BIGINT)"
        )
        for source, code, evidence in RULES:
            rows = con.execute(
                "SELECT concept_id,concept_name FROM concept WHERE vocabulary_id='Visit' AND domain_id='Visit' AND concept_code=? AND standard_concept='S' AND invalid_reason IS NULL",
                [code],
            ).fetchall()
            if len(rows) != 1:
                raise ValueError("Destino Visit ausente o ambiguo: " + code)
            cid, name = rows[0]
            n = con.execute(
                "SELECT count(*) FROM visit_occurrence v JOIN src_encounters s ON s.Id=v.visit_source_value WHERE s.ENCOUNTERCLASS=? AND v.visit_concept_id=0",
                [source],
            ).fetchone()[0]
            con.execute(
                "INSERT INTO visit_mapping_audit VALUES (?,?,?,?,?,?)",
                [source, cid, name, code, evidence, n],
            )
            con.execute(
                "UPDATE visit_occurrence v SET visit_concept_id=? FROM src_encounters s WHERE s.Id=v.visit_source_value AND s.ENCOUNTERCLASS=? AND v.visit_concept_id=0",
                [cid, source],
            )
        checks = validate_visits(con)
        if any(checks.values()):
            raise ValueError(checks)
        meta = json.loads(con.execute("SELECT metadata FROM lab12_run").fetchone()[0])
        meta["parent_run_id"] = meta["run_id"]
        meta["run_id"] = str(uuid.uuid4())
        meta["visit_migration"] = {
            "date_utc": datetime.now(timezone.utc).isoformat(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "before": before["queries"]["ceros"],
            "ohdsi_commit": "9ee6eb1b933c70af7b80711332aa92327af1f7c5",
            "source_url": "https://github.com/OHDSI/ETL-Synthea/blob/9ee6eb1b933c70af7b80711332aa92327af1f7c5/inst/sql/sql_server/cdm_version/v540/insert_visit_occurrence.sql",
        }
        meta["estado"] = "lab12_validado_listo_revision_academica_con_limitaciones"
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
        print(json.dumps(finalize(c), indent=2))
