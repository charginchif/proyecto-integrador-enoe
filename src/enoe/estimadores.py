"""Estimadores de población con incertidumbre por bootstrap de Rao-Wu.

Cada ``fab_*`` es una fábrica: recibe un dominio (``Sub``), precalcula lo que no depende de los
ponderadores (órdenes de clasificación, matrices de diseño, índices por entidad) y devuelve una
función ``estimador(w) -> vector`` que se evalúa con el ponderador original y con cada réplica.
Así el costo por réplica es pequeño y todo el análisis comparte las mismas réplicas (misma semilla).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from . import config as C
from .datos import Sub, bloques_diseno, ensamblar
from .survey import (Diseno, RangosPonderados, bootstrap_rao_wu, correlacion_ponderada, error_estandar,
                     intervalo_percentil, pvalor_normal, wls)

N_ENT = 32
QS = (0.10, 0.25, 0.50, 0.75, 0.90)


# --------------------------------------------------------------------------- #
# Contenedor de resultados
# --------------------------------------------------------------------------- #
@dataclass
class ResultadoBoot:
    nombres: list[str]
    theta: np.ndarray        # (K,) estimación puntual con los ponderadores originales
    reps: np.ndarray         # (B, K) réplicas

    def indice(self, nombre: str) -> int:
        return self.nombres.index(nombre)

    def columnas(self, nombres: list[str]) -> np.ndarray:
        return np.array([self.indice(n) for n in nombres])

    def serie(self, prefijo: str, n: int, ancho: int = 2, desde: int = 1) -> tuple[np.ndarray, np.ndarray]:
        """Vector de n estimaciones y matriz de réplicas con nombres prefijo_01 ... prefijo_n."""
        cols = self.columnas([f"{prefijo}_{i:0{ancho}d}" for i in range(desde, desde + n)])
        return self.theta[cols], self.reps[:, cols]

    def tabla(self, nivel: float = 0.95, nulo: float = 0.0, transformar=None) -> pd.DataFrame:
        """Estimación, error estándar bootstrap, IC percentil y prueba de Wald vs. ``nulo`` (en la escala original)."""
        ee = error_estandar(self.reps)
        ic = intervalo_percentil(self.reps, nivel)
        t = pd.DataFrame({"nombre": self.nombres, "est": self.theta, "ee": ee, "ic_inf": ic[0], "ic_sup": ic[1],
                          "z": (self.theta - nulo) / ee, "p": pvalor_normal(self.theta, ee, nulo)})
        if transformar is not None:
            for c in ("est", "ic_inf", "ic_sup"):
                t[c] = transformar(t[c])
        return t

    def derivar(self, nombre: str, f, columnas_entrada: list[str]) -> "ResultadoBoot":
        """Agrega una estimación derivada (aplicando f a las columnas indicadas, réplica por réplica)."""
        cols = self.columnas(columnas_entrada)
        nuevo_t = np.append(self.theta, f(*[self.theta[c] for c in cols]))
        nuevas_r = np.column_stack([self.reps, f(*[self.reps[:, c] for c in cols])])
        return ResultadoBoot(self.nombres + [nombre], nuevo_t, nuevas_r)


def correr(estimador, nombres: list[str], sub: Sub, diseno: Diseno, B: int, semilla: int,
           w_base: np.ndarray | None = None) -> ResultadoBoot:
    w = sub.w if w_base is None else w_base
    theta, reps = bootstrap_rao_wu(estimador, w, sub.psu, diseno, B, semilla)
    if theta.size != len(nombres):
        raise ValueError(f"El estimador devuelve {theta.size} valores pero hay {len(nombres)} nombres")
    return ResultadoBoot(list(nombres), theta, reps)


def _rank(v: np.ndarray) -> np.ndarray:
    return stats.rankdata(v)


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))


def _sufijos(prefijo: str, n: int, ancho: int = 2) -> list[str]:
    return [f"{prefijo}_{i:0{ancho}d}" for i in range(1, n + 1)]


# --------------------------------------------------------------------------- #
# 1. Universo (ocupados 15+): informalidad y escolaridad por entidad
# --------------------------------------------------------------------------- #
def fab_universo(U: Sub):
    ent = U.df["cve_ent"].to_numpy() - 1
    inf = U.col("informal")
    mujer = U.col("mujer")
    niv = U.df["niv_ins"].to_numpy()
    anios = U.col("anios_esc")
    valido = ~np.isnan(anios)
    anios0 = np.where(valido, anios, 0.0)
    region_de_ent = np.array([C.REGIONES.index(C.ENTIDADES[e + 1][3]) for e in range(N_ENT)])
    reg = region_de_ent[ent]

    nombres = (["til1_nac", "esc_nac", "part_mujeres", "til1_hombres", "til1_mujeres"]
               + _sufijos("til1_ent", N_ENT) + _sufijos("esc_ent", N_ENT) + _sufijos("ocup_ent", N_ENT)
               + [f"til1_reg_{r}" for r in C.REGIONES] + [f"til1_niv{k}" for k in (1, 2, 3, 4)]
               + ["r_pearson_til_esc", "rho_spearman_til_esc", "pendiente_til_esc"])

    def est(w):
        sw_e = np.bincount(ent, w, N_ENT)
        til_e = np.bincount(ent, w * inf, N_ENT) / sw_e
        wv = w * valido
        esc_e = np.bincount(ent, wv * anios0, N_ENT) / np.bincount(ent, wv, N_ENT)
        sw_r = np.bincount(reg, w, 4)
        til_r = np.bincount(reg, w * inf, 4) / sw_r
        sw_n = np.bincount(niv, w, 6)[1:5]
        til_n = np.bincount(niv, w * inf, 6)[1:5] / sw_n
        sw_s = np.bincount(mujer.astype(int), w, 2)
        til_s = np.bincount(mujer.astype(int), w * inf, 2) / sw_s
        r_p = _pearson(til_e, esc_e)
        rho = _pearson(_rank(til_e), _rank(esc_e))
        pend = float(np.cov(esc_e, til_e, ddof=1)[0, 1] / np.var(esc_e, ddof=1))
        return np.concatenate([
            [(w * inf).sum() / w.sum(), (wv * anios0).sum() / wv.sum(), sw_s[1] / sw_s.sum(), til_s[0], til_s[1]],
            til_e, esc_e, sw_e, til_r, til_n, [r_p, rho, pend]])

    return est, nombres


# --------------------------------------------------------------------------- #
# 2. Calidad del ingreso (ventana 15-65): grupos A/B/C/D por sexo y nivel
# --------------------------------------------------------------------------- #
def fab_grupos(V: Sub):
    g = V.df["grupo_ingreso"].map({"A": 0, "B": 1, "C": 2, "D": 3}).to_numpy()
    mujer = V.col("mujer").astype(int)
    niv = V.df["niv_ins"].to_numpy()
    gg = "ABCD"
    nombres = ([f"grp_{x}_nac" for x in gg] + [f"grp_{x}_h" for x in gg] + [f"grp_{x}_m" for x in gg]
               + [f"grp_{x}_dif_mh" for x in gg] + [f"grp_{x}_niv{k}" for k in (1, 2, 3, 4) for x in gg])

    def est(w):
        nac = np.bincount(g, w, 4) / w.sum()
        cel = np.bincount(mujer * 4 + g, w, 8).reshape(2, 4)
        h, m = cel[0] / cel[0].sum(), cel[1] / cel[1].sum()
        cn = np.bincount((niv - 1).clip(0, 4) * 4 + g, w, 20).reshape(5, 4)
        porniv = [cn[k] / cn[k].sum() for k in range(4)]
        return np.concatenate([nac, h, m, m - h] + porniv)

    return est, nombres


# --------------------------------------------------------------------------- #
# 3. Retorno de la escolaridad y correlación escolaridad-ingreso por entidad
# --------------------------------------------------------------------------- #
def fab_retorno(S: Sub):
    ent = S.df["cve_ent"].to_numpy()
    y = S.col("ln_ing_hora")
    x = S.col("anios_esc")
    mujer = S.col("mujer")
    eda_c, eda_c2 = S.col("eda_c"), S.col("eda_c2")
    idx = [np.flatnonzero(ent == e) for e in range(1, N_ENT + 1)]
    Xs = [np.column_stack([np.ones(len(i)), x[i], eda_c[i], eda_c2[i], mujer[i]]) for i in idx]
    ys = [y[i] for i in idx]
    rx = [RangosPonderados(x[i]) for i in idx]
    ry = [RangosPonderados(y[i]) for i in idx]
    orden = [np.argsort(v, kind="stable") for v in ys]
    ys_ord = [v[o] for v, o in zip(ys, orden)]
    rxn, ryn = RangosPonderados(x), RangosPonderados(y)

    bl = bloques_diseno(S.df, sin_mujer=False)
    Xn, _, _ = ensamblar(bl, ["const", "educ", "exper", "mujer", "geo"])
    bl2 = bloques_diseno(S.df, sin_mujer=True)
    Xsexo, _, _ = ensamblar(bl2, ["const", "educ", "exper", "geo"])
    m_h, m_m = np.flatnonzero(mujer == 0), np.flatnonzero(mujer == 1)

    nombres = (_sufijos("rho_ent", N_ENT) + _sufijos("ret_ent", N_ENT) + _sufijos("med_ent", N_ENT) + _sufijos("esc_ent", N_ENT)
               + ["rho_nac", "ret_nac", "ret_hombres", "ret_mujeres", "ret_dif_mh"]
               + [f"ret_Q{k}" for k in (1, 2, 3, 4)] + [f"rho_Q{k}" for k in (1, 2, 3, 4)]
               + ["ret_dif_Q4_Q1", "rho_dif_Q4_Q1", "rho_estatal_esc_med", "rho_estatal_ret_med"])

    def est(w):
        rho, ret, med, esc = (np.empty(N_ENT) for _ in range(4))
        for s in range(N_ENT):
            i = idx[s]
            ws = w[i]
            rho[s] = correlacion_ponderada(rx[s].rangos(ws), ry[s].rangos(ws), ws)
            ret[s] = wls(Xs[s], ys[s], ws)[1]
            wo = ws[orden[s]]
            cw = np.cumsum(wo)
            med[s] = np.interp(0.5, (cw - 0.5 * wo) / cw[-1], ys_ord[s])
            esc[s] = (ws * x[i]).sum() / ws.sum()
        rho_nac = correlacion_ponderada(rxn.rangos(w), ryn.rangos(w), w)
        b = wls(Xn, y, w)
        bh = wls(Xsexo[m_h], y[m_h], w[m_h])
        bm = wls(Xsexo[m_m], y[m_m], w[m_m])
        grupos = np.argsort(med).reshape(4, -1)          # 32 entidades -> 4 cuartiles de 8 por ingreso mediano
        retq = ret[grupos].mean(axis=1)
        rhoq = rho[grupos].mean(axis=1)
        return np.concatenate([rho, ret, med, esc, [rho_nac, b[1], bh[1], bm[1], bm[1] - bh[1]], retq, rhoq,
                               [retq[3] - retq[0], rhoq[3] - rhoq[0], _pearson(_rank(esc), _rank(med)),
                                _pearson(_rank(ret), _rank(med))]])

    return est, nombres


# --------------------------------------------------------------------------- #
# 4. Brechas de género (por hora, mensual, horas) por nivel y entidad; perfil por cuantiles
# --------------------------------------------------------------------------- #
def fab_brechas(S: Sub):
    ent = S.df["cve_ent"].to_numpy() - 1
    niv = S.df["niv_ins"].to_numpy() - 1                  # 0..3 (la muestra solo trae niveles 1-4)
    mujer = S.col("mujer").astype(int)
    yh, ym = S.col("ln_ing_hora"), S.col("ln_ing_mensual")
    yhr = S.col("log_horas")
    hrs = S.col("hrsocup")
    x = S.col("anios_esc")
    g = niv * 2 + mujer
    ge = ent * 2 + mujer
    idx_s = [np.flatnonzero(mujer == s) for s in (0, 1)]
    ord_s = [np.argsort(yh[i], kind="stable") for i in idx_s]
    ys_ord = [yh[i][o] for i, o in zip(idx_s, ord_s)]
    i_ord = [i[o] for i, o in zip(idx_s, ord_s)]

    nombres = ([f"gap_hora_niv{k}" for k in (1, 2, 3, 4)] + ["gap_hora_total"]
               + [f"gap_mens_niv{k}" for k in (1, 2, 3, 4)] + ["gap_mens_total"]
               + [f"gap_hrs_niv{k}" for k in (1, 2, 3, 4)] + ["gap_hrs_total"]
               + _sufijos("gap_hora_ent", N_ENT) + _sufijos("gap_mens_ent", N_ENT)
               + [f"q{int(100 * q)}_hombres" for q in QS] + [f"q{int(100 * q)}_mujeres" for q in QS]
               + [f"part_mujeres_niv{k}" for k in (1, 2, 3, 4)] + ["part_mujeres_total"]
               + ["esc_media_h", "esc_media_m", "horas_media_h", "horas_media_m",
                  "media_ln_hora_h", "media_ln_hora_m"]
               + [f"mln_hora_niv{k}_{s}" for k in (1, 2, 3, 4) for s in ("h", "m")]
               + [f"horas_niv{k}_{s}" for k in (1, 2, 3, 4) for s in ("h", "m")])

    def brecha_niveles(y, w):
        sw = np.bincount(g, w, 8)
        mu = np.bincount(g, w * y, 8) / sw
        sws = np.bincount(mujer, w, 2)
        mus = np.bincount(mujer, w * y, 2) / sws
        return np.concatenate([mu[0::2] - mu[1::2], [mus[0] - mus[1]]]), mus

    def est(w):
        gh, mus_h = brecha_niveles(yh, w)
        gm, _ = brecha_niveles(ym, w)
        gr, _ = brecha_niveles(yhr, w)
        sw_e = np.bincount(ge, w, 2 * N_ENT)
        gap_e = (np.bincount(ge, w * yh, 2 * N_ENT) / sw_e).reshape(N_ENT, 2)
        gap_e_m = (np.bincount(ge, w * ym, 2 * N_ENT) / sw_e).reshape(N_ENT, 2)
        qh = []
        for i, o, ys in zip(i_ord, ord_s, ys_ord):
            wo = w[i]
            cw = np.cumsum(wo)
            qh.append(np.interp(QS, (cw - 0.5 * wo) / cw[-1], ys))
        sw = np.bincount(g, w, 8)
        part = np.concatenate([sw[1::2] / (sw[0::2] + sw[1::2]), [w[mujer == 1].sum() / w.sum()]])
        sws = np.bincount(mujer, w, 2)
        esc_s = np.bincount(mujer, w * x, 2) / sws
        hor_s = np.bincount(mujer, w * hrs, 2) / sws
        mln_niv = np.bincount(g, w * yh, 8) / sw            # media de ln(ingreso/hora) por nivel y sexo
        hor_niv = np.bincount(g, w * hrs, 8) / sw           # horas semanales medias por nivel y sexo
        return np.concatenate([gh, gm, gr, gap_e[:, 0] - gap_e[:, 1], gap_e_m[:, 0] - gap_e_m[:, 1],
                               qh[0], qh[1], part, esc_s, hor_s, mus_h, mln_niv, hor_niv])

    return est, nombres


# --------------------------------------------------------------------------- #
# 5. Descomposición de Oaxaca-Blinder de la brecha por hora
# --------------------------------------------------------------------------- #
GRUPOS_OB = ["educ", "exper", "geo", "empleo", "rama", "horas"]


def fab_oaxaca(S: Sub, bloques: list[str] | None = None):
    bl = bloques_diseno(S.df, sin_mujer=True)
    usar = bloques or ["const", "educ", "exper", "geo", "empleo", "rama", "horas"]
    X, cols, rangos = ensamblar(bl, usar)
    y = S.col("ln_ing_hora")
    mujer = S.col("mujer").astype(int)
    ih, im = np.flatnonzero(mujer == 0), np.flatnonzero(mujer == 1)
    grupos = [g for g in GRUPOS_OB if g in rangos]
    nombres = (["ob_total"] + [f"ob_N_{k}" for k in ("explicada", "no_explicada")] + [f"ob_N_exp_{g}" for g in grupos]
               + [f"ob_H_{k}" for k in ("explicada", "no_explicada")] + [f"ob_M_{k}" for k in ("explicada", "no_explicada")])

    def est(w):
        wh, wm = w[ih], w[im]
        bh = wls(X[ih], y[ih], wh)
        bm = wls(X[im], y[im], wm)
        bp = wls(X, y, w)                                   # referencia agrupada (Neumark 1988)
        xh = (X[ih] * wh[:, None]).sum(0) / wh.sum()
        xm = (X[im] * wm[:, None]).sum(0) / wm.sum()
        dx = xh - xm
        total = float(xh @ bh - xm @ bm)
        expl_n = float(dx @ bp)
        noexp_n = float(xh @ (bh - bp) + xm @ (bp - bm))
        det = [float(dx[a:b] @ bp[a:b]) for a, b in (rangos[g] for g in grupos)]
        expl_h, noexp_h = float(dx @ bh), float(xm @ (bh - bm))      # referencia: coeficientes de los hombres
        expl_m, noexp_m = float(dx @ bm), float(xh @ (bh - bm))      # referencia: coeficientes de las mujeres
        return np.array([total, expl_n, noexp_n] + det + [expl_h, noexp_h, expl_m, noexp_m])

    return est, nombres


# --------------------------------------------------------------------------- #
# 6. Brecha simple (para el análisis de robustez sobre distintas muestras/outcomes/ponderadores)
# --------------------------------------------------------------------------- #
def fab_brecha_simple(df: pd.DataFrame, ycol: str, ajuste: np.ndarray | None = None, mediana: bool = False):
    niv = df["niv_ins"].to_numpy() - 1
    mujer = df["mujer"].to_numpy(int)
    y = df[ycol].to_numpy(float)
    g = niv * 2 + mujer
    nombres = [f"gap_niv{k}" for k in (1, 2, 3, 4)] + ["gap_total"]
    if mediana:
        idx = {(l, s): np.flatnonzero((niv == l) & (mujer == s)) for l in range(4) for s in (0, 1)}
        idx.update({(4, s): np.flatnonzero(mujer == s) for s in (0, 1)})
        orden = {k: i[np.argsort(y[i], kind="stable")] for k, i in idx.items()}

        def med(i, w):
            wo = w[i]
            cw = np.cumsum(wo)
            return np.interp(0.5, (cw - 0.5 * wo) / cw[-1], y[i])

        def est(w):
            w2 = w if ajuste is None else w * ajuste
            return np.array([med(orden[(l, 0)], w2) - med(orden[(l, 1)], w2) for l in range(5)])
        return est, nombres

    def est(w):
        w2 = w if ajuste is None else w * ajuste
        sw = np.bincount(g, w2, 8)
        mu = np.bincount(g, w2 * y, 8) / sw
        sws = np.bincount(mujer, w2, 2)
        mus = np.bincount(mujer, w2 * y, 2) / sws
        return np.concatenate([mu[0::2] - mu[1::2], [mus[0] - mus[1]]])

    return est, nombres


def fab_brecha_por(df: pd.DataFrame, col: str, categorias: list, ycol: str = "ln_ing_hora"):
    """Brecha por hora (hombres - mujeres, log-puntos) dentro de cada categoría de ``col``."""
    codigo = df[col].map({c: i for i, c in enumerate(categorias)}).to_numpy()
    mujer = df["mujer"].to_numpy(int)
    y = df[ycol].to_numpy(float)
    K = len(categorias)
    g = codigo * 2 + mujer
    nombres = [f"gap_{col}_{i}" for i in range(K)]

    def est(w):
        sw = np.bincount(g, w, 2 * K)
        mu = np.bincount(g, w * y, 2 * K) / sw
        return mu[0::2] - mu[1::2]

    return est, nombres


def brecha_pct(gap_log):
    """Diferencia de medias logarítmicas (hombres - mujeres) -> % menos que ganan las mujeres."""
    return 100.0 * (1.0 - np.exp(-np.asarray(gap_log)))
