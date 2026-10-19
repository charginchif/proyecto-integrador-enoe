"""Carga de resultados y cifras formateadas para el informe técnico (todo sale de results/ y de la base SQLite)."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from enoe import config as C  # noqa: E402

RES = C.RESULTS


def leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(RES / f"{nombre}.csv", encoding="utf-8-sig")


def f1(x: float) -> str:
    return f"{x:.1f}"


def n_es(x: float, d: int = 0) -> str:
    return f"{x:,.{d}f}"


def pval(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def cargar() -> SimpleNamespace:
    D = SimpleNamespace()
    D.R = json.loads((RES / "resumen.json").read_text(encoding="utf-8"))
    D.meta = json.loads((RES / "etl_meta.json").read_text(encoding="utf-8"))
    nombres = ["brecha_nivel", "escalera_brecha", "robustez_brecha", "robustez_retorno", "brecha_cuantiles", "oaxaca", "til1_entidad", "retorno_entidad",
               "calidad_ingreso", "perfil_grupos_ingreso", "no_respuesta_logit", "retorno_modelos", "premio_por_nivel", "til1_grupos", "brecha_subgrupos",
               "retorno_resumen", "til1_vs_escolaridad_estatal", "efecto_diseno", "etl_bitacora", "etl_expectativas", "etl_embudo_salarial",
               "etl_validacion_externa", "etl_imputacion_rangos", "etl_umbrales_atipicos", "descriptivos_salario", "tests_clasicos",
               "calidad_ingreso_chi2", "logit_informalidad", "brecha_estados", "calidad_ingreso_dif_mh"]
    for n in nombres:
        setattr(D, n, leer(n))
    D.bn = D.brecha_nivel.set_index("nivel")
    D.esc = D.escalera_brecha.set_index("modelo")
    D.cu = D.brecha_cuantiles.set_index("percentil")
    D.bit = D.etl_bitacora.set_index("id")
    D.perf = D.perfil_grupos_ingreso.set_index("grupo")
    D.rm = D.retorno_modelos.set_index("modelo")
    D.prem = D.premio_por_nivel.set_index("nivel")
    D.tg = D.til1_grupos.set_index("grupo")
    D.rr = D.retorno_resumen.set_index("indicador")
    D.asoc = D.til1_vs_escolaridad_estatal.set_index("indicador")
    D.deff = D.efecto_diseno.set_index("estimador")
    D.robr = D.robustez_retorno.set_index("especificacion")
    D.rob_tot = D.robustez_brecha[D.robustez_brecha["grupo"] == "Total"].set_index("especificacion")
    D.hora_specs = D.rob_tot[~D.rob_tot.index.str.startswith(("S6", "S8", "S9"))]
    cal, R = D.calidad_ingreso, D.R
    D.A_t, D.B_t, D.C_t, D.D_t = (float(cal[(cal.grupo == g) & (cal.poblacion == "Total")]["pct"].iloc[0]) for g in "ABCD")
    D.A_n1 = float(cal[(cal.grupo == "A") & (cal.poblacion == "Nivel 1. Primaria incompleta")]["pct"].iloc[0])
    D.A_n4 = float(cal[(cal.grupo == "A") & (cal.poblacion == "Nivel 4. Medio superior y superior")]["pct"].iloc[0])
    D.n_u, D.n_v, D.n_s = R["muestras"]["universo"], R["muestras"]["ventana_15_65"], R["muestras"]["salarial"]
    D.n_ext = R["muestras"]["salarial_ext"]
    D.nac = R["til1"]["nacional"]
    D.rt = R["retorno"]
    D.tot = D.bn.loc["Total"]
    D.g0, D.g5, D.g6 = D.esc.loc["G0 Sin controles"], D.esc.loc["G5 + rama de actividad"], D.esc.loc["G6 + horas trabajadas"]
    ob = D.oaxaca
    pr = ob[ob.especificacion.str.startswith("Principal")].copy()
    pr["clave"] = [c.strip(" ·") for c in pr["componente"]]
    D.ob = pr.set_index("clave")
    D.ob_h = ob[ob.especificacion.str.startswith("Con horas")].copy()
    D.mx_til, D.mn_til = D.til1_entidad.loc[D.til1_entidad.til1_est.idxmax()], D.til1_entidad.loc[D.til1_entidad.til1_est.idxmin()]
    D.ind = R["individual_informalidad"]
    D.dg = R["diagnosticos"]
    D.dq = D.rt["dif_q4_q1_log"]
    D.cero_reg = 100 * (1 - float(D.bit.loc["QA", "n_despues"]) / D.n_u)
    D.cero_pond = 100 - D.A_t
    # tablas de SQLite
    con = sqlite3.connect(C.DB_PATH)
    t = pd.read_sql("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY type DESC, name", con)
    t["filas"] = [pd.read_sql(f"SELECT COUNT(*) AS n FROM {n}", con)["n"][0] for n in t["name"]]
    D.sqlite_tablas = t[~t["name"].str.startswith("res_")].reset_index(drop=True)
    D.sqlite_n_res = int(t["name"].str.startswith("res_").sum())
    con.close()
    D.sqlite_mb = C.DB_PATH.stat().st_size / 1e6
    con = sqlite3.connect(C.DB_PATH)
    D.n_cols_fact = len(con.execute("PRAGMA table_info(fact_ocupado)").fetchall())
    D.ing_hora_min, D.ing_hora_max = con.execute("SELECT MIN(ing_hora), MAX(ing_hora) FROM fact_ocupado WHERE ing_hora IS NOT NULL").fetchone()
    con.close()
    return D
