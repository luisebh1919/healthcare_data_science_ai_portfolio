"""Validación en memoria y cobertura de fuentes completas; no es una carga CDM completa.

Lee Athena y las dos bases originales sin modificarlas. Conserva solo agregados
en el informe; la base persistente opcional contiene exclusivamente el esquema.
"""

import argparse
import ast
import json
from datetime import date
from pathlib import Path

import duckdb
from etl import (
    ROOT,
    EVENT_FILES,
    DOMAINS,
    load_vocab,
    demographics,
    visits,
    clinical_events,
    setup_audit,
    lit,
    digest,
    validate,
)
from schema import create_schema, validate_schema

REPO = ROOT.parent


def coverage(con, csv_dir, when):
    result = []
    for name in EVENT_FILES:
        path = csv_dir / (name + ".csv")
        print("Cobertura", name, flush=True)
        cols = {
            x[0].upper()
            for x in con.execute(
                f"DESCRIBE SELECT * FROM read_csv({lit(path)},all_varchar=true)"
            ).fetchall()
        }
        vocab = {
            "conditions": "SNOMED",
            "medications": "RxNorm",
            "observations": "LOINC",
            "procedures": "SNOMED",
            "immunizations": "CVX",
            "devices": "SNOMED",
        }[name]
        system = (
            "CASE lower(SYSTEM) WHEN 'snomed-ct' THEN 'SNOMED' WHEN 'snomed' THEN 'SNOMED' "
            "WHEN 'http://snomed.info/sct' THEN 'SNOMED' WHEN 'rxnorm' THEN 'RxNorm' ELSE SYSTEM END"
            if "SYSTEM" in cols
            else lit(vocab)
        )
        con.execute(
            f"CREATE OR REPLACE TEMP TABLE audit_codes AS SELECT CODE,{system} vocabulary_id,count(*) n "
            f"FROM read_csv({lit(path)},all_varchar=true,parallel=false) GROUP BY ALL"
        )
        con.execute(
            "CREATE OR REPLACE TEMP TABLE audit_targets AS SELECT DISTINCT n.CODE,n.vocabulary_id,"
            "s.concept_id source_id,t.concept_id target_id,t.domain_id FROM audit_codes n JOIN omop.concept s "
            "ON s.concept_code=n.CODE AND s.vocabulary_id=n.vocabulary_id JOIN omop.concept_relationship r "
            "ON r.concept_id_1=s.concept_id AND r.relationship_id='Maps to' AND r.invalid_reason IS NULL "
            f"AND {lit(when)}::DATE BETWEEN r.valid_start_date AND r.valid_end_date JOIN omop.concept t "
            "ON t.concept_id=r.concept_id_2 AND t.standard_concept='S' AND t.invalid_reason IS NULL "
            f"AND {lit(when)}::DATE BETWEEN t.valid_start_date AND t.valid_end_date"
        )
        con.execute(
            "INSERT INTO audit_targets SELECT n.CODE,n.vocabulary_id,s.concept_id,s.concept_id,s.domain_id "
            "FROM audit_codes n JOIN omop.concept s ON s.concept_code=n.CODE AND s.vocabulary_id=n.vocabulary_id "
            "AND s.standard_concept='S' AND s.invalid_reason IS NULL "
            f"AND {lit(when)}::DATE BETWEEN s.valid_start_date AND s.valid_end_date "
            "WHERE NOT EXISTS(SELECT 1 FROM audit_targets t WHERE t.source_id=s.concept_id)"
        )
        total, codes = con.execute("SELECT sum(n),count(*) FROM audit_codes").fetchone()
        mapped, mapped_codes = con.execute(
            "SELECT coalesce(sum(n),0),count(*) FROM audit_codes n "
            "WHERE EXISTS(SELECT 1 FROM audit_targets t WHERE t.CODE=n.CODE AND t.vocabulary_id=n.vocabulary_id)"
        ).fetchone()
        unsupported = con.execute(
            "SELECT coalesce(sum(n),0) FROM audit_codes n WHERE EXISTS"
            "(SELECT 1 FROM audit_targets t WHERE t.CODE=n.CODE AND t.vocabulary_id=n.vocabulary_id) "
            "AND NOT EXISTS(SELECT 1 FROM audit_targets t WHERE t.CODE=n.CODE AND t.vocabulary_id=n.vocabulary_id "
            f"AND t.domain_id IN ({','.join(lit(d) for d in DOMAINS)}))"
        ).fetchone()[0]
        missing = con.execute(
            "SELECT n.vocabulary_id,n.CODE,n.n,CASE WHEN NOT EXISTS(SELECT 1 FROM omop.concept c "
            "WHERE c.vocabulary_id=n.vocabulary_id AND c.concept_code=n.CODE) THEN 'source_code_absent' ELSE 'no_valid_standard_mapping' END "
            "FROM audit_codes n WHERE NOT EXISTS(SELECT 1 FROM audit_targets t WHERE t.CODE=n.CODE "
            "AND t.vocabulary_id=n.vocabulary_id) ORDER BY n.n DESC,n.CODE"
        ).fetchall()
        domains = con.execute(
            "SELECT domain_id,count(DISTINCT CODE) FROM audit_targets GROUP BY 1 ORDER BY 1"
        ).fetchall()
        result.append(
            {
                "source": name,
                "rows": total,
                "distinct_codes": codes,
                "mapped_rows": mapped,
                "mapped_codes": mapped_codes,
                "row_coverage_percent": round(100 * mapped / total, 4)
                if total
                else None,
                "mapped_only_to_unsupported_domains_rows": unsupported,
                "target_domains": domains,
                "unmapped_codes": [
                    dict(zip(["vocabulary", "code", "rows", "reason"], r))
                    for r in missing
                ],
            }
        )
    return result


def reconstruct(con):
    sql_dir = REPO / "final_project/sql"
    con.execute((sql_dir / "01_concept_sets.sql").read_text())
    # El SQL original asumía que visit_occurrence solo contenía inpatient.
    cohort_sql = (sql_dir / "02_cohort.sql").read_text()
    marker = "WHERE\n        CAST(p.birth_datetime"
    if cohort_sql.count(marker) != 1:
        raise ValueError("Revisar el SQL de cohorte: marcador inesperado")
    cohort_sql = cohort_sql.replace(
        marker,
        "WHERE\n        v.visit_concept_id = 9201 AND\n        CAST(p.birth_datetime",
    )
    con.execute(cohort_sql)
    outcome_sql = (
        (sql_dir / "04_outcome.sql")
        .read_text()
        .replace(
            "ON v.person_id = c.person_id",
            "ON v.person_id = c.person_id AND v.visit_concept_id = 9201",
        )
    )
    con.execute(outcome_sql)
    features_sql = (
        (sql_dir / "05_features.sql")
        .read_text()
        .replace("raw.main.medications", "source_medications")
        .replace("raw.main.observations", "source_observations")
    )
    con.execute(features_sql)
    con.execute(
        "CREATE TABLE results.analytic_standard_domains AS SELECT * FROM results.analytic_dataset"
    )
    # Comparación por UUID de paciente/visita: los IDs secuenciales cambian al incluir más visitas.
    compare_fields = [
        "index_admission",
        "index_discharge",
        "age",
        "sex",
        "prior_inpatient_hospitalizations_180d",
        "distinct_diagnoses_180d",
        "distinct_medications_180d",
        "measurement_count_180d",
        "readmission_30d",
    ]
    con.execute(
        "CREATE TEMP VIEW expected AS SELECT a.*,p.person_source_value,v.visit_source_value "
        "FROM original.results.analytic_dataset a JOIN original.omop.person p USING(person_id) "
        "JOIN original.omop.visit_occurrence v ON v.visit_occurrence_id=a.index_visit_id"
    )
    con.execute(
        "CREATE TEMP VIEW rebuilt AS SELECT a.*,p.person_source_value,v.visit_source_value "
        "FROM results.analytic_standard_domains a JOIN omop.person p USING(person_id) "
        "JOIN omop.visit_occurrence v ON v.visit_occurrence_id=a.index_visit_id"
    )
    result = {}
    for label in ["standard_domains", "original_source_definition"]:
        if label == "original_source_definition":
            # Mantener todos los códigos registrados en conditions.csv reproduce el
            # predictor original, incluidos hallazgos cuyo dominio OMOP es Observation.
            con.execute(
                "CREATE TEMP VIEW original_definition_conditions AS SELECT DISTINCT p.person_id,CAST(l.source_start AS DATE) "
                "condition_start_date,l.source_code condition_source_value FROM etl.lineage l "
                "JOIN omop.person p ON p.person_source_value=l.source_patient WHERE l.source_file='conditions'"
            )
            con.execute(
                features_sql.replace(
                    "omop.condition_occurrence c", "original_definition_conditions c"
                )
            )
            con.execute(
                "CREATE OR REPLACE TEMP VIEW rebuilt AS SELECT a.*,p.person_source_value,v.visit_source_value "
                "FROM results.analytic_dataset a JOIN omop.person p USING(person_id) "
                "JOIN omop.visit_occurrence v ON v.visit_occurrence_id=a.index_visit_id"
            )
        joined = "expected e JOIN rebuilt b USING(person_source_value)"
        diff = {
            field: con.execute(
                f"SELECT count(*) FROM {joined} WHERE e.{field} IS DISTINCT FROM b.{field}"
            ).fetchone()[0]
            for field in compare_fields
        }
        result[label] = {
            "patients": con.execute("SELECT count(*) FROM rebuilt").fetchone()[0],
            "events": con.execute(
                "SELECT sum(readmission_30d) FROM rebuilt"
            ).fetchone()[0],
            "missing_patients": con.execute(
                "SELECT count(*) FROM expected e WHERE NOT EXISTS(SELECT 1 FROM rebuilt b WHERE b.person_source_value=e.person_source_value)"
            ).fetchone()[0],
            "extra_patients": con.execute(
                "SELECT count(*) FROM rebuilt b WHERE NOT EXISTS(SELECT 1 FROM expected e WHERE e.person_source_value=b.person_source_value)"
            ).fetchone()[0],
            "different_index_visit": con.execute(
                f"SELECT count(*) FROM {joined} WHERE e.visit_source_value<>b.visit_source_value"
            ).fetchone()[0],
            "field_mismatches": diff,
        }
    result["training_24"] = compare_training(con)
    return result


def notebook_literals():
    """Extraer solo literales; no ejecutar ninguna celda, ajuste ni predicción."""
    notebook = REPO / "final_project/notebooks/02.4_readmission_modeling.ipynb"
    data = json.loads(notebook.read_text())
    result = {}
    for cell in data["cells"]:
        if cell["cell_type"] != "code":
            continue
        tree = ast.parse("".join(cell["source"]))
        for node in tree.body:
            if not isinstance(node, ast.Assign) or not isinstance(
                node.targets[0], ast.Name
            ):
                continue
            name = node.targets[0].id
            if name in ["patron_cancer", "grupos_diagnosticos", "grupos_medicamentos"]:
                result[name] = ast.literal_eval(node.value)
            if name in ["variables_numericas", "variables_categoricas"] and isinstance(
                node.value, ast.List
            ):
                result[name] = ast.literal_eval(node.value)
            if name == "fecha_corte":
                if (
                    not isinstance(node.value, ast.Call)
                    or node.value.func.attr != "Timestamp"
                ):
                    raise ValueError("Corte no literal")
                result[name] = ast.literal_eval(node.value.args[0])
    result["notebook_sha256"] = digest(notebook)
    return result


def compare_training(con):
    contract = notebook_literals()
    cutoff = lit(contract["fecha_corte"]) + "::TIMESTAMP"
    condition = (
        f"index_admission<{cutoff} AND index_discharge+INTERVAL 30 DAY<={cutoff}"
    )
    con.execute(
        "CREATE TEMP TABLE train_original AS SELECT * FROM expected WHERE " + condition
    )
    con.execute(
        "CREATE TEMP TABLE train_rebuilt AS SELECT * FROM rebuilt WHERE " + condition
    )
    con.execute(
        "CREATE TEMP TABLE train_standard AS SELECT a.*,p.person_source_value FROM "
        "results.analytic_standard_domains a JOIN omop.person p USING(person_id) WHERE "
        + condition
    )
    con.execute(
        "CREATE TEMP VIEW training_dx_original AS SELECT t.person_source_value,c.condition_source_value codigo,"
        "max(c.condition_source_description) descripcion FROM train_original t JOIN original.omop.condition_occurrence c "
        "ON c.person_id=t.person_id AND c.condition_start_date>=CAST(t.index_admission-INTERVAL 180 DAY AS DATE) "
        "AND c.condition_start_date<CAST(t.index_admission AS DATE) GROUP BY ALL"
    )
    con.execute(
        "CREATE TEMP VIEW training_dx_rebuilt AS SELECT t.person_source_value,l.source_code codigo,"
        "max(l.source_description) descripcion FROM train_rebuilt t JOIN etl.lineage l "
        "ON l.source_patient=t.person_source_value AND l.source_file='conditions' "
        "AND CAST(l.source_start AS DATE)>=CAST(t.index_admission-INTERVAL 180 DAY AS DATE) "
        "AND CAST(l.source_start AS DATE)<CAST(t.index_admission AS DATE) GROUP BY ALL"
    )
    for label, meds in [
        ("original", "raw.main.medications"),
        ("rebuilt", "source_medications"),
    ]:
        con.execute(
            f"CREATE TEMP VIEW training_meds_{label} AS SELECT t.person_source_value,CAST(m.code AS VARCHAR) codigo,"
            f"max(m.description) descripcion FROM train_{label} t JOIN {meds} m "
            "ON CAST(m.patient_id AS VARCHAR)=t.person_source_value AND m.start_at>=t.index_admission-INTERVAL 180 DAY "
            "AND m.start_at<t.index_admission GROUP BY ALL"
        )
        cancer = lit(contract["patron_cancer"])
        cardio = lit(contract["grupos_diagnosticos"]["dx_cardiovascular"])
        medication = lit(contract["grupos_medicamentos"]["med_antihipertensivos"])
        eligible = f"NOT regexp_matches(coalesce(descripcion,''),{cancer},'i') AND regexp_matches(coalesce(descripcion,''),'\\(disorder\\)','i')"
        con.execute(
            f"CREATE TEMP TABLE fe_{label} AS SELECT t.person_source_value,"
            f"(SELECT count(DISTINCT codigo) FROM training_dx_{label} d WHERE d.person_source_value=t.person_source_value AND {eligible}) distinct_nononcological_diagnoses_180d,"
            f"CAST(EXISTS(SELECT 1 FROM training_dx_{label} d WHERE d.person_source_value=t.person_source_value AND {eligible} AND regexp_matches(descripcion,{cardio},'i')) AS INTEGER) dx_cardiovascular,"
            f"CAST(EXISTS(SELECT 1 FROM training_meds_{label} d WHERE d.person_source_value=t.person_source_value AND regexp_matches(descripcion,{medication},'i')) AS INTEGER) med_antihipertensivos "
            f"FROM train_{label} t"
        )
    features = contract["variables_numericas"] + contract["variables_categoricas"]
    extra = [
        "dx_cardiovascular",
        "med_antihipertensivos",
        "distinct_nononcological_diagnoses_180d",
    ]
    counts = {}
    for table in ["train_original", "train_rebuilt", "train_standard"]:
        counts[table] = dict(
            zip(
                ["patients", "events"],
                con.execute(
                    f"SELECT count(*),sum(readmission_30d) FROM {table}"
                ).fetchone(),
            )
        )
    diffs = {
        f: con.execute(
            f"SELECT count(*) FROM train_original a JOIN train_rebuilt b USING(person_source_value) "
            f"WHERE a.{f} IS DISTINCT FROM b.{f}"
        ).fetchone()[0]
        for f in features
    }
    fe_diffs = {
        f: con.execute(
            f"SELECT count(*) FROM fe_original a JOIN fe_rebuilt b USING(person_source_value) "
            f"WHERE a.{f} IS DISTINCT FROM b.{f}"
        ).fetchone()[0]
        for f in extra
    }
    membership = con.execute(
        "SELECT count(*) FROM (SELECT person_source_value FROM train_original EXCEPT "
        "SELECT person_source_value FROM train_rebuilt)"
    ).fetchone()[0]
    membership_reverse = con.execute(
        "SELECT count(*) FROM (SELECT person_source_value FROM train_rebuilt EXCEPT "
        "SELECT person_source_value FROM train_original)"
    ).fetchone()[0]
    standard_diffs = {
        f: con.execute(
            f"SELECT count(*) FROM train_original a JOIN train_standard b USING(person_source_value) "
            f"WHERE a.{f} IS DISTINCT FROM b.{f}"
        ).fetchone()[0]
        for f in features
    }
    raw_events = con.execute(
        "SELECT count(*) FROM (SELECT * FROM training_dx_original EXCEPT ALL SELECT * FROM training_dx_rebuilt)"
    ).fetchone()[0]
    reverse_events = con.execute(
        "SELECT count(*) FROM (SELECT * FROM training_dx_rebuilt EXCEPT ALL SELECT * FROM training_dx_original)"
    ).fetchone()[0]
    return {
        "cutoff": contract["fecha_corte"],
        "notebook_sha256": contract["notebook_sha256"],
        "notebook_executed": False,
        "counts": counts,
        "missing_training_patients": membership,
        "extra_training_patients": membership_reverse,
        "feature_mismatches_original_definition": diffs,
        "feature_mismatches_standard_domains": standard_diffs,
        "engineered_feature_mismatches_original_definition": fe_diffs,
        "diagnosis_code_description_differences_both_directions": [
            raw_events,
            reverse_events,
        ],
        "base_feature_order": features,
        "engineered_feature_order": extra,
        "fe_presence_totals_original": dict(
            zip(
                extra,
                con.execute(
                    "SELECT sum(dx_cardiovascular),sum(med_antihipertensivos),sum(distinct_nononcological_diagnoses_180d) FROM fe_original"
                ).fetchone(),
            )
        ),
        "old_block_patients": con.execute(
            f"SELECT count(*) FROM expected WHERE index_admission<{cutoff}"
        ).fetchone()[0],
        "numeric_person_id_differences": con.execute(
            "SELECT count(*) FROM train_original a JOIN train_rebuilt b USING(person_source_value) WHERE a.person_id<>b.person_id"
        ).fetchone()[0],
        "patient_order_identical": con.execute(
            "SELECT list(person_source_value ORDER BY index_admission,person_id) FROM train_original"
        ).fetchone()[0]
        == con.execute(
            "SELECT list(person_source_value ORDER BY index_admission,person_id) FROM train_rebuilt"
        ).fetchone()[0],
        "excluded_followup_overlap": con.execute(
            f"SELECT count(*) FROM expected WHERE index_admission<{cutoff} AND index_discharge+INTERVAL 30 DAY>{cutoff}"
        ).fetchone()[0],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--vocab", type=Path, action="append", required=True)
    p.add_argument("--vocabulary-date", type=date.fromisoformat, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--schema-output", type=Path)
    p.add_argument("--comparison-output", type=Path)
    a = p.parse_args()
    before = {str(x): digest(x) for x in [a.raw, a.original]}
    report = {
        "scope": "in_memory_core_and_full_source_vocabulary_audit",
        "persistent_full_etl": "blocked_disk_space",
        "vocabulary_date": str(a.vocabulary_date),
        "duckdb": duckdb.__version__,
    }
    with duckdb.connect(":memory:") as con:
        con.execute(
            "SET threads=1; SET memory_limit='6GB'; SET preserve_insertion_order=true; SET max_temp_directory_size='0B'"
        )
        con.execute(f"ATTACH {lit(a.raw.resolve())} AS raw (READ_ONLY)")
        con.execute(f"ATTACH {lit(a.original.resolve())} AS original (READ_ONLY)")
        con.execute(
            "CREATE TEMP VIEW source_medications AS SELECT CAST(PATIENT AS VARCHAR) patient_id,"
            f"CAST(START AS TIMESTAMP) start_at,CODE code,DESCRIPTION description FROM read_csv({lit(a.csv / 'medications.csv')},all_varchar=true,parallel=false)"
        )
        con.execute(
            "CREATE TEMP VIEW source_observations AS SELECT CAST(PATIENT AS VARCHAR) patient_id,"
            f"CAST(DATE AS TIMESTAMP) observed_at,TYPE observation_type,CATEGORY category FROM read_csv({lit(a.csv / 'observations.csv')},all_varchar=true,parallel=false)"
        )
        create_schema(con)
        setup_audit(con)
        print("Cargando vocabularios en memoria", flush=True)
        load_vocab(con, a.vocab)
        report["vocabularies"] = [
            dict(zip(["id", "version"], r))
            for r in con.execute(
                "SELECT vocabulary_id,vocabulary_version FROM omop.vocabulary ORDER BY 1"
            ).fetchall()
        ]
        report["vocabulary_counts"] = {
            t: con.execute(f"SELECT count(*) FROM omop.{t}").fetchone()[0]
            for t in ["concept", "concept_relationship", "concept_ancestor"]
        }
        demographics(con, a.csv, a.vocabulary_date)
        visits(con, a.csv, a.vocabulary_date)
        print("Transformando conditions.csv en memoria", flush=True)
        clinical_events(con, "conditions", a.csv, a.vocabulary_date)
        report["core_validation"] = validate(con)
        print("Reconstruyendo cohorte y predictores", flush=True)
        report["cohort_comparison"] = reconstruct(con)
        report["coverage"] = coverage(con, a.csv, a.vocabulary_date)
        report["source_sha256"] = before
        report["original_databases_unchanged"] = before == {
            str(x): digest(x) for x in [a.raw, a.original]
        }
        report["clinical_etl_executed_sources"] = [
            "patients",
            "encounters",
            "conditions",
            "organizations",
            "providers",
        ]
        report["clinical_etl_not_executed_sources"] = [
            "medications",
            "observations",
            "procedures",
            "immunizations",
            "devices",
        ]
        if a.comparison_output:
            if a.comparison_output.exists():
                raise FileExistsError(a.comparison_output)
            a.comparison_output.parent.mkdir(parents=True, exist_ok=True)
            # Solo tablas de auditoría: no se presenta como una OMOP poblada completa.
            con.execute(f"ATTACH {lit(a.comparison_output.resolve())} AS comparison")
            con.execute("CREATE SCHEMA comparison.results")
            for table in [
                "train_original",
                "train_rebuilt",
                "train_standard",
                "fe_original",
                "fe_rebuilt",
            ]:
                con.execute(
                    f"CREATE TABLE comparison.results.{table} AS SELECT * FROM {table}"
                )
            con.execute(
                "CREATE TABLE comparison.results.cohort_rebuilt AS SELECT * FROM results.analytic_dataset"
            )
            con.execute("CREATE TABLE comparison.results.audit_report(metadata JSON)")
            con.execute(
                "INSERT INTO comparison.results.audit_report VALUES (?)",
                [json.dumps(report, default=str)],
            )
            con.execute("DETACH comparison")
    if a.schema_output:
        a.schema_output.parent.mkdir(parents=True, exist_ok=True)
        existed = a.schema_output.exists()
        with duckdb.connect(str(a.schema_output), read_only=existed) as c:
            if not existed:
                create_schema(c)
            report["persistent_schema"] = validate_schema(c)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    )
    print(
        json.dumps(
            {
                "report": str(a.report),
                "cohort_comparison": report["cohort_comparison"],
                "unchanged": report["original_databases_unchanged"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
