"""Pruebas aisladas de la migración; registros suplementarios explícitos de prueba."""

import csv
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corregir_dominios import migrate, validate_migration
from finalizar_visitas import RULES, finalize
from pipeline import snapshot
from reubicar_no_mapeados import relocate
from test_informe import create_fixture


class Migracion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = create_fixture(self.root / "fixture", True)
        self.ref = self.root / "gender.zip"
        buffer = io.StringIO()
        w = csv.writer(buffer)
        w.writerow(
            [
                "CONCEPT_ID",
                "CONCEPT_NAME",
                "DOMAIN_ID",
                "VOCABULARY_ID",
                "CONCEPT_CLASS_ID",
                "STANDARD_CONCEPT",
                "CONCEPT_CODE",
                "VALID_START_DATE",
                "VALID_END_DATE",
                "INVALID_REASON",
            ]
        )
        for cid, name, code in [(8507, "MALE", "M"), (8532, "FEMALE", "F")]:
            w.writerow(
                [
                    cid,
                    name,
                    "Gender",
                    "Gender",
                    "Gender",
                    "S",
                    code,
                    "1970-01-01",
                    "2099-12-31",
                    "",
                ]
            )
        with zipfile.ZipFile(self.ref, "w") as z:
            z.writestr("GiBleed_5.3/CONCEPT.csv", buffer.getvalue())
        self.con = duckdb.connect(str(self.db))

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def test_gender_and_mapped_observation(self):
        migrate(self.con, self.ref)
        self.assertEqual(
            self.con.execute("SELECT gender_concept_id FROM person").fetchone()[0], 8532
        )
        self.assertEqual(
            self.con.execute(
                "SELECT observation_concept_id FROM observation"
            ).fetchone()[0],
            102,
        )
        self.assertTrue(all(v == 0 for v in validate_migration(self.con).values()))
        self.assertEqual(
            snapshot(self.con)["corrections"]["reconciliacion_clinica"][0][
                "sin_destino"
            ],
            0,
        )

    def test_measurement_has_no_invented_numeric_result(self):
        self.con.execute(
            "UPDATE rejected_domain SET domain_id='Measurement',target_id=108"
        )
        self.con.execute(
            "INSERT INTO concept_relationship VALUES (102,108,'Maps to',DATE '1970-01-01',DATE '2099-12-31',NULL)"
        )
        migrate(self.con, self.ref)
        self.assertEqual(
            self.con.execute(
                "SELECT measurement_concept_id,value_as_number,unit_concept_id FROM measurement"
            ).fetchone(),
            (108, None, None),
        )

    def test_unmapped_known_domain_is_relocated_without_standard(self):
        self.con.execute(
            "UPDATE concept SET domain_id='Observation' WHERE concept_code='C'"
        )
        migrate(self.con, self.ref)
        relocate(self.con)
        self.assertEqual(
            self.con.execute("SELECT count(*) FROM condition_occurrence").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.con.execute("SELECT count(*) FROM observation").fetchone()[0], 2
        )
        self.assertEqual(
            self.con.execute(
                "SELECT observation_concept_id,observation_source_concept_id FROM observation WHERE observation_source_value='C'"
            ).fetchone(),
            (0, 103),
        )
        self.assertTrue(all(v == 0 for v in validate_migration(self.con).values()))

    def test_unknown_gender_is_not_imputed(self):
        self.con.execute("UPDATE person SET gender_source_value='X'")
        migrate(self.con, self.ref)
        self.assertEqual(
            self.con.execute("SELECT gender_concept_id FROM person").fetchone()[0], 0
        )

    def test_repeat_migration_is_rejected(self):
        migrate(self.con, self.ref)
        with self.assertRaises(ValueError):
            migrate(self.con, self.ref)

    def test_invalid_target_rolls_back(self):
        self.con.execute("UPDATE rejected_domain SET target_id=-99")
        with self.assertRaises(ValueError):
            migrate(self.con, self.ref)
        self.assertEqual(
            self.con.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_name='clinical_lineage'"
            ).fetchone()[0],
            0,
        )

    def test_visit_rules_and_hospice(self):
        migrate(self.con, self.ref)
        for i, (source, code, _) in enumerate(RULES, 200):
            self.con.execute(
                "INSERT INTO concept VALUES (?,?,'Visit','Visit','Fixture','S',?,DATE '1970-01-01',DATE '2099-12-31',NULL)",
                [i, "Visita artificial " + source, code],
            )
        for i, source in enumerate([r[0] for r in RULES] + ["hospice"], 2):
            label = "e_" + source
            self.con.execute(
                "INSERT INTO src_encounters (source_row,Id,PATIENT,START,STOP,ENCOUNTERCLASS) SELECT ?,?,PATIENT,START,STOP,? FROM src_encounters WHERE Id='e'",
                [i, label, source],
            )
            self.con.execute(
                "INSERT INTO visit_occurrence (visit_occurrence_id,person_id,visit_concept_id,visit_start_date,visit_start_datetime,visit_end_date,visit_end_datetime,visit_type_concept_id,visit_source_value) SELECT ?,person_id,0,visit_start_date,visit_start_datetime,visit_end_date,visit_end_datetime,0,? FROM visit_occurrence WHERE visit_occurrence_id=1",
                [i, label],
            )
        for table, column in [
            ("vocabulary", "vocabulary_id"),
            ("domain", "domain_id"),
            ("concept_class", "concept_class_id"),
        ]:
            self.con.execute(
                f"CREATE TABLE {table} AS SELECT DISTINCT {column} FROM concept"
            )
        self.assertTrue(all(v == 0 for v in finalize(self.con).values()))
        self.assertEqual(
            self.con.execute(
                "SELECT visit_concept_id FROM visit_occurrence WHERE visit_source_value='e_hospice'"
            ).fetchone()[0],
            0,
        )
        self.assertTrue(all(v == 0 for v in snapshot(self.con)["validation"].values()))
        with self.assertRaises(ValueError):
            finalize(self.con)

    def test_missing_visit_concept_rolls_back(self):
        migrate(self.con, self.ref)
        with self.assertRaises(ValueError):
            finalize(self.con)
        self.assertEqual(
            self.con.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_name='visit_mapping_audit'"
            ).fetchone()[0],
            0,
        )

    def test_queries_do_not_require_etl_lineage_in_reference(self):
        from pipeline import queries

        self.con.execute("DROP TABLE condition_lineage")
        self.assertEqual(queries(self.con)["personas"][0]["personas"], 1)
