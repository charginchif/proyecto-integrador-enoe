"""Modelos paramétricos con inferencia de diseño muestral.

Todos los modelos usan el ponderador ``fac_tri`` y errores estándar de sándwich con
linealización de Taylor que respetan estratos y UPM (``survey.regresion_diseno`` y
``survey.logit_diseno``), equivalentes a lo que reporta ``svy:`` en Stata o ``survey`` en R.
Los puntos estimados coinciden con statsmodels (ver tests/test_modelos.py); lo que cambia
es la varianza, que statsmodels no calcula bien con ponderadores de muestreo y conglomerados.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan

from . import config as C
from .datos import ESCALERA, Sub, bloques_diseno, ensamblar
from .survey import Diseno, holm, logit_diseno, regresion_diseno


def _pct_menos(b):
    """Coeficiente de 'mujer' en log-puntos -> % menos que ganan las mujeres respecto a los hombres."""
    return 100 * (1 - np.exp(b))


def _pct_mas(b):
    return 100 * (np.exp(b) - 1)


# --------------------------------------------------------------------------- #
# Brecha de género: escalera de controles
# --------------------------------------------------------------------------- #
def escalera_brecha(S: Sub, diseno: Diseno) -> pd.DataFrame:
    """Coeficiente de 'mujer' en ln(ingreso por hora) al ir agregando controles (G0 ... G6)."""
    y, w = S.col("ln_ing_hora"), S.w
    bl = bloques_diseno(S.df)
    filas = []
    for nombre, bloques in ESCALERA.items():
        X, cols, _ = ensamblar(bl, bloques)
        r = regresion_diseno(X, y, w, S.psu, diseno, cols)
        f = r.fila("mujer")
        f.update(modelo=nombre, n=len(y), n_parametros=X.shape[1], r2=r.extra["r2"],
                 brecha_pct=_pct_menos(f["coef"]), brecha_pct_inf=_pct_menos(f["ic_sup"]), brecha_pct_sup=_pct_menos(f["ic_inf"]))
        filas.append(f)
    t = pd.DataFrame(filas)
    return t[["modelo", "coef", "ee", "ic_inf", "ic_sup", "p", "brecha_pct", "brecha_pct_inf", "brecha_pct_sup", "r2", "n", "n_parametros"]]


def retorno_modelos(S: Sub, diseno: Diseno) -> pd.DataFrame:
    """Rendimiento de un año adicional de escolaridad bajo especificaciones sucesivas (ecuación de Mincer)."""
    y, w = S.col("ln_ing_hora"), S.w
    bl = bloques_diseno(S.df)
    esp = {
        "M1 Mincer simple": ["const", "educ"],
        "M2 + edad, edad² y sexo": ["const", "educ", "exper", "mujer"],
        "M3 + entidad y localidad": ["const", "educ", "exper", "mujer", "geo"],
        "M4 + posición, informalidad y rama": ["const", "educ", "exper", "mujer", "geo", "empleo", "rama"],
    }
    filas = []

    def agrega(res, coef, etiqueta):
        f = res.fila(coef)
        f.update(modelo=etiqueta, n=len(y), r2=res.extra["r2"], retorno_pct=_pct_mas(f["coef"]),
                 retorno_pct_inf=_pct_mas(f["ic_inf"]), retorno_pct_sup=_pct_mas(f["ic_sup"]))
        filas.append(f)

    for nombre, bloques in esp.items():
        X, cols, _ = ensamblar(bl, bloques)
        agrega(regresion_diseno(X, y, w, S.psu, diseno, cols), "anios_esc", nombre)
    # Interacción escolaridad x sexo: ¿el rendimiento de estudiar es distinto para las mujeres?
    X, cols, _ = ensamblar(bl, ["const", "educ", "exper", "mujer", "geo"])
    X = np.column_stack([X, S.col("anios_esc") * S.col("mujer")])
    r = regresion_diseno(X, y, w, S.psu, diseno, cols + ["anios_esc:mujer"])
    agrega(r, "anios_esc", "M5 interacción: efecto en hombres")
    agrega(r, "anios_esc:mujer", "M5 interacción: diferencia de las mujeres")
    return pd.DataFrame(filas)


def premio_por_nivel(S: Sub, diseno: Diseno) -> pd.DataFrame:
    """Premio salarial de cada nivel respecto a 'primaria incompleta' (controlando edad, sexo y entidad)."""
    d = S.df
    y, w = S.col("ln_ing_hora"), S.w
    X, cols, _ = ensamblar(bloques_diseno(d), ["const", "exper", "mujer", "geo"])
    niveles = [2, 3, 4, 5]
    X = np.column_stack([X, np.column_stack([(d["niv_det"].to_numpy() == k).astype(float) for k in niveles])])
    cols = cols + [C.NIV_DET[k] for k in niveles]
    r = regresion_diseno(X, y, w, S.psu, diseno, cols)
    filas = []
    for k in niveles:
        f = r.fila(C.NIV_DET[k])
        filas.append(dict(nivel=C.NIV_DET[k], premio_pct=_pct_mas(f["coef"]), inf=_pct_mas(f["ic_inf"]), sup=_pct_mas(f["ic_sup"]),
                          p=f["p"], n=int((d["niv_det"] == k).sum())))
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Pruebas clásicas (sin ponderar), como en el protocolo: Welch y Mann-Whitney por nivel
# --------------------------------------------------------------------------- #
def tests_clasicos(S: Sub, ycol: str = "ln_ing_hora") -> pd.DataFrame:
    d = S.df
    filas = []
    grupos = [(f"{k}. {C.NIV_INS[k]}", d["niv_ins"] == k) for k in (1, 2, 3, 4)] + [("Total", d["niv_ins"].between(1, 4))]
    for etiqueta, m in grupos:
        h = d.loc[m & (d["mujer"] == 0), ycol].to_numpy()
        f = d.loc[m & (d["mujer"] == 1), ycol].to_numpy()
        t = stats.ttest_ind(h, f, equal_var=False)
        u = stats.mannwhitneyu(h, f, alternative="two-sided")
        sp = np.sqrt(((len(h) - 1) * h.var(ddof=1) + (len(f) - 1) * f.var(ddof=1)) / (len(h) + len(f) - 2))
        filas.append(dict(nivel=etiqueta, n_hombres=len(h), n_mujeres=len(f),
                          dif_medias_ln=h.mean() - f.mean(), t_welch=t.statistic, p_welch=t.pvalue,
                          U=u.statistic, p_mwu=u.pvalue, d_cohen=(h.mean() - f.mean()) / sp,
                          r_biserial=2 * u.statistic / (len(h) * len(f)) - 1))
    t = pd.DataFrame(filas)
    cuatro = t["nivel"] != "Total"
    t["p_welch_holm"] = np.nan
    t["p_mwu_holm"] = np.nan
    t.loc[cuatro, "p_welch_holm"] = holm(t.loc[cuatro, "p_welch"].to_numpy())
    t.loc[cuatro, "p_mwu_holm"] = holm(t.loc[cuatro, "p_mwu"].to_numpy())
    return t


# --------------------------------------------------------------------------- #
# Supuestos y diagnósticos
# --------------------------------------------------------------------------- #
def diagnosticos(S: Sub, diseno: Diseno) -> dict:
    y, w = S.col("ln_ing_hora"), S.w
    X, cols, _ = ensamblar(bloques_diseno(S.df), ESCALERA["G6 + horas trabajadas"])
    n, p = X.shape
    ols = sm.OLS(y, X).fit()
    bp = het_breuschpagan(ols.resid, X)
    # VIF = diagonal de la inversa de la matriz de correlación (sin constante)
    sin_const = [i for i, c in enumerate(cols) if c != "const"]
    R = np.corrcoef(X[:, sin_const], rowvar=False)
    vif = pd.Series(np.diag(np.linalg.inv(R)), index=[cols[i] for i in sin_const])
    clave = ["anios_esc", "eda_c", "eda_c2", "informal", "log_horas", "mujer"]
    # Influencia (distancia de Cook) con apalancamiento vía QR
    Q, _ = np.linalg.qr(X)
    h = (Q ** 2).sum(axis=1)
    e = ols.resid
    s2 = float(e @ e) / (n - p)
    cook = e ** 2 / (p * s2) * h / (1 - h) ** 2
    keep = cook < np.quantile(cook, 0.999)
    im = cols.index("mujer")
    b_all = regresion_diseno(X, y, w, S.psu, diseno, cols).coef[im]
    b_trim = sm.WLS(y[keep], X[keep], weights=w[keep]).fit().params[im]
    rng = np.random.default_rng(C.SEMILLA)
    return {
        "n": n, "p": p,
        "r2_ols": float(ols.rsquared), "r2_ajustado_ols": float(ols.rsquared_adj),
        "breusch_pagan_LM": float(bp[0]), "breusch_pagan_p": float(bp[1]),
        "vif_clave": vif[clave].round(2).to_dict(), "vif_max_variables_clave": float(vif[clave].max()),
        "cook_max": float(cook.max()), "cook_prop_mayor_4_sobre_n": float((cook > 4 / n).mean()),
        "coef_mujer_con_todo": float(b_all), "coef_mujer_sin_influyentes": float(b_trim),
        "asimetria_residuos": float(stats.skew(e)), "curtosis_exceso_residuos": float(stats.kurtosis(e)),
        "asimetria_ln_ingreso": float(stats.skew(y)), "curtosis_exceso_ln_ingreso": float(stats.kurtosis(y)),
        "asimetria_ingreso_nivel": float(stats.skew(S.col("ing_hora"))), "curtosis_exceso_ingreso_nivel": float(stats.kurtosis(S.col("ing_hora"))),
        "dagostino_k2_p_ln_ingreso": float(stats.normaltest(y).pvalue),
        "shapiro_p_ln_ingreso_n5000": float(stats.shapiro(rng.choice(y, 5000, replace=False)).pvalue),
        "residuos_ols": e, "ajustados_ols": ols.fittedvalues,
    }


# --------------------------------------------------------------------------- #
# Informalidad y no respuesta (modelos de elección binaria)
# --------------------------------------------------------------------------- #
def _tabla_logit(res, claves: list[str]) -> pd.DataFrame:
    filas = []
    for c in claves:
        f = res.fila(c)
        filas.append(dict(variable=c, coef=f["coef"], ee=f["ee"], razon_momios=np.exp(f["coef"]),
                          rm_inf=np.exp(f["ic_inf"]), rm_sup=np.exp(f["ic_sup"]), p=f["p"]))
    return pd.DataFrame(filas)


def logit_informalidad(V: Sub, diseno: Diseno) -> tuple[pd.DataFrame, dict]:
    """P(empleo informal) ~ escolaridad + sexo + edad + entidad + localidad (ocupados 15-65)."""
    ok = V.df["anios_esc_valido"].to_numpy()
    sub = Sub(V.df.loc[ok].reset_index(drop=True), V.psu[ok])
    X, cols, _ = ensamblar(bloques_diseno(sub.df), ["const", "educ", "mujer", "exper", "geo"])
    y, w = sub.col("informal"), sub.w
    lg = logit_diseno(X, y, w, sub.psu, diseno, cols)
    lpm = regresion_diseno(X, y, w, sub.psu, diseno, cols)
    p = lg.extra["p"]
    i = cols.index("anios_esc")
    ame = float(np.average(p * (1 - p), weights=w) * lg.coef[i])
    im = cols.index("mujer")
    X1, X0 = X.copy(), X.copy()
    X1[:, im], X0[:, im] = 1.0, 0.0
    sig = lambda z: 1 / (1 + np.exp(-z))
    ame_mujer = float(np.average(sig(X1 @ lg.coef) - sig(X0 @ lg.coef), weights=w))
    f = lpm.fila("anios_esc")
    resumen = {"n": len(y), "ame_anios_esc_pp": 100 * ame, "ame_mujer_pp": 100 * ame_mujer,
               "lpm_anios_esc_pp": 100 * f["coef"], "lpm_anios_esc_pp_inf": 100 * f["ic_inf"], "lpm_anios_esc_pp_sup": 100 * f["ic_sup"],
               "mcfadden": lg.extra["mcfadden"]}
    return _tabla_logit(lg, ["anios_esc", "mujer", "eda_c", "eda_c2"]), resumen


def logit_reporte(V: Sub, diseno: Diseno) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """¿Quién no declara el monto exacto? Dos logit: A vs (B o D)  y  D vs (A o B).

    Devuelve (tabla modelo 1, tabla modelo 2, probabilidades p̂ del modelo 1 para el IPW).
    """
    d = V.df
    m = (d["grupo_ingreso"].isin(["A", "B", "D"]) & d["anios_esc_valido"] & d["nivel_especificado"]).to_numpy()
    sub = Sub(d.loc[m].reset_index(drop=True), V.psu[m])
    X, cols, _ = ensamblar(bloques_diseno(sub.df), ["const", "mujer", "educ", "exper", "empleo", "rama", "geo"])
    w = sub.w
    claves = ["mujer", "anios_esc", "informal", "pos_empleador", "pos_cuenta_propia", "eda_c"]
    salidas, p_hat = [], None
    for nombre, y in [("A_vs_resto", (sub.df["grupo_ingreso"] == "A").astype(float).to_numpy()),
                      ("D_vs_resto", (sub.df["grupo_ingreso"] == "D").astype(float).to_numpy())]:
        lg = logit_diseno(X, y, w, sub.psu, diseno, cols)
        t = _tabla_logit(lg, claves)
        t.insert(0, "modelo", nombre)
        salidas.append(t)
        if nombre == "A_vs_resto":
            p_hat = pd.DataFrame({"persona_id": sub.df["persona_id"], "p_reporta": lg.extra["p"]})
    return salidas[0], salidas[1], p_hat


def chi2_calidad(V: Sub) -> pd.DataFrame:
    """χ² de independencia (sin corrección de diseño; solo descriptivo) y V de Cramér: grupo de ingreso vs. covariables."""
    d = V.df[V.df["niv_ins"].between(1, 4)]
    filas = []
    for etiqueta, col in [("sexo", "sex"), ("nivel de instrucción", "niv_ins"), ("informalidad", "informal"), ("posición", "pos_ocu")]:
        tab = pd.crosstab(d["grupo_ingreso"], d[col])
        chi2, p, gl, _ = stats.chi2_contingency(tab)
        v = np.sqrt(chi2 / (tab.to_numpy().sum() * (min(tab.shape) - 1)))
        filas.append(dict(variable=etiqueta, chi2=chi2, gl=gl, p=p, v_cramer=v, n=int(tab.to_numpy().sum())))
    return pd.DataFrame(filas)
