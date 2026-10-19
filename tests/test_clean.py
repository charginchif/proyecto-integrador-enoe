"""Pruebas de las reglas de limpieza y transformación con datos sintéticos controlados."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from enoe import clean, config as C, transform  # noqa: E402


def fila(**kw):
    base = dict(r_def=0, c_res=1, eda=30.0, clase2=1, fac_tri=100, cve_ent=9, anios_esc=12, hrsocup=40, niv_ins=4,
                ingocup=8000, ing7c=1, salario=8364, grupo="x")
    base.update(kw)
    return base


class TestCobertura(unittest.TestCase):
    def test_cada_regla_excluye_lo_que_debe(self):
        df = pd.DataFrame([
            fila(),                       # entra
            fila(r_def=15),               # entrevista incompleta
            fila(c_res=2),                # nuevo residente
            fila(eda=14.0),               # menor de 15
            fila(eda=np.nan),             # edad en blanco
            fila(eda=99.0),               # edad no especificada
            fila(clase2=3),               # no ocupado
            fila(fac_tri=0),              # ponderador cero
        ])
        bit = clean.Bitacora()
        d = clean.aplicar_cobertura(df, bit)
        self.assertEqual(len(d), 1)
        tabla = bit.a_dataframe().set_index("id")
        self.assertEqual(tabla.loc["L1", "afectados"], 1)
        self.assertEqual(tabla.loc["L2", "afectados"], 1)
        self.assertEqual(tabla.loc["L3", "afectados"], 3)   # 14, NaN y 99
        self.assertEqual(tabla.loc["L4", "afectados"], 1)
        self.assertEqual(tabla.loc["L5", "afectados"], 1)

    def test_ventana_15_65(self):
        d = clean.marcar_ventana(pd.DataFrame([fila(eda=15.0), fila(eda=65.0), fila(eda=66.0)]), clean.Bitacora())
        self.assertEqual(d["en_ventana_15_65"].tolist(), [True, True, False])


class TestFaltantes(unittest.TestCase):
    def test_recodificacion(self):
        df = pd.DataFrame([
            fila(anios_esc=99, niv_ins=5), fila(hrsocup=0), fila(hrsocup=113), fila(hrsocup=112), fila(hrsocup=1),
        ])
        d = clean.recodificar_faltantes(df, clean.Bitacora())
        self.assertTrue(np.isnan(d.loc[0, "anios_esc"]))
        self.assertFalse(d.loc[0, "nivel_especificado"])
        self.assertEqual(d["horas_validas"].tolist(), [True, False, False, True, True])
        self.assertTrue(d.loc[[1, 2], "hrsocup"].isna().all())
        self.assertEqual(d.loc[1, "hrsocup_raw"], 0)


class TestIngreso(unittest.TestCase):
    def test_grupos_mutuamente_excluyentes(self):
        df = pd.DataFrame([
            fila(ingocup=5000, ing7c=1),
            fila(ingocup=0, ing7c=2),
            fila(ingocup=0, ing7c=6),
            fila(ingocup=0, ing7c=7),
        ])
        d = clean.clasificar_ingreso(df, clean.Bitacora())
        self.assertEqual(d["grupo_ingreso"].tolist(), ["A", "B", "C", "D"])

    def test_ingreso_sin_clasificar_falla(self):
        with self.assertRaises(ValueError):
            clean.clasificar_ingreso(pd.DataFrame([fila(ingocup=0, ing7c=0)]), clean.Bitacora())

    def test_ingreso_por_hora_y_log(self):
        df = pd.DataFrame([fila(ingocup=4300, hrsocup=10.0)])
        df["grupo_ingreso"] = "A"; df["horas_validas"] = True
        d = transform.agregar_ingreso_hora(df)
        self.assertAlmostEqual(d.loc[0, "ing_hora"], 4300 / (10 * 4.3))
        self.assertAlmostEqual(d.loc[0, "ln_ing_hora"], np.log(100.0))

    def test_atipicos_por_entidad(self):
        rng = np.random.default_rng(0)
        filas = []
        for ent in (1, 2):
            for v in rng.normal(4.0 + ent, 0.5, 1000):
                filas.append(dict(cve_ent=ent, ln_ing_hora=v, grupo_ingreso="A", horas_validas=True, en_ventana_15_65=True))
        d = pd.DataFrame(filas)
        marcado, umbrales = clean.marcar_atipicos(d, clean.Bitacora())
        # ~1 % de cada entidad (0.5 % por cola) debe quedar marcado, y la proporción es la misma en ambas
        prop = marcado.groupby("cve_ent")["outlier_ing_hora"].mean()
        self.assertTrue(((prop > 0.008) & (prop < 0.012)).all())
        self.assertEqual(len(umbrales), 2)


class TestImputacion(unittest.TestCase):
    def test_imputacion_usa_mediana_del_rango_y_respeta_salario(self):
        a = [fila(ingocup=int(r * 8364), grupo_ingreso="A", p6c=np.nan) for r in (1.2, 1.4, 1.6, 1.8)]
        a += [fila(ingocup=int(r * 8364), grupo_ingreso="A", p6c=np.nan) for r in (0.4, 0.6, 0.8)]
        a += [fila(ingocup=int(r * 8364), grupo_ingreso="A", p6c=np.nan) for r in (2.2, 2.6)]
        a += [fila(ingocup=int(r * 8364), grupo_ingreso="A", p6c=np.nan) for r in (3.5, 4.5)]
        a += [fila(ingocup=int(r * 8364), grupo_ingreso="A", p6c=np.nan) for r in (6.0, 8.0)]
        a += [fila(ingocup=int(r * 8364), grupo_ingreso="A", p6c=np.nan) for r in (12.0, 14.0)]
        b = [fila(ingocup=0, ing7c=2, grupo_ingreso="B", p6c=3.0, salario=12596)]
        df = pd.DataFrame(a + b)
        df["hrsocup"] = 40.0
        d, ref = transform.imputar_rangos(df)
        mediana_3 = ref.set_index("p6c").loc[3, "razon_mediana_sm"]
        self.assertAlmostEqual(mediana_3, 1.5, delta=0.01)
        self.assertAlmostEqual(d.iloc[-1]["ing_mensual_imp"], 12596 * mediana_3, delta=1)  # usa SU salario mínimo (frontera)
        self.assertTrue(d.iloc[-1]["ing_imputado"])
        self.assertFalse(d.iloc[0]["ing_imputado"])


if __name__ == "__main__":
    unittest.main()
