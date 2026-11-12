"""Fixture artificial: nunca representa vocabularios ATHENA ni resultados clínicos."""

import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import duckdb
from generar_reporte import generate
from pipeline import build, snapshot


def write_csv(path, columns, rows, delimiter=","):
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(columns)
        writer.writerows(rows)


def create_fixture(root, vocabulary):
    root.mkdir(parents=True, exist_ok=True)
    write_csv(
        root / "patients.csv",
        ["Id", "BIRTHDATE", "GENDER", "RACE", "ETHNICITY"],
        [["p", "1980-01-01", "F", "white", "nonhispanic"]],
    )
    write_csv(
        root / "encounters.csv",
        ["Id", "PATIENT", "START", "STOP", "ENCOUNTERCLASS"],
        [["e", "p", "2020-01-01T12:00:00Z", "2020-01-03T12:00:00Z", "inpatient"]],
    )
    write_csv(
        root / "conditions.csv",
        ["PATIENT", "ENCOUNTER", "START", "STOP", "CODE", "DESCRIPTION", "SYSTEM"],
        [
            ["p", "e", "2020-01-02", "", "A", "Artificial A", "SNOMED-CT"],
            ["p", "e", "2020-01-02", "", "B", "Artificial B", "SNOMED-CT"],
            ["p", "e", "2019-01-01", "", "C", "Artificial C", "SNOMED-CT"],
        ],
    )
    if vocabulary:
        columns = [
            "concept_id",
            "concept_name",
            "domain_id",
            "vocabulary_id",
            "concept_class_id",
            "standard_concept",
            "concept_code",
            "valid_start_date",
            "valid_end_date",
            "invalid_reason",
        ]
        concepts = []
        # IDs artificiales, nombres explícitos; no confundir con IDs oficiales.
        for i, name, domain, vocab, standard, code in [
            (0, "Sin concepto fixture", "Metadata", "None", "", "0"),
            (101, "Condición artificial A", "Condition", "SNOMED", "S", "A"),
            (102, "Observación artificial B", "Observation", "SNOMED", "S", "B"),
            (103, "Origen artificial C", "Condition", "SNOMED", "", "C"),
            (104, "Sexo artificial", "Gender", "Gender", "S", "F"),
            (105, "Visita artificial", "Visit", "Visit", "S", "IP"),
            (106, "Dummy ICD", "Condition", "ICD10CM", "", "X"),
            (107, "Dummy Rx", "Drug", "RxNorm", "S", "RX"),
            (108, "Dummy LOINC", "Measurement", "LOINC", "S", "L"),
            (109, "Dummy ATC", "Drug", "ATC", "", "AT"),
        ]:
            concepts.append(
                [
                    i,
                    name,
                    domain,
                    vocab,
                    "Fixture",
                    standard,
                    code,
                    "19700101",
                    "20991231",
                    "",
                ]
            )
        write_csv(root / "CONCEPT.csv", columns, concepts, "\t")
        write_csv(
            root / "CONCEPT_RELATIONSHIP.csv",
            [
                "concept_id_1",
                "concept_id_2",
                "relationship_id",
                "valid_start_date",
                "valid_end_date",
                "invalid_reason",
            ],
            [
                [101, 101, "Maps to", "19700101", "20991231", ""],
                [102, 102, "Maps to", "19700101", "20991231", ""],
            ],
            "\t",
        )
        write_csv(
            root / "CONCEPT_ANCESTOR.csv",
            [
                "ancestor_concept_id",
                "descendant_concept_id",
                "min_levels_of_separation",
                "max_levels_of_separation",
            ],
            [[101, 101, 0, 0]],
            "\t",
        )
    db = root / "fixture.duckdb"
    with contextlib.redirect_stdout(io.StringIO()):
        build(
            Namespace(
                csv=root,
                db=db,
                vocab=root if vocabulary else None,
                allow_unmapped=not vocabulary,
                results=root / "snapshot.json",
            )
        )
    return db


class Informe(unittest.TestCase):
    def test_transition_uses_selected_database(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            db0 = create_fixture(root / "sin", False)
            db1 = create_fixture(root / "con", True)
            report = root / "report.md"
            result = root / "results.json"
            a = generate(db0, report, result)
            self.assertIn("ATHENA ausente", report.read_text())
            self.assertEqual(a["counts"]["concept"], 0)
            report.write_text("OBSOLETO: 830799 eventos")
            result.write_text("JSON anterior deliberadamente inválido")
            b = generate(db1, report, result)
            self.assertNotEqual(a["run_id"], b["run_id"])
            self.assertEqual(b["counts"]["concept"], 10)
            self.assertEqual(b["counts"]["condition_occurrence"], 2)
            self.assertEqual(b["counts"]["rejected_domain"], 1)
            self.assertNotIn("OBSOLETO", report.read_text())
            self.assertNotIn("ATHENA ausente", report.read_text())
            self.assertIn("Condición artificial A", report.read_text())
            self.assertEqual(json.loads(result.read_text())["run_id"], b["run_id"])
            with duckdb.connect(str(db1), read_only=True) as con:
                self.assertEqual(
                    con.execute(
                        "SELECT condition_source_concept_id FROM condition_occurrence WHERE condition_source_value='C'"
                    ).fetchone()[0],
                    103,
                )

    def test_missing_database_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "report.md"
            report.write_text("conservar")
            with self.assertRaises(FileNotFoundError):
                generate(root / "missing.duckdb", report, root / "results.json")
            self.assertEqual(report.read_text(), "conservar")

    def test_manifest_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            db = create_fixture(Path(temp), True)
            with duckdb.connect(str(db)) as con:
                con.execute("DELETE FROM concept")
                with self.assertRaises(ValueError):
                    snapshot(con)
