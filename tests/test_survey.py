"""Pruebas del módulo survey: estadísticos ponderados y bootstrap de Rao-Wu."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from enoe import survey as S  # noqa: E402


def diseno_sintetico(seed=0, H=25, m=12):
    """Muestra estratificada y por conglomerados con efecto de UPM (diseño no ignorable)."""
    rng = np.random.default_rng(seed)
    filas, upm_id = [], 0
    for h in range(H):
        n_h = int(rng.integers(2, 7))
        for _ in range(n_h):
            upm_id += 1
            efecto = rng.normal(0, 1.0)
            for _ in range(m):
                filas.append((h, upm_id, 10 + 2 * h / H + efecto + rng.normal(0, 1), rng.uniform(0.5, 3)))
    d = pd.DataFrame(filas, columns=["estrato_col", "upm", "y", "w"])
    return d


class TestEstadisticosPonderados(unittest.TestCase):
    def test_cuantil_con_pesos_iguales_coincide_con_hazen(self):
        rng = np.random.default_rng(1)
        x = rng.normal(size=501)
        w = np.ones_like(x)
        for q in [0.05, 0.25, 0.5, 0.9]:
            self.assertAlmostEqual(S.cuantil_ponderado(x, w, q), np.percentile(x, 100 * q, method="hazen"), places=10)

    def test_media_ponderada(self):
        self.assertAlmostEqual(S.media_ponderada(np.array([1.0, 3.0]), np.array([1.0, 3.0])), 2.5)

    def test_spearman_pesos_iguales_igual_scipy(self):
        rng = np.random.default_rng(2)
        x = rng.integers(0, 15, 400).astype(float)          # muchos empates, como los años de escolaridad
        y = x * 0.4 + rng.normal(size=400)
        self.assertAlmostEqual(S.spearman_ponderado(x, y, np.ones(400)), stats.spearmanr(x, y).statistic, places=10)

    def test_spearman_pesos_enteros_igual_datos_expandidos(self):
        rng = np.random.default_rng(3)
        x = rng.integers(0, 10, 120).astype(float)
        y = x + rng.normal(size=120)
        w = rng.integers(1, 6, 120).astype(float)
        xe, ye = np.repeat(x, w.astype(int)), np.repeat(y, w.astype(int))
        self.assertAlmostEqual(S.spearman_ponderado(x, y, w), stats.spearmanr(xe, ye).statistic, places=10)

    def test_wls_recupera_coeficientes(self):
        rng = np.random.default_rng(4)
        X = np.column_stack([np.ones(5000), rng.normal(size=5000)])
        y = X @ np.array([2.0, -0.7]) + rng.normal(scale=0.1, size=5000)
        beta = S.wls(X, y, rng.uniform(0.5, 2, 5000))
        np.testing.assert_allclose(beta, [2.0, -0.7], atol=0.01)

    def test_holm(self):
        aj = S.holm(np.array([0.01, 0.04, 0.03, 0.005]))
        np.testing.assert_allclose(aj, [0.03, 0.06, 0.06, 0.02])


class TestDisenoYRaoWu(unittest.TestCase):
    def test_colapsar_estratos_une_unicos(self):
        t = pd.DataFrame({"upm": [1, 2, 3, 4, 5], "cve_ent": [1, 1, 1, 1, 1], "est_d_tri": [10, 10, 11, 12, 12]})
        col = S.colapsar_estratos(t)
        self.assertEqual(col.groupby(col).size().min(), 2)
        self.assertEqual(col.loc[3], col.loc[4])  # el estrato 11 (1 UPM) se une con su vecino 12

    def test_factores_tienen_esperanza_uno(self):
        d = diseno_sintetico()
        dis = S.Diseno.desde_tabla(d.drop_duplicates("upm"))
        F = dis.matriz_factores(3000, semilla=7)
        self.assertEqual(F.shape, (dis.n_upm, 3000))
        np.testing.assert_allclose(F.mean(axis=1), 1.0, atol=0.08)
        self.assertTrue((F >= 0).all())

    def test_factores_reproducibles(self):
        d = diseno_sintetico()
        dis = S.Diseno.desde_tabla(d.drop_duplicates("upm"))
        np.testing.assert_array_equal(dis.matriz_factores(5, 11), dis.matriz_factores(5, 11))

    def test_varianza_bootstrap_igual_a_taylor(self):
        d = diseno_sintetico(seed=5)
        dis = S.Diseno.desde_tabla(d.drop_duplicates("upm"))
        idx = dis.indice_upm(d["upm"])
        y, w = d["y"].to_numpy(), d["w"].to_numpy()
        theta, reps = S.bootstrap_rao_wu(lambda ww: S.media_ponderada(y, ww), w, idx, dis, B=4000, semilla=3)
        var_boot = reps.var(axis=0, ddof=1)[0]
        var_taylor = S.varianza_taylor_media(y, w, d["estrato_col"].to_numpy(), d["upm"].to_numpy())
        self.assertAlmostEqual(var_boot / var_taylor, 1.0, delta=0.08)
        self.assertAlmostEqual(theta[0], S.media_ponderada(y, w))

    def test_el_diseno_complejo_aumenta_la_varianza_respecto_a_mas(self):
        """Con efecto de conglomerado, tratar la muestra como m.a.s. subestima el error estándar (deff > 1)."""
        d = diseno_sintetico(seed=9)
        y, w = d["y"].to_numpy(), d["w"].to_numpy()
        var_mas = np.average((y - np.average(y, weights=w)) ** 2, weights=w) / len(y)
        var_dis = S.varianza_taylor_media(y, w, d["estrato_col"].to_numpy(), d["upm"].to_numpy())
        self.assertGreater(var_dis / var_mas, 1.5)

    def test_dominios_usan_toda_la_estructura(self):
        d = diseno_sintetico()
        dis = S.Diseno.desde_tabla(d.drop_duplicates("upm"))
        with self.assertRaises(KeyError):
            dis.indice_upm(np.array([10_000_000]))

    def test_ic_percentil_y_pvalor(self):
        reps = np.random.default_rng(0).normal(1.0, 0.1, size=(5000, 1))
        lo, hi = S.intervalo_percentil(reps)[:, 0]
        self.assertTrue(0.79 < lo < 0.81 and 1.19 < hi < 1.21)
        self.assertLess(S.pvalor_normal(np.array([1.0]), np.array([0.1]))[0], 1e-20)


if __name__ == "__main__":
    unittest.main()
