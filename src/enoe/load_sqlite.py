"""Carga (L de ETL) al almacén relacional SQLite.

Modelo: esquema en estrella con una tabla de hechos (``fact_ocupado``: una fila por persona
ocupada) y dimensiones pequeñas. Se usa SQLite porque los datos son tabulares, las consultas
son agregaciones con JOIN (promedios ponderados por entidad, nivel, sexo...) y el volumen
(~190 mil filas) cabe en un archivo único, transaccional (ACID), sin servidor y reproducible.
Las restricciones (PK, FK, CHECK) hacen que el propio motor rechace datos inconsistentes.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from . import config as C

DDL_DIMENSIONES = """
CREATE TABLE dim_entidad (
    cve_ent        INTEGER PRIMARY KEY CHECK (cve_ent BETWEEN 1 AND 32),
    entidad        TEXT NOT NULL,
    entidad_oficial TEXT NOT NULL,
    abreviatura    TEXT NOT NULL,
    region         TEXT NOT NULL,
    mosaico_col    INTEGER NOT NULL,
    mosaico_fila   INTEGER NOT NULL
);
CREATE TABLE dim_sexo (sex INTEGER PRIMARY KEY, sexo TEXT NOT NULL);
CREATE TABLE dim_nivel_instruccion (niv_ins INTEGER PRIMARY KEY, nivel TEXT NOT NULL);
CREATE TABLE dim_nivel_detalle (niv_det INTEGER PRIMARY KEY, nivel TEXT NOT NULL);
CREATE TABLE dim_posicion_ocupacion (pos_ocu INTEGER PRIMARY KEY, posicion TEXT NOT NULL);
CREATE TABLE dim_rama (rama_est2 INTEGER PRIMARY KEY, rama TEXT NOT NULL);
CREATE TABLE dim_tamano_localidad (t_loc_tri INTEGER PRIMARY KEY, tamano TEXT NOT NULL);
CREATE TABLE dim_ing7c (ing7c INTEGER PRIMARY KEY, rango TEXT NOT NULL);
CREATE TABLE dim_grupo_ingreso (grupo TEXT PRIMARY KEY CHECK (grupo IN ('A','B','C','D')), descripcion TEXT NOT NULL);
CREATE TABLE dim_upm (
    upm              INTEGER PRIMARY KEY,
    cve_ent          INTEGER NOT NULL REFERENCES dim_entidad (cve_ent),
    est_d_tri        INTEGER NOT NULL,
    estrato_col      INTEGER NOT NULL,
    n_registros_sdemt INTEGER NOT NULL
);
"""

DDL_HECHOS = """
CREATE TABLE fact_ocupado (
    persona_id        TEXT PRIMARY KEY,
    cve_ent           INTEGER NOT NULL REFERENCES dim_entidad (cve_ent),
    upm               INTEGER NOT NULL REFERENCES dim_upm (upm),
    fac_tri           REAL    NOT NULL CHECK (fac_tri > 0),
    sex               INTEGER NOT NULL REFERENCES dim_sexo (sex),
    eda               INTEGER NOT NULL CHECK (eda BETWEEN 15 AND 98),
    grupo_edad        TEXT    NOT NULL,
    anios_esc         REAL    CHECK (anios_esc IS NULL OR anios_esc BETWEEN 0 AND 30),
    niv_ins           INTEGER NOT NULL REFERENCES dim_nivel_instruccion (niv_ins),
    niv_det           INTEGER REFERENCES dim_nivel_detalle (niv_det),
    pos_ocu           INTEGER NOT NULL REFERENCES dim_posicion_ocupacion (pos_ocu),
    emp_ppal          INTEGER NOT NULL CHECK (emp_ppal IN (1, 2)),
    informal          INTEGER NOT NULL CHECK (informal IN (0, 1)),
    rama_est2         INTEGER NOT NULL REFERENCES dim_rama (rama_est2),
    t_loc_tri         INTEGER NOT NULL REFERENCES dim_tamano_localidad (t_loc_tri),
    ur                INTEGER NOT NULL,
    hrsocup           REAL,
    hrsocup_raw       INTEGER NOT NULL CHECK (hrsocup_raw BETWEEN 0 AND 168),
    ingocup           INTEGER NOT NULL CHECK (ingocup >= 0),
    ing7c             INTEGER NOT NULL REFERENCES dim_ing7c (ing7c),
    p6b1              INTEGER,
    p6c               INTEGER,
    salario           INTEGER NOT NULL,
    grupo_ingreso     TEXT    NOT NULL REFERENCES dim_grupo_ingreso (grupo),
    ing_mensual       REAL,
    ing_hora          REAL,
    ln_ing_hora       REAL,
    ing_mensual_imp   REAL,
    ing_hora_imp      REAL,
    en_ventana_15_65  INTEGER NOT NULL,
    anios_esc_valido  INTEGER NOT NULL,
    horas_validas     INTEGER NOT NULL,
    nivel_especificado INTEGER NOT NULL,
    outlier_ing_hora  INTEGER NOT NULL,
    en_muestra_salarial     INTEGER NOT NULL,
    en_muestra_salarial_ext INTEGER NOT NULL
);
"""

DDL_INDICES = """
CREATE INDEX ix_fact_entidad          ON fact_ocupado (cve_ent);
CREATE INDEX ix_fact_upm              ON fact_ocupado (upm);
CREATE INDEX ix_fact_entidad_sexo     ON fact_ocupado (cve_ent, sex);
CREATE INDEX ix_fact_muestra_salarial ON fact_ocupado (en_muestra_salarial, cve_ent);
CREATE INDEX ix_fact_grupo_ingreso    ON fact_ocupado (grupo_ingreso);
"""

DDL_VISTAS = """
CREATE VIEW v_til_entidad AS
SELECT e.cve_ent, e.entidad,
       COUNT(*)                                                         AS n_muestra,
       ROUND(SUM(f.fac_tri))                                            AS ocupados_estimados,
       ROUND(100.0 * SUM(f.fac_tri * f.informal) / SUM(f.fac_tri), 2)   AS til1_pct
FROM fact_ocupado f JOIN dim_entidad e USING (cve_ent)
GROUP BY e.cve_ent, e.entidad;

CREATE VIEW v_escolaridad_entidad AS
SELECT e.cve_ent, e.entidad,
       ROUND(SUM(f.fac_tri * f.anios_esc) /
             SUM(CASE WHEN f.anios_esc IS NOT NULL THEN f.fac_tri END), 3) AS anios_esc_medios
FROM fact_ocupado f JOIN dim_entidad e USING (cve_ent)
WHERE f.en_ventana_15_65 = 1
GROUP BY e.cve_ent, e.entidad;

CREATE VIEW v_calidad_ingreso_entidad AS
SELECT e.cve_ent, e.entidad, f.grupo_ingreso,
       COUNT(*) AS n_muestra,
       ROUND(100.0 * SUM(f.fac_tri) /
             (SELECT SUM(g.fac_tri) FROM fact_ocupado g
               WHERE g.cve_ent = f.cve_ent AND g.en_ventana_15_65 = 1), 2) AS pct_ponderado
FROM fact_ocupado f JOIN dim_entidad e USING (cve_ent)
WHERE f.en_ventana_15_65 = 1
GROUP BY e.cve_ent, e.entidad, f.grupo_ingreso;

CREATE VIEW v_muestra_salarial AS
SELECT f.*, e.entidad, e.abreviatura, e.region, s.sexo, n.nivel, p.posicion, r.rama, t.tamano
FROM fact_ocupado f
JOIN dim_entidad e              ON e.cve_ent   = f.cve_ent
JOIN dim_sexo s                 ON s.sex       = f.sex
JOIN dim_nivel_instruccion n    ON n.niv_ins   = f.niv_ins
JOIN dim_posicion_ocupacion p   ON p.pos_ocu   = f.pos_ocu
JOIN dim_rama r                 ON r.rama_est2 = f.rama_est2
JOIN dim_tamano_localidad t     ON t.t_loc_tri = f.t_loc_tri
WHERE f.en_muestra_salarial = 1;
"""

COLUMNAS_HECHOS = [
    "persona_id", "cve_ent", "upm", "fac_tri", "sex", "eda", "grupo_edad", "anios_esc", "niv_ins", "niv_det",
    "pos_ocu", "emp_ppal", "informal", "rama_est2", "t_loc_tri", "ur", "hrsocup", "hrsocup_raw", "ingocup",
    "ing7c", "p6b1", "p6c", "salario", "grupo_ingreso", "ing_mensual", "ing_hora", "ln_ing_hora",
    "ing_mensual_imp", "ing_hora_imp", "en_ventana_15_65", "anios_esc_valido", "horas_validas",
    "nivel_especificado", "outlier_ing_hora", "en_muestra_salarial", "en_muestra_salarial_ext",
]
_BOOLEANAS = ["en_ventana_15_65", "anios_esc_valido", "horas_validas", "nivel_especificado",
              "outlier_ing_hora", "en_muestra_salarial", "en_muestra_salarial_ext"]


def conectar(db_path: Path | None = None) -> sqlite3.Connection:
    con = sqlite3.connect(db_path or C.DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def crear_esquema(db_path: Path | None = None) -> sqlite3.Connection:
    ruta = Path(db_path or C.DB_PATH)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    for sufijo in ("", "-wal", "-shm", "-journal"):
        p = Path(str(ruta) + sufijo)
        if p.exists():
            p.unlink()
    con = conectar(ruta)
    con.executescript(DDL_DIMENSIONES + DDL_HECHOS)
    return con


def poblar_dimensiones(con: sqlite3.Connection, tabla_upm: pd.DataFrame) -> None:
    cur = con.cursor()
    cur.executemany("INSERT INTO dim_entidad VALUES (?,?,?,?,?,?,?)",
                    [(k, v[0], v[1], v[2], v[3], v[4], v[5]) for k, v in C.ENTIDADES.items()])
    cur.executemany("INSERT INTO dim_sexo VALUES (?,?)", list(C.SEXO.items()))
    cur.executemany("INSERT INTO dim_nivel_instruccion VALUES (?,?)", list(C.NIV_INS.items()))
    cur.executemany("INSERT INTO dim_nivel_detalle VALUES (?,?)", list(C.NIV_DET.items()))
    cur.executemany("INSERT INTO dim_posicion_ocupacion VALUES (?,?)", list(C.POS_OCU.items()))
    cur.executemany("INSERT INTO dim_rama VALUES (?,?)", list(C.RAMA_EST2.items()))
    cur.executemany("INSERT INTO dim_tamano_localidad VALUES (?,?)", list(C.T_LOC_TRI.items()))
    cur.executemany("INSERT INTO dim_ing7c VALUES (?,?)", list(C.ING7C.items()))
    cur.executemany("INSERT INTO dim_grupo_ingreso VALUES (?,?)", list(C.GRUPO_INGRESO.items()))
    t = tabla_upm[["upm", "cve_ent", "est_d_tri", "estrato_col", "n_registros_sdemt"]].astype(int)
    cur.executemany("INSERT INTO dim_upm VALUES (?,?,?,?,?)", t.itertuples(index=False, name=None))
    con.commit()


def cargar_hechos(con: sqlite3.Connection, df: pd.DataFrame) -> int:
    f = df[COLUMNAS_HECHOS].copy()
    for c in _BOOLEANAS:
        f[c] = f[c].astype(int)
    f.to_sql("fact_ocupado", con, if_exists="append", index=False, chunksize=20_000)
    con.commit()
    return len(f)


def crear_indices_y_vistas(con: sqlite3.Connection) -> None:
    con.executescript(DDL_INDICES + DDL_VISTAS)
    con.commit()


def guardar_tabla(con: sqlite3.Connection, nombre: str, df: pd.DataFrame) -> None:
    """Guarda tablas auxiliares (bitácora, resultados del análisis...) reemplazándolas."""
    df.to_sql(nombre, con, if_exists="replace", index=False)


def verificar(con: sqlite3.Connection) -> dict:
    """Comprobaciones de integridad del archivo recién creado."""
    out = {
        "integrity_check": con.execute("PRAGMA integrity_check").fetchone()[0],
        "foreign_key_violations": len(con.execute("PRAGMA foreign_key_check").fetchall()),
        "filas_fact_ocupado": con.execute("SELECT COUNT(*) FROM fact_ocupado").fetchone()[0],
        "filas_dim_upm": con.execute("SELECT COUNT(*) FROM dim_upm").fetchone()[0],
        "suma_ponderadores": con.execute("SELECT SUM(fac_tri) FROM fact_ocupado").fetchone()[0],
        "til1_nacional_sql": con.execute(
            "SELECT 100.0*SUM(fac_tri*informal)/SUM(fac_tri) FROM fact_ocupado").fetchone()[0],
    }
    return out
