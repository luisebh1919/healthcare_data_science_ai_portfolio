"""Pruebas de regresión sobre la carga real; mutaciones dentro de rollback."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import duckdb
from pipeline import queries, validate
from test_informe import create_fixture


class Validacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db = (
            Path(os.environ["LAB12_DB"])
            if "LAB12_DB" in os.environ
            else create_fixture(Path(cls.temp.name), False)
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.con = duckdb.connect(str(self.db))
        self.con.execute("BEGIN")

    def tearDown(self):
        self.con.execute("ROLLBACK")
        self.con.close()

    def test_integridad_y_consultas(self):
        self.assertTrue(all(v == 0 for v in validate(self.con).values()))
        self.assertEqual(
            set(queries(self.con)),
            {
                "personas",
                "sexo",
                "nacimiento",
                "observacion",
                "diagnosticos",
                "visitas",
                "tipos_visita",
                "vocabularios",
                "ceros",
                "estandar_origen",
                "ventana",
                "athena",
            },
        )

    def test_detecta_pk(self):
        self.con.execute("INSERT INTO person SELECT * FROM person LIMIT 1")
        self.assertEqual(validate(self.con)["person_pk"], 1)

    def test_detecta_fk(self):
        self.con.execute(
            "UPDATE condition_occurrence SET person_id=-1 WHERE condition_occurrence_id=(SELECT min(condition_occurrence_id) FROM condition_occurrence)"
        )
        self.assertEqual(validate(self.con)["condition_occurrence_person_fk"], 1)

    def test_detecta_mapeo_invalido(self):
        self.con.execute(
            "UPDATE condition_occurrence SET condition_concept_id=-999 WHERE condition_occurrence_id=(SELECT min(condition_occurrence_id) FROM condition_occurrence)"
        )
        self.assertEqual(validate(self.con)["conceptos_condition_invalidos"], 1)

    def test_periodos_y_duplicacion(self):
        before = queries(self.con)["ventana"]
        self.con.execute(
            "INSERT INTO observation_period SELECT observation_period_id+100000000,person_id,observation_period_start_date,observation_period_end_date,period_type_concept_id FROM observation_period LIMIT 1"
        )
        self.assertEqual(validate(self.con)["periodos_solapados"], 1)
        self.assertEqual(queries(self.con)["ventana"], before)


if __name__ == "__main__":
    unittest.main()
