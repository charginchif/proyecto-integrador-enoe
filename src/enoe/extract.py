"""Extracción (E de ETL): lectura tipada de los microdatos y auditoría de los archivos de origen.

Principios:
  * Solo se leen las columnas necesarias (usecols) -> menor memoria y contrato explícito.
  * Los CSV de INEGI usan codificación latin-1 y traen blancos (' ') en columnas numéricas
    cuando la pregunta no aplica; esas columnas se leen como texto y se convierten con
    errors="coerce" para no perder información ni fallar.
  * Se registra el SHA-256 de cada archivo para poder demostrar con qué datos se corrió el pipeline.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pandas as pd

from . import config as C

log = logging.getLogger(__name__)

COLS_SDEMT = [
    # llave de persona
    "cd_a", "cve_ent", "con", "upm", "d_sem", "n_pro_viv", "v_sel", "n_hog", "h_mud", "n_ent", "n_ren",
    # diseño muestral y ponderador
    "est_d_tri", "fac_tri", "t_loc_tri", "ur", "zona", "salario", "tipo", "mes_cal",
    # control de calidad de la entrevista
    "r_def", "c_res",
    # persona
    "sex", "eda", "niv_ins", "anios_esc",
    # condición de actividad y características del empleo
    "clase1", "clase2", "pos_ocu", "emp_ppal", "rama_est1", "rama_est2",
    "hrsocup", "ingocup", "ing_x_hrs", "ing7c",
]
# Columnas que traen blancos cuando no aplican -> se leen como texto
_TEXTO_SDEMT = {"sex": str, "eda": str}

COLS_COE2T = C.LLAVE_PERSONA + ["p6b1", "p6b2", "p6c"]
_TEXTO_COE2T = {"p6b1": str, "p6b2": str, "p6c": str}


def ruta_tabla(tabla: str, raw_dir: Path | None = None) -> Path:
    raw_dir = Path(raw_dir) if raw_dir else C.RAW_DIR
    return raw_dir / f"ENOE_{tabla}{C.PERIODO}.csv"


def sha256(path: Path, bloque: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(bloque):
            h.update(chunk)
    return h.hexdigest()


def _num(serie: pd.Series) -> pd.Series:
    """Texto -> número; blancos y basura -> NaN."""
    return pd.to_numeric(serie.str.strip(), errors="coerce")


def leer_sdemt(raw_dir: Path | None = None) -> pd.DataFrame:
    """Lee la tabla sociodemográfica (una fila por persona residente del hogar, todas las edades)."""
    ruta = ruta_tabla("SDEMT", raw_dir)
    log.info("Leyendo %s", ruta)
    df = pd.read_csv(ruta, encoding="latin-1", usecols=COLS_SDEMT, dtype=_TEXTO_SDEMT, low_memory=False)
    for c in _TEXTO_SDEMT:
        df[c] = _num(df[c])
    faltan = set(COLS_SDEMT) - set(df.columns)
    if faltan:
        raise ValueError(f"Faltan columnas en SDEMT: {sorted(faltan)}")
    return df[COLS_SDEMT]


def leer_coe2t(raw_dir: Path | None = None) -> pd.DataFrame:
    """Lee del cuestionario de ocupación (parte 2) solo las variables de captación del ingreso.

    p6b1: tipo/periodicidad de pago del monto declarado (1-6) o motivo por el que no hay monto (7, 8)
    p6b2: monto declarado (pesos mensuales)
    p6c : rango en salarios mínimos cuando no se dio monto exacto (1-7) o no sabe/no responde (8, 9)
    """
    ruta = ruta_tabla("COE2T", raw_dir)
    log.info("Leyendo %s", ruta)
    df = pd.read_csv(ruta, encoding="latin-1", usecols=COLS_COE2T, dtype=_TEXTO_COE2T, low_memory=False)
    for c in _TEXTO_COE2T:
        df[c] = _num(df[c])
    return df[COLS_COE2T]


def auditar_archivo(tabla: str, n_filas: int, n_columnas: int, raw_dir: Path | None = None) -> dict:
    ruta = ruta_tabla(tabla, raw_dir)
    return {
        "tabla": tabla,
        "archivo": ruta.name,
        "bytes": ruta.stat().st_size,
        "sha256": sha256(ruta),
        "filas": int(n_filas),
        "columnas_leidas": int(n_columnas),
    }
