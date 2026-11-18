"""DDL OHDSI 5.4.2: adaptación explícita de tipos al motor DuckDB."""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "sql/vendor"


def fields():
    with (VENDOR / "OMOP_CDMv5.4_Field_Level.csv").open(
        newline="", encoding="cp1252"
    ) as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["cdmFieldName"] = row["cdmFieldName"].strip('"')
    return rows


def ddl():
    sql = (VENDOR / "OMOPCDM_postgresql_5.4_ddl.sql").read_text()
    sql = sql.replace("@cdmDatabaseSchema", "omop")
    # NUMERIC sin escala en PostgreSQL admite decimales arbitrarios. El valor
    # predeterminado de DuckDB (18,3) redondearía mediciones; usar DOUBLE.
    sql = re.sub(r"\bNUMERIC\b", "DOUBLE", sql, flags=re.I)
    return "CREATE SCHEMA omop;\n" + sql


def create_schema(con):
    con.execute(ddl())
    con.execute("CREATE SCHEMA etl")


def validate_schema(con):
    expected = {}
    for row in fields():
        expected.setdefault(row["cdmTableName"].lower(), []).append(row)
    errors = []
    for table, rows in expected.items():
        actual = {
            r[0]: (r[1], r[2]) for r in con.execute(f"DESCRIBE omop.{table}").fetchall()
        }
        names = {r["cdmFieldName"].lower() for r in rows}
        if set(actual) != names:
            errors.append({"table": table, "fields": sorted(set(actual) ^ names)})
        for r in rows:
            name = r["cdmFieldName"].lower()
            t = r["cdmDatatype"].lower()
            target = (
                "VARCHAR"
                if t.startswith("varchar") or t == "text"
                else {
                    "integer": "INTEGER",
                    "datetime": "TIMESTAMP",
                    "date": "DATE",
                    "float": "DOUBLE",
                    "numeric": "DOUBLE",
                }.get(t, t.upper())
            )
            if name in actual and actual[name] != (
                target,
                "NO" if r["isRequired"] == "Yes" else "YES",
            ):
                errors.append(
                    {
                        "table": table,
                        "field": name,
                        "actual": actual[name],
                        "expected": target,
                    }
                )
    return {
        "tables": len(expected),
        "fields": sum(map(len, expected.values())),
        "errors": errors,
    }
