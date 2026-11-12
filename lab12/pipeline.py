"""ETL mínimo autorizado por Lab 12. No representa un CDM completo."""

import argparse
import hashlib
import json
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def queries(con, sql_path=None):
    result = {}
    migrated = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='clinical_lineage'"
    ).fetchone()[0]
    if migrated:
        con.execute(
            "CREATE OR REPLACE TEMP VIEW lab12_clinical_lineage AS SELECT source_row,event_table,target_concept_id FROM clinical_lineage"
        )
    elif con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='condition_lineage'"
    ).fetchone()[0]:
        con.execute(
            "CREATE OR REPLACE TEMP VIEW lab12_clinical_lineage AS SELECT l.source_row,'condition_occurrence' AS event_table,c.condition_concept_id AS target_concept_id FROM condition_lineage l JOIN condition_occurrence c USING(condition_occurrence_id)"
        )
    else:
        # Referencias externas CDM no tienen las tablas internas de este ETL.
        con.execute(
            "CREATE OR REPLACE TEMP VIEW lab12_clinical_lineage AS SELECT NULL::BIGINT source_row,NULL::VARCHAR event_table,NULL::BIGINT target_concept_id WHERE FALSE"
        )
    for block in (
        (sql_path or ROOT / "sql/consultas_omop.sql")
        .read_text()
        .split("-- nombre: ")[1:]
    ):
        name, sql = block.split("\n", 1)
        cur = con.execute(sql)
        result[name.strip()] = [
            dict(zip([x[0] for x in cur.description], row)) for row in cur.fetchall()
        ]
    return result


def validate(con):
    checks = {}
    for table, pk in [
        ("person", "person_id"),
        ("visit_occurrence", "visit_occurrence_id"),
        ("condition_occurrence", "condition_occurrence_id"),
        ("observation_period", "observation_period_id"),
    ]:
        checks[table + "_pk"] = con.execute(
            f"SELECT count(*)-count(DISTINCT {pk}) FROM {table}"
        ).fetchone()[0]
        if table != "person":
            checks[table + "_person_fk"] = con.execute(
                f"SELECT count(*) FROM {table} d WHERE NOT EXISTS (SELECT 1 FROM person p WHERE p.person_id=d.person_id)"
            ).fetchone()[0]
    checks["condition_visit_fk"] = con.execute(
        "SELECT count(*) FROM condition_occurrence d WHERE visit_occurrence_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM visit_occurrence v WHERE v.visit_occurrence_id=d.visit_occurrence_id AND v.person_id=d.person_id)"
    ).fetchone()[0]
    checks["periodos_invertidos"] = con.execute(
        "SELECT count(*) FROM observation_period WHERE observation_period_start_date>observation_period_end_date"
    ).fetchone()[0]
    checks["periodos_solapados"] = con.execute(
        "SELECT count(*) FROM observation_period a JOIN observation_period b ON a.person_id=b.person_id AND a.observation_period_id<b.observation_period_id AND a.observation_period_start_date<=b.observation_period_end_date AND b.observation_period_start_date<=a.observation_period_end_date"
    ).fetchone()[0]
    checks["conceptos_condition_invalidos"] = con.execute(
        "SELECT count(*) FROM condition_occurrence d WHERE condition_concept_id<>0 AND NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=d.condition_concept_id AND c.standard_concept='S' AND c.domain_id='Condition' AND c.invalid_reason IS NULL)"
    ).fetchone()[0]
    for table, col in [
        ("person", "gender_concept_id"),
        ("visit_occurrence", "visit_concept_id"),
    ]:
        checks[table + "_concept_fk"] = con.execute(
            f"SELECT count(*) FROM {table} d WHERE {col}<>0 AND NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=d.{col})"
        ).fetchone()[0]
    checks["person_count"] = abs(
        con.execute("SELECT count(*) FROM person").fetchone()[0]
        - con.execute("SELECT count(*) FROM src_patients").fetchone()[0]
    )
    checks["visit_count"] = abs(
        con.execute("SELECT count(*) FROM visit_occurrence").fetchone()[0]
        - con.execute("SELECT count(*) FROM src_encounters").fetchone()[0]
    )
    if con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='clinical_lineage'"
    ).fetchone()[0]:
        checks["condition_reconciliation"] = con.execute(
            "SELECT count(*) FROM src_conditions s WHERE NOT EXISTS (SELECT 1 FROM clinical_lineage l WHERE l.source_row=s.source_row)"
        ).fetchone()[0]
    else:
        checks["condition_reconciliation"] = abs(
            con.execute("SELECT count(*) FROM src_conditions").fetchone()[0]
            - con.execute(
                "SELECT count(*) FROM (SELECT source_row FROM condition_lineage UNION SELECT source_row FROM rejected_domain)"
            ).fetchone()[0]
        )
    q = queries(con)
    checks["clinical_population"] = abs(
        q["personas"][0]["personas"]
        - con.execute("SELECT count(*) FROM person").fetchone()[0]
    )
    checks["clinical_window"] = int(
        q["ventana"][0]["dentro"] > q["ventana"][0]["todos"]
    )
    return checks


def build(args):
    if args.db.exists():
        raise ValueError(
            "La salida ya existe. Use otra ruta para preservar la base anterior."
        )
    for name in ["patients", "encounters", "conditions"]:
        if not (args.csv / (name + ".csv")).is_file():
            raise FileNotFoundError(name + ".csv")
    if not args.vocab and not args.allow_unmapped:
        raise ValueError(
            "Falta --vocab; use --allow-unmapped solo para auditoría provisional."
        )
    args.db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(args.db))
    con.execute("SET threads=4")
    con.execute("BEGIN")
    for name in ["patients", "encounters", "conditions"]:
        con.execute(
            f"CREATE TABLE src_{name} AS SELECT row_number() OVER () AS source_row,* FROM read_csv(?,all_varchar=true)",
            [str(args.csv / (name + ".csv"))],
        )
    schemas = {
        "concept": "concept_id BIGINT,concept_name VARCHAR,domain_id VARCHAR,vocabulary_id VARCHAR,concept_class_id VARCHAR,standard_concept VARCHAR,concept_code VARCHAR,valid_start_date DATE,valid_end_date DATE,invalid_reason VARCHAR",
        "concept_relationship": "concept_id_1 BIGINT,concept_id_2 BIGINT,relationship_id VARCHAR,valid_start_date DATE,valid_end_date DATE,invalid_reason VARCHAR",
        "concept_ancestor": "ancestor_concept_id BIGINT,descendant_concept_id BIGINT,min_levels_of_separation INTEGER,max_levels_of_separation INTEGER",
    }
    for table, schema in schemas.items():
        con.execute(f"CREATE TABLE {table} ({schema})")
        if args.vocab:
            file = args.vocab / (table.upper() + ".csv")
            overrides = (
                ",types={'concept_code':'VARCHAR'}" if table == "concept" else ""
            )
            con.execute(
                f"INSERT INTO {table} BY NAME SELECT * FROM read_csv(?,delim='\t',header=true,dateformat='%Y%m%d'{overrides})",
                [str(file)],
            )
    if args.vocab:
        present = {
            r[0]
            for r in con.execute(
                "SELECT DISTINCT vocabulary_id FROM concept"
            ).fetchall()
        }
        if not {"SNOMED", "ICD10CM", "RxNorm", "LOINC", "ATC"} <= present:
            raise ValueError(
                "La descarga no incluye los cinco vocabularios requeridos."
            )
    if con.execute(
        "SELECT count(*)-count(DISTINCT concept_id) FROM concept"
    ).fetchone()[0]:
        raise ValueError("concept_id duplicado")
    auxiliary = []
    if args.vocab:
        for table in [
            "vocabulary",
            "domain",
            "relationship",
            "concept_class",
            "concept_synonym",
            "drug_strength",
            "pack_content",
            "concept_metadata",
            "concept_relationship_metadata",
        ]:
            path = args.vocab / (table.upper() + ".csv")
            if path.is_file():
                con.execute(
                    f"CREATE TABLE {table} AS SELECT * FROM read_csv(?,delim='\t',header=true,all_varchar=true,null_padding=true)",
                    [str(path)],
                )
                auxiliary.append(table)
        for table, columns in [
            ("concept_relationship", ["concept_id_1", "concept_id_2"]),
            ("concept_ancestor", ["ancestor_concept_id", "descendant_concept_id"]),
        ]:
            for column in columns:
                missing = con.execute(
                    f"SELECT count(*) FROM {table} r WHERE NOT EXISTS (SELECT 1 FROM concept c WHERE c.concept_id=r.{column})"
                ).fetchone()[0]
                if missing:
                    raise ValueError(
                        f"Dependencias ausentes: {table}.{column}: {missing}"
                    )
    # No se inventan conceptos: sin vocabulario, incluso sexo y tipos quedan en cero.
    con.execute(
        "CREATE MACRO cid(code) AS (SELECT coalesce(max(concept_id),0) FROM concept WHERE vocabulary_id='Gender' AND concept_code=code AND standard_concept='S' AND invalid_reason IS NULL)"
    )
    con.execute(
        "CREATE TABLE person AS SELECT row_number() OVER(ORDER BY Id)::BIGINT person_id,cid(CASE GENDER WHEN 'M' THEN 'M' WHEN 'F' THEN 'F' END)::INTEGER gender_concept_id,year(CAST(BIRTHDATE AS DATE))::INTEGER year_of_birth,month(CAST(BIRTHDATE AS DATE))::INTEGER month_of_birth,day(CAST(BIRTHDATE AS DATE))::INTEGER day_of_birth,CAST(BIRTHDATE AS TIMESTAMP) birth_datetime,0::INTEGER race_concept_id,0::INTEGER ethnicity_concept_id,NULL::BIGINT location_id,NULL::BIGINT provider_id,NULL::BIGINT care_site_id,Id person_source_value,GENDER gender_source_value,0::INTEGER gender_source_concept_id,RACE race_source_value,0::INTEGER race_source_concept_id,ETHNICITY ethnicity_source_value,0::INTEGER ethnicity_source_concept_id FROM src_patients"
    )
    con.execute(
        "CREATE TABLE visit_occurrence AS SELECT row_number() OVER(ORDER BY e.Id)::BIGINT visit_occurrence_id,p.person_id,coalesce(c.concept_id,0)::INTEGER visit_concept_id,CAST(e.START AS DATE) visit_start_date,CAST(e.START AS TIMESTAMP) visit_start_datetime,CAST(coalesce(e.STOP,e.START) AS DATE) visit_end_date,CAST(coalesce(e.STOP,e.START) AS TIMESTAMP) visit_end_datetime,0::INTEGER visit_type_concept_id,NULL::BIGINT provider_id,NULL::BIGINT care_site_id,e.Id visit_source_value,0::INTEGER visit_source_concept_id,0::INTEGER admitted_from_concept_id,NULL::VARCHAR admitted_from_source_value,0::INTEGER discharged_to_concept_id,NULL::VARCHAR discharged_to_source_value,NULL::BIGINT preceding_visit_occurrence_id FROM src_encounters e JOIN person p ON p.person_source_value=e.PATIENT LEFT JOIN concept c ON c.vocabulary_id='Visit' AND c.concept_code=CASE e.ENCOUNTERCLASS WHEN 'inpatient' THEN 'IP' WHEN 'emergency' THEN 'ER' WHEN 'ambulatory' THEN 'OP' WHEN 'outpatient' THEN 'OP' WHEN 'wellness' THEN 'OP' END AND c.standard_concept='S' AND c.invalid_reason IS NULL"
    )
    # Fenotipo por mapeo vigente; se preservan mapeos múltiples y se rechazan otros dominios.
    con.execute(
        "CREATE TABLE mapping AS SELECT DISTINCT s.concept_code,s.concept_id source_id,t.concept_id target_id,t.domain_id FROM concept s JOIN concept_relationship r ON r.concept_id_1=s.concept_id AND r.relationship_id='Maps to' AND r.invalid_reason IS NULL JOIN concept t ON t.concept_id=r.concept_id_2 AND t.standard_concept='S' AND t.invalid_reason IS NULL WHERE s.vocabulary_id='SNOMED' AND s.invalid_reason IS NULL"
    )
    con.execute(
        "CREATE TABLE mapped AS SELECT s.*,p.person_id,v.visit_occurrence_id,coalesce(m.source_id,sc.concept_id) source_id,m.target_id,m.domain_id FROM src_conditions s JOIN person p ON p.person_source_value=s.PATIENT LEFT JOIN visit_occurrence v ON v.visit_source_value=s.ENCOUNTER LEFT JOIN mapping m ON m.concept_code=s.CODE LEFT JOIN concept sc ON sc.vocabulary_id='SNOMED' AND sc.concept_code=s.CODE AND sc.invalid_reason IS NULL"
    )
    con.execute(
        "CREATE TABLE rejected_domain AS SELECT * FROM mapped WHERE domain_id IS NOT NULL AND domain_id<>'Condition'"
    )
    con.execute(
        "CREATE TABLE condition_lineage AS SELECT row_number() OVER(ORDER BY source_row,target_id)::BIGINT condition_occurrence_id,source_row FROM mapped WHERE domain_id='Condition' OR domain_id IS NULL"
    )
    con.execute(
        "CREATE TABLE condition_occurrence AS SELECT row_number() OVER(ORDER BY source_row,target_id)::BIGINT condition_occurrence_id,person_id,coalesce(target_id,0)::INTEGER condition_concept_id,CAST(START AS DATE) condition_start_date,CAST(START AS TIMESTAMP) condition_start_datetime,CAST(STOP AS DATE) condition_end_date,CAST(STOP AS TIMESTAMP) condition_end_datetime,0::INTEGER condition_type_concept_id,0::INTEGER condition_status_concept_id,NULL::VARCHAR stop_reason,NULL::BIGINT provider_id,visit_occurrence_id,NULL::BIGINT visit_detail_id,CODE condition_source_value,coalesce(source_id,0)::INTEGER condition_source_concept_id,NULL::VARCHAR condition_status_source_value FROM mapped WHERE domain_id='Condition' OR domain_id IS NULL"
    )
    con.execute(
        "CREATE TABLE observation_period AS SELECT row_number() OVER(ORDER BY person_id)::BIGINT observation_period_id,person_id,min(visit_start_date) observation_period_start_date,max(visit_end_date) observation_period_end_date,0::INTEGER period_type_concept_id FROM visit_occurrence GROUP BY person_id"
    )
    checks = validate(con)
    if any(checks.values()):
        raise ValueError(checks)
    con.execute("COMMIT")
    counts = {
        t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        for t in [
            "person",
            "visit_occurrence",
            "condition_occurrence",
            "observation_period",
            "concept",
            "concept_relationship",
            "concept_ancestor",
            "rejected_domain",
        ]
    }
    source = {}
    for name in ["patients", "encounters", "conditions"]:
        path = args.csv / (name + ".csv")
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        source[name] = {
            "sha256": h.hexdigest(),
            "bytes": path.stat().st_size,
            "rows": con.execute(f"SELECT count(*) FROM src_{name}").fetchone()[0],
        }
    missing = con.execute(
        "SELECT count(*) FILTER(WHERE CODE IS NULL OR trim(CODE)='') missing_code,count(*) FILTER(WHERE PATIENT IS NULL) missing_patient FROM src_conditions"
    ).fetchone()
    metadata = {
        "run_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "estado": "provisional_sin_vocabulario"
        if not args.vocab
        else "con_vocabulario_pendiente_revision",
        "python": platform.python_version(),
        "duckdb": duckdb.__version__,
        "source": source,
        "vocab_files": {},
        "auxiliary_tables": auxiliary,
    }
    if args.vocab:
        for name in [*schemas, *auxiliary]:
            path = args.vocab / (name.upper() + ".csv")
            h = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            metadata["vocab_files"][name] = {
                "sha256": h.hexdigest(),
                "bytes": path.stat().st_size,
            }
        manifest = args.vocab / "manifest.json"
        if manifest.is_file():
            metadata["athena_packages"] = json.loads(manifest.read_text())
    con.execute("CREATE TABLE lab12_run (metadata VARCHAR)")
    con.execute("INSERT INTO lab12_run VALUES (?)", [json.dumps(metadata)])
    payload = snapshot(con)
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    con.close()
    print(json.dumps({"counts": counts, "validation": checks}, indent=2))


def snapshot(con):
    """Recalcula todos los agregados desde esta base, nunca desde JSON anterior."""
    rows = con.execute("SELECT metadata FROM lab12_run").fetchall()
    if len(rows) != 1:
        raise ValueError("Se exige una ejecución identificable en lab12_run")
    metadata = json.loads(rows[0][0])
    counts = {
        t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        for t in [
            "person",
            "visit_occurrence",
            "condition_occurrence",
            "observation_period",
            "concept",
            "concept_relationship",
            "concept_ancestor",
            "rejected_domain",
        ]
    }
    migrated = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name='clinical_lineage'"
    ).fetchone()[0]
    if migrated:
        for t in ["observation", "measurement"]:
            counts[t] = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    if bool(counts["concept"]) != bool(metadata["vocab_files"]):
        raise ValueError(
            "Vocabulario y manifiesto no coinciden; reconstruya una base nueva."
        )
    missing = con.execute(
        "SELECT count(*) FILTER(WHERE CODE IS NULL OR trim(CODE)=''),count(*) FILTER(WHERE PATIENT IS NULL) FROM src_conditions"
    ).fetchone()
    sql_hashes = {
        name: hashlib.sha256((ROOT / "sql" / name).read_bytes()).hexdigest()
        for name in ["consultas_omop.sql", "calidad_vocabularios.sql"]
    }
    checks = validate(con)
    q = queries(con)
    corrections = {}
    if migrated:
        from corregir_dominios import validate_migration

        checks.update(validate_migration(con))
        corrections = queries(con, ROOT / "sql/consultas_ampliadas.sql")
        q["ceros"] += corrections["ceros_nuevos"]
        sql_hashes["consultas_ampliadas.sql"] = hashlib.sha256(
            (ROOT / "sql/consultas_ampliadas.sql").read_bytes()
        ).hexdigest()
    final_audit = {}
    if metadata.get("visit_migration"):
        from finalizar_visitas import validate_visits
        from integridad_auxiliar import audit

        checks.update(validate_visits(con))
        final_audit = queries(con, ROOT / "sql/auditoria_final.sql")
        final_audit["auxiliary_integrity"] = audit(con)
        for row in (
            final_audit["temporalidad"]
            + final_audit["duplicados_y_traza"]
            + final_audit["diccionarios"]
            + final_audit["auxiliary_integrity"]
        ):
            checks[row["control"]] = row["discrepancias"]
        sql_hashes["auditoria_final.sql"] = hashlib.sha256(
            (ROOT / "sql/auditoria_final.sql").read_bytes()
        ).hexdigest()
    return {
        **metadata,
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "sql_sha256": sql_hashes,
        "counts": counts,
        "missing_source": {
            "condition_code": missing[0],
            "condition_patient": missing[1],
        },
        "validation": checks,
        "mapping_audit": queries(con, ROOT / "sql/calidad_vocabularios.sql"),
        "corrections": corrections,
        "final_audit": final_audit,
        "queries": q,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--db", type=Path, default=ROOT / "local/omop.duckdb")
    p.add_argument("--vocab", type=Path)
    p.add_argument("--allow-unmapped", action="store_true")
    p.add_argument("--results", type=Path, default=ROOT / "resultados/resultados.json")
    build(p.parse_args())
