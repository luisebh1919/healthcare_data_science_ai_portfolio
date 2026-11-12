"""Combina descargas ATHENA sin filtrar vocabularios ni relaciones."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import duckdb
from pipeline import literal


def prepare(packages, output):
    if output.exists():
        raise ValueError("Use un directorio de salida nuevo")
    output.mkdir(parents=True)
    con = duckdb.connect(str(output / "merge.duckdb"))
    con.execute("SET threads=4")
    manifest = {"packages": [], "tables": {}}
    tables = {}
    for i, p in enumerate(packages):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        folder = output / f"package_{i}"
        folder.mkdir()
        with zipfile.ZipFile(p) as z:
            names = {
                Path(n).name.upper(): n
                for n in z.namelist()
                if n.upper().endswith(".CSV")
            }
            for needed in [
                "CONCEPT.csv",
                "CONCEPT_RELATIONSHIP.csv",
                "CONCEPT_ANCESTOR.csv",
                "VOCABULARY.csv",
            ]:
                if needed.upper() not in names:
                    raise ValueError(f"{p.name}: falta {needed}")
            for name, member in names.items():
                file = folder / name
                with z.open(member) as src, file.open("wb") as dst:
                    import shutil

                    shutil.copyfileobj(src, dst)
                tables.setdefault(name[:-4].lower(), []).append(file)
        manifest["packages"].append({"file": p.name, "sha256": h})
    for table, files in tables.items():
        union = " UNION ALL ".join(
            f"SELECT * FROM read_csv({literal(f)},delim='\t',all_varchar=true,header=true,null_padding=true)"
            for f in files
        )
        con.execute(f'CREATE TABLE "{table}" AS SELECT DISTINCT * FROM ({union})')
        keys = {
            "concept": ["concept_id"],
            "vocabulary": ["vocabulary_id"],
            "concept_relationship": ["concept_id_1", "concept_id_2", "relationship_id"],
            "concept_ancestor": ["ancestor_concept_id", "descendant_concept_id"],
        }.get(table)
        if (
            keys
            and con.execute(
                f'SELECT count(*) FROM (SELECT {",".join(keys)} FROM "{table}" GROUP BY ALL HAVING count(*)>1)'
            ).fetchone()[0]
        ):
            raise ValueError("Versiones contradictorias para claves en " + table)
        con.execute(
            f"COPY {table} TO {literal(output / (table.upper() + '.csv'))} (HEADER,DELIMITER '\t')"
        )
        manifest["tables"][table] = con.execute(
            f"SELECT count(*) FROM {table}"
        ).fetchone()[0]
    present = {
        r[0]
        for r in con.execute("SELECT DISTINCT vocabulary_id FROM concept").fetchall()
    }
    if not {"SNOMED", "ICD10CM", "RxNorm", "LOINC", "ATC"} <= present:
        raise ValueError("Faltan vocabularios requeridos")
    manifest["vocabularies"] = [
        dict(zip(["vocabulary_id", "vocabulary_version"], r))
        for r in con.execute(
            "SELECT vocabulary_id,vocabulary_version FROM vocabulary ORDER BY 1"
        ).fetchall()
    ]
    con.close()
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--zip", type=Path, action="append", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    prepare(a.zip, a.out)
