"""Genera todas las figuras del proyecto a partir de los resultados guardados (results/*.csv) y la base SQLite."""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import pandas as pd

from . import config as C
from . import modelos as M
from . import viz
from .datos import cargar_datos


def leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(C.RESULTS / f"{nombre}.csv", encoding="utf-8-sig")


def cargar_insumos() -> dict:
    D = cargar_datos()
    W = D.salarial
    r = {n: leer(n) for n in ["etl_bitacora", "etl_embudo_salarial", "calidad_ingreso", "retorno_entidad", "retorno_resumen", "brecha_nivel",
                              "escalera_brecha", "oaxaca", "brecha_cuantiles", "robustez_brecha", "til1_entidad", "til1_vs_escolaridad_estatal"]}
    r["resumen"] = json.loads((C.RESULTS / "resumen.json").read_text(encoding="utf-8"))
    r["D"], r["W"] = D, W
    return r


def generar_todas(guardar: bool = True) -> dict:
    x = cargar_insumos()
    D, W = x["D"], x["W"]
    ret, til, res = x["retorno_entidad"], x["til1_entidad"], x["resumen"]
    rr = x["retorno_resumen"].set_index("indicador")["est"]
    asoc = x["til1_vs_escolaridad_estatal"].set_index("indicador")["est"]
    diag = M.diagnosticos(W, D.diseno)
    figs = {
        "01_embudo_datos": viz.fig_embudo(x["etl_bitacora"], x["etl_embudo_salarial"]),
        "02_calidad_ingreso": viz.fig_calidad_ingreso(x["calidad_ingreso"]),
        "03_distribucion_ingreso": viz.fig_distribucion_ingreso(W.df),
        "04_ingreso_por_escolaridad": viz.fig_ingreso_por_escolaridad(W.df),
        "05_retorno_estados": viz.fig_retorno_estados(ret, rr["Rendimiento nacional por año de escolaridad (%)"]),
        "06_spearman_estados": viz.fig_spearman_estados(ret, rr["Spearman nacional (escolaridad - ingreso/hora)"]),
        "07_escolaridad_vs_ingreso_estatal": viz.fig_dispersion_estatal(ret, rr["Spearman entre estados: escolaridad media vs. ingreso mediano"]),
        "08_cajas_nivel_sexo": viz.fig_cajas_nivel_sexo(W.df),
        "09_brecha_por_nivel": viz.fig_brecha_nivel(x["brecha_nivel"]),
        "10_escalera_controles": viz.fig_escalera(x["escalera_brecha"]),
        "11_oaxaca_blinder": viz.fig_oaxaca(x["oaxaca"]),
        "12_brecha_cuantiles": viz.fig_cuantiles(x["brecha_cuantiles"]),
        "13_robustez_brecha": viz.fig_robustez(x["robustez_brecha"]),
        "14_mapa_informalidad": viz.fig_mapa_informalidad(til),
        "15_informalidad_vs_escolaridad": viz.fig_informalidad_vs_escolaridad(til, asoc["rho_spearman_til_esc"]),
        "16_diagnosticos_modelo": viz.fig_diagnosticos(diag["residuos_ols"], diag["ajustados_ols"]),
        "17_brecha_subgrupos": viz.fig_brecha_subgrupos(leer("brecha_subgrupos")),
    }
    if guardar:
        for nombre, fig in figs.items():
            viz.guardar(fig, nombre)
            plt.close(fig)
    return figs


def generar_diagramas(guardar: bool = True) -> dict:
    """Diagramas explicativos (arquitectura, esquema en estrella, Rao-Wu, ...) para el informe y la presentación."""
    from . import viz_diagramas as vd

    spear, rho_ej, _ = vd.fig_spearman_ejemplo()
    figs = {
        "D01_kdd": vd.fig_kdd(),
        "D02_arquitectura": vd.fig_arquitectura(),
        "D03_esquema_estrella": vd.fig_esquema_estrella(),
        "D04_diseno_muestral": vd.fig_diseno_muestral(),
        "D05_rao_wu": vd.fig_rao_wu(),
        "D06_como_leer_ic": vd.fig_como_leer_ic(leer("brecha_cuantiles"), leer("brecha_nivel"), leer("brecha_subgrupos")),
        "D07_oaxaca_idea": vd.fig_oaxaca_idea(leer("oaxaca")),
        "D08_spearman_ejemplo": spear,
    }
    if guardar:
        for nombre, fig in figs.items():
            viz.guardar(fig, nombre)
            plt.close(fig)
    return figs
