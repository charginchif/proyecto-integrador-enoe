"""Transformación (T de ETL / fase 3 del KDD): uniones, variables derivadas e imputación por rangos."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from .survey import mediana_ponderada

_DESC_P6C = {
    1: "Menos de 1 SM", 2: "Exactamente 1 SM", 3: "Más de 1 a 2 SM", 4: "Más de 2 a 3 SM",
    5: "Más de 3 a 5 SM", 6: "Más de 5 a 10 SM", 7: "Más de 10 SM",
}
_P6C_A_ING7C = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 5}


def asignar_persona_id(df: pd.DataFrame) -> pd.DataFrame:
    """Llave sustituta legible: ent-upm-d_sem-n_pro_viv-v_sel-n_hog-h_mud-n_ent-n_ren-cd_a-con."""
    d = df.copy()
    pid = d["cve_ent"].astype(str).str.zfill(2)
    for c in ["upm", "d_sem", "n_pro_viv", "v_sel", "n_hog", "h_mud", "n_ent", "n_ren", "cd_a", "con"]:
        pid = pid + "-" + d[c].astype(str)
    d.insert(0, "persona_id", pid)
    return d


def unir_coe2t(df: pd.DataFrame, coe2: pd.DataFrame) -> pd.DataFrame:
    """Une el detalle de captación del ingreso (COE2T) con la llave de persona; debe ser 1 a 1."""
    union = df.merge(coe2, on=C.LLAVE_PERSONA, how="left", validate="one_to_one", indicator=True)
    sin_par = int((union["_merge"] != "both").sum())
    if sin_par:
        raise ValueError(f"{sin_par} ocupados de SDEMT no tienen registro en COE2T")
    return union.drop(columns="_merge")


def agregar_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Variables derivadas de persona y empleo."""
    d = df.copy()
    d["sex"] = d["sex"].astype(int)
    d["eda"] = d["eda"].astype(int)
    d["mujer"] = (d["sex"] == 2).astype(int)
    d["edad2"] = d["eda"] ** 2 / 100.0
    d["grupo_edad"] = pd.cut(
        d["eda"], bins=[14, 24, 34, 44, 54, 64, 98],
        labels=["15-24", "25-34", "35-44", "45-54", "55-64", "65+"],
    ).astype(str)

    if not d["emp_ppal"].isin([1, 2]).all():
        raise ValueError("emp_ppal debe ser 1 (informal) o 2 (formal) en todos los ocupados")
    d["informal"] = (d["emp_ppal"] == 1).astype(int)

    # Nivel detallado: se parte el nivel 4 (media superior y superior) con los años de escolaridad.
    niv_det = d["niv_ins"].where(d["niv_ins"].between(1, 3))
    es4 = d["niv_ins"] == 4
    niv_det = niv_det.where(~es4, np.where(d["anios_esc"] >= 16, 5, 4))
    niv_det = niv_det.where(~(es4 & d["anios_esc"].isna()))  # sin años, el desglose no es identificable
    d["niv_det"] = niv_det

    d["entidad"] = d["cve_ent"].map({k: v[0] for k, v in C.ENTIDADES.items()})
    d["region"] = d["cve_ent"].map({k: v[3] for k, v in C.ENTIDADES.items()})
    d["log_horas"] = np.log(d["hrsocup"])
    return d


def agregar_ingreso_hora(df: pd.DataFrame) -> pd.DataFrame:
    """Ingreso mensual e ingreso por hora del grupo A, recalculados y verificados contra INEGI."""
    d = df.copy()
    es_a = d["grupo_ingreso"] == "A"
    d["ing_mensual"] = d["ingocup"].where(es_a).astype(float)
    d["ln_ing_mensual"] = np.log(d["ing_mensual"])
    d["ing_hora"] = (d["ingocup"] / (d["hrsocup"] * C.SEMANAS_POR_MES)).where(es_a & d["horas_validas"])
    d["ln_ing_hora"] = np.log(d["ing_hora"])
    # El ingreso por hora que publica INEGI debe ser idéntico al recalculado (se comprueba en las expectativas)
    return d


def tabla_referencia_rangos(df: pd.DataFrame) -> pd.DataFrame:
    """Para cada rango p6c, mediana ponderada de (ingocup/salario) entre quienes SÍ dieron monto exacto.

    Imputación "hot-deck por rango": a quien solo declaró "entre 2 y 3 salarios mínimos" se le asigna
    la mediana observada de quienes ganan entre 2 y 3 SM (no el punto medio, porque la distribución
    dentro del rango es asimétrica). El código 2 ("exactamente 1 SM") vale 1.0 por definición.
    """
    a = df[df["grupo_ingreso"] == "A"]
    razon = (a["ingocup"] / a["salario"]).to_numpy()
    w = a["fac_tri"].to_numpy()
    filas = []
    for k, (lo, hi) in C.P6C_RANGOS_SM.items():
        if k == 2:
            ref, n_ref = 1.0, int((razon == 1.0).sum())
        else:
            sel = (razon < 1.0) if k == 1 else ((razon > lo) & (razon <= hi))
            ref, n_ref = mediana_ponderada(razon[sel], w[sel]), int(sel.sum())
        filas.append(dict(p6c=k, rango=_DESC_P6C[k], limite_inf_sm=lo, limite_sup_sm=hi,
                          n_referencia_A=n_ref, razon_mediana_sm=ref))
    return pd.DataFrame(filas)


def imputar_rangos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Crea ing_mensual_imp / ing_hora_imp: A = observado, B = imputado por rango, C y D = sin dato."""
    d = df.copy()
    ref = tabla_referencia_rangos(d)
    mapa = ref.set_index("p6c")["razon_mediana_sm"]
    es_b = d["grupo_ingreso"] == "B"
    razon_b = d["p6c"].map(mapa)
    # Respaldo (no debería usarse): si faltara p6c se usa la mediana del rango ing7c
    sin_p6c = es_b & razon_b.isna()
    if sin_p6c.any():
        razon_ing7c = ref.assign(ing7c=ref["p6c"].map(_P6C_A_ING7C)).groupby("ing7c")["razon_mediana_sm"].median()
        razon_b = razon_b.where(~sin_p6c, d["ing7c"].map(razon_ing7c))
    d["ing_mensual_imp"] = np.where(d["grupo_ingreso"] == "A", d["ingocup"], np.where(es_b, d["salario"] * razon_b, np.nan))
    d["ing_hora_imp"] = d["ing_mensual_imp"] / (d["hrsocup"] * C.SEMANAS_POR_MES)
    d["ln_ing_hora_imp"] = np.log(d["ing_hora_imp"])
    d["ing_imputado"] = es_b & d["ing_mensual_imp"].notna()
    ref["n_B_imputados"] = ref["p6c"].map(d.loc[es_b, "p6c"].value_counts()).fillna(0).astype(int)
    ref.attrs["b_sin_p6c"] = int(sin_p6c.sum())
    return d, ref
