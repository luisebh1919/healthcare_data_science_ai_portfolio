"""Entrada compatible con la ruta histórica; implementación en src/build_db.py."""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "src/build_db.py"), run_name="__main__"
    )
