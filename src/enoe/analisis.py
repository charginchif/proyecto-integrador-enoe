"""Orquestador del análisis estadístico (fases de Minería e Interpretación del KDD).

``ejecutar_analisis`` corre, en orden: informalidad, calidad del ingreso, rendimiento de la
escolaridad, brechas de género, descomposición de Oaxaca-Blinder, robustez y modelos paramétricos, y
devuelve un diccionario de tablas (DataFrames) y un resumen de cifras clave (dict).
Todas las pasadas del bootstrap usan la MISMA semilla, por lo que la réplica b es el mismo
remuestreo en todos los análisis (permite comparar y combinar resultados de forma coherente).
"""
from __future__ import annotations

import json
import logging
import time

import numpy as np
import pandas as pd
from scipy import stats

from . import config as C
from . import estimadores as E
from . import modelos as M
from .datos import Datos, Sub, cargar_datos
from .estimadores import ResultadoBoot, brecha_pct, correr
from .survey import holm

log = logging.getLogger("enoe.analisis")

NIVELES = [1, 2, 3, 4]


# --------------------------------------------------------------------------- #
# utilidades
# --------------------------------------------------------------------------- #
def _por_entidad(tb: pd.DataFrame, prefijo: str) -> pd.DataFrame:
    m = tb["nombre"].str.extract(rf"^{prefijo}_(\d\d)$")[0]
    t = tb[m.notna()].copy()
    t["cve_ent"] = m[m.notna()].astype(int)
    return t.drop(columns="nombre").set_index("cve_ent").sort_index()


def _rangos(r: ResultadoBoot, prefijo: str, descendente: bool = True) -> pd.DataFrame:
    """Rango de cada entidad (1 = mayor valor) con su intervalo bootstrap al 95 %."""
    est, reps = r.serie(prefijo, E.N_ENT)
    signo = -1.0 if descendente else 1.0
    rk_est = stats.rankdata(signo * est)
    rk_rep = stats.rankdata(signo * reps, axis=1)
    return pd.DataFrame({"rango": rk_est.astype(int), "rango_inf": np.percentile(rk_rep, 2.5, axis=0).round().astype(int),
                         "rango_sup": np.percentile(rk_rep, 97.5, axis=0).round().astype(int)}, index=np.arange(1, E.N_ENT + 1))


def _fmt_p(p: float) -> str:
    return "<0.0001" if p < 1e-4 else f"{p:.4f}"


def _nombre_ent() -> pd.DataFrame:
    return pd.DataFrame({"cve_ent": list(C.ENTIDADES), "entidad": [v[0] for v in C.ENTIDADES.values()],
                         "abreviatura": [v[2] for v in C.ENTIDADES.values()], "region": [v[3] for v in C.ENTIDADES.values()]}).set_index("cve_ent")


# --------------------------------------------------------------------------- #
# tablas derivadas de cada bloque
# --------------------------------------------------------------------------- #
def tablas_informalidad(r: ResultadoBoot) -> dict[str, pd.DataFrame]:
    tb = r.tabla()
    ent = _nombre_ent().join(_por_entidad(tb, "til1_ent")[["est", "ee", "ic_inf", "ic_sup"]].rename(columns=lambda c: f"til1_{c}"))
    ent = ent.join(_por_entidad(tb, "esc_ent")[["est", "ic_inf", "ic_sup"]].rename(columns=lambda c: f"esc15_{c}"))
    ent = ent.join(_por_entidad(tb, "ocup_ent")[["est"]].rename(columns={"est": "ocupados_est"}))
    ent[["til1_est", "til1_ic_inf", "til1_ic_sup"]] *= 100
    rk = _rangos(r, "til1_ent").add_prefix("til1_")
    ent = ent.join(rk)
    idx = tb.set_index("nombre")
    nac = pd.DataFrame([
        ("Nacional", idx.loc["til1_nac"]), ("Hombres", idx.loc["til1_hombres"]), ("Mujeres", idx.loc["til1_mujeres"]),
        *[(f"Región {rg}", idx.loc[f"til1_reg_{rg}"]) for rg in C.REGIONES],
        *[(f"Nivel {k}. {C.NIV_INS[k]}", idx.loc[f"til1_niv{k}"]) for k in NIVELES],
    ], columns=["grupo", "fila"])
    nac = pd.concat([nac[["grupo"]], pd.DataFrame(nac["fila"].tolist()).reset_index(drop=True)], axis=1)
    nac[["est", "ee", "ic_inf", "ic_sup"]] *= 100
    asoc = idx.loc[["r_pearson_til_esc", "rho_spearman_til_esc", "pendiente_til_esc"], ["est", "ee", "ic_inf", "ic_sup", "p"]].copy()
    asoc.loc["pendiente_til_esc", ["est", "ee", "ic_inf", "ic_sup"]] *= 100   # puntos porcentuales por año de escolaridad media
    return {"til1_entidad": ent.reset_index(), "til1_grupos": nac, "til1_vs_escolaridad_estatal": asoc.reset_index().rename(columns={"nombre": "indicador"})}


def tabla_calidad_ingreso(r: ResultadoBoot) -> pd.DataFrame:
    tb = r.tabla().set_index("nombre")
    filas = []
    for x in "ABCD":
        for etiqueta, clave in [("Total", f"grp_{x}_nac"), ("Hombres", f"grp_{x}_h"), ("Mujeres", f"grp_{x}_m"),
                                *[(f"Nivel {k}. {C.NIV_INS[k]}", f"grp_{x}_niv{k}") for k in NIVELES]]:
            f = tb.loc[clave]
            filas.append(dict(grupo=x, descripcion=C.GRUPO_INGRESO[x], poblacion=etiqueta, pct=100 * f["est"],
                              inf=100 * f["ic_inf"], sup=100 * f["ic_sup"]))
    dif = tb.loc[[f"grp_{x}_dif_mh" for x in "ABCD"]].reset_index()
    dif["grupo"] = list("ABCD")
    dif = dif.assign(dif_pp=100 * dif["est"], dif_inf=100 * dif["ic_inf"], dif_sup=100 * dif["ic_sup"])[["grupo", "dif_pp", "dif_inf", "dif_sup", "p"]]
    return pd.DataFrame(filas), dif


def tablas_retorno(r: ResultadoBoot, W: Sub) -> dict[str, pd.DataFrame]:
    tb = r.tabla()
    ent = _nombre_ent()
    for pref, nom, esc in [("rho_ent", "rho", 1), ("ret_ent", "ret", 100), ("med_ent", "mln", 1), ("esc_ent", "esc_sal", 1)]:
        t = _por_entidad(tb, pref)[["est", "ee", "ic_inf", "ic_sup"]]
        if nom == "ret":                                      # log-puntos por año -> % por año
            t = 100 * (np.exp(t[["est", "ic_inf", "ic_sup"]]) - 1).assign(ee=np.nan)
        if nom == "mln":                                      # ln de la mediana -> pesos por hora
            t = np.exp(t[["est", "ic_inf", "ic_sup"]]).assign(ee=np.nan)
        ent = ent.join(t.rename(columns=lambda c: f"{nom}_{c}"))
    ent = ent.join(_rangos(r, "rho_ent").add_prefix("rho_"))
    ent = ent.join(_rangos(r, "med_ent").add_prefix("med_"))
    ent["n_salarial"] = W.df.groupby("cve_ent").size()
    ent["pob_salarial_millones"] = W.df.groupby("cve_ent")["fac_tri"].sum() / 1e6
    orden = ent["mln_est"].rank(method="first").astype(int)
    ent["cuartil_ingreso"] = pd.cut(orden, bins=[0, 8, 16, 24, 32], labels=[1, 2, 3, 4]).astype(int)
    idx = tb.set_index("nombre")
    resumen = []
    for nombre, etiqueta in [("rho_nac", "Spearman nacional (escolaridad - ingreso/hora)"),
                             ("ret_nac", "Rendimiento nacional por año de escolaridad (%)"),
                             ("ret_hombres", "Rendimiento por año - hombres (%)"),
                             ("ret_mujeres", "Rendimiento por año - mujeres (%)"),
                             ("ret_dif_mh", "Diferencia mujeres - hombres (log-puntos)"),
                             *[(f"ret_Q{k}", f"Rendimiento medio, cuartil {k} de ingreso estatal (%)") for k in (1, 2, 3, 4)],
                             *[(f"rho_Q{k}", f"Spearman medio, cuartil {k} de ingreso estatal") for k in (1, 2, 3, 4)],
                             ("ret_dif_Q4_Q1", "Diferencia de rendimiento Q4 - Q1 (log-puntos)"),
                             ("rho_dif_Q4_Q1", "Diferencia de Spearman Q4 - Q1"),
                             ("rho_estatal_esc_med", "Spearman entre estados: escolaridad media vs. ingreso mediano"),
                             ("rho_estatal_ret_med", "Spearman entre estados: rendimiento vs. ingreso mediano")]:
        f = idx.loc[nombre]
        e, lo, hi = f["est"], f["ic_inf"], f["ic_sup"]
        if nombre in ("ret_nac", "ret_hombres", "ret_mujeres") or nombre.startswith("ret_Q"):
            e, lo, hi = (100 * (np.exp(v) - 1) for v in (e, lo, hi))
        resumen.append(dict(indicador=etiqueta, est=e, ee=f["ee"], ic_inf=lo, ic_sup=hi, p=f["p"]))
    return {"retorno_entidad": ent.reset_index(), "retorno_resumen": pd.DataFrame(resumen)}


def tabla_brecha_nivel(r: ResultadoBoot, W: Sub, clasicos: pd.DataFrame) -> pd.DataFrame:
    t = r.tabla().set_index("nombre")
    filas = []
    for k in NIVELES + ["total"]:
        sfx = f"niv{k}" if k != "total" else "total"
        if k == "total":
            nivel, mh, mm, hh, hm = "Total", t.loc["media_ln_hora_h", "est"], t.loc["media_ln_hora_m", "est"], t.loc["horas_media_h", "est"], t.loc["horas_media_m", "est"]
            sub = W.df
        else:
            nivel = f"{k}. {C.NIV_INS[k]}"
            mh, mm = t.loc[f"mln_hora_niv{k}_h", "est"], t.loc[f"mln_hora_niv{k}_m", "est"]
            hh, hm = t.loc[f"horas_niv{k}_h", "est"], t.loc[f"horas_niv{k}_m", "est"]
            sub = W.df[W.df["niv_ins"] == k]
        gh, gm, gr = t.loc[f"gap_hora_{sfx}"], t.loc[f"gap_mens_{sfx}"], t.loc[f"gap_hrs_{sfx}"]
        filas.append(dict(
            nivel=nivel, n_hombres=int((sub["mujer"] == 0).sum()), n_mujeres=int((sub["mujer"] == 1).sum()),
            part_mujeres_pct=100 * t.loc[f"part_mujeres_{sfx}", "est"],
            ing_hora_h=float(np.exp(mh)), ing_hora_m=float(np.exp(mm)),
            gap_hora_log=gh["est"], gap_hora_ee=gh["ee"], brecha_hora_pct=brecha_pct(gh["est"]),
            brecha_hora_inf=brecha_pct(gh["ic_inf"]), brecha_hora_sup=brecha_pct(gh["ic_sup"]), p_hora=gh["p"],
            brecha_mens_pct=brecha_pct(gm["est"]), brecha_mens_inf=brecha_pct(gm["ic_inf"]), brecha_mens_sup=brecha_pct(gm["ic_sup"]), p_mens=gm["p"],
            horas_h=hh, horas_m=hm, menos_horas_mujeres_pct=brecha_pct(gr["est"]),
            menos_horas_inf=brecha_pct(gr["ic_inf"]), menos_horas_sup=brecha_pct(gr["ic_sup"]),
        ))
    out = pd.DataFrame(filas)
    cuatro = out["nivel"] != "Total"
    out["p_hora_holm"] = np.nan
    out.loc[cuatro, "p_hora_holm"] = holm(out.loc[cuatro, "p_hora"].to_numpy())
    cl = clasicos.set_index("nivel")
    for col in ["p_welch", "p_welch_holm", "p_mwu", "p_mwu_holm", "d_cohen", "r_biserial"]:
        out[col] = [cl.loc[n if n == "Total" else n, col] for n in out["nivel"]]
    return out


def tabla_brecha_estados(r: ResultadoBoot) -> pd.DataFrame:
    tb = r.tabla()
    ent = _nombre_ent()
    for pref, nom in [("gap_hora_ent", "brecha_hora"), ("gap_mens_ent", "brecha_mens")]:
        t = _por_entidad(tb, pref)[["est", "ic_inf", "ic_sup", "p"]]
        t = t.assign(est=brecha_pct(t["est"]), ic_inf=brecha_pct(t["ic_inf"]), ic_sup=brecha_pct(t["ic_sup"]))
        ent = ent.join(t.rename(columns=lambda c: f"{nom}_{c}"))
    return ent.reset_index()


def tabla_cuantiles(r: ResultadoBoot) -> pd.DataFrame:
    filas = []
    for q in E.QS:
        k = int(100 * q)
        r2 = r.derivar(f"gap_q{k}", lambda a, b: a - b, [f"q{k}_hombres", f"q{k}_mujeres"])
        t = r2.tabla().set_index("nombre")
        h, m, g = t.loc[f"q{k}_hombres"], t.loc[f"q{k}_mujeres"], t.loc[f"gap_q{k}"]
        filas.append(dict(percentil=k, ing_hora_h=float(np.exp(h["est"])), ing_hora_m=float(np.exp(m["est"])),
                          brecha_pct=brecha_pct(g["est"]), inf=brecha_pct(g["ic_inf"]), sup=brecha_pct(g["ic_sup"]), p=g["p"]))
    return pd.DataFrame(filas)


def tabla_oaxaca(r: ResultadoBoot, etiqueta: str) -> pd.DataFrame:
    t = r.tabla().set_index("nombre")
    nombres = {"ob_total": "Brecha total (log-puntos)", "ob_N_explicada": "Explicada por características (referencia agrupada)",
               "ob_N_no_explicada": "No explicada (referencia agrupada)", "ob_N_exp_educ": "  · escolaridad",
               "ob_N_exp_exper": "  · edad / experiencia", "ob_N_exp_geo": "  · entidad y tamaño de localidad",
               "ob_N_exp_empleo": "  · posición e informalidad", "ob_N_exp_rama": "  · rama de actividad",
               "ob_N_exp_horas": "  · horas trabajadas",
               "ob_H_explicada": "Explicada (coef. de hombres como referencia)", "ob_H_no_explicada": "No explicada (coef. de hombres)",
               "ob_M_explicada": "Explicada (coef. de mujeres como referencia)", "ob_M_no_explicada": "No explicada (coef. de mujeres)"}
    filas = []
    for k, etq in nombres.items():
        if k in t.index:
            f = t.loc[k]
            filas.append(dict(especificacion=etiqueta, componente=etq, log_puntos=f["est"], ee=f["ee"], ic_inf=f["ic_inf"], ic_sup=f["ic_sup"], p=f["p"]))
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# robustez de la brecha por hora
# --------------------------------------------------------------------------- #
def robustez_brecha(D: Datos, W: Sub, r_base: ResultadoBoot, ipw: pd.DataFrame, escalera: pd.DataFrame,
                    clasicos: pd.DataFrame, B: int) -> pd.DataFrame:
    df = D.df
    comunes = df["horas_validas"] & df["anios_esc_valido"] & df["nivel_especificado"] & df["en_ventana_15_65"]
    specs = []

    def tabla_spec(nombre, descripcion, res: ResultadoBoot, n):
        t = res.tabla().set_index("nombre")
        for g in [f"gap_niv{k}" for k in NIVELES] + ["gap_total"]:
            f = t.loc[g]
            specs.append(dict(especificacion=nombre, descripcion=descripcion, grupo="Total" if g == "gap_total" else f"Nivel {g[-1]}",
                              brecha_pct=brecha_pct(f["est"]), inf=brecha_pct(f["ic_inf"]), sup=brecha_pct(f["ic_sup"]), p=f["p"], n=n))

    # S0 base
    est, nom = E.fab_brecha_simple(W.df, "ln_ing_hora")
    tabla_spec("S0 Base", "Grupo A, 15-65 años, sin atípicos, ponderado", correr(est, nom, W, D.diseno, B, C.SEMILLA), len(W))
    # S1 sin recorte de atípicos
    S1 = D.subconjunto(comunes & df["grupo_ingreso"].eq("A"))
    est, nom = E.fab_brecha_simple(S1.df, "ln_ing_hora")
    tabla_spec("S1 Sin recorte", "No se eliminan los atípicos de ingreso por hora", correr(est, nom, S1, D.diseno, B, C.SEMILLA), len(S1))
    # S2 asalariados
    S2 = D.subconjunto(df["en_muestra_salarial"] & (df["pos_ocu"] == 1))
    est, nom = E.fab_brecha_simple(S2.df, "ln_ing_hora")
    tabla_spec("S2 Solo asalariados", "Trabajadores subordinados y remunerados", correr(est, nom, S2, D.diseno, B, C.SEMILLA), len(S2))
    # S3 con rangos imputados
    S3 = D.salarial_ext
    est, nom = E.fab_brecha_simple(S3.df, "ln_ing_hora_imp")
    tabla_spec("S3 Con rangos imputados", "Grupo A + grupo B (ingreso imputado por rango de SM)", correr(est, nom, S3, D.diseno, B, C.SEMILLA), len(S3))
    # S4 corrección por no respuesta (IPW)
    p = W.df[["persona_id"]].merge(ipw, on="persona_id", how="left")["p_reporta"].clip(0.05, 0.95).to_numpy()
    est, nom = E.fab_brecha_simple(W.df, "ln_ing_hora", ajuste=1.0 / p)
    tabla_spec("S4 Ajuste por no respuesta", "Ponderadores multiplicados por 1/P(declara monto exacto)", correr(est, nom, W, D.diseno, B, C.SEMILLA), len(W))
    # S5 mediana
    est, nom = E.fab_brecha_simple(W.df, "ln_ing_hora", mediana=True)
    tabla_spec("S5 Medianas", "Diferencia de medianas ponderadas (robusta a asimetría)", correr(est, nom, W, D.diseno, B, C.SEMILLA), len(W))
    # S6 mensual (otro estimando)
    est, nom = E.fab_brecha_simple(W.df, "ln_ing_mensual")
    tabla_spec("S6 Ingreso mensual", "Ingreso mensual en lugar de por hora (incluye diferencia de jornada)", correr(est, nom, W, D.diseno, B, C.SEMILLA), len(W))
    # S7 sin ponderar (clásico)
    cl = clasicos.set_index("nivel")
    d = W.df
    for nivel, m in [(f"{k}. {C.NIV_INS[k]}", d["niv_ins"] == k) for k in NIVELES] + [("Total", d["niv_ins"].between(1, 4))]:
        h, f = d.loc[m & (d["mujer"] == 0), "ln_ing_hora"], d.loc[m & (d["mujer"] == 1), "ln_ing_hora"]
        dif = h.mean() - f.mean()
        se = np.sqrt(h.var(ddof=1) / len(h) + f.var(ddof=1) / len(f))
        specs.append(dict(especificacion="S7 Sin ponderar", descripcion="Medias de la muestra sin ponderadores ni diseño (IC clásico de Welch)",
                          grupo="Total" if nivel == "Total" else f"Nivel {nivel[0]}", brecha_pct=brecha_pct(dif),
                          inf=brecha_pct(dif - 1.96 * se), sup=brecha_pct(dif + 1.96 * se), p=cl.loc[nivel, "p_welch"], n=len(h) + len(f)))
    # S8/S9 ajustada por regresión (solo total)
    for g, etiqueta in [("G5 + rama de actividad", "S8 Ajustada (sin horas)"), ("G6 + horas trabajadas", "S9 Ajustada (con horas; sesgo de división)")]:
        f = escalera.set_index("modelo").loc[g]
        specs.append(dict(especificacion=etiqueta, descripcion=f"Regresión WLS con controles ({g[:2]}), IC robusto por UPM", grupo="Total",
                          brecha_pct=f["brecha_pct"], inf=f["brecha_pct_inf"], sup=f["brecha_pct_sup"], p=f["p"], n=int(f["n"])))
    return pd.DataFrame(specs)


def tabla_brecha_subgrupos(D: Datos, W: Sub, B: int) -> pd.DataFrame:
    """Heterogeneidad de la brecha por hora: informalidad, edad, posición, región, localidad y nivel detallado."""
    df = W.df
    dims = [
        ("Informalidad", "informal", {0: "Formal", 1: "Informal"}),
        ("Grupo de edad", "grupo_edad", {g: g for g in ["15-24", "25-34", "35-44", "45-54", "55-64", "65+"]}),
        ("Posición en la ocupación", "pos_ocu", {1: "Subordinado y remunerado", 2: "Empleador", 3: "Cuenta propia"}),
        ("Región", "region", {r: r for r in C.REGIONES}),
        ("Tamaño de localidad", "t_loc_tri", C.T_LOC_TRI),
        ("Nivel de instrucción detallado", "niv_det", C.NIV_DET),
    ]
    filas = []
    for dim, col, mapa in dims:
        cats = [c for c in mapa if (df[col] == c).any()]
        est, nom = E.fab_brecha_por(df, col, cats)
        r = correr(est, nom, W, D.diseno, B, C.SEMILLA)
        t = r.tabla()
        pv = t["p"].to_numpy()
        for i, c in enumerate(cats):
            sub = df[df[col] == c]
            filas.append(dict(dimension=dim, categoria=mapa[c], n_hombres=int((sub["mujer"] == 0).sum()), n_mujeres=int((sub["mujer"] == 1).sum()),
                              brecha_pct=brecha_pct(t.loc[i, "est"]), inf=brecha_pct(t.loc[i, "ic_inf"]), sup=brecha_pct(t.loc[i, "ic_sup"]),
                              p=pv[i], p_holm_dimension=np.nan))
        idx = [j for j, f in enumerate(filas) if f["dimension"] == dim]
        for j, ph in zip(idx, holm(np.array([filas[j]["p"] for j in idx]))):
            filas[j]["p_holm_dimension"] = ph
    return pd.DataFrame(filas)


def robustez_retorno(D: Datos, W: Sub, ipw: pd.DataFrame) -> pd.DataFrame:
    """¿El rendimiento de un año de escolaridad (≈5 %) depende de a quién se incluye en la muestra?"""
    from .datos import bloques_diseno, ensamblar
    from .survey import regresion_diseno

    df = D.df
    comunes = df["horas_validas"] & df["anios_esc_valido"] & df["nivel_especificado"] & df["en_ventana_15_65"]
    p = W.df[["persona_id"]].merge(ipw, on="persona_id", how="left")["p_reporta"].clip(0.05, 0.95).to_numpy()
    casos = [
        ("R0 Base", "Grupo A, 15-65 años, sin atípicos, ponderado", W, "ln_ing_hora", None),
        ("R1 Sin recorte", "No se eliminan los atípicos", D.subconjunto(comunes & df["grupo_ingreso"].eq("A")), "ln_ing_hora", None),
        ("R2 Solo asalariados", "Trabajadores subordinados y remunerados", D.subconjunto(df["en_muestra_salarial"] & (df["pos_ocu"] == 1)), "ln_ing_hora", None),
        ("R3 Con rangos imputados", "Grupo A + grupo B (ingreso imputado por rango)", D.salarial_ext, "ln_ing_hora_imp", None),
        ("R4 Ajuste por no respuesta", "Ponderadores x 1/P(declara monto exacto)", W, "ln_ing_hora", 1.0 / p),
        ("R5 Sin ponderar", "Sin ponderadores (errores por UPM)", W, "ln_ing_hora", "uno"),
        ("R6 Ingreso mensual", "Ingreso mensual en vez de por hora", W, "ln_ing_mensual", None),
    ]
    filas = []
    for nombre, desc, S, ycol, ajuste in casos:
        X, cols, _ = ensamblar(bloques_diseno(S.df), ["const", "educ", "exper", "mujer", "geo"])
        w = np.ones(len(S)) if isinstance(ajuste, str) else (S.w if ajuste is None else S.w * ajuste)
        f = regresion_diseno(X, S.col(ycol), w, S.psu, D.diseno, cols).fila("anios_esc")
        filas.append(dict(especificacion=nombre, descripcion=desc, n=len(S), retorno_pct=100 * (np.exp(f["coef"]) - 1),
                          inf=100 * (np.exp(f["ic_inf"]) - 1), sup=100 * (np.exp(f["ic_sup"]) - 1), p=f["p"]))
    return pd.DataFrame(filas)


def perfil_grupos_ingreso(V: Sub) -> pd.DataFrame:
    """¿En qué se distinguen quienes declaran monto exacto (A) de quienes dan solo un rango (B), no reciben (C) o no especifican (D)?"""
    d = V.df[V.df["niv_ins"].between(1, 4) & V.df["anios_esc_valido"]]
    filas = []
    for g, s in d.groupby("grupo_ingreso"):
        w = s["fac_tri"].to_numpy()
        m = lambda c: float(np.average(s[c].to_numpy(float), weights=w))
        filas.append(dict(grupo=g, descripcion=C.GRUPO_INGRESO[g], n=len(s), poblacion_millones=w.sum() / 1e6,
                          mujeres_pct=100 * m("mujer"), anios_esc=m("anios_esc"), edad=m("eda"), informal_pct=100 * m("informal"),
                          empleadores_pct=100 * float(np.average((s["pos_ocu"] == 2).to_numpy(float), weights=w)),
                          cuenta_propia_pct=100 * float(np.average((s["pos_ocu"] == 3).to_numpy(float), weights=w)),
                          sin_pago_pct=100 * float(np.average((s["pos_ocu"] == 4).to_numpy(float), weights=w)),
                          horas_semana=float(np.average(s["hrsocup_raw"].to_numpy(float), weights=w))))
    return pd.DataFrame(filas)


def efecto_diseno(U: Sub, W: Sub, r_univ: ResultadoBoot, r_brech: ResultadoBoot) -> pd.DataFrame:
    """deff = Var(diseño complejo, bootstrap) / Var(m.a.s. con el mismo n)."""
    filas = []
    tu = r_univ.tabla().set_index("nombre")
    p = tu.loc["til1_nac", "est"]
    n = len(U)
    filas.append(dict(estimador="TIL1 nacional", n=n, ee_diseno=tu.loc["til1_nac", "ee"], ee_mas=np.sqrt(p * (1 - p) / n)))
    tb = r_brech.tabla().set_index("nombre")
    d = W.df
    h, f = d.loc[d["mujer"] == 0, "ln_ing_hora"], d.loc[d["mujer"] == 1, "ln_ing_hora"]
    filas.append(dict(estimador="Media de ln(ingreso/hora), hombres", n=len(h), ee_diseno=np.nan, ee_mas=h.std(ddof=1) / np.sqrt(len(h))))
    filas.append(dict(estimador="Media de ln(ingreso/hora), mujeres", n=len(f), ee_diseno=np.nan, ee_mas=f.std(ddof=1) / np.sqrt(len(f))))
    filas.append(dict(estimador="Brecha por hora total (log-puntos)", n=len(d), ee_diseno=tb.loc["gap_hora_total", "ee"],
                      ee_mas=np.sqrt(h.var(ddof=1) / len(h) + f.var(ddof=1) / len(f))))
    t = pd.DataFrame(filas)
    t["deff"] = (t["ee_diseno"] / t["ee_mas"]) ** 2
    t["n_efectivo"] = t["n"] / t["deff"]
    return t


# --------------------------------------------------------------------------- #
# ejecución completa
# --------------------------------------------------------------------------- #
def ejecutar_analisis(B: int | None = None, D: Datos | None = None) -> tuple[dict, dict]:
    B = B or C.N_BOOTSTRAP
    t0 = time.time()
    D = D or cargar_datos()
    U, V, W = D.universo, D.ventana, D.salarial
    T: dict[str, pd.DataFrame] = {}
    log.info("Datos: universo=%s ventana=%s salarial=%s | B=%d", f"{len(U):,}", f"{len(V):,}", f"{len(W):,}", B)

    def paso(nombre):
        log.info("[%6.1fs] %s", time.time() - t0, nombre)

    # 1. Informalidad (universo 15+)
    paso("Informalidad por entidad (universo 15+)")
    est, nom = E.fab_universo(U)
    r_univ = correr(est, nom, U, D.diseno, B, C.SEMILLA)
    T.update(tablas_informalidad(r_univ))

    # 2. Calidad del ingreso (ventana 15-65)
    paso("Calidad del ingreso (grupos A/B/C/D)")
    est, nom = E.fab_grupos(V)
    r_grp = correr(est, nom, V, D.diseno, B, C.SEMILLA)
    T["calidad_ingreso"], T["calidad_ingreso_dif_mh"] = tabla_calidad_ingreso(r_grp)
    T["calidad_ingreso_chi2"] = M.chi2_calidad(V)

    # 3. Modelos de no respuesta e IPW
    paso("Modelos de no respuesta (logit con errores por UPM)")
    lg_a, lg_d, ipw = M.logit_reporte(V, D.diseno)
    T["no_respuesta_logit"] = pd.concat([lg_a, lg_d])

    # 4. Rendimiento y correlación por entidad
    paso("Rendimiento de la escolaridad y Spearman por entidad")
    est, nom = E.fab_retorno(W)
    r_ret = correr(est, nom, W, D.diseno, B, C.SEMILLA)
    T.update(tablas_retorno(r_ret, W))
    T["retorno_modelos"] = M.retorno_modelos(W, D.diseno)
    T["premio_por_nivel"] = M.premio_por_nivel(W, D.diseno)

    # 5. Brechas de género
    paso("Brechas de género (hora, mensual, horas)")
    est, nom = E.fab_brechas(W)
    r_brech = correr(est, nom, W, D.diseno, B, C.SEMILLA)
    T["tests_clasicos"] = M.tests_clasicos(W)
    T["brecha_nivel"] = tabla_brecha_nivel(r_brech, W, T["tests_clasicos"])
    T["brecha_estados"] = tabla_brecha_estados(r_brech)
    T["brecha_cuantiles"] = tabla_cuantiles(r_brech)
    T["escalera_brecha"] = M.escalera_brecha(W, D.diseno)

    # 6. Oaxaca-Blinder (sin y con horas)
    paso("Descomposición de Oaxaca-Blinder")
    est, nom = E.fab_oaxaca(W, ["const", "educ", "exper", "geo", "empleo", "rama"])
    r_ob = correr(est, nom, W, D.diseno, B, C.SEMILLA)
    est2, nom2 = E.fab_oaxaca(W, ["const", "educ", "exper", "geo", "empleo", "rama", "horas"])
    r_ob2 = correr(est2, nom2, W, D.diseno, B, C.SEMILLA)
    T["oaxaca"] = pd.concat([tabla_oaxaca(r_ob, "Principal (sin horas)"), tabla_oaxaca(r_ob2, "Con horas (sesgo de división)")])

    # 7. Robustez
    paso("Robustez de la brecha por hora (S0-S9)")
    T["robustez_brecha"] = robustez_brecha(D, W, r_brech, ipw, T["escalera_brecha"], T["tests_clasicos"], B)
    T["brecha_subgrupos"] = tabla_brecha_subgrupos(D, W, B)
    T["robustez_retorno"] = robustez_retorno(D, W, ipw)
    T["perfil_grupos_ingreso"] = perfil_grupos_ingreso(V)

    # 8. Informalidad individual y diagnósticos
    paso("Modelos de informalidad y diagnósticos")
    T["logit_informalidad"], resumen_inf = M.logit_informalidad(V, D.diseno)
    diag = M.diagnosticos(W, D.diseno)
    diag.pop("residuos_ols"), diag.pop("ajustados_ols")          # arreglos grandes: no van al JSON
    T["efecto_diseno"] = efecto_diseno(U, W, r_univ, r_brech)

    # 9. Descriptivos de la muestra salarial
    T["descriptivos_salario"] = descriptivos_salario(W)

    resumen = construir_resumen(D, T, r_univ, r_ret, r_brech, r_ob, r_ob2, resumen_inf, diag, B)
    paso("Análisis terminado")
    return T, resumen


class _Codificador(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.floating,)):
            return None if np.isnan(o) else float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)


def guardar_resultados(T: dict, resumen: dict, db_path=None) -> None:
    """CSV por tabla, JSON de cifras clave y tablas ``res_*`` dentro de la base SQLite."""
    from . import load_sqlite

    C.RESULTS.mkdir(parents=True, exist_ok=True)
    for nombre, df in T.items():
        df.to_csv(C.RESULTS / f"{nombre}.csv", index=False, encoding="utf-8-sig")
    (C.RESULTS / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False, cls=_Codificador), encoding="utf-8")
    con = load_sqlite.conectar(db_path)
    for nombre, df in T.items():
        load_sqlite.guardar_tabla(con, f"res_{nombre}", df)
    con.commit()
    con.close()


def descriptivos_salario(W: Sub) -> pd.DataFrame:
    from .survey import cuantil_ponderado, media_ponderada

    d = W.df
    filas = []
    for etiqueta, m in [("Total", np.ones(len(d), bool)), ("Hombres", d["mujer"] == 0), ("Mujeres", d["mujer"] == 1)]:
        s = d[m]
        w = s["fac_tri"].to_numpy()
        for var, nombre in [("ing_hora", "Ingreso por hora ($)"), ("ing_mensual", "Ingreso mensual ($)"), ("hrsocup", "Horas por semana"),
                            ("anios_esc", "Años de escolaridad"), ("eda", "Edad")]:
            x = s[var].to_numpy(float)
            filas.append(dict(grupo=etiqueta, variable=nombre, n=len(s), media_pond=media_ponderada(x, w),
                              mediana_pond=cuantil_ponderado(x, w, 0.5), p10=cuantil_ponderado(x, w, 0.1),
                              p90=cuantil_ponderado(x, w, 0.9), media_simple=float(x.mean()), asimetria=float(stats.skew(x))))
    return pd.DataFrame(filas)


def construir_resumen(D, T, r_univ, r_ret, r_brech, r_ob, r_ob2, resumen_inf, diag, B) -> dict:
    """Cifras clave que citan el cuaderno, la presentación y el tablero (una sola fuente de verdad)."""
    til = T["til1_grupos"].set_index("grupo")
    ent = T["til1_entidad"].sort_values("til1_est", ascending=False)
    ret = T["retorno_entidad"]
    bn = T["brecha_nivel"].set_index("nivel")
    rb = T["retorno_resumen"].set_index("indicador")
    esc = T["escalera_brecha"].set_index("modelo")
    ob = T["oaxaca"]
    asoc = T["til1_vs_escolaridad_estatal"].set_index("indicador")
    robustez = T["robustez_brecha"]

    def d(fila, *cols):
        return {c: float(fila[c]) for c in cols}

    resumen = {
        "B": B,
        "muestras": {"universo": len(D.df), "ventana_15_65": int(D.df["en_ventana_15_65"].sum()),
                     "salarial": int(D.df["en_muestra_salarial"].sum()), "salarial_ext": int(D.df["en_muestra_salarial_ext"].sum()),
                     "ocupados_millones": float(D.df["fac_tri"].sum() / 1e6), "salarial_poblacion_millones": float(D.df.loc[D.df["en_muestra_salarial"], "fac_tri"].sum() / 1e6)},
        "til1": {"nacional": d(til.loc["Nacional"], "est", "ic_inf", "ic_sup"), "hombres": d(til.loc["Hombres"], "est", "ic_inf", "ic_sup"),
                 "mujeres": d(til.loc["Mujeres"], "est", "ic_inf", "ic_sup"),
                 "top3": [dict(entidad=r.entidad, pct=float(r.til1_est), inf=float(r.til1_ic_inf), sup=float(r.til1_ic_sup)) for r in ent.head(3).itertuples()],
                 "bottom3": [dict(entidad=r.entidad, pct=float(r.til1_est), inf=float(r.til1_ic_inf), sup=float(r.til1_ic_sup)) for r in ent.tail(3).iloc[::-1].itertuples()],
                 "por_nivel": {k: float(til.loc[f"Nivel {k}. {C.NIV_INS[k]}", "est"]) for k in NIVELES},
                 "regiones": {rg: float(til.loc[f"Región {rg}", "est"]) for rg in C.REGIONES}},
        "til1_vs_escolaridad_estatal": {k: d(asoc.loc[k], "est", "ic_inf", "ic_sup") for k in asoc.index},
        "individual_informalidad": resumen_inf,
        "retorno": {"nacional_pct": d(rb.loc["Rendimiento nacional por año de escolaridad (%)"], "est", "ic_inf", "ic_sup"),
                    "hombres_pct": d(rb.loc["Rendimiento por año - hombres (%)"], "est", "ic_inf", "ic_sup"),
                    "mujeres_pct": d(rb.loc["Rendimiento por año - mujeres (%)"], "est", "ic_inf", "ic_sup"),
                    "dif_mujeres_hombres_log": d(rb.loc["Diferencia mujeres - hombres (log-puntos)"], "est", "ic_inf", "ic_sup", "p"),
                    "spearman_nacional": d(rb.loc["Spearman nacional (escolaridad - ingreso/hora)"], "est", "ic_inf", "ic_sup"),
                    "q1_pct": d(rb.loc["Rendimiento medio, cuartil 1 de ingreso estatal (%)"], "est", "ic_inf", "ic_sup"),
                    "q4_pct": d(rb.loc["Rendimiento medio, cuartil 4 de ingreso estatal (%)"], "est", "ic_inf", "ic_sup"),
                    "dif_q4_q1_log": d(rb.loc["Diferencia de rendimiento Q4 - Q1 (log-puntos)"], "est", "ic_inf", "ic_sup", "p"),
                    "dif_rho_q4_q1": d(rb.loc["Diferencia de Spearman Q4 - Q1"], "est", "ic_inf", "ic_sup", "p"),
                    "rho_estatal_esc_ingreso": d(rb.loc["Spearman entre estados: escolaridad media vs. ingreso mediano"], "est", "ic_inf", "ic_sup"),
                    "rho_estatal_ret_ingreso": d(rb.loc["Spearman entre estados: rendimiento vs. ingreso mediano"], "est", "ic_inf", "ic_sup"),
                    "rho_max": dict(entidad=ret.loc[ret["rho_est"].idxmax(), "entidad"], **d(ret.loc[ret["rho_est"].idxmax()], "rho_est", "rho_ic_inf", "rho_ic_sup")),
                    "rho_min": dict(entidad=ret.loc[ret["rho_est"].idxmin(), "entidad"], **d(ret.loc[ret["rho_est"].idxmin()], "rho_est", "rho_ic_inf", "rho_ic_sup")),
                    "ret_max": dict(entidad=ret.loc[ret["ret_est"].idxmax(), "entidad"], **d(ret.loc[ret["ret_est"].idxmax()], "ret_est", "ret_ic_inf", "ret_ic_sup")),
                    "ret_min": dict(entidad=ret.loc[ret["ret_est"].idxmin(), "entidad"], **d(ret.loc[ret["ret_est"].idxmin()], "ret_est", "ret_ic_inf", "ret_ic_sup"))},
        "brecha": {"total_hora": d(bn.loc["Total"], "brecha_hora_pct", "brecha_hora_inf", "brecha_hora_sup", "p_hora"),
                   "total_mens": d(bn.loc["Total"], "brecha_mens_pct", "brecha_mens_inf", "brecha_mens_sup"),
                   "total_horas": d(bn.loc["Total"], "menos_horas_mujeres_pct", "menos_horas_inf", "menos_horas_sup", "horas_h", "horas_m"),
                   "por_nivel": {k: d(bn.loc[f"{k}. {C.NIV_INS[k]}"], "brecha_hora_pct", "brecha_hora_inf", "brecha_hora_sup", "p_hora", "p_hora_holm", "brecha_mens_pct", "n_hombres", "n_mujeres") for k in NIVELES},
                   "escalera": {m: d(esc.loc[m], "brecha_pct", "brecha_pct_inf", "brecha_pct_sup", "p") for m in esc.index},
                   "robustez_total": {r.especificacion: dict(pct=float(r.brecha_pct), inf=float(r.inf), sup=float(r.sup)) for r in robustez[robustez["grupo"] == "Total"].itertuples()}},
        "oaxaca": {r.componente.strip(" ·"): dict(est=float(r.log_puntos), inf=float(r.ic_inf), sup=float(r.ic_sup)) for r in ob[ob["especificacion"].str.startswith("Principal")].itertuples()},
        "oaxaca_con_horas": {r.componente.strip(" ·"): dict(est=float(r.log_puntos), inf=float(r.ic_inf), sup=float(r.ic_sup)) for r in ob[ob["especificacion"].str.startswith("Con horas")].itertuples()},
        "retorno_robustez": {r.especificacion: dict(pct=float(r.retorno_pct), inf=float(r.inf), sup=float(r.sup)) for r in T["robustez_retorno"].itertuples()},
        "diagnosticos": diag,
        "efecto_diseno": {r.estimador: dict(deff=float(r.deff), n_efectivo=float(r.n_efectivo)) for r in T["efecto_diseno"].itertuples() if not np.isnan(r.deff)},
    }
    return resumen
