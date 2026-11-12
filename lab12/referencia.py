"""Importa exclusivamente Parquet de Eunomia y ejecuta el mismo SQL."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import duckdb
from pipeline import ROOT, literal, queries

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("zip", type=Path)
    args = p.parse_args()
    out = ROOT / "local/referencia"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.zip) as z:
        for member in z.namelist():
            if member.startswith("Synthea27NjParquet/") and member.endswith(".parquet"):
                (out / Path(member).name).write_bytes(z.read(member))
    con = duckdb.connect()
    for f in out.glob("*.parquet"):
        con.execute(
            f'CREATE VIEW "{f.stem}" AS SELECT * FROM read_parquet({literal(f)})'
        )
    result = queries(con)
    (ROOT / "resultados/referencia_resultados.json").write_text(
        json.dumps(
            {
                "dataset": "OHDSI/EunomiaDatasets Synthea27NjParquet_5.4",
                "sha256": hashlib.sha256(args.zip.read_bytes()).hexdigest(),
                "sql_sha256": hashlib.sha256(
                    (ROOT / "sql/consultas_omop.sql").read_bytes()
                ).hexdigest(),
                "duckdb": duckdb.__version__,
                "queries": result,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )
    print(
        json.dumps(
            {k: result[k] for k in ["personas", "observacion", "visitas"]}, indent=2
        )
    )
