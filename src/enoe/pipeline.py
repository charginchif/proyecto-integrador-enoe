"""Orquestador del ETL: extrae -> limpia -> transforma -> valida -> carga a SQLite.

Uso desde línea de comandos:  python scripts/run_etl.py
Cada etapa es una función independiente (importable desde el cuaderno); este módulo solo las encadena.
"""
from __future__ import annotations

import json
import logging
import platform
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import clean, config as C, extract, load_sqlite, survey, transform, validacion

log = logging.getLogger("enoe.pipeline")


def configurar_logging(archivo: Path | None = None) -> None:
    C.LOGS.mkdir(parents=True, exist_ok=True)
    archivo = archivo or (C.LOGS / f"etl_{datetime.now():%Y%m%d_%H%M%S}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[logging.FileHandler(archivo, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
        force=True,
    )


def construir_tabla_upm(sdemt: pd.DataFrame) -> pd.DataFrame:
    """Una fila por UPM de la muestra completa, con su estrato original y su estrato colapsado."""
    upm = (sdemt.groupby("upm", as_index=False)
           .agg(cve_ent=("cve_ent", "first"), est_d_tri=("est_d_tri", "first"), n_registros_sdemt=("upm", "size")))
    assert (sdemt.groupby("upm")["est_d_tri"].nunique() == 1).all(), "Una UPM aparece en más de un estrato"
    assert (sdemt.groupby("upm")["cve_ent"].nunique() == 1).all(), "Una UPM aparece en más de una entidad"
    upm["estrato_col"] = upm["upm"].map(survey.colapsar_estratos(upm))
    return upm


def construir_base_analitica(sdemt: pd.DataFrame, coe2: pd.DataFrame, tabla_upm: pd.DataFrame):
    """Aplica en orden todas las reglas y devuelve (base, bitácora, embudo, umbrales, imputación, expectativas)."""
    bit = clean.Bitacora()
    d = clean.aplicar_cobertura(sdemt, bit)
    d = clean.marcar_ventana(d, bit)
    d = transform.unir_coe2t(d, coe2)
    d = transform.asignar_persona_id(d)
    d = clean.recodificar_faltantes(d, bit)
    d = clean.clasificar_ingreso(d, bit)
    d = transform.agregar_variables(d)
    d = transform.agregar_ingreso_hora(d)
    d, imputacion = transform.imputar_rangos(d)
    d, umbrales = clean.marcar_atipicos(d, bit)
    d = clean.definir_muestras(d)
    d = d.merge(tabla_upm[["upm", "estrato_col"]], on="upm", how="left", validate="many_to_one")
    embudo = clean.embudo_muestra_salarial(d)
    expectativas = clean.verificar_expectativas(d)
    return d, bit.a_dataframe(), embudo, umbrales, imputacion, expectativas


def ejecutar_etl(raw_dir: Path | None = None, db_path: Path | None = None) -> dict:
    inicio = datetime.now()
    log.info("== ETL ENOE %s ==", C.PERIODO_ETIQUETA)
    sdemt = extract.leer_sdemt(raw_dir)
    coe2 = extract.leer_coe2t(raw_dir)
    log.info("SDEMT: %s filas | COE2T: %s filas", f"{len(sdemt):,}", f"{len(coe2):,}")
    archivos = [extract.auditar_archivo("SDEMT", len(sdemt), sdemt.shape[1], raw_dir),
                extract.auditar_archivo("COE2T", len(coe2), coe2.shape[1], raw_dir)]

    ext = validacion.comparar_con_inegi(sdemt)
    base_menores = validacion.efecto_base_menores_15(sdemt)
    log.info("Validación externa (INEGI):\n%s", ext.round(3).to_string(index=False))

    tabla_upm = construir_tabla_upm(sdemt)
    log.info("Diseño: %d UPM, %d estratos originales -> %d colapsados", len(tabla_upm),
             tabla_upm["est_d_tri"].nunique(), tabla_upm["estrato_col"].nunique())

    base, bitacora, embudo, umbrales, imputacion, expectativas = construir_base_analitica(sdemt, coe2, tabla_upm)
    log.info("Universo analítico: %s ocupados de 15+ | ventana 15-65: %s | muestra salarial: %s | ampliada: %s",
             f"{len(base):,}", f"{int(base['en_ventana_15_65'].sum()):,}",
             f"{int(base['en_muestra_salarial'].sum()):,}", f"{int(base['en_muestra_salarial_ext'].sum()):,}")
    log.info("Embudo muestra salarial:\n%s", embudo.to_string(index=False))

    fallidas = expectativas[(~expectativas["cumple"]) & expectativas["critica"]]
    if len(fallidas):
        raise AssertionError("Expectativas críticas incumplidas:\n" + fallidas.to_string(index=False))
    log.info("Expectativas de calidad: %d/%d cumplidas", int(expectativas["cumple"].sum()), len(expectativas))

    # --- Carga ---
    con = load_sqlite.crear_esquema(db_path)
    load_sqlite.poblar_dimensiones(con, tabla_upm)
    n = load_sqlite.cargar_hechos(con, base)
    load_sqlite.crear_indices_y_vistas(con)
    verif = load_sqlite.verificar(con)
    assert verif["integrity_check"] == "ok" and verif["foreign_key_violations"] == 0, verif
    assert verif["filas_fact_ocupado"] == len(base)
    log.info("SQLite: %s filas cargadas | integridad=%s | violaciones FK=%d", f"{n:,}", verif["integrity_check"], verif["foreign_key_violations"])

    meta = {
        "periodo": C.PERIODO_ETIQUETA,
        "inicio": inicio.isoformat(timespec="seconds"),
        "fin": datetime.now().isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "sqlite": sqlite3.sqlite_version,
        "semilla": C.SEMILLA,
        "parametros": {k: getattr(C, k) for k in ["EDAD_MIN", "EDAD_MAX_ANALISIS", "HORAS_MAX", "SEMANAS_POR_MES",
                                                  "RECORTE_PCT", "N_BOOTSTRAP", "ALPHA"]},
        "archivos_origen": archivos,
        "verificacion_sqlite": verif,
        "efecto_base_menores_15": base_menores,
        "n_upm": int(len(tabla_upm)),
        "n_estratos_originales": int(tabla_upm["est_d_tri"].nunique()),
        "n_estratos_colapsados": int(tabla_upm["estrato_col"].nunique()),
        "n_b_sin_p6c": int(imputacion.attrs.get("b_sin_p6c", 0)),
    }
    for nombre, df in [("etl_bitacora", bitacora), ("etl_embudo_salarial", embudo),
                       ("etl_expectativas", expectativas), ("etl_validacion_externa", ext),
                       ("etl_umbrales_atipicos", umbrales), ("etl_imputacion_rangos", imputacion)]:
        load_sqlite.guardar_tabla(con, nombre, df)
        df.to_csv(C.RESULTS / f"{nombre}.csv", index=False, encoding="utf-8-sig")
    load_sqlite.guardar_tabla(con, "etl_run", pd.DataFrame([{"clave": k, "valor": json.dumps(v, ensure_ascii=False, default=str)}
                                                            for k, v in meta.items()]))
    con.commit()
    con.close()
    (C.RESULTS / "etl_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    log.info("ETL terminado en %.1f s", (datetime.now() - inicio).total_seconds())
    return dict(base=base, bitacora=bitacora, embudo=embudo, expectativas=expectativas, validacion_externa=ext,
                umbrales=umbrales, imputacion=imputacion, tabla_upm=tabla_upm, meta=meta)
