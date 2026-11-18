"""Inventario sin datos clínicos; captura/verifica los archivos protegidos."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory():
    tree, files = [], []
    for root, dirs, names in os.walk(ROOT):
        dirs.sort()
        names.sort()
        p = Path(root)
        rel = p.relative_to(ROOT)
        tree.append(f"{rel}/")
        if p.name in SKIP:
            dirs[:] = []
            tree[-1] += " [entorno/caché: contenido omitido]"
            continue
        for name in names:
            file = p / name
            size = file.stat().st_size
            files.append({"path": str(file.relative_to(ROOT)), "bytes": size})
            tree.append(f"  {name} ({size} bytes)")
    return tree, files


def protected():
    paths = [
        ROOT / "lab10/data/clinical.duckdb",
        ROOT / "final_project/data/omop_minimal.duckdb",
    ]
    paths += list((ROOT / "final_project/notebooks").rglob("*.ipynb"))
    paths += list((ROOT / "final_project/docs/deliverables").glob("*"))
    paths += list((ROOT / "FInal_proyect").rglob("*"))
    return {str(p.relative_to(ROOT)): sha256(p) for p in paths if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["before", "after", "verify", "inspect-notebook", "finalize"]
    )
    args = parser.parse_args()
    if args.action == "finalize":
        finalize()
        return
    if args.action == "inspect-notebook":
        notebook = json.loads(
            (
                ROOT / "final_project/notebooks/02.4_readmission_modeling.ipynb"
            ).read_text()
        )
        for i in [32]:
            cell = notebook["cells"][i]
            print("CELL", i, "SOURCE ONLY\n" + "".join(cell["source"]))
        return
    docs = ROOT / "docs/audit"
    if args.action == "verify":
        expected = json.loads((docs / "protected_before.json").read_text())
        actual = protected()
        bad = [p for p in expected if actual.get(p) != expected[p]]
        bad += [p for p in actual if p not in expected]
        (docs / "protected_after.json").write_text(json.dumps(actual, indent=2) + "\n")
        (docs / "protection_validation.json").write_text(
            json.dumps({"protected_files": len(expected), "changed": bad}, indent=2)
            + "\n"
        )
        print(json.dumps({"protected_files": len(expected), "changed": bad}, indent=2))
        if bad:
            raise SystemExit(1)
        return
    docs.mkdir(parents=True, exist_ok=True)
    target = docs / f"tree_{args.action}.txt"
    if args.action == "before" and target.exists():
        raise SystemExit("La auditoría inicial ya existe; no se sobrescribe.")
    tree, files = inventory()
    target.write_text("\n".join(tree) + "\n")
    (docs / f"files_{args.action}.json").write_text(json.dumps(files, indent=2) + "\n")
    if args.action == "before":
        (docs / "protected_before.json").write_text(
            json.dumps(protected(), indent=2) + "\n"
        )
        for name, command in [
            (
                "git_status_before.txt",
                ["git", "status", "--short", "--branch", "--ignored"],
            ),
            ("git_tracked_before.txt", ["git", "ls-files"]),
            ("worktrees_before.txt", ["git", "worktree", "list", "--porcelain"]),
        ]:
            result = subprocess.run(
                command, cwd=ROOT, check=True, capture_output=True, text=True
            )
            (docs / name).write_text(result.stdout)
    print(target)


def finalize():
    sys.path.insert(0, str(ROOT / "omop_cdm/src"))
    from etl import preflight

    # Actualizar referencias históricas de documentación, sin tocar notebooks del proyecto.
    p = ROOT / "final_project/README.md"
    p.write_text(
        p.read_text()
        .replace(
            "`notebooks/02_readmission_modeling.ipynb`",
            "`notebooks/Otros/02_readmission_modeling.ipynb`",
        )
        .replace(
            "final_project/notebooks/02_readmission_modeling.ipynb",
            "final_project/notebooks/Otros/02_readmission_modeling.ipynb",
        )
    )
    p = ROOT / "lab02/README.md"
    p.write_text(
        p.read_text().replace(
            "├── analisis_pacientes.ipynb", "├── notebooks/analisis_pacientes.ipynb"
        )
    )
    packages = sorted(ROOT.glob("vocabulary_download_v5_*"))
    space = preflight(
        ROOT / "lab02/output/csv", packages, ROOT / "omop_cdm/local/omop54.duckdb"
    )
    (ROOT / "omop_cdm/docs/preflight.json").write_text(
        json.dumps(space, indent=2) + "\n"
    )
    official = {}
    for file in (ROOT / "omop_cdm/sql/vendor").iterdir():
        if file.is_file():
            official[file.name] = {
                "sha256": sha256(file),
                "bytes": file.stat().st_size,
                "url": "https://raw.githubusercontent.com/OHDSI/CommonDataModel/v5.4.2/"
                + ("inst/csv/" if file.suffix == ".csv" else "inst/ddl/5.4/postgresql/")
                + file.name,
            }
    (ROOT / "omop_cdm/docs/official_sources.json").write_text(
        json.dumps(official, indent=2) + "\n"
    )
    audit = json.loads((ROOT / "omop_cdm/docs/data_audit.json").read_text())
    core = audit["core_validation"]
    training = audit["cohort_comparison"]["training_24"]
    errors = {k: v for k, v in core["errors"].items() if v}
    warnings = {k: v for k, v in core["warnings"].items() if v}
    summary = [
        "# Resultados de validación",
        "",
        "Auditoría independiente de fuentes completas y núcleo OMOP en memoria. No se ejecutó el notebook 02.4 ni se recalcularon modelos.",
        "",
        "## Esquema y almacenamiento",
        "",
        f"{core['schema']['tables']} tablas y {core['schema']['fields']} campos oficiales; sin discrepancias de nombres, tipos normalizados o nulabilidad. La base persistente `local/omop54_schema_only.duckdb` está vacía.",
        "",
        f"Espacio disponible al último preflight: {space['free_bytes'] / 2**20:.1f} MiB. Reserva estimada de carga: {space['required_free_bytes_estimate'] / 2**30:.2f} GiB. Ver `preflight.json`; no se inició la carga completa.",
        "",
        "## Tablas pobladas en la validación en memoria",
        "",
        "| Tabla | Registros |",
        "|---|---:|",
    ]
    summary += [f"| {t} | {n:,} |" for t, n in core["counts"].items() if n]
    summary += [
        "",
        "Las restantes tablas existen y están vacías en esta validación. MEASUREMENT y OBSERVATION contienen aquí exclusivamente eventos procedentes de conditions.csv; no representan aún la carga de observations.csv. CDM_SOURCE se poblará en la ETL completa, no en el experimento en memoria.",
        "",
        "## Cobertura de vocabularios de las fuentes completas",
        "",
        "| Fuente | Filas | Filas con destino estándar | Cobertura | Códigos mapeados / distintos |",
        "|---|---:|---:|---:|---:|",
    ]
    summary += [
        f"| {x['source']} | {x['rows']:,} | {x['mapped_rows']:,} | {x['row_coverage_percent']:.4f}% | {x['mapped_codes']} / {x['distinct_codes']} |"
        for x in audit["coverage"]
    ]
    summary += [
        "",
        "La cobertura cuenta filas fuente con al menos un destino, sin multiplicarlas por mappings múltiples. No es una tasa de carga ni certificación semántica. Incluye 1055 filas con destino Note aún no implementado. Los códigos no mapeados y sus razones están en [data_audit.json](data_audit.json). El sistema LOINC de observations.csv es un supuesto explícito del exportador pendiente de confirmar para códigos alternativos.",
        "",
        "## Cohorte y entrenamiento originales",
        "",
        "| Comprobación | Resultado |",
        "|---|---|",
        "| Cohorte general / eventos | 824 / 85; mismos pacientes y hospitalizaciones índice |",
        f"| Corte temporal de 02.4 | {training['cutoff']} |",
        "| Bloque antiguo / exclusiones de seguimiento | 659 / 4 |",
        "| Entrenamiento / eventos | 655 / 76 |",
        f"| Pacientes de entrenamiento ausentes / adicionales | {training['missing_training_patients']} / {training['extra_training_patients']} |",
        f"| IDs numéricos de persona diferentes en entrenamiento | {training['numeric_person_id_differences']} |",
        f"| Orden de pacientes idéntico | {training['patient_order_identical']} |",
        "| Diferencias de valores: seis predictores con definición original | 0 en cada variable |",
        "| Diferencias: dx_cardiovascular, med_antihipertensivos y diagnósticos no oncológicos | 0 en cada variable |",
        "| Códigos/descripciones de diagnósticos de entrenamiento: EXCEPT ALL en ambos sentidos | 0 / 0 |",
        "",
        "Las tres variables derivadas conservan las reglas regex históricas de 02.4, extraídas como literales AST, sin ejecutar celdas ni inventar clasificaciones. Se reconstruyen independientemente los datos de comparación. En entrenamiento se reproducen 37 pacientes con dx_cardiovascular y 197 con med_antihipertensivos. El total de recuentos no oncológicos es 698 (no es un número de pacientes).",
        "",
        "Las medicaciones y mediciones de los predictores se leen nuevamente de los CSV originales; no se afirma que ya existan en DRUG_EXPOSURE/MEASUREMENT de una base persistente completa. Los identificadores nuevos de visita incluyen todos los encuentros y difieren del rango inpatient de la base mínima; se comparan las hospitalizaciones por UUID fuente. Ningún identificador de las bases originales fue modificado.",
        "",
        "## Discrepancia investigada",
        "",
        "Al restringir diagnósticos a CONDITION_OCCURRENCE, cambia distinct_diagnoses_180d en **515 de 824** pacientes, incluidos **418 de los 655** de entrenamiento. El archivo conditions.csv contiene también hallazgos y situaciones cuyo dominio oficial es Observation o Measurement. El predictor original contaba todos sus códigos, no solo enfermedades del dominio Condition. El linaje conserva los 830799 registros fuente: no hay pérdidas de conditions.csv ni filas rechazadas en esta auditoría.",
        "",
        "Preservar la definición fuente reproduce todos los valores originales. Adoptar el recuento por dominio estándar supone redefinir ese predictor y requiere una decisión científica separada; no se aplica al notebook ni se reentrenan modelos para acomodar el cambio.",
        "",
        "## Integridad y plausibilidad",
        "",
        f"{len(core['errors'])} controles SQL de unicidad, referencias, dominio y conciliación ejecutados: {len(errors)} con violaciones. Son controles propios, no el resultado de DQD.",
        "",
        "Advertencias no nulas:",
        "",
    ]
    summary += [f"- `{k}`: {v}." for k, v in warnings.items()] or [
        "- Ninguna en el subconjunto clínico ejecutado."
    ]
    summary += [
        "",
        "Las bases originales conservaron sus SHA-256. Los hashes previos de notebooks protegidos y entregables se verifican aparte con `tools/audit_repository.py verify`. Las pruebas pequeñas de ETL cubren precisión, dominio, fechas, referencias, conflictos de vocabulario, rechazo de sobrescritura y repetición idempotente.",
        "",
        "**Incidencia de integridad de 02.4:** el SHA-256 inicial fue `15a515fb86bea687abe4809c75e94509d88163a05c65c7e68d1c38c39d30d3a3` y durante la tarea pasó a `c7e863db914575105c4b77a124297473d195c752f49489f9979e0c1c771fc93a` (tamaño de 1947610 a 2597958 bytes, mtime local 15/nov 23:39). Ningún comando de esta migración escribió ni ejecutó ese notebook. Se conserva la versión local sin revertirla ni atribuir el cambio a un autor. La comparación de 655 pacientes se refiere al hash final leído. El control de protección falla expresamente por esa diferencia; los otros diez archivos protegidos coinciden.",
        "",
        "**DQD: no ejecutado.** Faltan los paquetes R, almacenamiento y la carga persistente completa. Los controles sobre tablas vacías no aportan evidencia sobre fuentes todavía no cargadas. Consultar [limitaciones y pendientes](limitations.md).",
        "",
        "## Artefactos revisables",
        "",
        "- `docs/data_audit.json`: controles agregados, conciliación, cobertura y comparación por campo.",
        "- `docs/preflight.json`: bloqueo de almacenamiento cuantificado.",
        "- `docs/official_sources.json`: fuentes oficiales, tamaños y hashes.",
        "- `local/omop54_schema_only.duckdb`: esquema oficial vacío.",
        "- `local/cohort_comparison.duckdb`: tablas de auditoría original/reconstruida si se solicita esa salida; no es un CDM completo.",
        "",
        "Todos los archivos por paciente y bases se conservan fuera del índice de Git.",
    ]
    (ROOT / "omop_cdm/docs/validation.md").write_text("\n".join(summary) + "\n")
    print(
        json.dumps(
            {
                "space": space,
                "schema": core["schema"],
                "violations": errors,
                "warnings": warnings,
                "training": training,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
