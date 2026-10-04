"""Construye lab10/data/clinical.duckdb a partir de sql/carga.sql."""

from pathlib import Path
import os

import duckdb


LAB_DIR = Path(__file__).resolve().parent
DATABASE_PATH = LAB_DIR / "data" / "clinical.duckdb"
SQL_PATH = LAB_DIR / "sql" / "carga.sql"


def main() -> None:
    DATABASE_PATH.parent.mkdir(exist_ok=True)

    # Las rutas de los CSV en carga.sql son relativas a lab10/.
    os.chdir(LAB_DIR)
    sql = SQL_PATH.read_text(encoding="utf-8")

    with duckdb.connect(str(DATABASE_PATH)) as connection:
        connection.execute(sql)

        print("Filas cargadas:")
        for table in (
            "patients",
            "encounters",
            "conditions",
            "medications",
            "observations",
        ):
            count = connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count:,}")

    print(f"Base construida: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
