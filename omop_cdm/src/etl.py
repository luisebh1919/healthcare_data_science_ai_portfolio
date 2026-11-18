"""Synthea CSV → OMOP 5.4 en una salida nueva. No modifica fuentes ni bases existentes."""

import argparse
import hashlib
import json
import os
import shutil
from datetime import date
from pathlib import Path

import duckdb
from schema import ROOT, VENDOR, create_schema, fields, validate_schema

VOCAB_TABLES = [
    "concept",
    "vocabulary",
    "domain",
    "concept_class",
    "relationship",
    "concept_relationship",
    "concept_ancestor",
    "concept_synonym",
    "drug_strength",
]
EVENT_FILES = [
    "conditions",
    "medications",
    "observations",
    "procedures",
    "immunizations",
    "devices",
]
DOMAINS = {
    "Condition": ("condition_occurrence", "condition_occurrence_id", "condition"),
    "Drug": ("drug_exposure", "drug_exposure_id", "drug"),
    "Measurement": ("measurement", "measurement_id", "measurement"),
    "Observation": ("observation", "observation_id", "observation"),
    "Procedure": ("procedure_occurrence", "procedure_occurrence_id", "procedure"),
    "Device": ("device_exposure", "device_exposure_id", "device"),
}
VISIT_CODES = {
    "inpatient": "IP",
    "emergency": "ER",
    "urgentcare": "ER",
    "ambulatory": "OP",
    "outpatient": "OP",
    "wellness": "OP",
    "home": "OMOP4822459",
    "virtual": "OMOP5556618",
    "snf": "LTCP",
}


def lit(value):
    return "'" + str(value).replace("'", "''") + "'"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def insert(con, table, expressions, relation):
    cols = ",".join(expressions)
    con.execute(
        f"INSERT INTO omop.{table} ({cols}) SELECT {','.join(expressions.values())} FROM {relation}"
    )


def csv_view(con, name, path):
    # Una sola hebra y preserve_insertion_order mantienen la fila física de CSV.
    con.execute(
        f"CREATE OR REPLACE TEMP VIEW {name} AS SELECT row_number() OVER () source_row,* "
        f"FROM read_csv({lit(path)},header=true,all_varchar=true,parallel=false)"
    )


def load_vocab(con, packages):
    for table in VOCAB_TABLES:
        paths = [
            p
            for folder in packages
            for p in folder.iterdir()
            if p.name.lower() == table + ".csv"
        ]
        if not paths:
            raise ValueError("Falta tabla oficial de vocabulario: " + table)
        selects = []
        for name, typ, *_ in con.execute(f"DESCRIBE omop.{table}").fetchall():
            if typ == "DATE":
                selects.append(
                    f"coalesce(try_strptime({name},'%Y%m%d')::DATE,try_cast({name} AS DATE)) AS {name}"
                )
            else:
                selects.append(f"CAST({name} AS {typ}) AS {name}")
        union = " UNION ALL ".join(
            f"SELECT {','.join(selects)} FROM read_csv({lit(p)},"
            "header=true,delim='\t',all_varchar=true)"
            for p in paths
        )
        con.execute(f"INSERT INTO omop.{table} SELECT DISTINCT * FROM ({union})")
        # Se consolida solo igualdad de filas; conflictos de claves se detienen.
        keys = {
            "concept": "concept_id",
            "vocabulary": "vocabulary_id",
            "domain": "domain_id",
            "concept_class": "concept_class_id",
            "relationship": "relationship_id",
            "concept_relationship": "concept_id_1,concept_id_2,relationship_id",
            "concept_ancestor": "ancestor_concept_id,descendant_concept_id",
        }.get(table)
        if (
            keys
            and con.execute(
                f"SELECT count(*) FROM (SELECT {keys} FROM omop.{table} GROUP BY ALL HAVING count(*)>1)"
            ).fetchone()[0]
        ):
            raise ValueError("Paquetes contradictorios en " + table)


def concept(con, vocabulary, code, domain, as_of):
    rows = con.execute(
        "SELECT concept_id FROM omop.concept WHERE vocabulary_id=? AND concept_code=? "
        "AND domain_id=? AND standard_concept='S' AND invalid_reason IS NULL "
        "AND ? BETWEEN valid_start_date AND valid_end_date",
        [vocabulary, code, domain, as_of],
    ).fetchall()
    if len(rows) > 1:
        raise ValueError("Concepto ambiguo: " + vocabulary + "/" + code)
    return rows[0][0] if rows else 0


def setup_audit(con):
    con.execute(
        "CREATE TABLE etl.lineage(source_file VARCHAR,source_row BIGINT,target_table VARCHAR,"
        "target_id INTEGER,source_code VARCHAR,source_description VARCHAR,source_value VARCHAR,"
        "source_unit VARCHAR,source_start VARCHAR,source_end VARCHAR,source_patient VARCHAR,"
        "source_encounter VARCHAR,source_concept_id INTEGER,target_concept_id INTEGER,reason VARCHAR)"
    )
    con.execute(
        "CREATE TABLE etl.source_counts(source_file VARCHAR,source_rows BIGINT,status VARCHAR)"
    )
    con.execute(
        "CREATE TABLE etl.rejected(source_file VARCHAR,source_row BIGINT,reason VARCHAR,payload JSON)"
    )


def demographics(con, csv_dir, as_of):
    csv_view(con, "src_patients", csv_dir / "patients.csv")
    gender = (
        "CASE GENDER "
        + " ".join(
            f"WHEN {lit(x)} THEN {concept(con, 'Gender', x, 'Gender', as_of)}"
            for x in ["M", "F"]
        )
        + " ELSE 0 END"
    )
    insert(
        con,
        "person",
        {
            "person_id": "row_number() OVER(ORDER BY Id)",
            "gender_concept_id": gender,
            "year_of_birth": "year(CAST(BIRTHDATE AS DATE))",
            "month_of_birth": "month(CAST(BIRTHDATE AS DATE))",
            "day_of_birth": "day(CAST(BIRTHDATE AS DATE))",
            "birth_datetime": "CAST(BIRTHDATE AS TIMESTAMP)",
            "race_concept_id": "0",
            "ethnicity_concept_id": "0",
            "person_source_value": "Id",
            "gender_source_value": "GENDER",
            "gender_source_concept_id": gender,
            "race_source_value": "RACE",
            "ethnicity_source_value": "ETHNICITY",
        },
        "src_patients",
    )
    con.execute(
        "INSERT INTO etl.source_counts SELECT 'patients',count(*),'loaded' FROM src_patients"
    )
    insert(
        con,
        "death",
        {
            "person_id": "p.person_id",
            "death_date": "CAST(s.DEATHDATE AS DATE)",
            "death_datetime": "CAST(s.DEATHDATE AS TIMESTAMP)",
        },
        "src_patients s JOIN omop.person p ON p.person_source_value=s.Id WHERE s.DEATHDATE IS NOT NULL",
    )
    # Organización/proveedor se conservan sin asignar especialidades por texto libre.
    if (csv_dir / "organizations.csv").exists():
        csv_view(con, "src_organizations", csv_dir / "organizations.csv")
        insert(
            con,
            "care_site",
            {
                "care_site_id": "row_number() OVER(ORDER BY Id)",
                "care_site_name": "NAME",
                "care_site_source_value": "Id",
            },
            "src_organizations",
        )
        con.execute(
            "INSERT INTO etl.source_counts SELECT 'organizations',count(*),'loaded' FROM src_organizations"
        )
    if (csv_dir / "providers.csv").exists():
        csv_view(con, "src_providers", csv_dir / "providers.csv")
        insert(
            con,
            "provider",
            {
                "provider_id": "row_number() OVER(ORDER BY s.Id)",
                "provider_name": "s.NAME",
                "provider_source_value": "s.Id",
                "specialty_source_value": "s.SPECIALITY",
                "gender_source_value": "s.GENDER",
                "care_site_id": "cs.care_site_id",
            },
            "src_providers s LEFT JOIN omop.care_site cs ON cs.care_site_source_value=s.ORGANIZATION",
        )
        con.execute(
            "INSERT INTO etl.source_counts SELECT 'providers',count(*),'loaded' FROM src_providers"
        )


def visits(con, csv_dir, as_of):
    csv_view(con, "src_encounters", csv_dir / "encounters.csv")
    codes = (
        "CASE e.ENCOUNTERCLASS "
        + " ".join(
            f"WHEN {lit(k)} THEN {concept(con, 'Visit', v, 'Visit', as_of)}"
            for k, v in VISIT_CODES.items()
        )
        + " ELSE 0 END"
    )
    visit_type = concept(con, "Type Concept", "OMOP4976900", "Type Concept", as_of)
    # No se imputa el alta de visitas sin STOP. Quedan en cuarentena explícita.
    con.execute(
        "INSERT INTO etl.rejected SELECT 'encounters',e.source_row,CASE WHEN p.person_id IS NULL "
        "THEN 'missing_patient' ELSE 'missing_or_invalid_date' END,to_json(e) FROM src_encounters e "
        "LEFT JOIN omop.person p ON p.person_source_value=e.PATIENT WHERE p.person_id IS NULL "
        "OR try_cast(e.START AS TIMESTAMP) IS NULL OR try_cast(e.STOP AS TIMESTAMP) IS NULL "
        "OR CAST(e.STOP AS TIMESTAMP)<CAST(e.START AS TIMESTAMP)"
    )
    insert(
        con,
        "visit_occurrence",
        {
            "visit_occurrence_id": "row_number() OVER(ORDER BY CAST(e.START AS TIMESTAMP),e.Id)",
            "person_id": "p.person_id",
            "visit_concept_id": codes,
            "visit_start_date": "CAST(e.START AS DATE)",
            "visit_start_datetime": "CAST(e.START AS TIMESTAMP)",
            "visit_end_date": "CAST(e.STOP AS DATE)",
            "visit_end_datetime": "CAST(e.STOP AS TIMESTAMP)",
            "visit_type_concept_id": str(visit_type),
            "visit_source_value": "e.Id",
            "care_site_id": "cs.care_site_id",
            "provider_id": "pr.provider_id",
        },
        "src_encounters e JOIN omop.person p ON p.person_source_value=e.PATIENT "
        "LEFT JOIN omop.care_site cs ON cs.care_site_source_value=e.ORGANIZATION "
        "LEFT JOIN omop.provider pr ON pr.provider_source_value=e.PROVIDER "
        "WHERE NOT EXISTS(SELECT 1 FROM etl.rejected r WHERE r.source_file='encounters' AND r.source_row=e.source_row)",
    )
    con.execute(
        "UPDATE omop.visit_occurrence v SET preceding_visit_occurrence_id=t.prev FROM "
        "(SELECT visit_occurrence_id,lag(visit_occurrence_id) OVER(PARTITION BY person_id "
        "ORDER BY visit_start_datetime,visit_occurrence_id) prev FROM omop.visit_occurrence) t "
        "WHERE t.visit_occurrence_id=v.visit_occurrence_id"
    )
    con.execute(
        "INSERT INTO etl.source_counts SELECT 'encounters',count(*),'loaded_or_rejected' FROM src_encounters"
    )
    period_type = concept(con, "Type Concept", "OMOP4976955", "Type Concept", as_of)
    insert(
        con,
        "observation_period",
        {
            "observation_period_id": "row_number() OVER(ORDER BY person_id)",
            "person_id": "person_id",
            "observation_period_start_date": "min(visit_start_date)",
            "observation_period_end_date": "max(visit_end_date)",
            "period_type_concept_id": str(period_type),
        },
        "omop.visit_occurrence GROUP BY person_id",
    )


def normalize_events(con, name, path):
    csv_view(con, "src_event", path)
    cols = {x[0].upper() for x in con.execute("DESCRIBE src_event").fetchall()}
    start = "DATE" if "DATE" in cols else "START"
    stop = "STOP" if "STOP" in cols else "NULL"
    system = (
        "CASE lower(SYSTEM) WHEN 'snomed-ct' THEN 'SNOMED' WHEN 'snomed' THEN 'SNOMED' "
        "WHEN 'http://snomed.info/sct' THEN 'SNOMED' WHEN 'rxnorm' THEN 'RxNorm' "
        "WHEN 'http://www.nlm.nih.gov/research/umls/rxnorm' THEN 'RxNorm' "
        "WHEN 'loinc' THEN 'LOINC' WHEN 'http://loinc.org' THEN 'LOINC' "
        "WHEN 'cvx' THEN 'CVX' ELSE SYSTEM END"
        if "SYSTEM" in cols
        else lit(
            {
                "medications": "RxNorm",
                "observations": "LOINC",
                "immunizations": "CVX",
            }.get(name, "SNOMED")
        )
    )
    value = "VALUE" if "VALUE" in cols else "NULL::VARCHAR"
    unit = "UNITS" if "UNITS" in cols else "NULL::VARCHAR"
    fallback = lit(
        {
            "conditions": "Condition",
            "medications": "Drug",
            "procedures": "Procedure",
            "immunizations": "Drug",
            "devices": "Device",
        }.get(name, "Observation")
    )
    if name == "observations":
        fallback = "CASE WHEN TYPE='numeric' THEN 'Measurement' ELSE 'Observation' END"
    con.execute(
        "CREATE OR REPLACE TEMP TABLE normalized AS SELECT source_row,PATIENT,ENCOUNTER,CODE,DESCRIPTION,"
        f"{system} vocabulary_id,{start} start_value,{stop} end_value,{value} AS event_value,{unit} AS event_unit,"
        f"{fallback} fallback_domain,to_json(src_event) payload FROM src_event"
    )


def map_events(con, as_of):
    con.execute(
        "CREATE OR REPLACE TEMP TABLE mappings AS SELECT DISTINCT s.concept_code,s.vocabulary_id,"
        "s.concept_id source_id,t.concept_id target_id,t.domain_id FROM "
        "(SELECT DISTINCT vocabulary_id,CODE FROM normalized) n "
        "JOIN omop.concept s ON s.vocabulary_id=n.vocabulary_id AND s.concept_code=n.CODE "
        "JOIN omop.concept_relationship r ON r.concept_id_1=s.concept_id AND r.relationship_id='Maps to' "
        f"AND r.invalid_reason IS NULL AND {lit(as_of)}::DATE BETWEEN r.valid_start_date AND r.valid_end_date "
        "JOIN omop.concept t ON t.concept_id=r.concept_id_2 AND t.standard_concept='S' AND t.invalid_reason IS NULL "
        f"AND {lit(as_of)}::DATE BETWEEN t.valid_start_date AND t.valid_end_date"
    )
    # Los conceptos estándar pueden ser su propio destino aun sin una relación reflexiva exportada.
    con.execute(
        "INSERT INTO mappings SELECT DISTINCT s.concept_code,s.vocabulary_id,s.concept_id,s.concept_id,s.domain_id "
        "FROM (SELECT DISTINCT vocabulary_id,CODE FROM normalized) n JOIN omop.concept s "
        "ON s.vocabulary_id=n.vocabulary_id AND s.concept_code=n.CODE AND s.standard_concept='S' AND s.invalid_reason IS NULL "
        f"AND {lit(as_of)}::DATE BETWEEN s.valid_start_date AND s.valid_end_date "
        "WHERE NOT EXISTS(SELECT 1 FROM mappings m WHERE m.source_id=s.concept_id)"
    )
    # La misma cadena puede tener varias versiones fuente; no multiplicar conceptos no mapeados.
    con.execute(
        "CREATE OR REPLACE TEMP TABLE source_codes AS SELECT vocabulary_id,concept_code,"
        "CASE WHEN count(*)=1 THEN min(concept_id) ELSE 0 END source_id "
        "FROM omop.concept WHERE (vocabulary_id,concept_code) IN "
        "(SELECT vocabulary_id,CODE FROM normalized) GROUP BY ALL"
    )
    con.execute(
        "CREATE OR REPLACE TEMP TABLE mapped AS SELECT n.*,p.person_id,v.visit_occurrence_id,"
        "coalesce(m.source_id,sc.source_id,0)::INTEGER source_id,coalesce(m.target_id,0)::INTEGER target_id,"
        "coalesce(m.domain_id,n.fallback_domain) domain_id,"
        "CASE WHEN m.target_id IS NOT NULL THEN 'mapped' WHEN sc.source_id IS NULL THEN 'source_code_absent' "
        "WHEN sc.source_id=0 THEN 'ambiguous_source_code' ELSE 'no_valid_standard_mapping' END mapping_reason "
        "FROM normalized n LEFT JOIN omop.person p ON p.person_source_value=n.PATIENT "
        "LEFT JOIN omop.visit_occurrence v ON v.visit_source_value=n.ENCOUNTER AND v.person_id=p.person_id "
        "LEFT JOIN mappings m ON m.vocabulary_id=n.vocabulary_id AND m.concept_code=n.CODE "
        "LEFT JOIN source_codes sc ON sc.vocabulary_id=n.vocabulary_id AND sc.concept_code=n.CODE"
    )


def clinical_events(con, name, csv_dir, as_of):
    normalize_events(con, name, csv_dir / (name + ".csv"))
    map_events(con, as_of)
    con.execute(
        f"INSERT INTO etl.source_counts SELECT {lit(name)},count(*),'loaded_or_rejected' FROM normalized"
    )
    # Detener la ambigüedad clínica en vez de inventar un destino fuera del dominio oficial.
    con.execute(
        f"INSERT INTO etl.rejected SELECT DISTINCT {lit(name)},source_row,"
        "CASE WHEN person_id IS NULL THEN 'missing_patient' WHEN try_cast(start_value AS TIMESTAMP) IS NULL "
        "THEN 'invalid_start' WHEN end_value IS NOT NULL AND try_cast(end_value AS TIMESTAMP) IS NULL "
        "THEN 'invalid_end' WHEN CAST(end_value AS TIMESTAMP)<CAST(start_value AS TIMESTAMP) THEN 'inverted_dates' "
        "WHEN ENCOUNTER IS NOT NULL AND visit_occurrence_id IS NULL THEN 'missing_or_wrong_patient_visit' "
        f"ELSE 'unsupported_target_domain:'||domain_id END,payload FROM mapped WHERE person_id IS NULL "
        "OR try_cast(start_value AS TIMESTAMP) IS NULL OR (end_value IS NOT NULL AND try_cast(end_value AS TIMESTAMP) IS NULL) "
        "OR try_cast(end_value AS TIMESTAMP)<try_cast(start_value AS TIMESTAMP) "
        "OR (ENCOUNTER IS NOT NULL AND visit_occurrence_id IS NULL) "
        f"OR domain_id NOT IN ({','.join(lit(d) for d in DOMAINS)})"
    )
    ehr = concept(con, "Type Concept", "OMOP4976890", "Type Concept", as_of)
    for domain, (table, pk, prefix) in DOMAINS.items():
        offset = con.execute(
            f"SELECT coalesce(max({pk}),0) FROM omop.{table}"
        ).fetchone()[0]
        con.execute(
            "CREATE OR REPLACE TEMP TABLE selected AS SELECT row_number() OVER(ORDER BY source_row,target_id)+"
            f"{offset} event_id,* FROM mapped m WHERE domain_id={lit(domain)} "
            f"AND NOT EXISTS(SELECT 1 FROM etl.rejected r WHERE r.source_file={lit(name)} AND r.source_row=m.source_row)"
        )
        expr = {
            pk: "event_id",
            "person_id": "person_id",
            prefix + "_concept_id": "target_id",
            prefix + "_type_concept_id": str(ehr),
            prefix + "_source_value": "CODE",
            prefix + "_source_concept_id": "source_id",
            "visit_occurrence_id": "visit_occurrence_id",
        }
        dt = "CAST(start_value AS TIMESTAMP)"
        end = "CAST(end_value AS TIMESTAMP)"
        if domain in ["Condition", "Drug", "Device"]:
            stem = {
                "Condition": "condition",
                "Drug": "drug_exposure",
                "Device": "device_exposure",
            }[domain]
            expr.update(
                {
                    stem + "_start_date": f"{dt}::DATE",
                    stem + "_start_datetime": dt,
                    stem + "_end_date": f"{end}::DATE",
                    stem + "_end_datetime": end,
                }
            )
            if domain == "Drug":
                # Convention ETL-Synthea: fin sin STOP = inicio, explicitado en linaje.
                expr["drug_exposure_end_date"] = f"coalesce({end},{dt})::DATE"
                expr["drug_exposure_end_datetime"] = f"coalesce({end},{dt})"
                expr["verbatim_end_date"] = f"{end}::DATE"
        else:
            expr.update({prefix + "_date": f"{dt}::DATE", prefix + "_datetime": dt})
            if domain == "Procedure":
                expr.update(
                    {
                        "procedure_end_date": f"{end}::DATE",
                        "procedure_end_datetime": end,
                    }
                )
            else:
                expr.update(
                    {
                        "value_as_number": "try_cast(event_value AS DOUBLE)",
                        "value_source_value": "event_value",
                        "unit_source_value": "event_unit",
                        "unit_concept_id": "coalesce((SELECT min(c.concept_id) FROM omop.concept c WHERE c.vocabulary_id='UCUM' AND c.concept_code=event_unit AND c.domain_id='Unit' AND c.standard_concept='S' AND c.invalid_reason IS NULL HAVING count(*)=1),0)",
                    }
                )
                if domain == "Observation":
                    expr["value_as_string"] = (
                        "CASE WHEN try_cast(event_value AS DOUBLE) IS NULL THEN event_value END"
                    )
        insert(con, table, expr, "selected")
        con.execute(
            f"INSERT INTO etl.lineage SELECT {lit(name)},source_row,{lit(table)},event_id,CODE,DESCRIPTION,event_value,event_unit,"
            "start_value,end_value,PATIENT,ENCOUNTER,source_id,target_id,mapping_reason FROM selected"
        )
    con.execute(
        "DROP TABLE normalized; DROP TABLE mapped; DROP TABLE mappings; DROP TABLE source_codes; DROP TABLE selected"
    )


def validate(con):
    result = {
        "schema": validate_schema(con),
        "errors": {},
        "warnings": {},
        "counts": {},
        "reconciliation": [],
    }
    for table in sorted({r["cdmTableName"].lower() for r in fields()}):
        result["counts"][table] = con.execute(
            f"SELECT count(*) FROM omop.{table}"
        ).fetchone()[0]
    for r in fields():
        t = r["cdmTableName"].lower()
        col = r["cdmFieldName"].lower()
        key = f"{t}.{col}"
        q = f"omop.{t}"
        if r["isPrimaryKey"] == "Yes":
            result["errors"][key + ".unique"] = con.execute(
                f'SELECT count(*)-count(DISTINCT "{col}") FROM {q}'
            ).fetchone()[0]
        if r["isForeignKey"] == "Yes" and r["fkTableName"] not in ["NA", ""]:
            ft = r["fkTableName"].lower()
            fc = r["fkFieldName"].lower()
            result["errors"][key + ".fk"] = con.execute(
                f'SELECT count(*) FROM {q} s WHERE "{col}" IS NOT NULL '
                f'AND NOT EXISTS(SELECT 1 FROM omop.{ft} f WHERE f."{fc}"=s."{col}")'
            ).fetchone()[0]
        if r["cdmDatatype"].startswith("varchar") and "MAX" not in r["cdmDatatype"]:
            length = int(r["cdmDatatype"].split("(")[1].split(")")[0])
            result["warnings"][key + ".length"] = con.execute(
                f'SELECT count(*) FROM {q} WHERE length("{col}")>{length}'
            ).fetchone()[0]
    for domain, (table, pk, prefix) in DOMAINS.items():
        result["errors"][table + ".standard_domain"] = con.execute(
            f"SELECT count(*) FROM omop.{table} e "
            f"WHERE {prefix}_concept_id<>0 AND NOT EXISTS(SELECT 1 FROM omop.concept c "
            f"WHERE c.concept_id=e.{prefix}_concept_id AND c.domain_id={lit(domain)} "
            "AND c.standard_concept='S' AND c.invalid_reason IS NULL)"
        ).fetchone()[0]
        result["errors"][table + ".visit_patient"] = con.execute(
            f"SELECT count(*) FROM omop.{table} e JOIN omop.visit_occurrence v "
            "USING(visit_occurrence_id) WHERE e.person_id<>v.person_id"
        ).fetchone()[0]
        start = (
            prefix + "_date"
            if domain in ["Measurement", "Observation", "Procedure"]
            else {
                "Condition": "condition",
                "Drug": "drug_exposure",
                "Device": "device_exposure",
            }[domain]
            + "_start_date"
        )
        result["warnings"][table + ".outside_visit"] = con.execute(
            f"SELECT count(*) FROM omop.{table} e JOIN omop.visit_occurrence v "
            f"USING(visit_occurrence_id) WHERE e.{start}<v.visit_start_date OR e.{start}>v.visit_end_date"
        ).fetchone()[0]
        result["warnings"][table + ".before_birth"] = con.execute(
            f"SELECT count(*) FROM omop.{table} e JOIN omop.person p "
            f"USING(person_id) WHERE e.{start}<CAST(p.birth_datetime AS DATE)"
        ).fetchone()[0]
        result["warnings"][table + ".outside_observation_period"] = con.execute(
            f"SELECT count(*) FROM omop.{table} e "
            f"WHERE NOT EXISTS(SELECT 1 FROM omop.observation_period p WHERE p.person_id=e.person_id AND "
            f"e.{start} BETWEEN p.observation_period_start_date AND p.observation_period_end_date)"
        ).fetchone()[0]
    for name, n, status in con.execute("SELECT * FROM etl.source_counts").fetchall():
        if name in EVENT_FILES:
            loaded = con.execute(
                "SELECT count(DISTINCT source_row) FROM etl.lineage WHERE source_file=?",
                [name],
            ).fetchone()[0]
            rejected = con.execute(
                "SELECT count(DISTINCT source_row) FROM etl.rejected WHERE source_file=?",
                [name],
            ).fetchone()[0]
            result["reconciliation"].append(
                {
                    "source": name,
                    "source_rows": n,
                    "loaded_source_rows": loaded,
                    "rejected_source_rows": rejected,
                }
            )
            result["errors"][name + ".reconciliation"] = abs(n - loaded - rejected)
    result["errors"]["encounters.reconciliation"] = abs(
        con.execute(
            "SELECT source_rows FROM etl.source_counts WHERE source_file='encounters'"
        ).fetchone()[0]
        - result["counts"]["visit_occurrence"]
        - con.execute(
            "SELECT count(*) FROM etl.rejected WHERE source_file='encounters'"
        ).fetchone()[0]
    )
    result["mapping"] = [
        dict(zip(["source", "rows", "mapped_rows", "percent"], r))
        for r in con.execute(
            "SELECT source_file,count(DISTINCT source_row),count(DISTINCT source_row) FILTER(WHERE target_concept_id<>0),"
            "round(100.0*count(DISTINCT source_row) FILTER(WHERE target_concept_id<>0)/count(DISTINCT source_row),4) "
            "FROM etl.lineage GROUP BY source_file ORDER BY 1"
        ).fetchall()
    ]
    result["dqd"] = "not_run"
    for table, column in [
        ("person", "gender_concept_id"),
        ("person", "race_concept_id"),
        ("person", "ethnicity_concept_id"),
        ("visit_occurrence", "visit_concept_id"),
    ]:
        result["warnings"][table + "." + column + ".unmapped"] = con.execute(
            f"SELECT count(*) FROM omop.{table} WHERE {column}=0"
        ).fetchone()[0]
    return result


def preflight(csv_dir, packages, output):
    if output.exists() or Path(str(output) + ".wal").exists():
        raise FileExistsError(
            "Salida existente: se rechaza cualquier modificación: " + str(output)
        )
    for name in ["patients", "encounters"] + EVENT_FILES:
        if not (csv_dir / (name + ".csv")).is_file():
            raise FileNotFoundError(name + ".csv")
    source_bytes = sum(
        p.stat().st_size
        for p in csv_dir.glob("*.csv")
        if p.stem
        in ["patients", "encounters", "organizations", "providers"] + EVENT_FILES
    )
    vocab_bytes = sum(
        p.stat().st_size for folder in packages for p in folder.glob("*") if p.is_file()
    )
    parent = output.parent
    while not parent.exists():
        parent = parent.parent
    free = shutil.disk_usage(parent).free
    # Incluye linaje, índices de ejecución, WAL y temporales; no es un tamaño observado.
    needed = max(2**30, int(source_bytes * 4 + vocab_bytes * 2))
    result = {
        "source_bytes": source_bytes,
        "vocab_bytes": vocab_bytes,
        "free_bytes": free,
        "required_free_bytes_estimate": needed,
        "enough_space": free >= needed,
    }
    return result


def make_manifest(csv_dir, packages, source_date, vocab_date):
    manifest = {
        "source_date": str(source_date),
        "vocabulary_date": str(vocab_date),
        "cdm_version": "5.4.2",
        "duckdb": duckdb.__version__,
        "files": {},
        "implementation": {},
    }
    for folder in [csv_dir] + packages:
        for p in sorted(folder.iterdir()):
            if not p.is_file() or p.suffix.lower() != ".csv":
                continue
            manifest["files"][str(p.resolve())] = {
                "bytes": p.stat().st_size,
                "sha256": digest(p),
            }
    for p in list((ROOT / "src").glob("*.py")) + list(VENDOR.glob("*")):
        manifest["implementation"][str(p.relative_to(ROOT))] = digest(p)
    return manifest


def build(csv_dir, packages, output, source_date, vocab_date):
    if output.exists():
        manifest = make_manifest(csv_dir, packages, source_date, vocab_date)
        try:
            with duckdb.connect(str(output), read_only=True) as c:
                prior, report = c.execute(
                    "SELECT manifest,validation FROM etl.run"
                ).fetchone()
        except (duckdb.Error, TypeError) as exc:
            raise FileExistsError(
                "La salida existente no pertenece a esta ETL"
            ) from exc
        if json.loads(prior) != manifest:
            raise FileExistsError(
                "Las entradas o el código cambiaron; elegir otra salida, sin sobrescribir"
            )
        return {**json.loads(report), "replay": "identical_inputs_no_write"}
    space = preflight(csv_dir, packages, output)
    if not space["enough_space"]:
        raise OSError("Espacio insuficiente; no se crea la base: " + json.dumps(space))
    manifest = make_manifest(csv_dir, packages, source_date, vocab_date)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Nombre nuevo reservado de manera exclusiva antes de que DuckDB lo abra.
    staging = output.with_name(output.name + ".building")
    fd = os.open(staging, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    # DuckDB requiere ausencia del archivo vacío. El directorio exclusivo evita carreras.
    staging.unlink()
    lock = output.with_name(output.name + ".lock")
    lock.mkdir()
    try:
        if output.exists():
            raise FileExistsError(output)
        with duckdb.connect(str(staging)) as con:
            con.execute(
                "SET threads=1; SET memory_limit='3GB'; SET preserve_insertion_order=true"
            )
            con.execute("BEGIN")
            create_schema(con)
            setup_audit(con)
            load_vocab(con, packages)
            demographics(con, csv_dir, vocab_date)
            visits(con, csv_dir, vocab_date)
            for name in EVENT_FILES:
                print("ETL", name, flush=True)
                clinical_events(con, name, csv_dir, vocab_date)
            version = concept(con, "CDM", "CDM v5.4.2", "Metadata", vocab_date)
            voc = con.execute(
                "SELECT vocabulary_version FROM omop.vocabulary WHERE vocabulary_id='None'"
            ).fetchone()
            con.execute(
                "INSERT INTO omop.cdm_source(cdm_source_name,cdm_source_abbreviation,cdm_holder,"
                "source_description,source_documentation_reference,cdm_etl_reference,source_release_date,cdm_release_date,"
                "cdm_version,cdm_version_concept_id,vocabulary_version) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    "Synthea Massachusetts",
                    "Synthea",
                    "Repositorio académico",
                    "ETL independiente; ver limitaciones",
                    "https://github.com/synthetichealth/synthea",
                    "omop_cdm/src/etl.py",
                    source_date,
                    date.today(),
                    "5.4.2",
                    version,
                    (voc[0] if voc and voc[0] else "not supplied"),
                ],
            )
            report = validate(con)
            con.execute("CREATE TABLE etl.run(manifest JSON,validation JSON)")
            con.execute(
                "INSERT INTO etl.run VALUES (?,?)",
                [json.dumps(manifest), json.dumps(report)],
            )
            if report["schema"]["errors"] or any(report["errors"].values()):
                raise ValueError("Validación fallida: " + json.dumps(report))
            con.execute("COMMIT; CHECKPOINT")
        # Enlace exclusivo: no sustituye una base creada por otro proceso.
        os.link(staging, output)
        staging.unlink()
        return report
    finally:
        lock.rmdir()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--vocab", type=Path, action="append", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--source-date", type=date.fromisoformat, required=True)
    p.add_argument("--vocabulary-date", type=date.fromisoformat, required=True)
    p.add_argument("--preflight", action="store_true")
    a = p.parse_args()
    result = (
        preflight(a.csv, a.vocab, a.output)
        if a.preflight
        else build(a.csv, a.vocab, a.output, a.source_date, a.vocabulary_date)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
