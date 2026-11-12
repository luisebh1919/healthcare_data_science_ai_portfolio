"""Compara consultas repetidas y las huellas reales de insumos, sin reconstruir ETL."""

import argparse
import hashlib
import json
from pathlib import Path

import duckdb
from pipeline import ROOT, snapshot


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def normalize(value):
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items() if k != "queried_at"}
    if isinstance(value, list):
        return sorted(
            [normalize(v) for v in value],
            key=lambda v: json.dumps(v, sort_keys=True, default=str),
        )
    return value


def verify(db, csv_dir, vocab_dir, gender_zip, reference_zip):
    with duckdb.connect(str(db), read_only=True) as c:
        first = snapshot(c)
    with duckdb.connect(str(db), read_only=True) as c:
        second = snapshot(c)
    matches = []
    for name, meta in first["source"].items():
        matches.append(
            {
                "input": "synthea/" + name,
                "sha256": digest(csv_dir / (name + ".csv")),
                "expected": meta["sha256"],
            }
        )
    for name, meta in first["vocab_files"].items():
        matches.append(
            {
                "input": "athena/" + name,
                "sha256": digest(vocab_dir / (name.upper() + ".csv")),
                "expected": meta["sha256"],
            }
        )
    matches.append(
        {
            "input": "suplemento_gender",
            "sha256": digest(gender_zip),
            "expected": first["migration"]["gender_reference_sha256"],
        }
    )
    reference = json.loads((ROOT / "resultados/referencia_resultados.json").read_text())
    matches.append(
        {
            "input": "referencia_eunomia",
            "sha256": digest(reference_zip),
            "expected": reference["sha256"],
        }
    )
    for row in matches:
        row["matches"] = row["sha256"] == row.pop("expected")
    repeat = normalize(first) == normalize(second)
    same_sql = reference["sql_sha256"] == digest(ROOT / "sql/consultas_omop.sql")
    if not repeat or not same_sql or not all(r["matches"] for r in matches):
        raise ValueError("La reproducción o los insumos no coinciden")
    result = {
        "run_id": first["run_id"],
        "duckdb": duckdb.__version__,
        "repeated_queries_equal": repeat,
        "reference_uses_same_sql": same_sql,
        "logical_results_sha256": hashlib.sha256(
            json.dumps(normalize(first), sort_keys=True, default=str).encode()
        ).hexdigest(),
        "inputs": matches,
        "scope": "Repetición de consultas en conexiones independientes e identidad de insumos; no se repitió el ETL completo.",
    }
    (ROOT / "resultados/reproducibilidad.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "repeated_queries_equal": repeat,
                "reference_uses_same_sql": same_sql,
                "input_files_verified": len(matches),
            }
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--vocab", type=Path, required=True)
    p.add_argument("--gender-reference", type=Path, required=True)
    p.add_argument("--reference", type=Path, required=True)
    a = p.parse_args()
    verify(a.db, a.csv, a.vocab, a.gender_reference, a.reference)
