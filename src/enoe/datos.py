"""Acceso a los datos limpios (SQLite) y construcción de matrices de diseño para los modelos.

``Datos`` empaqueta el universo (ocupados de 15+), el diseño muestral completo y el índice de UPM
de cada fila. ``Datos.subconjunto`` devuelve un dominio (p. ej. la muestra salarial) que conserva la
referencia a TODAS las UPM del diseño: así el bootstrap trata correctamente la estimación en dominios.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C
from .survey import Diseno

REF_ENTIDAD = 9          # Ciudad de México como categoría de referencia de efectos fijos de entidad
REF_LOCALIDAD = 1
REF_POSICION = 1
REF_RAMA = 3             # industria manufacturera
EDAD_CENTRO = 40


@dataclass
class Sub:
    """Un dominio de la muestra: filas + índice de UPM + ponderador original."""

    df: pd.DataFrame
    psu: np.ndarray

    @property
    def w(self) -> np.ndarray:
        return self.df["fac_tri"].to_numpy(dtype=float)

    def __len__(self) -> int:
        return len(self.df)

    def col(self, nombre: str) -> np.ndarray:
        return self.df[nombre].to_numpy(dtype=float)


@dataclass
class Datos:
    df: pd.DataFrame
    diseno: Diseno

    def __post_init__(self) -> None:
        self.psu = self.diseno.indice_upm(self.df["upm"])

    def subconjunto(self, mascara) -> Sub:
        m = np.asarray(mascara, dtype=bool)
        return Sub(self.df.loc[m].reset_index(drop=True), self.psu[m])

    @property
    def universo(self) -> Sub:
        return Sub(self.df.reset_index(drop=True), self.psu)

    @property
    def ventana(self) -> Sub:
        return self.subconjunto(self.df["en_ventana_15_65"])

    @property
    def salarial(self) -> Sub:
        return self.subconjunto(self.df["en_muestra_salarial"])

    @property
    def salarial_ext(self) -> Sub:
        return self.subconjunto(self.df["en_muestra_salarial_ext"])


def cargar_datos(db_path: Path | None = None) -> Datos:
    con = sqlite3.connect(db_path or C.DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM fact_ocupado", con)
        upm = pd.read_sql("SELECT upm, estrato_col FROM dim_upm", con)
    finally:
        con.close()
    for c in ["en_ventana_15_65", "anios_esc_valido", "horas_validas", "nivel_especificado",
              "outlier_ing_hora", "en_muestra_salarial", "en_muestra_salarial_ext"]:
        df[c] = df[c].astype(bool)
    df["mujer"] = (df["sex"] == 2).astype(int)
    df["ln_ing_mensual"] = np.log(df["ing_mensual"])
    df["log_horas"] = np.log(df["hrsocup"])
    df["ln_ing_hora_imp"] = np.log(df["ing_hora_imp"])
    df["entidad"] = df["cve_ent"].map({k: v[0] for k, v in C.ENTIDADES.items()})
    df["region"] = df["cve_ent"].map({k: v[3] for k, v in C.ENTIDADES.items()})
    df["eda_c"] = df["eda"] - EDAD_CENTRO
    df["eda_c2"] = df["eda_c"] ** 2 / 100.0
    return Datos(df, Diseno.desde_tabla(upm))


# --------------------------------------------------------------------------- #
# Matrices de diseño por bloques (se ensamblan según la especificación)
# --------------------------------------------------------------------------- #
def _dummies(serie: pd.Series, categorias: list[int], ref: int, prefijo: str, etiquetas: dict | None = None):
    cats = [c for c in categorias if c != ref]
    M = np.column_stack([(serie.to_numpy() == c).astype(float) for c in cats])
    nombres = [f"{prefijo}{etiquetas[c] if etiquetas else c}" for c in cats]
    return M, nombres


def bloques_diseno(df: pd.DataFrame, sin_mujer: bool = False) -> dict[str, tuple[np.ndarray, list[str]]]:
    """Bloques de columnas reutilizables: const, mujer, educ, exper, geo, empleo, rama, horas."""
    n = len(df)
    geo_e, geo_en = _dummies(df["cve_ent"], list(C.ENTIDADES), REF_ENTIDAD, "ent_", {k: v[2] for k, v in C.ENTIDADES.items()})
    geo_l, geo_ln = _dummies(df["t_loc_tri"], list(C.T_LOC_TRI), REF_LOCALIDAD, "loc_")
    pos, pos_n = _dummies(df["pos_ocu"], [1, 2, 3], REF_POSICION, "pos_", {2: "empleador", 3: "cuenta_propia"})
    rama, rama_n = _dummies(df["rama_est2"], [k for k in C.RAMA_EST2 if k != 0], REF_RAMA, "rama_")
    bloques = {
        "const": (np.ones((n, 1)), ["const"]),
        "mujer": (df[["mujer"]].to_numpy(float), ["mujer"]),
        "educ": (df[["anios_esc"]].to_numpy(float), ["anios_esc"]),
        "exper": (df[["eda_c", "eda_c2"]].to_numpy(float), ["eda_c", "eda_c2"]),
        "geo": (np.hstack([geo_e, geo_l]), geo_en + geo_ln),
        "empleo": (np.hstack([df[["informal"]].to_numpy(float), pos]), ["informal"] + pos_n),
        "rama": (rama, rama_n),
        "horas": (df[["log_horas"]].to_numpy(float), ["log_horas"]),
    }
    if sin_mujer:
        bloques.pop("mujer")
    return bloques


def ensamblar(bloques: dict, nombres_bloques: list[str]):
    """Concatena bloques en una matriz X; devuelve (X, nombres de columnas, rango de columnas por bloque)."""
    mats, nombres, rangos, pos = [], [], {}, 0
    for b in nombres_bloques:
        M, nm = bloques[b]
        mats.append(M)
        nombres += nm
        rangos[b] = (pos, pos + M.shape[1])
        pos += M.shape[1]
    return np.hstack(mats), nombres, rangos


ESCALERA = {
    "G0 Sin controles": ["const", "mujer"],
    "G1 + escolaridad": ["const", "mujer", "educ"],
    "G2 + edad y edad²": ["const", "mujer", "educ", "exper"],
    "G3 + entidad y tamaño de localidad": ["const", "mujer", "educ", "exper", "geo"],
    "G4 + posición e informalidad": ["const", "mujer", "educ", "exper", "geo", "empleo"],
    "G5 + rama de actividad": ["const", "mujer", "educ", "exper", "geo", "empleo", "rama"],
    "G6 + horas trabajadas": ["const", "mujer", "educ", "exper", "geo", "empleo", "rama", "horas"],
}
