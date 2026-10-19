"""Diseño muestral complejo y estadísticos ponderados.

La ENOE es una encuesta probabilística, bietápica, estratificada y por conglomerados:

        estrato (est_d_tri)  ->  UPM (upm)  ->  vivienda  ->  persona

El ponderador ``fac_tri`` expande la muestra a la población (suma ~131 millones de personas).
Tratar la muestra como aleatoria simple (i.i.d.) subestima los errores estándar porque las
personas de una misma UPM se parecen entre sí (efecto de diseño). Por eso, la incertidumbre
se mide con el **bootstrap de Rao y Wu (1988)** (rescaled bootstrap): en cada estrato con
n_h UPM se remuestrean n_h - 1 UPM con reemplazo y se reescalan los ponderadores por
n_h/(n_h - 1) x (número de veces que salió la UPM).

Propiedades que se verifican en tests/test_survey.py:
  * E[factor] = 1 para cada UPM (los totales ponderados son insesgados bajo el remuestreo).
  * La varianza bootstrap de una media reproduce la de linealización de Taylor.
  * Con ponderadores iguales, Spearman ponderado = scipy.stats.spearmanr.

Estimación en dominios (subpoblaciones): las réplicas se construyen sobre TODAS las UPM de la
muestra completa (tabla ``dim_upm``) y cada fila de un subconjunto toma el factor de su UPM. Así
no se pierde variabilidad cuando una UPM no aporta casos al dominio (error común al filtrar antes).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# 1. Diseño: estratos colapsados y factores de Rao-Wu
# --------------------------------------------------------------------------- #
def colapsar_estratos(tabla_upm: pd.DataFrame) -> pd.Series:
    """Fusiona los estratos con una sola UPM con su vecino más cercano de la misma entidad.

    Un estrato con una única UPM no permite estimar varianza (n_h - 1 = 0). El remedio estándar
    ("collapsed strata") es unirlo con un estrato adyacente. Devuelve ``estrato_col`` indexado
    por ``upm``.
    """
    d = tabla_upm[["upm", "cve_ent", "est_d_tri"]].drop_duplicates("upm").copy()
    padre: dict[int, int] = {}

    def raiz(s: int) -> int:
        while padre.get(s, s) != s:
            s = padre[s]
        return s

    for _, g in d.groupby("cve_ent"):
        conteo = g.groupby("est_d_tri")["upm"].nunique().sort_index()
        estratos = list(conteo.index)
        for s in conteo[conteo < 2].index:
            i = estratos.index(s)
            vecino = estratos[i + 1] if i + 1 < len(estratos) else estratos[i - 1]
            ra, rb = raiz(int(s)), raiz(int(vecino))
            if ra != rb:
                padre[max(ra, rb)] = min(ra, rb)
    d["estrato_col"] = d["est_d_tri"].map(lambda s: raiz(int(s)))
    resultado = d.set_index("upm")["estrato_col"]
    assert resultado.groupby(resultado).size().min() >= 1
    n_por_estrato = d.groupby("estrato_col")["upm"].nunique()
    assert (n_por_estrato >= 2).all(), "Quedaron estratos con una sola UPM tras colapsar"
    return resultado


@dataclass
class Diseno:
    """Estructura mínima del diseño para generar réplicas de Rao-Wu."""

    upm_ids: np.ndarray        # (P,) ids de UPM, ordenados por estrato
    estrato_idx: np.ndarray    # (P,) índice 0..H-1 del estrato de cada UPM
    n_h: np.ndarray            # (H,) UPM por estrato
    inicio_h: np.ndarray       # (H,) posición de la primera UPM de cada estrato

    @classmethod
    def desde_tabla(cls, tabla_upm: pd.DataFrame) -> "Diseno":
        """``tabla_upm`` debe traer ``upm`` y ``estrato_col`` (una fila por UPM)."""
        t = tabla_upm[["upm", "estrato_col"]].drop_duplicates("upm").sort_values(["estrato_col", "upm"])
        estrato_idx, _ = pd.factorize(t["estrato_col"], sort=True)
        n_h = np.bincount(estrato_idx)
        if (n_h < 2).any():
            raise ValueError("Hay estratos con una sola UPM; aplique colapsar_estratos primero")
        inicio_h = np.r_[0, np.cumsum(n_h)[:-1]]
        return cls(t["upm"].to_numpy(), estrato_idx.astype(np.int64), n_h.astype(np.int64), inicio_h.astype(np.int64))

    @property
    def n_upm(self) -> int:
        return len(self.upm_ids)

    @property
    def n_estratos(self) -> int:
        return len(self.n_h)

    def indice_upm(self, upm_filas: pd.Series | np.ndarray) -> np.ndarray:
        """Posición (0..P-1) de la UPM de cada fila de un subconjunto de datos."""
        idx = pd.Index(self.upm_ids).get_indexer(np.asarray(upm_filas))
        if (idx < 0).any():
            raise KeyError("Hay UPM en los datos que no están en el diseño")
        return idx

    def iterar_factores(self, B: int, semilla: int) -> Iterator[np.ndarray]:
        """Genera B vectores (P,) de factores de Rao-Wu; reproducibles dada la semilla."""
        rng = np.random.default_rng(semilla)
        m_h = self.n_h - 1                                   # UPM a remuestrear por estrato
        est_de_extraccion = np.repeat(np.arange(self.n_estratos), m_h)
        n_ext = self.n_h[est_de_extraccion]
        ini_ext = self.inicio_h[est_de_extraccion]
        escala = (self.n_h / (self.n_h - 1.0))[self.estrato_idx]  # (P,)
        total = len(est_de_extraccion)
        for _ in range(B):
            u = rng.random(total)
            elegidas = ini_ext + np.floor(u * n_ext).astype(np.int64)
            cuentas = np.bincount(elegidas, minlength=self.n_upm)
            yield cuentas * escala

    def matriz_factores(self, B: int, semilla: int) -> np.ndarray:
        return np.column_stack(list(self.iterar_factores(B, semilla)))


# --------------------------------------------------------------------------- #
# 2. Estadísticos ponderados
# --------------------------------------------------------------------------- #
def media_ponderada(x: np.ndarray, w: np.ndarray) -> float:
    sw = w.sum()
    return float((x * w).sum() / sw) if sw > 0 else np.nan


def cuantil_ponderado(x: np.ndarray, w: np.ndarray, q) -> np.ndarray | float:
    """Cuantil ponderado con interpolación lineal sobre las posiciones (cum_w - w/2)/W.

    Con ponderadores iguales coincide con ``np.percentile(..., method='hazen')``.
    """
    orden = np.argsort(x, kind="stable")
    xs, ws = x[orden], w[orden]
    cw = np.cumsum(ws)
    pos = (cw - 0.5 * ws) / cw[-1]
    res = np.interp(q, pos, xs)
    return float(res) if np.ndim(q) == 0 else res


def mediana_ponderada(x: np.ndarray, w: np.ndarray) -> float:
    return cuantil_ponderado(x, w, 0.5)


class RangosPonderados:
    """Rangos medios ponderados de un vector fijo ``x`` para ponderadores cambiantes.

    El orden y los grupos de empates se precalculan una vez; cada llamada con un nuevo ``w``
    (p. ej. en cada réplica del bootstrap) cuesta O(n). Rango medio de un grupo de empates =
    (W_menores + W_menores_o_iguales)/2.
    """

    def __init__(self, x: np.ndarray):
        x = np.asarray(x)
        self.n = len(x)
        self.orden = np.argsort(x, kind="stable")
        xs = x[self.orden]
        nuevo = np.r_[True, xs[1:] != xs[:-1]]
        self.inicio = np.flatnonzero(nuevo)
        self.grupo = np.cumsum(nuevo) - 1
        self.fin = np.r_[self.inicio[1:], self.n] - 1

    def rangos(self, w: np.ndarray) -> np.ndarray:
        ws = w[self.orden]
        cw = np.cumsum(ws)
        w_le = cw[self.fin]
        w_grupo = np.add.reduceat(ws, self.inicio)
        medio = 0.5 * ((w_le - w_grupo) + w_le)
        r = np.empty(self.n)
        r[self.orden] = medio[self.grupo]
        return r


def correlacion_ponderada(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    sw = w.sum()
    if sw <= 0:
        return np.nan
    mx, my = (w * x).sum() / sw, (w * y).sum() / sw
    sxy = (w * (x - mx) * (y - my)).sum()
    sxx = (w * (x - mx) ** 2).sum()
    syy = (w * (y - my) ** 2).sum()
    return float(sxy / np.sqrt(sxx * syy)) if sxx > 0 and syy > 0 else np.nan


def spearman_ponderado(x: np.ndarray, y: np.ndarray, w: np.ndarray,
                       rx: RangosPonderados | None = None, ry: RangosPonderados | None = None) -> float:
    """Correlación de Spearman ponderada = Pearson ponderada entre rangos medios ponderados."""
    rx = rx or RangosPonderados(x)
    ry = ry or RangosPonderados(y)
    return correlacion_ponderada(rx.rangos(w), ry.rangos(w), w)


def wls(X: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Mínimos cuadrados ponderados (ecuaciones normales). X ya incluye la constante."""
    Xw = X * w[:, None]
    return np.linalg.solve(X.T @ Xw, Xw.T @ y)


# --------------------------------------------------------------------------- #
# 3. Inferencia por réplicas
# --------------------------------------------------------------------------- #
def bootstrap_rao_wu(estimador: Callable[[np.ndarray], np.ndarray], w: np.ndarray, psu_idx: np.ndarray,
                     diseno: Diseno, B: int, semilla: int) -> tuple[np.ndarray, np.ndarray]:
    """Evalúa ``estimador(w)`` con los ponderadores originales y con B ponderadores replicados.

    Devuelve (theta_hat de forma (K,), réplicas de forma (B, K)).
    """
    theta = np.atleast_1d(np.asarray(estimador(w), dtype=float))
    reps = np.empty((B, theta.size))
    for b, f in enumerate(diseno.iterar_factores(B, semilla)):
        reps[b] = estimador(w * f[psu_idx])
    return theta, reps


def error_estandar(reps: np.ndarray) -> np.ndarray:
    return np.nanstd(reps, axis=0, ddof=1)


def intervalo_percentil(reps: np.ndarray, nivel: float = 0.95) -> np.ndarray:
    """IC percentil de forma (2, K): fila 0 = inferior, fila 1 = superior."""
    a = (1 - nivel) / 2
    return np.nanpercentile(reps, [100 * a, 100 * (1 - a)], axis=0)


def pvalor_normal(theta: np.ndarray, se: np.ndarray, nulo: float = 0.0) -> np.ndarray:
    """Prueba de Wald bilateral con error estándar bootstrap (aprox. normal; gl >> 1000)."""
    from scipy import stats

    z = (np.asarray(theta) - nulo) / np.asarray(se)
    return 2 * stats.norm.sf(np.abs(z))


def holm(pvalores: np.ndarray) -> np.ndarray:
    """Ajuste de Holm-Bonferroni (controla la tasa de error por familia, FWER)."""
    p = np.asarray(pvalores, dtype=float)
    m = len(p)
    orden = np.argsort(p)
    aj = np.empty(m)
    maximo = 0.0
    for rango, i in enumerate(orden):
        maximo = max(maximo, (m - rango) * p[i])
        aj[i] = min(1.0, maximo)
    return aj


# --------------------------------------------------------------------------- #
# 4. Regresión con linealización de Taylor (estratos + UPM): equivalente a "svy" de Stata
# --------------------------------------------------------------------------- #
def matriz_central_diseno(scores: np.ndarray, psu_idx: np.ndarray, diseno: Diseno) -> np.ndarray:
    """Suma sobre estratos de n_h/(n_h-1) x suma de productos cruzados de los totales de scores por UPM
    (centrados en la media del estrato). Incluye UPM del diseño sin casos en el dominio (scores = 0)."""
    from scipy import sparse

    n = len(psu_idx)
    a_upm = sparse.csr_matrix((np.ones(n), (psu_idx, np.arange(n))), shape=(diseno.n_upm, n))
    S = a_upm @ scores
    medias = np.add.reduceat(S, diseno.inicio_h, axis=0) / diseno.n_h[:, None]
    dev = S - medias[diseno.estrato_idx]
    escala = (diseno.n_h / (diseno.n_h - 1.0))[diseno.estrato_idx]
    return (dev * escala[:, None]).T @ dev


@dataclass
class AjusteDiseno:
    """Coeficientes y covarianza robusta de diseño de un modelo lineal o logit ponderado."""

    nombres: list[str]
    coef: np.ndarray
    cov: np.ndarray
    extra: dict

    @property
    def ee(self) -> np.ndarray:
        return np.sqrt(np.diag(self.cov))

    def fila(self, nombre: str) -> dict:
        i = self.nombres.index(nombre)
        b, se = float(self.coef[i]), float(self.ee[i])
        from scipy import stats as _st

        return dict(coef=b, ee=se, ic_inf=b - 1.959964 * se, ic_sup=b + 1.959964 * se, p=float(2 * _st.norm.sf(abs(b / se))))


def regresion_diseno(X: np.ndarray, y: np.ndarray, w: np.ndarray, psu_idx: np.ndarray, diseno: Diseno,
                     nombres: list[str]) -> AjusteDiseno:
    """WLS con covarianza de sándwich estratificada y por conglomerados."""
    Xw = X * w[:, None]
    A = X.T @ Xw
    beta = np.linalg.solve(A, Xw.T @ y)
    e = y - X @ beta
    meat = matriz_central_diseno(X * (w * e)[:, None], psu_idx, diseno)
    Ainv = np.linalg.inv(A)
    ybar = (w * y).sum() / w.sum()
    r2 = 1 - (w * e ** 2).sum() / (w * (y - ybar) ** 2).sum()
    return AjusteDiseno(nombres, beta, Ainv @ meat @ Ainv, {"r2": float(r2), "n": len(y)})


def logit_diseno(X: np.ndarray, y: np.ndarray, w: np.ndarray, psu_idx: np.ndarray, diseno: Diseno,
                 nombres: list[str], max_iter: int = 50, tol: float = 1e-10) -> AjusteDiseno:
    """Logit de pseudo-verosimilitud ponderada (IRLS) con covarianza de sándwich de diseño."""
    beta = np.zeros(X.shape[1])
    for _ in range(max_iter):
        eta = X @ beta
        p = 1.0 / (1.0 + np.exp(-eta))
        W = w * p * (1 - p)
        z = eta + (y - p) / np.clip(p * (1 - p), 1e-12, None)
        nuevo = np.linalg.solve(X.T @ (X * W[:, None]), X.T @ (W * z))
        if np.max(np.abs(nuevo - beta)) < tol:
            beta = nuevo
            break
        beta = nuevo
    eta = X @ beta
    p = 1.0 / (1.0 + np.exp(-eta))
    A = X.T @ (X * (w * p * (1 - p))[:, None])
    meat = matriz_central_diseno(X * (w * (y - p))[:, None], psu_idx, diseno)
    Ainv = np.linalg.inv(A)
    ll = (w * (y * np.log(p) + (1 - y) * np.log1p(-p))).sum()
    p0 = (w * y).sum() / w.sum()
    ll0 = (w * (y * np.log(p0) + (1 - y) * np.log1p(-p0))).sum()
    return AjusteDiseno(nombres, beta, Ainv @ meat @ Ainv, {"mcfadden": float(1 - ll / ll0), "n": len(y), "p": p})


def varianza_taylor_media(y: np.ndarray, w: np.ndarray, estrato: np.ndarray, upm: np.ndarray) -> float:
    """Varianza de la media ponderada por linealización de Taylor (estratificado + conglomerados).

    Se usa como verificación independiente del bootstrap en los tests y en el cuaderno.
    """
    ybar = (w * y).sum() / w.sum()
    z = w * (y - ybar) / w.sum()
    df = pd.DataFrame({"h": estrato, "c": upm, "z": z}).groupby(["h", "c"], as_index=False)["z"].sum()
    var = 0.0
    for _, g in df.groupby("h"):
        n_h = len(g)
        if n_h > 1:
            var += n_h / (n_h - 1.0) * ((g["z"] - g["z"].mean()) ** 2).sum()
    return float(var)
