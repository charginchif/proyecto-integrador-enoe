"""Pruebas de regresión/logit con inferencia de diseño: puntos = statsmodels; varianza = sándwich correcto."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from enoe import estimadores as E, survey as S  # noqa: E402


def diseno_mas(n):
    """Cada observación es su propia UPM y todas están en un único estrato (equivale a m.a.s. con sándwich HC)."""
    tabla = pd.DataFrame({"upm": np.arange(n), "estrato_col": 0})
    return S.Diseno.desde_tabla(tabla), np.arange(n)


class TestRegresionDiseno(unittest.TestCase):
    def test_wls_puntos_y_errores_igual_a_statsmodels_hc(self):
        rng = np.random.default_rng(0)
        n = 4000
        X = np.column_stack([np.ones(n), rng.normal(size=n), rng.integers(0, 2, n)])
        y = X @ np.array([1.0, 0.5, -0.3]) + rng.normal(size=n) * (1 + np.abs(X[:, 1]))   # heterocedástico
        w = rng.uniform(0.5, 3, n)
        dis, psu = diseno_mas(n)
        r = S.regresion_diseno(X, y, w, psu, dis, ["c", "x", "g"])
        sm_r = sm.WLS(y, X, weights=w).fit(cov_type="HC1")
        np.testing.assert_allclose(r.coef, sm_r.params, rtol=1e-9)
        np.testing.assert_allclose(r.ee, sm_r.bse, rtol=0.01)

    def test_logit_puntos_igual_a_statsmodels_con_pesos_enteros(self):
        rng = np.random.default_rng(1)
        n = 3000
        X = np.column_stack([np.ones(n), rng.normal(size=n)])
        p = 1 / (1 + np.exp(-(0.3 + 0.8 * X[:, 1])))
        y = (rng.uniform(size=n) < p).astype(float)
        w = rng.integers(1, 5, n).astype(float)
        dis, psu = diseno_mas(n)
        r = S.logit_diseno(X, y, w, psu, dis, ["c", "x"])
        ref = sm.GLM(y, X, family=sm.families.Binomial(), freq_weights=w).fit()
        np.testing.assert_allclose(r.coef, ref.params, rtol=1e-6)
        self.assertAlmostEqual(r.coef[1], 0.8, delta=0.1)

    def test_el_efecto_de_conglomerado_agranda_el_error(self):
        """Con UPM que comparten un efecto, el error de diseño debe superar al de m.a.s."""
        rng = np.random.default_rng(2)
        H, m = 30, 15
        filas = []
        for h in range(H):
            for c in range(4):
                u = rng.normal(0, 1)
                for _ in range(m):
                    filas.append((h, h * 10 + c, u + rng.normal(), 1.0))
        d = pd.DataFrame(filas, columns=["estrato_col", "upm", "y", "w"])
        dis = S.Diseno.desde_tabla(d.drop_duplicates("upm"))
        psu = dis.indice_upm(d["upm"])
        X = np.ones((len(d), 1))
        r_clus = S.regresion_diseno(X, d["y"].to_numpy(), d["w"].to_numpy(), psu, dis, ["c"])
        dis1, psu1 = diseno_mas(len(d))
        r_mas = S.regresion_diseno(X, d["y"].to_numpy(), d["w"].to_numpy(), psu1, dis1, ["c"])
        self.assertGreater(r_clus.ee[0] / r_mas.ee[0], 1.5)

    def test_dominios_ponderadores_cero_fuera(self):
        """Estimar en un dominio con la estructura completa = poner ponderador 0 fuera del dominio."""
        rng = np.random.default_rng(3)
        n = 2000
        X = np.column_stack([np.ones(n), rng.normal(size=n)])
        y = X @ np.array([1.0, 0.4]) + rng.normal(size=n)
        dom = rng.uniform(size=n) < 0.5
        w = np.where(dom, 1.0, 0.0)
        dis, psu = diseno_mas(n)
        completo = S.regresion_diseno(X, y, w + 1e-12, psu, dis, ["c", "x"])
        recortado = sm.WLS(y[dom], X[dom]).fit()
        np.testing.assert_allclose(completo.coef, recortado.params, rtol=1e-6)


class TestEstimadoresBootstrap(unittest.TestCase):
    def test_oaxaca_identidad(self):
        """explicada + no explicada = brecha total, con cualquier referencia."""
        from enoe import datos as Dt
        n = 6000
        rng = np.random.default_rng(4)
        df = pd.DataFrame({
            "cve_ent": rng.integers(1, 33, n), "niv_ins": rng.integers(1, 5, n), "mujer": rng.integers(0, 2, n),
            "anios_esc": rng.integers(0, 20, n).astype(float), "eda": rng.integers(15, 66, n), "informal": rng.integers(0, 2, n),
            "pos_ocu": rng.choice([1, 2, 3], n), "rama_est2": rng.integers(1, 12, n), "t_loc_tri": rng.integers(1, 5, n),
            "log_horas": rng.normal(3.6, 0.3, n), "fac_tri": rng.uniform(50, 500, n), "upm": rng.integers(1, 200, n),
        })
        df["eda_c"] = df["eda"] - 40
        df["eda_c2"] = df["eda_c"] ** 2 / 100
        df["ln_ing_hora"] = 3 + 0.05 * df["anios_esc"] - 0.1 * df["mujer"] + rng.normal(0, 0.5, n)
        sub = Dt.Sub(df, np.zeros(n, dtype=int))
        est, nombres = E.fab_oaxaca(sub)
        v = dict(zip(nombres, est(sub.w)))
        self.assertAlmostEqual(v["ob_total"], v["ob_N_explicada"] + v["ob_N_no_explicada"], places=10)
        self.assertAlmostEqual(v["ob_total"], v["ob_H_explicada"] + v["ob_H_no_explicada"], places=10)
        self.assertAlmostEqual(v["ob_total"], v["ob_M_explicada"] + v["ob_M_no_explicada"], places=10)
        self.assertAlmostEqual(sum(v[k] for k in nombres if k.startswith("ob_N_exp_")), v["ob_N_explicada"], places=10)
        w = sub.w
        m = df["mujer"].to_numpy() == 0
        brecha = np.average(df.loc[m, "ln_ing_hora"], weights=w[m]) - np.average(df.loc[~m, "ln_ing_hora"], weights=w[~m])
        self.assertAlmostEqual(v["ob_total"], brecha, places=10)

    def test_brecha_pct(self):
        self.assertAlmostEqual(float(E.brecha_pct(np.log(1 / 0.8))), 20.0, places=8)   # mujeres ganan 80 % de lo que ganan los hombres


if __name__ == "__main__":
    unittest.main()
