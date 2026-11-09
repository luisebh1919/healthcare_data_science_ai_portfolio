"""Compara nombres de campos con el DDL PostgreSQL oficial; no certifica semántica."""

import json
import re
import sys
from pathlib import Path

import duckdb
from pipeline import ROOT

ddl = Path(sys.argv[1]).read_text()
con = duckdb.connect(
    str(Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "local/omop.duckdb"),
    read_only=True,
)
result = {}
tables = ["person", "observation_period", "visit_occurrence", "condition_occurrence"]
for t in ["observation", "measurement"]:
    if con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE lower(table_name)=?", [t]
    ).fetchone()[0]:
        tables.append(t)
for table in tables:
    match = re.search(
        r"CREATE TABLE\s+\S*" + table + r"\s*\((.*?)\);", ddl, re.IGNORECASE | re.DOTALL
    )
    if not match:
        raise ValueError("Tabla no encontrada: " + table)
    official = {
        line.strip().split()[0].lower() for line in match[1].split(",") if line.strip()
    }
    actual = {r[0].lower() for r in con.execute(f"DESCRIBE {table}").fetchall()}
    result[table] = {
        "faltantes": sorted(official - actual),
        "adicionales": sorted(actual - official),
    }
(ROOT / "docs/comparacion_esquema.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
