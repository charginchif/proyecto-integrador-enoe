"""Datos de las páginas interactivas (tesina: sitio/index.html; presentación: sitio/presentacion.html): todo sale de results/ y de la base SQLite, nada se escribe a mano.

``datos_web()`` devuelve un diccionario listo para ``json.dumps``; la página lo incrusta y dibuja las gráficas en el navegador.
Los números se redondean a lo que se muestra (2 decimales como máximo) para que el archivo pese poco.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from enoe import config as C  # noqa: E402
from enoe import load_mongo as L  # noqa: E402
from enoe.survey import cuantil_ponderado  # noqa: E402
from informe_datos import cargar  # noqa: E402


def r(x, d: int = 2):
    """Redondea y convierte a tipos de Python (None si falta)."""
    if x is None or (isinstance(x, float) and np.isnan(x)) or (isinstance(x, (np.floating,)) and np.isnan(x)):
        return None
    return round(float(x), d)


def curva_ingreso(minimo: int = 60) -> list[dict]:
    """Mediana ponderada del ingreso por hora según los años de escolaridad y el sexo (celdas con al menos ``minimo`` observaciones)."""
    con = sqlite3.connect(C.DB_PATH)
    df = pd.read_sql("SELECT anios_esc, sex, ing_hora, fac_tri FROM fact_ocupado WHERE en_muestra_salarial = 1", con)
    con.close()
    filas: dict[int, dict] = {}
    for (a, s), g in df.groupby(["anios_esc", "sex"]):
        if len(g) >= minimo:
            fila = filas.setdefault(int(a), {"a": int(a)})
            fila["m" if s == 2 else "h"] = r(cuantil_ponderado(g["ing_hora"].to_numpy(float), g["fac_tri"].to_numpy(float), 0.5), 2)
            fila["nm" if s == 2 else "nh"] = int(len(g))
    return [filas[k] for k in sorted(filas)]


def datos_extra(D) -> dict:
    """Series que solo usa la tesina (figuras del capítulo de resultados que la presentación no necesita)."""
    ob = D.ob
    claves = [("Brecha total", "Brecha total (log-puntos)", "total"), ("Explicada por características", "Explicada por características (referencia agrupada)", "explicada"),
              ("escolaridad", "escolaridad", "comp"), ("edad / experiencia", "edad / experiencia", "comp"), ("entidad y localidad", "entidad y tamaño de localidad", "comp"),
              ("posición e informalidad", "posición e informalidad", "comp"), ("rama de actividad", "rama de actividad", "comp"), ("No explicada", "No explicada (referencia agrupada)", "noexp")]
    oaxaca_full = [{"n": n, "t": t, "v": r(ob.loc[k, "log_puntos"] * 100, 2), "lo": r(ob.loc[k, "ic_inf"] * 100, 2), "hi": r(ob.loc[k, "ic_sup"] * 100, 2)} for n, k, t in claves]
    rb = D.rob_tot
    robustez = [{"id": i.split(" ")[0], "n": i, "d": rb.loc[i, "descripcion"], "v": r(rb.loc[i, "brecha_pct"], 1), "lo": r(rb.loc[i, "inf"], 1), "hi": r(rb.loc[i, "sup"], 1),
                 "p": r(rb.loc[i, "p"], 4), "N": int(rb.loc[i, "n"])} for i in rb.index]
    subgrupos = [{"dim": f.dimension, "cat": f.categoria, "v": r(f.brecha_pct, 1), "lo": r(f.inf, 1), "hi": r(f.sup, 1), "pv": r(f.p_holm_dimension, 4), "sig": bool(f.p_holm_dimension < 0.05),
                  "nh": int(f.n_hombres), "nm": int(f.n_mujeres)} for f in D.brecha_subgrupos.itertuples()]
    return {"oaxaca_full": oaxaca_full, "robustez": robustez, "subgrupos": subgrupos}


def datos_web(extra: bool = False) -> dict:
    D = cargar()
    R, rt, tot = D.R, D.rt, D.tot
    niv = {1: C.NIV_INS[1], 2: C.NIV_INS[2], 3: C.NIV_INS[3], 4: C.NIV_INS[4]}

    # --- estados -------------------------------------------------------------------------------------------------------------
    til = D.til1_entidad.set_index("cve_ent")
    ret = D.retorno_entidad.set_index("cve_ent")
    bre = D.brecha_estados.set_index("cve_ent")
    docs = {d["cve_ent"]: d for d in L.documentos_entidades()}
    estados = []
    for cve, (nombre, _oficial, abrev, region, col, fila) in C.ENTIDADES.items():
        t, g, b = til.loc[cve], ret.loc[cve], bre.loc[cve]
        estados.append({
            "id": int(cve), "n": nombre, "a": abrev, "r": region, "col": int(col), "fila": int(fila),
            "til": [r(t.til1_est, 1), r(t.til1_ic_inf, 1), r(t.til1_ic_sup, 1), int(t.til1_rango), int(t.til1_rango_inf), int(t.til1_rango_sup)],
            "esc": [r(t.esc15_est, 2), r(t.esc15_ic_inf, 2), r(t.esc15_ic_sup, 2)],
            "ocu": int(round(t.ocupados_est)),
            "ret": [r(g.ret_est, 2), r(g.ret_ic_inf, 2), r(g.ret_ic_sup, 2)],
            "rho": [r(g.rho_est, 3), r(g.rho_ic_inf, 3), r(g.rho_ic_sup, 3), int(g.rho_rango), int(g.rho_rango_inf), int(g.rho_rango_sup)],
            "mln": [r(g.mln_est, 1), r(g.mln_ic_inf, 1), r(g.mln_ic_sup, 1), int(g.med_rango)],
            "q": int(g.cuartil_ingreso),
            "bh": [r(b.brecha_hora_est, 1), r(b.brecha_hora_ic_inf, 1), r(b.brecha_hora_ic_sup, 1), r(b.brecha_hora_p, 3)],
            "bm": [r(b.brecha_mens_est, 1), r(b.brecha_mens_ic_inf, 1), r(b.brecha_mens_ic_sup, 1)],
            "nsal": int(g.n_salarial),
        })

    # --- documento de MongoDB de cada entidad (extracto para la lámina de ingeniería) -------------------------------------------
    def redondear(x):
        if isinstance(x, float):
            return round(x, 2)
        if isinstance(x, dict):
            return {k: redondear(v) for k, v in x.items()}
        if isinstance(x, list):
            return [redondear(v) for v in x]
        return x

    mongo = {str(cve): redondear({k: d[k] for k in ("_id", "cve_ent", "entidad", "region", "periodo", "informalidad", "rendimiento_escolaridad", "brecha_genero")})
             for cve, d in docs.items()}

    # --- premio por nivel, brecha por nivel, escalera, cuantiles, Oaxaca-Blinder -----------------------------------------------------
    etiquetas_premio = ["Primaria completa", "Secundaria completa", "Media superior (12 a 15 años)", "Licenciatura o posgrado (16+ años)"]
    premio = [{"n": et, "v": r(f.premio_pct, 1), "lo": r(f.inf, 1), "hi": r(f.sup, 1), "N": int(f.n)} for et, f in zip(etiquetas_premio, D.premio_por_nivel.itertuples())]

    brecha_nivel = []
    for k in D.bn.index:
        f = D.bn.loc[k]
        brecha_nivel.append({
            "n": k.split(". ", 1)[-1], "h": [r(f.brecha_hora_pct, 1), r(f.brecha_hora_inf, 1), r(f.brecha_hora_sup, 1)],
            "m": [r(f.brecha_mens_pct, 1), r(f.brecha_mens_inf, 1), r(f.brecha_mens_sup, 1)],
            "t": [r(f.menos_horas_mujeres_pct, 1), r(f.menos_horas_inf, 1), r(f.menos_horas_sup, 1)],
            "ih": r(f.ing_hora_h, 2), "im": r(f.ing_hora_m, 2), "hh": r(f.horas_h, 1), "hm": r(f.horas_m, 1), "p": r(f.p_hora_holm, 4),
        })

    etiquetas_escalera = {"G0": "Sin controles", "G1": "+ escolaridad", "G2": "+ edad", "G3": "+ entidad y localidad", "G4": "+ posición e informalidad", "G5": "+ rama de actividad",
                          "G6": "+ horas trabajadas"}
    escalera = [{"id": f.modelo[:2], "n": etiquetas_escalera[f.modelo[:2]], "v": r(f.brecha_pct, 1), "lo": r(f.brecha_pct_inf, 1), "hi": r(f.brecha_pct_sup, 1), "r2": r(f.r2, 3)}
                for f in D.escalera_brecha.itertuples()]

    cuantiles = [{"p": int(i), "h": r(f.ing_hora_h, 2), "m": r(f.ing_hora_m, 2), "v": r(f.brecha_pct, 1), "lo": r(f.inf, 1), "hi": r(f.sup, 1), "pv": r(f.p, 4)} for i, f in D.cu.iterrows()]

    ob = D.ob
    componentes = [("Brecha total", "Brecha total (log-puntos)"), ("Explicada por características", "Explicada por características (referencia agrupada)"),
                   ("No explicada", "No explicada (referencia agrupada)")]
    oaxaca = [{"n": n, "v": r(ob.loc[k, "log_puntos"] * 100, 2), "lo": r(ob.loc[k, "ic_inf"] * 100, 2), "hi": r(ob.loc[k, "ic_sup"] * 100, 2)} for n, k in componentes]

    # --- calidad del ingreso, embudo y validación -----------------------------------------------------------------------------------------
    cal = D.calidad_ingreso
    poblaciones = [("Total", "Total"), ("Hombres", "Hombres"), ("Mujeres", "Mujeres")] + [(f"Nivel {k}. {niv[k]}", niv[k]) for k in (1, 2, 3, 4)]
    calidad = []
    for clave, etiqueta in poblaciones:
        sub = cal[cal.poblacion == clave].set_index("grupo")
        calidad.append({"n": etiqueta, "g": "total" if clave == "Total" else "sexo" if clave in ("Hombres", "Mujeres") else "nivel", **{g: r(sub.loc[g, "pct"], 1) for g in "ABCD"}})

    b, w = D.bit, D.etl_embudo_salarial.set_index("id")
    embudo = [
        {"n": "Registros de la tabla SDEMT", "v": int(b.loc["L0", "n_despues"]), "k": 1},
        {"n": "Entrevista completa", "v": int(b.loc["L1", "n_despues"])},
        {"n": "Residente habitual", "v": int(b.loc["L2", "n_despues"])},
        {"n": "Personas de 15 años o más", "v": int(b.loc["L3", "n_despues"])},
        {"n": "Ocupados (universo del estudio)", "v": int(b.loc["L4", "n_despues"]), "k": 1},
        {"n": "Ocupados de 15 a 65 años", "v": int(b.loc["L6", "n_despues"])},
        {"n": "… con monto exacto de ingreso", "v": int(w.loc["W1", "n"])},
        {"n": "… con horas trabajadas válidas", "v": int(w.loc["W2", "n"])},
        {"n": "… con escolaridad especificada", "v": int(w.loc["W3", "n"])},
        {"n": "Muestra salarial (sin atípicos)", "v": int(w.loc["W4", "n"]), "k": 1},
    ]
    validacion = [{"n": f.indicador, "p": r(f.estimado_proyecto, 1), "o": r(f.oficial_inegi, 1), "ok": bool(f.coincide)} for f in D.etl_validacion_externa.itertuples()]

    # --- informalidad ------------------------------------------------------------------------------------------------------------------------
    tg = D.tg
    til_nivel = [{"n": niv[k], "v": r(tg.loc[f"Nivel {k}. {niv[k]}", "est"], 1), "lo": r(tg.loc[f"Nivel {k}. {niv[k]}", "ic_inf"], 1), "hi": r(tg.loc[f"Nivel {k}. {niv[k]}", "ic_sup"], 1)}
                 for k in (1, 2, 3, 4)]
    til_region = [{"n": reg, "v": r(tg.loc[f"Región {reg}", "est"], 1)} for reg in ("Norte", "Centro-Norte", "Centro", "Sur")]

    rr = D.rr
    retorno_q = [{"q": k, "v": r(rr.loc[f"Rendimiento medio, cuartil {k} de ingreso estatal (%)", "est"], 1), "lo": r(rr.loc[f"Rendimiento medio, cuartil {k} de ingreso estatal (%)", "ic_inf"], 1),
                  "hi": r(rr.loc[f"Rendimiento medio, cuartil {k} de ingreso estatal (%)", "ic_sup"], 1)} for k in (1, 2, 3, 4)]

    asoc = D.asoc
    k = {
        "ret": [r(rt["nacional_pct"]["est"], 1), r(rt["nacional_pct"]["ic_inf"], 1), r(rt["nacional_pct"]["ic_sup"], 1)],
        "ret_h": r(rt["hombres_pct"]["est"], 1), "ret_m": r(rt["mujeres_pct"]["est"], 1),
        "rho_nac": [r(rt["spearman_nacional"]["est"], 2), r(rt["spearman_nacional"]["ic_inf"], 2), r(rt["spearman_nacional"]["ic_sup"], 2)],
        "dq": [r(rt["dif_q4_q1_log"]["est"], 3), r(rt["dif_q4_q1_log"]["ic_inf"], 3), r(rt["dif_q4_q1_log"]["ic_sup"], 3), r(rt["dif_q4_q1_log"]["p"], 2)],
        "rho_max": [rt["rho_max"]["entidad"], r(rt["rho_max"]["rho_est"], 2)], "rho_min": [rt["rho_min"]["entidad"], r(rt["rho_min"]["rho_est"], 2)],
        "bh": [r(tot.brecha_hora_pct, 1), r(tot.brecha_hora_inf, 1), r(tot.brecha_hora_sup, 1), r(tot.p_hora, 6)],
        "bm": [r(tot.brecha_mens_pct, 1), r(tot.brecha_mens_inf, 1), r(tot.brecha_mens_sup, 1)],
        "menos_horas": r(tot.menos_horas_mujeres_pct, 1), "horas_h": r(tot.horas_h, 1), "horas_m": r(tot.horas_m, 1),
        "g1": [r(D.esc.loc["G1 + escolaridad", "brecha_pct"], 1), r(D.esc.loc["G1 + escolaridad", "brecha_pct_inf"], 1), r(D.esc.loc["G1 + escolaridad", "brecha_pct_sup"], 1)],
        "g5": [r(D.g5["brecha_pct"], 1), r(D.g5["brecha_pct_inf"], 1), r(D.g5["brecha_pct_sup"], 1)],
        "til": [r(D.nac["est"], 1), r(D.nac["ic_inf"], 1), r(D.nac["ic_sup"], 1)],
        "rho_til": r(asoc.loc["rho_spearman_til_esc", "est"], 2), "pend_til": r(asoc.loc["pendiente_til_esc", "est"], 1),
        "deff": r(D.deff.loc["TIL1 nacional", "deff"], 1), "n_efectivo": int(round(D.deff.loc["TIL1 nacional", "n_efectivo"])), "B": int(R["B"]),
        "ocupados_millones": r(R["muestras"]["ocupados_millones"], 1),
    }
    n = {"registros": int(b.loc["L0", "n_despues"]), "universo": int(D.n_u), "ventana": int(D.n_v), "salarial": int(D.n_s), "salarial_ext": int(D.n_ext),
         "filas_fact": int(D.n_u), "cols_fact": int(D.n_cols_fact), "pruebas_datos": int(len(D.etl_expectativas)), "variables_derivadas": 13}

    salida = {
        "k": k, "n": n, "estados": estados, "mongo": mongo, "curva": curva_ingreso(), "premio": premio, "brecha_nivel": brecha_nivel, "escalera": escalera,
        "cuantiles": cuantiles, "oaxaca": oaxaca, "calidad": calidad, "embudo": embudo, "validacion": validacion, "til_nivel": til_nivel, "til_region": til_region,
        "retorno_q": retorno_q,
    }
    if extra:
        salida.update(datos_extra(D))
        salida["n"]["pruebas"] = int(D.n_pruebas)
    return salida


if __name__ == "__main__":
    import json

    d = datos_web()
    txt = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(txt) / 1024:.0f} KB; claves:", ", ".join(f"{k}({len(v)})" if isinstance(v, (list, dict)) else k for k, v in d.items()))
