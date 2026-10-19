"""Validación externa: ¿nuestros filtros y ponderadores reproducen las cifras oficiales del INEGI?

Si la base de 15 años y más con ``fac_tri`` reproduce la PEA, la tasa de participación y la
tasa de informalidad (TIL1) que publica el INEGI, entonces la interpretación de los ponderadores,
de ``clase1/clase2`` y de ``emp_ppal`` es correcta y las estimaciones posteriores son comparables
con la estadística oficial.
"""
from __future__ import annotations

import pandas as pd

from . import config as C


def comparar_con_inegi(sdemt: pd.DataFrame) -> pd.DataFrame:
    """``sdemt``: tabla SDEMT cruda y completa (todas las edades), tal como sale de extract.leer_sdemt."""
    ref = C.REFERENCIA_INEGI
    v = sdemt[(sdemt["r_def"] == 0) & (sdemt["c_res"].isin([1, 3])) & sdemt["eda"].between(C.EDAD_MIN, 98)]
    pob = v["fac_tri"].sum()
    pea = v.loc[v["clase1"] == 1, "fac_tri"].sum()
    oc = v[v["clase2"] == 1]
    informales = oc.loc[oc["emp_ppal"] == 1, "fac_tri"].sum()
    filas = [
        ("PEA (millones)", pea / 1e6, ref["pea_millones"], 1),
        ("Tasa de participación (%)", 100 * pea / pob, ref["tasa_participacion_pct"], 1),
        ("Ocupación informal (millones)", informales / 1e6, ref["ocupacion_informal_millones"], 1),
        ("TIL1 nacional (%)", 100 * informales / oc["fac_tri"].sum(), ref["til1_nacional_pct"], 1),
    ]
    for ent, oficial in ref["til1_estatal_pct"].items():
        o = oc[oc["cve_ent"] == ent]
        filas.append((f"TIL1 {C.ENTIDADES[ent][0]} (%)", 100 * o.loc[o["emp_ppal"] == 1, "fac_tri"].sum() / o["fac_tri"].sum(), oficial, 1))
    t = pd.DataFrame(filas, columns=["indicador", "estimado_proyecto", "oficial_inegi", "decimales"])
    t["diferencia"] = t["estimado_proyecto"] - t["oficial_inegi"]
    t["coincide"] = [round(a, d) == b for a, b, d in zip(t["estimado_proyecto"], t["oficial_inegi"], t["decimales"])]
    return t.drop(columns="decimales")


def efecto_base_menores_15(sdemt: pd.DataFrame) -> dict:
    """Muestra por qué hay que restringir a 15+: con los menores trabajando el TIL1 sube ~0.3 pp."""
    v = sdemt[(sdemt["r_def"] == 0) & (sdemt["c_res"].isin([1, 3])) & (sdemt["clase2"] == 1)]

    def til(d: pd.DataFrame) -> float:
        return 100 * d.loc[d["emp_ppal"] == 1, "fac_tri"].sum() / d["fac_tri"].sum()

    return {"til1_con_menores_de_15": til(v), "til1_base_15_y_mas": til(v[v["eda"] >= 15]),
            "menores_de_15_ocupados_en_muestra": int((v["eda"] < 15).sum())}
