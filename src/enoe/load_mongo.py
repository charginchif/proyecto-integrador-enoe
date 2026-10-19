"""Capa documental (NoSQL): documentos para MongoDB, exportación NDJSON y carga con pymongo.

Arquitectura de persistencia políglota (ver docs/modelo_de_datos_nosql.md):

    SQLite (relacional, esquema en estrella)  -> análisis: JOIN y agregaciones ponderadas sobre ~190 mil filas
    MongoDB (documental)                      -> servicio de lectura: una "ficha" por entidad, consultable por clave

Colecciones:
    entidades  : 32 documentos; cada uno anida indicadores, intervalos y desgloses de UNA entidad
                 (patrón "embedding": todo lo que el tablero muestra al elegir un estado está en un solo documento).
    personas   : un documento por persona ocupada con subdocumentos anidados (persona, trabajo, ingreso, diseño).
    metadatos  : linaje del pipeline (versiones, semilla, huellas SHA-256 de los archivos de origen).

Si pymongo o el servidor no están disponibles, ``exportar`` deja los mismos documentos en archivos NDJSON
listos para ``mongoimport``; el código de carga no cambia.
"""
from __future__ import annotations

import gzip
import json
import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C

DIR_MONGO = C.DATA_PROCESSED / "mongo"


def _limpio(x):
    """Convierte tipos numpy/NaN a tipos JSON/BSON válidos (NaN -> None)."""
    if isinstance(x, (np.floating, float)):
        return None if (isinstance(x, float) and math.isnan(x)) or (isinstance(x, np.floating) and np.isnan(x)) else float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, dict):
        return {k: _limpio(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_limpio(v) for v in x]
    return x


# --------------------------------------------------------------------------- #
# Construcción de documentos
# --------------------------------------------------------------------------- #
def documentos_entidades(resultados: Path | None = None, db_path: Path | None = None) -> list[dict]:
    r = Path(resultados or C.RESULTS)
    til = pd.read_csv(r / "til1_entidad.csv").set_index("cve_ent")
    ret = pd.read_csv(r / "retorno_entidad.csv").set_index("cve_ent")
    brecha = pd.read_csv(r / "brecha_estados.csv").set_index("cve_ent")
    con = sqlite3.connect(db_path or C.DB_PATH)
    cal = pd.read_sql("SELECT cve_ent, grupo_ingreso, pct_ponderado FROM v_calidad_ingreso_entidad", con)
    n_est = pd.read_sql("""SELECT cve_ent, COUNT(*) AS n_universo, SUM(en_ventana_15_65) AS n_ventana,
                                  SUM(en_muestra_salarial) AS n_salarial FROM fact_ocupado GROUP BY cve_ent""", con).set_index("cve_ent")
    con.close()
    docs = []
    for e, (nombre, oficial, abrev, region, _, _) in C.ENTIDADES.items():
        t, g, b = til.loc[e], ret.loc[e], brecha.loc[e]
        c = cal[cal["cve_ent"] == e].set_index("grupo_ingreso")["pct_ponderado"].to_dict()
        docs.append(_limpio({
            "_id": e, "cve_ent": e, "entidad": nombre, "entidad_oficial": oficial, "abreviatura": abrev, "region": region,
            "periodo": C.PERIODO_ETIQUETA, "fuente": "INEGI, ENOE (SDEMT, COE2T)",
            "muestra": {"universo": int(n_est.loc[e, "n_universo"]), "ventana_15_65": int(n_est.loc[e, "n_ventana"]),
                        "salarial": int(n_est.loc[e, "n_salarial"]), "ocupados_estimados": t["ocupados_est"]},
            "informalidad": {"til1_pct": t["til1_est"], "ic95": [t["til1_ic_inf"], t["til1_ic_sup"]],
                             "lugar": int(t["til1_rango"]), "lugar_ic95": [int(t["til1_rango_inf"]), int(t["til1_rango_sup"])]},
            "escolaridad": {"anios_medios_ocupados": t["esc15_est"], "ic95": [t["esc15_ic_inf"], t["esc15_ic_sup"]],
                            "anios_medios_muestra_salarial": g["esc_sal_est"]},
            "ingreso_hora": {"mediana_pesos": g["mln_est"], "ic95": [g["mln_ic_inf"], g["mln_ic_sup"]],
                             "lugar": int(g["med_rango"]), "cuartil": int(g["cuartil_ingreso"])},
            "rendimiento_escolaridad": {"pct_por_anio": g["ret_est"], "ic95": [g["ret_ic_inf"], g["ret_ic_sup"]]},
            "correlacion_spearman": {"rho": g["rho_est"], "ic95": [g["rho_ic_inf"], g["rho_ic_sup"]],
                                     "lugar": int(g["rho_rango"]), "lugar_ic95": [int(g["rho_rango_inf"]), int(g["rho_rango_sup"])]},
            "brecha_genero": {"hora_pct": b["brecha_hora_est"], "hora_ic95": [b["brecha_hora_ic_inf"], b["brecha_hora_ic_sup"]],
                              "mensual_pct": b["brecha_mens_est"], "mensual_ic95": [b["brecha_mens_ic_inf"], b["brecha_mens_ic_sup"]]},
            "calidad_ingreso_pct": {k: c.get(k) for k in "ABCD"},
        }))
    return docs


def documentos_personas(db_path: Path | None = None, lote: int = 20_000):
    """Generador de documentos de persona (por lotes, sin cargar todo en memoria como dicts)."""
    con = sqlite3.connect(db_path or C.DB_PATH)
    sql = """SELECT f.persona_id, f.cve_ent, e.entidad, f.upm, f.fac_tri, s.sexo, f.eda, f.anios_esc, n.nivel, f.niv_det,
                    p.posicion, f.informal, r.rama, f.hrsocup, t.tamano, f.grupo_ingreso, f.ing_mensual, f.ing_hora,
                    f.ln_ing_hora, i.rango AS rango_sm, f.ing_mensual_imp, f.en_ventana_15_65, f.en_muestra_salarial
             FROM fact_ocupado f
             JOIN dim_entidad e ON e.cve_ent = f.cve_ent  JOIN dim_sexo s ON s.sex = f.sex
             JOIN dim_nivel_instruccion n ON n.niv_ins = f.niv_ins  JOIN dim_posicion_ocupacion p ON p.pos_ocu = f.pos_ocu
             JOIN dim_rama r ON r.rama_est2 = f.rama_est2  JOIN dim_tamano_localidad t ON t.t_loc_tri = f.t_loc_tri
             JOIN dim_ing7c i ON i.ing7c = f.ing7c"""
    try:
        for chunk in pd.read_sql(sql, con, chunksize=lote):
            for r in chunk.to_dict("records"):
                yield _limpio({
                    "_id": r["persona_id"], "cve_ent": r["cve_ent"], "entidad": r["entidad"], "fac_tri": r["fac_tri"],
                    "persona": {"sexo": r["sexo"], "edad": r["eda"],
                                "escolaridad": {"anios": r["anios_esc"], "nivel": r["nivel"]}},
                    "trabajo": {"posicion": r["posicion"], "informal": bool(r["informal"]), "rama": r["rama"],
                                "horas_semana": r["hrsocup"], "tamano_localidad": r["tamano"]},
                    "ingreso": {"grupo": r["grupo_ingreso"], "rango_sm": r["rango_sm"], "mensual": r["ing_mensual"],
                                "por_hora": r["ing_hora"], "ln_por_hora": r["ln_ing_hora"], "mensual_imputado": r["ing_mensual_imp"]},
                    "diseno": {"upm": r["upm"]},
                    "muestras": {"ventana_15_65": bool(r["en_ventana_15_65"]), "salarial": bool(r["en_muestra_salarial"])},
                })
    finally:
        con.close()


def documento_metadatos(resultados: Path | None = None) -> list[dict]:
    meta = json.loads((Path(resultados or C.RESULTS) / "etl_meta.json").read_text(encoding="utf-8"))
    return [_limpio({"_id": f"etl_{C.PERIODO_ETIQUETA}", **meta})]


# --------------------------------------------------------------------------- #
# Exportación y carga
# --------------------------------------------------------------------------- #
def exportar_ndjson(docs, ruta: Path, comprimir: bool = False) -> int:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    abre = (lambda p: gzip.open(p, "wt", encoding="utf-8")) if comprimir else (lambda p: open(p, "w", encoding="utf-8"))
    n = 0
    with abre(ruta) as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
            n += 1
    return n


def exportar_todo(dir_salida: Path | None = None) -> dict:
    d = Path(dir_salida or DIR_MONGO)
    ent = documentos_entidades()
    (d / "entidades.json").parent.mkdir(parents=True, exist_ok=True)
    (d / "entidades.json").write_text(json.dumps(ent, ensure_ascii=False, indent=1), encoding="utf-8")
    cuentas = {"entidades": exportar_ndjson(ent, d / "entidades.ndjson"),
               "metadatos": exportar_ndjson(documento_metadatos(), d / "metadatos.ndjson"),
               "personas": exportar_ndjson(documentos_personas(), d / "personas.ndjson.gz", comprimir=True)}
    return cuentas


INDICES = {
    "entidades": [([("cve_ent", 1)], {"unique": True}), ([("region", 1)], {}), ([("informalidad.til1_pct", -1)], {})],
    "personas": [([("cve_ent", 1)], {}), ([("cve_ent", 1), ("ingreso.grupo", 1)], {}),
                 ([("cve_ent", 1), ("persona.sexo", 1)], {}),
                 ([("cve_ent", 1)], {"name": "ix_salarial_por_entidad", "partialFilterExpression": {"muestras.salarial": True}})],
}


def cargar_mongo(uri: str = "mongodb://localhost:27017", base: str = "enoe_2025t4", lote: int = 5000) -> dict:
    """Carga idempotente (reemplaza las colecciones). Requiere ``pip install pymongo`` y un servidor accesible."""
    try:
        from pymongo import MongoClient
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("pymongo no está instalado: ejecute 'pip install pymongo' o use --exportar") from e
    cli = MongoClient(uri, serverSelectionTimeoutMS=4000)
    cli.admin.command("ping")
    db = cli[base]
    cuentas = {}
    for nombre, docs in [("entidades", documentos_entidades()), ("metadatos", documento_metadatos()), ("personas", documentos_personas())]:
        db.drop_collection(nombre)
        col, buf, n = db[nombre], [], 0
        for d in docs:
            buf.append(d)
            if len(buf) >= lote:
                col.insert_many(buf, ordered=False)
                n += len(buf)
                buf = []
        if buf:
            col.insert_many(buf, ordered=False)
            n += len(buf)
        for claves, opts in INDICES.get(nombre, []):
            col.create_index(claves, **opts)
        cuentas[nombre] = n
    return cuentas


# --------------------------------------------------------------------------- #
# Consultas: pipeline de agregación de MongoDB y su equivalente verificable en Python/SQL
# --------------------------------------------------------------------------- #
PIPELINE_TIL1_POR_ENTIDAD = [
    {"$match": {"cve_ent": {"$gte": 1}}},
    {"$group": {"_id": "$cve_ent", "entidad": {"$first": "$entidad"}, "ocupados": {"$sum": "$fac_tri"},
                "informales": {"$sum": {"$cond": ["$trabajo.informal", "$fac_tri", 0]}}}},
    {"$project": {"entidad": 1, "ocupados": 1, "til1_pct": {"$multiply": [100, {"$divide": ["$informales", "$ocupados"]}]}}},
    {"$sort": {"til1_pct": -1}},
]


def til1_por_entidad_desde_ndjson(ruta: Path | None = None) -> pd.DataFrame:
    """Ejecuta en Python exactamente la lógica del pipeline anterior sobre los documentos exportados."""
    ruta = Path(ruta or DIR_MONGO / "personas.ndjson.gz")
    acum: dict[int, list] = {}
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        for linea in f:
            d = json.loads(linea)
            a = acum.setdefault(d["cve_ent"], [d["entidad"], 0.0, 0.0])
            a[1] += d["fac_tri"]
            if d["trabajo"]["informal"]:
                a[2] += d["fac_tri"]
    out = pd.DataFrame([(k, v[0], v[1], 100 * v[2] / v[1]) for k, v in acum.items()], columns=["cve_ent", "entidad", "ocupados", "til1_pct"])
    return out.sort_values("til1_pct", ascending=False).reset_index(drop=True)


def ficha_entidad(clave: int | str, ruta: Path | None = None) -> dict:
    """Equivalente a db.entidades.find_one({'cve_ent': 9}) o por nombre; funciona sin servidor."""
    docs = json.loads((Path(ruta or DIR_MONGO / "entidades.json")).read_text(encoding="utf-8"))
    for d in docs:
        if d["cve_ent"] == clave or str(clave).lower() in (d["entidad"].lower(), d["abreviatura"].lower()):
            return d
    raise KeyError(clave)
