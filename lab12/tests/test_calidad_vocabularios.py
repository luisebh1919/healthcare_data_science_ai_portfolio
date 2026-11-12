"""Regresiones de clasificación: el ID fuente cero no demuestra inexistencia."""

import sys
import tempfile
import unittest
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generar_reporte import generate
from pipeline import ROOT, queries
from test_informe import create_fixture


class CalidadVocabularios(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = create_fixture(Path(self.temp.name), True)
        self.con = duckdb.connect(str(self.db))

    def tearDown(self):
        self.con.close()
        self.temp.cleanup()

    def audit(self):
        return queries(self.con, ROOT / "sql/calidad_vocabularios.sql")

    def test_invalid_is_not_absent(self):
        self.con.execute("UPDATE concept SET invalid_reason='D' WHERE concept_code='C'")
        self.con.execute(
            "UPDATE condition_occurrence SET condition_source_concept_id=0 WHERE condition_source_value='C'"
        )
        self.assertEqual(
            self.audit()["no_mapeados"][0]["motivo"], "concepto_invalido_D"
        )

    def test_obsolete_is_distinct(self):
        self.con.execute("UPDATE concept SET invalid_reason='U' WHERE concept_code='C'")
        self.assertEqual(
            self.audit()["no_mapeados"][0]["motivo"], "concepto_obsoleto_U"
        )

    def test_absent_is_distinct(self):
        self.con.execute(
            "UPDATE condition_occurrence SET condition_source_value='no_existe' WHERE condition_source_value='C'"
        )
        self.assertEqual(
            self.audit()["no_mapeados"][0]["motivo"], "codigo_no_presente_en_paquete"
        )

    def test_domain_exclusion_has_trace_and_mapping(self):
        a = self.audit()
        self.assertEqual(a["reconciliacion"][0]["fuente_sin_traza"], 0)
        self.assertEqual(a["cobertura_otros_dominios"][0]["porcentaje_sin_mapeo"], 0)
        self.assertEqual(
            a["cobertura_otros_dominios"][0]["porcentaje_fuera_tabla_clinica"], 100
        )
        self.assertTrue(all(r["huerfanos"] == 0 for r in a["dependencias"]))

    def test_report_rejects_orphan_relationship(self):
        self.con.execute(
            "INSERT INTO concept_relationship VALUES (101,-999,'Maps to',DATE '1970-01-01',DATE '2099-12-31',NULL)"
        )
        self.con.close()
        root = Path(self.temp.name)
        with self.assertRaises(ValueError):
            generate(self.db, root / "report.md", root / "results.json")
        self.con = duckdb.connect(str(self.db))
