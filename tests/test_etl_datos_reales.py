"""Pruebas de integración sobre la base SQLite generada con los microdatos reales.

Se omiten automáticamente si todavía no se ha corrido scripts/run_etl.py.
"""
import sqlite3
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from enoe import config as C  # noqa: E402


@unittest.skipUnless(C.DB_PATH.exists(), "Falta data/processed/enoe_2025t4.sqlite (corra scripts/run_etl.py)")
class TestBaseSQLite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = sqlite3.connect(C.DB_PATH)
        cls.con.execute("PRAGMA foreign_keys = ON")

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def q(self, sql):
        return pd.read_sql(sql, self.con)

    def test_integridad(self):
        self.assertEqual(self.con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(len(self.con.execute("PRAGMA foreign_key_check").fetchall()), 0)

    def test_cifras_oficiales_inegi(self):
        r = self.q("SELECT SUM(fac_tri) AS ocupados, 100.0*SUM(fac_tri*informal)/SUM(fac_tri) AS til1 FROM fact_ocupado")
        self.assertAlmostEqual(r.loc[0, "til1"], 55.0, places=1)           # TIL1 oficial 55.0 %
        self.assertAlmostEqual(r.loc[0, "ocupados"] / 1e6, 59.8, places=1)  # ~59.8 millones de ocupados

    def test_til1_estatal_oficial(self):
        v = self.q("SELECT cve_ent, til1_pct FROM v_til_entidad").set_index("cve_ent")["til1_pct"]
        for ent, oficial in C.REFERENCIA_INEGI["til1_estatal_pct"].items():
            self.assertAlmostEqual(v[ent], oficial, places=1)

    def test_conteos_de_la_cascada(self):
        n = self.q("SELECT COUNT(*) AS n, SUM(en_ventana_15_65) AS v, SUM(en_muestra_salarial) AS s FROM fact_ocupado").iloc[0]
        self.assertEqual(int(n["n"]), 190_187)
        self.assertEqual(int(n["v"]), 181_198)
        self.assertTrue(100_000 < int(n["s"]) < 125_000)

    def test_muestra_salarial_cumple_su_definicion(self):
        r = self.q("""SELECT COUNT(*) AS n FROM fact_ocupado WHERE en_muestra_salarial = 1 AND NOT
                      (grupo_ingreso = 'A' AND horas_validas = 1 AND anios_esc_valido = 1 AND nivel_especificado = 1
                       AND en_ventana_15_65 = 1 AND outlier_ing_hora = 0 AND ln_ing_hora IS NOT NULL)""")
        self.assertEqual(int(r.loc[0, "n"]), 0)

    def test_32_entidades_y_ponderador_positivo(self):
        r = self.q("SELECT COUNT(DISTINCT cve_ent) AS e, MIN(fac_tri) AS m FROM fact_ocupado").iloc[0]
        self.assertEqual(int(r["e"]), 32)
        self.assertGreater(r["m"], 0)

    def test_vista_calidad_suma_100(self):
        r = self.q("SELECT cve_ent, SUM(pct_ponderado) AS s FROM v_calidad_ingreso_entidad GROUP BY cve_ent")
        self.assertTrue(((r["s"] - 100).abs() < 0.1).all())


if __name__ == "__main__":
    unittest.main()
