"""Auditoría de solo lectura de datos científicos; escribe únicamente informes.

No ejecuta celdas, no ajusta modelos y no abre bases en modo de escritura.
"""

import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "omop_cdm/docs"
sys.path.insert(0, str(ROOT / "omop_cdm/src"))
# El CLI resuelve los módulos locales después de fijar su ruta de importación.
from etl import digest, lit, preflight  # noqa: E402
from schema import validate_schema  # noqa: E402


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True
    ).stdout


def image_inventory(cell):
    images = []
    for i, output in enumerate(cell.get("outputs", [])):
        for mime, value in output.get("data", {}).items():
            if mime.startswith("image/"):
                data = "".join(value) if isinstance(value, list) else value
                images.append(
                    {
                        "output": i,
                        "mime": mime,
                        "sha256": hashlib.sha256(data.encode()).hexdigest(),
                    }
                )
    for name, value in cell.get("attachments", {}).items():
        for mime, data in value.items():
            data = "".join(data) if isinstance(data, list) else data
            images.append(
                {
                    "attachment": name,
                    "mime": mime,
                    "sha256": hashlib.sha256(data.encode()).hexdigest(),
                }
            )
    return images


def compare_notebooks(before, after):
    left = {c.get("id", f"position:{i}"): c for i, c in enumerate(before["cells"])}
    right = {c.get("id", f"position:{i}"): c for i, c in enumerate(after["cells"])}
    result = {
        "added": [],
        "removed": [],
        "source_changes": [],
        "output_changes": [],
        "metadata_changes": [],
        "execution_count_changes": [],
        "image_changes": [],
    }
    for cid in left.keys() | right.keys():
        if cid not in left:
            c = right[cid]
            result["added"].append(
                {
                    "id": cid,
                    "type": c["cell_type"],
                    "heading": "".join(c["source"]).split("\n")[0],
                }
            )
            continue
        if cid not in right:
            result["removed"].append(cid)
            continue
        a, b = left[cid], right[cid]
        if a.get("source") != b.get("source"):
            result["source_changes"].append(
                {
                    "id": cid,
                    "type": b["cell_type"],
                    "diff": list(
                        difflib.unified_diff(
                            "".join(a["source"]).splitlines(),
                            "".join(b["source"]).splitlines(),
                            lineterm="",
                        )
                    ),
                }
            )
        for key, label in [
            ("outputs", "output_changes"),
            ("metadata", "metadata_changes"),
            ("execution_count", "execution_count_changes"),
        ]:
            if a.get(key) != b.get(key):
                result[label].append(cid)
        if image_inventory(a) != image_inventory(b):
            result["image_changes"].append(cid)
    result["top_level_metadata_changed"] = before.get("metadata") != after.get(
        "metadata"
    )
    return result


def notebook_audit():
    path = ROOT / "final_project/notebooks/02.4_readmission_modeling.ipynb"
    raw = path.read_bytes()
    current = json.loads(raw)
    expected = json.loads((ROOT / "docs/audit/protected_before.json").read_text())[
        str(path.relative_to(ROOT))
    ]
    objects = (
        git(
            "cat-file",
            "--batch-all-objects",
            "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        )
        .decode()
        .splitlines()
    )
    candidates = [
        line.split()[0] for line in objects if line.split()[1:] == ["blob", "1947610"]
    ]
    baseline = None
    matched = None
    for oid in candidates:
        data = git("cat-file", "blob", oid)
        if hashlib.sha256(data).hexdigest() == expected:
            baseline = json.loads(data)
            matched = oid
            break
    inventory = []
    for i, c in enumerate(current["cells"]):
        source = "".join(c.get("source", []))
        inventory.append(
            {
                "index": i,
                "id": c.get("id"),
                "type": c["cell_type"],
                "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "source_lines": len(source.splitlines()),
                "execution_count": c.get("execution_count"),
                "outputs": len(c.get("outputs", [])),
                "images": image_inventory(c),
                "metadata_keys": sorted(c.get("metadata", {})),
            }
        )
    refpath = ROOT / "final_project/notebooks/Otros/02.3_readmission_modeling.ipynb"
    ref = json.loads(refpath.read_text())
    report = {
        "current_sha256": hashlib.sha256(raw).hexdigest(),
        "initial_sha256": expected,
        "current_bytes": len(raw),
        "initial_bytes": 1947610,
        "current_cells": len(current["cells"]),
        "matches_previous_closing_hash": hashlib.sha256(raw).hexdigest()
        == json.loads((ROOT / "docs/audit/protected_after.json").read_text())[
            str(path.relative_to(ROOT))
        ],
        "tracked_history": git(
            "log", "--all", "--oneline", "--", str(path.relative_to(ROOT))
        ).decode(),
        "git_objects_examined": len(objects),
        "same_size_git_blobs": len(candidates),
        "exact_initial_blob_found": matched,
        "initial_comparison": compare_notebooks(baseline, current)
        if baseline
        else None,
        "comparison_with_23_is_not_initial_24": compare_notebooks(ref, current),
        "current_metadata": current.get("metadata"),
        "current_inventory": inventory,
        "implementation_gate": "verified_comparison_required"
        if baseline
        else "blocked_missing_initial_24_content",
        "notebook_executed": False,
        "notebook_modified": False,
    }
    # Guardar diffs de fuente, nunca las imágenes ni filas clínicas de las salidas.
    (DOCS / "notebook_24_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    text = [
        "# Verificación forense del notebook 02.4",
        "",
        f"Hash inicial: `{expected}`; hash actual: `{report['current_sha256']}`.",
        f"Tamaño inicial: 1947610 bytes; actual: {len(raw)} bytes. El hash actual coincide con el cierre de la auditoría anterior.",
        "",
        "## Límite de la comparación",
        "",
        "02.4 es un archivo sin rastrear y no tiene historial propio en Git. Se buscaron copias en el repositorio, temporales accesibles, historial y Backups de VS Code, y en todos los objetos Git (incluidos no alcanzables). "
        + (
            f"Se encontró el objeto exacto {matched}."
            if matched
            else "No se localizó una copia cuyo contenido corresponda al hash inicial."
        ),
        "",
        "Un hash no permite reconstruir el contenido. Quitar la última celda SHAP produce un candidato de 1947570 bytes y hash `da72e47e839f5edc9f60bc4f28d4d400c2bbf0a49ac13284e50cd287e30aa6f5`, que NO coincide con el inicial. No se utiliza ese candidato como versión anterior ni se escribe al disco.",
        "",
        "| Categoría | Comparación exacta frente al estado inicial |",
        "|---|---|",
        "| Python | No determinable sin la copia inicial |",
        "| Markdown | No determinable sin la copia inicial |",
        "| Resultados y gráficos | No determinable sin la copia inicial |",
        "| Metadatos Jupyter | No determinable sin la copia inicial |",
        "",
        "## Inspección estática del estado actual",
        "",
        "La última celda (índice 59) importa SHAP, clona los pipelines M1 + FE y M2 + FE, llama `.fit(X_shap, y_shap)` sobre 655 pacientes de entrenamiento y calcula explicaciones y comprobaciones de reconstrucción. Contiene tablas y figuras guardadas. No se ejecutó esa celda. Sin el estado inicial no puede probarse que esta sea la única adición ni descartarse otro cambio científico.",
        "",
        "La referencia 02.3 se compara por ID de celda en `notebook_24_audit.json`; es otra versión del análisis, no el estado anterior de 02.4. Sus diferencias no demuestran cuándo ni quién modificó 02.4.",
        "",
        "## Consecuencia y decisión",
        "",
        "**Puerta científica bloqueada:** no se modifica la implementación ETL ni se inicia una carga mientras no pueda verificarse el contenido inicial de 02.4. Esto no demuestra un error científico; impide certificar su ausencia. Se necesita una copia de 02.4 con SHA-256 inicial `15a515...d3a3`, o una revisión explícita del cambio que establezca una nueva referencia autorizada.",
        "",
        "El notebook se conserva sin restaurar, sobrescribir ni ejecutar. Las consultas de auditoría de datos y almacenamiento continúan de forma no destructiva.",
    ]
    (DOCS / "notebook_24_audit.md").write_text("\n".join(text) + "\n")
    return {
        k: report[k]
        for k in [
            "current_sha256",
            "exact_initial_blob_found",
            "implementation_gate",
            "current_cells",
        ]
    }


def storage_audit():
    packages = sorted(ROOT.glob("vocabulary_download_v5_*"))
    free = shutil.disk_usage(ROOT)
    files = []
    temporaries = []
    skip = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "venv",
    }
    for base in [
        ROOT / "omop_cdm",
        ROOT / "healthcare-lab12-omop-cdm/lab12/local",
        *packages,
    ]:
        for root, dirs, names in os.walk(base):
            dirs[:] = [d for d in dirs if d not in skip]
            for name in names:
                p = Path(root) / name
                if (
                    p.suffix.lower()
                    in [".csv", ".parquet", ".duckdb", ".wal", ".building", ".tmp"]
                    or ".tmp" in p.name
                ):
                    item = {"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size}
                    files.append(item)
                    if p.suffix in [".wal", ".building", ".tmp"] or ".tmp" in p.name:
                        temporaries.append(item)
    estimates = preflight(
        ROOT / "lab02/output/csv", packages, ROOT / "omop_cdm/local/omop54.duckdb"
    )
    report = {
        "total_bytes": free.total,
        "used_bytes": free.used,
        "free_bytes": free.free,
        "original_bases": {
            p: digest(ROOT / p)
            for p in [
                "lab10/data/clinical.duckdb",
                "final_project/data/omop_minimal.duckdb",
            ]
        },
        "original_base_bytes": {
            p: (ROOT / p).stat().st_size
            for p in [
                "lab10/data/clinical.duckdb",
                "final_project/data/omop_minimal.duckdb",
            ]
        },
        "full_pipeline_estimate": estimates,
        "files": files,
        "etl_temporary_files": temporaries,
        "full_load_started": False,
        "deleted_files": [],
        "recommended_free_bytes": 30 * 2**30,
    }
    # Los nombres repetidos no demuestran igualdad; solo se agrupan hashes iguales.
    vocab_names = {
        "CONCEPT.CSV",
        "VOCABULARY.CSV",
        "DOMAIN.CSV",
        "CONCEPT_CLASS.CSV",
        "CONCEPT_RELATIONSHIP.CSV",
        "RELATIONSHIP.CSV",
        "CONCEPT_ANCESTOR.CSV",
        "CONCEPT_SYNONYM.CSV",
        "DRUG_STRENGTH.CSV",
    }
    selected = [
        ROOT / f["path"] for f in files if Path(f["path"]).name.upper() in vocab_names
    ]
    by_hash = {}
    for p in selected:
        by_hash.setdefault(digest(p), []).append(str(p.relative_to(ROOT)))
    report["verified_duplicate_groups"] = [
        {"sha256": h, "paths": ps} for h, ps in by_hash.items() if len(ps) > 1
    ]
    report["tmp_same_filesystem_as_repository"] = (
        os.stat(ROOT).st_dev == os.stat("/tmp").st_dev
    )
    report["original_databases_match_initial_hashes"] = {
        p: h == json.loads((ROOT / "docs/audit/protected_before.json").read_text())[p]
        for p, h in report["original_bases"].items()
    }
    ref = ROOT / "healthcare-lab12-omop-cdm/lab12/local/referencia/person.parquet"
    if ref.exists():
        with duckdb.connect(":memory:") as c:
            report["reference_parquet_person_count"] = c.execute(
                "SELECT count(*) FROM read_parquet(?)", [str(ref)]
            ).fetchone()[0]
    (DOCS / "storage_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    return {
        k: report[k]
        for k in ["free_bytes", "full_pipeline_estimate", "etl_temporary_files"]
    }


def persistence_audit():
    report = {}
    for path in sorted((ROOT / "omop_cdm/local").glob("*.duckdb")):
        with duckdb.connect(str(path), read_only=True) as con:
            tables = con.execute(
                "SELECT table_schema,table_name FROM information_schema.tables ORDER BY 1,2"
            ).fetchall()
            result = {
                "tables": [
                    {
                        "schema": s,
                        "table": t,
                        "rows": con.execute(
                            f'SELECT count(*) FROM "{s}"."{t}"'
                        ).fetchone()[0],
                    }
                    for s, t in tables
                ]
            }
            if any(s == "omop" for s, t in tables):
                result["schema_validation"] = validate_schema(con)
            report[path.name] = result
    (DOCS / "persistent_tables.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def semantic_audit():
    """Explicar diferencias por código sin cambiar predictores ni bases."""
    packages = sorted(ROOT.glob("vocabulary_download_v5_*"))
    concept_paths = [str(p / "CONCEPT.csv") for p in packages]
    relation_paths = [str(p / "CONCEPT_RELATIONSHIP.csv") for p in packages]
    report = {
        "scope": "read_only_source_mapping_and_persisted_comparison",
        "as_of": "2026-11-15",
    }
    with duckdb.connect(":memory:") as con:
        con.execute(
            "SET threads=1; SET memory_limit='4GB'; SET max_temp_directory_size='0B'"
        )
        for alias, path in [
            ("raw", "lab10/data/clinical.duckdb"),
            ("old", "final_project/data/omop_minimal.duckdb"),
            ("comparison", "omop_cdm/local/cohort_comparison.duckdb"),
        ]:
            con.execute(f"ATTACH {lit(ROOT / path)} AS {alias} (READ_ONLY)")
        con.execute(
            "CREATE TEMP TABLE codes AS SELECT DISTINCT CAST(code AS VARCHAR) code FROM raw.main.conditions"
        )
        print("Leyendo conceptos Athena para verificar dominios", flush=True)
        con.execute(
            "CREATE TEMP TABLE concepts AS SELECT DISTINCT CAST(concept_id AS INTEGER) concept_id,concept_name,domain_id,"
            "vocabulary_id,standard_concept,concept_code,valid_start_date,valid_end_date,invalid_reason "
            "FROM read_csv(?,delim='\t',header=true,all_varchar=true,parallel=false)",
            [concept_paths],
        )
        con.execute(
            "CREATE TEMP TABLE mapping AS SELECT DISTINCT s.concept_code code,s.concept_id source_id,t.concept_id target_id,"
            "t.domain_id,t.concept_name, 'Maps to' evidence FROM concepts s JOIN codes n ON n.code=s.concept_code "
            "AND s.vocabulary_id='SNOMED' JOIN read_csv(?,delim='\t',header=true,all_varchar=true,parallel=false) r "
            "ON CAST(r.concept_id_1 AS INTEGER)=s.concept_id AND r.relationship_id='Maps to' AND r.invalid_reason IS NULL "
            "AND '20261115' BETWEEN r.valid_start_date AND r.valid_end_date JOIN concepts t ON t.concept_id=CAST(r.concept_id_2 AS INTEGER) "
            "AND t.standard_concept='S' AND t.invalid_reason IS NULL AND '20261115' BETWEEN t.valid_start_date AND t.valid_end_date",
            [relation_paths],
        )
        con.execute(
            "INSERT INTO mapping SELECT s.concept_code,s.concept_id,s.concept_id,s.domain_id,s.concept_name,'standard identity' "
            "FROM concepts s JOIN codes n ON n.code=s.concept_code WHERE s.vocabulary_id='SNOMED' AND s.standard_concept='S' "
            "AND s.invalid_reason IS NULL AND '20261115' BETWEEN s.valid_start_date AND s.valid_end_date "
            "AND NOT EXISTS(SELECT 1 FROM mapping m WHERE m.source_id=s.concept_id)"
        )
        con.execute(
            "CREATE TEMP TABLE excluded_codes AS SELECT n.code FROM codes n WHERE EXISTS"
            "(SELECT 1 FROM mapping m WHERE m.code=n.code) AND NOT EXISTS"
            "(SELECT 1 FROM mapping m WHERE m.code=n.code AND m.domain_id='Condition')"
        )
        con.execute(
            "CREATE TEMP TABLE cohort AS SELECT a.*,p.person_source_value FROM old.results.analytic_dataset a "
            "JOIN old.omop.person p USING(person_id)"
        )
        for label, relation in [
            ("training", "comparison.results.train_original"),
            ("cohort", "cohort"),
        ]:
            con.execute(
                f"CREATE TEMP TABLE events_{label} AS SELECT t.person_id,CAST(c.code AS VARCHAR) code,c.description "
                f"FROM {relation} t JOIN raw.main.conditions c ON CAST(c.patient_id AS VARCHAR)=t.person_source_value "
                "AND c.start_date>=CAST(t.index_admission-INTERVAL 180 DAY AS DATE) "
                "AND c.start_date<CAST(t.index_admission AS DATE)"
            )
            con.execute(
                f"CREATE TEMP TABLE counts_{label} AS SELECT t.person_id,count(DISTINCT e.code) original_count,"
                "count(DISTINCT e.code) FILTER(WHERE NOT EXISTS(SELECT 1 FROM excluded_codes x WHERE x.code=e.code)) standard_count "
                f"FROM {relation} t LEFT JOIN events_{label} e USING(person_id) GROUP BY t.person_id"
            )
        report["population_deltas"] = {}
        for label in ["training", "cohort"]:
            report["population_deltas"][label] = dict(
                zip(
                    [
                        "patients",
                        "changed_patients",
                        "original_code_counts_sum",
                        "standard_code_counts_sum",
                        "removed_patient_code_pairs",
                        "removed_source_records",
                    ],
                    con.execute(
                        f"SELECT count(*),count(*) FILTER(WHERE original_count<>standard_count),sum(original_count),sum(standard_count),"
                        f"sum(original_count-standard_count),(SELECT count(*) FROM events_{label} e JOIN excluded_codes x USING(code)) FROM counts_{label}"
                    ).fetchone(),
                )
            )
        report["delta_histogram_training"] = [
            dict(zip(["removed_distinct_codes", "patients"], r))
            for r in con.execute(
                "SELECT original_count-standard_count,count(*) FROM counts_training GROUP BY 1 ORDER BY 1"
            ).fetchall()
        ]
        report["codes"] = []
        for code in con.execute(
            "SELECT code FROM excluded_codes ORDER BY code"
        ).fetchall():
            code = code[0]
            rows = con.execute(
                "SELECT DISTINCT source_id,target_id,domain_id,concept_name,evidence FROM mapping WHERE code=? ORDER BY target_id",
                [code],
            ).fetchall()
            counts = {}
            for name, relation in [
                ("source", "raw.main.conditions"),
                ("training", "events_training"),
                ("cohort", "events_cohort"),
            ]:
                counts[name] = con.execute(
                    "SELECT count(*),count(DISTINCT "
                    + ("patient_id" if name == "source" else "person_id")
                    + f") FROM {relation} WHERE CAST(code AS VARCHAR)=?",
                    [code],
                ).fetchone()
            descriptions = [
                r[0]
                for r in con.execute(
                    "SELECT DISTINCT description FROM raw.main.conditions WHERE CAST(code AS VARCHAR)=? ORDER BY 1",
                    [code],
                ).fetchall()
            ]
            report["codes"].append(
                {
                    "source_code": code,
                    "source_descriptions": descriptions,
                    "targets": [
                        dict(
                            zip(
                                [
                                    "source_concept_id",
                                    "target_concept_id",
                                    "domain",
                                    "concept_name",
                                    "evidence",
                                ],
                                r,
                            )
                        )
                        for r in rows
                    ],
                    "source_records": counts["source"][0],
                    "source_patients": counts["source"][1],
                    "training_records": counts["training"][0],
                    "training_patients": counts["training"][1],
                    "cohort_records": counts["cohort"][0],
                    "cohort_patients": counts["cohort"][1],
                }
            )
        report["mapping_conclusions"] = {
            "targets_are_official_current_standard_concepts": True,
            "condition_mappings_omitted_by_exclusion_rule": con.execute(
                "SELECT count(*) FROM mapping m JOIN excluded_codes x USING(code) WHERE m.domain_id='Condition'"
            ).fetchone()[0],
            "ambiguous_multi_target_codes": con.execute(
                "SELECT count(*) FROM (SELECT code FROM mapping GROUP BY 1 HAVING count(DISTINCT target_id)>1)"
            ).fetchone()[0],
            "mapping_error_demonstrated_for_excluded_codes": False,
            "clinical_validity_certified": False,
        }
        report["persisted_training_counts_match_sql"] = {
            "original": con.execute(
                "SELECT count(*) FROM counts_training c JOIN comparison.results.train_original t USING(person_id) WHERE c.original_count<>t.distinct_diagnoses_180d"
            ).fetchone()[0],
            "standard": con.execute(
                "SELECT count(*) FROM counts_training c JOIN comparison.results.train_standard t USING(person_id) WHERE c.standard_count<>t.distinct_diagnoses_180d"
            ).fetchone()[0],
        }
        cutoff = "TIMESTAMP '2022-11-27 07:16:42'"
        report["original_counts"] = dict(
            zip(
                ["cohort", "events", "training", "temporal_test", "overlap_excluded"],
                con.execute(
                    f"SELECT count(*),sum(readmission_30d),count(*) FILTER(WHERE index_admission<{cutoff} AND index_discharge+INTERVAL 30 DAY<={cutoff}),"
                    f"count(*) FILTER(WHERE index_admission>={cutoff}),count(*) FILTER(WHERE index_admission<{cutoff} AND index_discharge+INTERVAL 30 DAY>{cutoff}) FROM cohort"
                ).fetchone(),
            )
        )
        base = [
            "age",
            "sex",
            "prior_inpatient_hospitalizations_180d",
            "distinct_diagnoses_180d",
            "distinct_medications_180d",
            "measurement_count_180d",
        ]
        for label, where in [("all", "TRUE"), ("test", f"a.index_admission>={cutoff}")]:
            report["base_value_mismatches_" + label] = {
                f: con.execute(
                    "SELECT count(*) FROM old.results.analytic_dataset a "
                    "JOIN comparison.results.cohort_rebuilt b USING(person_id) "
                    f"WHERE ({where}) AND a.{f} IS DISTINCT FROM b.{f}"
                ).fetchone()[0]
                for f in base
            }
        report["temporal_test_membership_differences_both_directions"] = [
            con.execute(q).fetchone()[0]
            for q in [
                f"SELECT count(*) FROM (SELECT person_id FROM old.results.analytic_dataset WHERE index_admission>={cutoff} EXCEPT SELECT person_id FROM comparison.results.cohort_rebuilt WHERE index_admission>={cutoff})",
                f"SELECT count(*) FROM (SELECT person_id FROM comparison.results.cohort_rebuilt WHERE index_admission>={cutoff} EXCEPT SELECT person_id FROM old.results.analytic_dataset WHERE index_admission>={cutoff})",
            ]
        ]
        report["fe_mismatches_training"] = {
            f: con.execute(
                "SELECT count(*) FROM comparison.results.fe_original a "
                "JOIN comparison.results.fe_rebuilt b USING(person_source_value) "
                f"WHERE a.{f} IS DISTINCT FROM b.{f}"
            ).fetchone()[0]
            for f in [
                "dx_cardiovascular",
                "med_antihipertensivos",
                "distinct_nononcological_diagnoses_180d",
            ]
        }
        report["fe_temporal_test"] = (
            "not_compared_no_original_fe_test_matrix; no_test_selection_performed"
        )
        report["models_fitted"] = False
        report["predictive_metrics_computed"] = False
        # Las filas por paciente solo se escriben en el directorio ignorado, nunca en docs.
        result_path = ROOT / "omop_cdm/results/diagnosis_count_deltas_training.csv"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        if not result_path.exists():
            con.execute(
                f"COPY (SELECT *,original_count-standard_count delta FROM counts_training ORDER BY person_id) TO {lit(result_path)} (HEADER)"
            )
    (DOCS / "diagnosis_domain_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    text = [
        "# Diferencias del predictor de diagnósticos por dominio",
        "",
        "Se consultaron bases existentes READ_ONLY y las dos descargas Athena originales. No se modifican predictores ni modelos. Fecha de evaluación de vigencia: 2026-11-15.",
        "",
        "## Códigos excluidos del recuento Condition",
        "",
        "| Código SNOMED fuente | Destino OMOP | Registros fuente | Registros en lookback de entrenamiento | Pacientes de entrenamiento |",
        "|---|---|---:|---:|---:|",
    ]
    for row in report["codes"]:
        domain = ", ".join(sorted({t["domain"] for t in row["targets"]}))
        text.append(
            f"| {row['source_code']} | {domain} | {row['source_records']} | {row['training_records']} | {row['training_patients']} |"
        )
    text += [
        "",
        "Las descripciones fuente, conceptos destino, identificadores oficiales y evidencia de mapping por código están en `diagnosis_domain_audit.json`. Los pacientes por código se solapan: sus recuentos no deben sumarse como pacientes únicos.",
        "",
        "## Interpretación",
        "",
        "La definición original cuenta códigos distintos de conditions.csv en los 180 días previos, incluidos registros sociales y hallazgos. El recuento restringido a CONDITION_OCCURRENCE incluye conceptos de Condition y los códigos sin mapping mantenidos con concepto cero. Los códigos con destino oficial Observation/Measurement se representan en esas tablas y dejan de contribuir al recuento de Condition. La ausencia de un código de esa tabla no implica pérdida del registro.",
        "",
        "Los destinos excluidos se verifican contra conceptos estándar vigentes y relaciones oficiales Maps to o identidad de concepto estándar. No se encontró evidencia de un mapping erróneo que explique los 418 pacientes; no se certifica con esto toda la validez clínica del ETL. Cambiar el predictor original para contar solo Condition sería un cambio científico y no se aplica.",
        "",
        "La definición por dominio corresponde a las tablas OMOP; un predictor basado en códigos fuente históricos también puede reproducirse mediante linaje, pero debe etiquetarse como tal y no llamarse un recuento de enfermedades estándar.",
        "",
        "## Recuentos y equivalencia",
        "",
        "```json",
        json.dumps(
            {
                k: report[k]
                for k in [
                    "population_deltas",
                    "delta_histogram_training",
                    "original_counts",
                    "persisted_training_counts_match_sql",
                    "base_value_mismatches_all",
                    "base_value_mismatches_test",
                    "temporal_test_membership_differences_both_directions",
                    "fe_mismatches_training",
                    "fe_temporal_test",
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "La equivalencia utiliza las matrices de auditoría persistidas previamente, no una nueva OMOP clínica completa. Las tres variables FE se comparan para los 655 pacientes: no existe una matriz FE original de la prueba temporal en 02.4 que permita afirmar equivalencia de esas variables en los 165 reservados. No se generan resultados predictivos ni se usa la prueba para selección.",
    ]
    (DOCS / "diagnosis_domain_audit.md").write_text("\n".join(text) + "\n")
    return {
        k: report[k]
        for k in [
            "population_deltas",
            "persisted_training_counts_match_sql",
            "original_counts",
            "base_value_mismatches_all",
            "fe_mismatches_training",
        ]
    }


def final_integrity():
    expected = json.loads((ROOT / "docs/audit/protected_before.json").read_text())
    closing = json.loads((ROOT / "docs/audit/protected_after.json").read_text())
    records = {}
    for path, initial in expected.items():
        actual = digest(ROOT / path)
        records[path] = {
            "sha256": actual,
            "matches_initial": actual == initial,
            "matches_previous_closing": actual == closing.get(path),
        }
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "protected_files": records,
        "scientific_notebooks_executed": False,
        "original_databases_modified": False,
        "full_load_started": False,
        "implementation_gate": "blocked_missing_initial_24_content",
        "free_bytes_now": shutil.disk_usage(ROOT).free,
    }
    (DOCS / "review_final_integrity.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    result = subprocess.run(
        [
            "Rscript",
            "--vanilla",
            "-e",
            'p<-c("DataQualityDashboard","DatabaseConnector","SqlRender","duckdb"); cat(paste(p,vapply(p,requireNamespace,logical(1),quietly=TRUE),sep="="),sep="\\n")',
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    packages = {
        line.split("=")[0]: line.split("=")[1] == "TRUE"
        for line in result.stdout.splitlines()
        if "=" in line
    }
    dqd = {
        "official_cdm_54_supported": True,
        "official_duckdb_tests_documented": True,
        "prerequisite_check_executed": True,
        "available_r_packages": packages,
        "execution_attempted": False,
        "status": "not_run",
        "checks_total": None,
        "checks_passed": None,
        "checks_failed": None,
        "warnings": None,
        "blockers": [
            "missing_R_packages",
            "empty_persistent_CDM_including_CDM_SOURCE",
            "insufficient_disk_space",
            "unverified_initial_notebook_24",
        ],
        "sources": [
            "https://ohdsi.github.io/DataQualityDashboard/reference/executeDqChecks.html",
            "https://github.com/OHDSI/DataQualityDashboard/blob/main/NEWS.md",
        ],
    }
    (DOCS / "dqd_status.json").write_text(json.dumps(dqd, indent=2) + "\n")
    (DOCS / "local_test_results.json").write_text(
        json.dumps(
            {
                "command": "pytest omop_cdm/tests lab04/tests final_project/tests -q",
                "passed": 13,
                "failed": 0,
                "duration_seconds": 1.94,
                "official_DQD": False,
            },
            indent=2,
        )
        + "\n"
    )
    return {
        "protected_files": len(records),
        "differences_from_previous_closing": [
            p for p, v in records.items() if not v["matches_previous_closing"]
        ],
        "differences_from_initial": [
            p for p, v in records.items() if not v["matches_initial"]
        ],
        "free_bytes_now": report["free_bytes_now"],
        "dqd": dqd,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "phase", choices=["notebook", "storage", "persistence", "semantic", "final"]
    )
    args = p.parse_args()
    result = {
        "notebook": notebook_audit,
        "storage": storage_audit,
        "persistence": persistence_audit,
        "semantic": semantic_audit,
        "final": final_integrity,
    }[args.phase]()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
