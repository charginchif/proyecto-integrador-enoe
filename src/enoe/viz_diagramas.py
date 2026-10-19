"""Diagramas explicativos del proyecto (matplotlib, mismo estilo y paleta que viz.py).

Se usan en el informe técnico (Word) y en la presentación completa. Las coordenadas están en pulgadas:
cada figura es un lienzo (w x h) con ejes que ocupan toda la figura, lo que facilita ubicar cajas y flechas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon
from scipy import stats

from . import config as C
from .viz import AZUL, BASE, MUTED, NARANJA, SUP, TXT, TXT2, aplicar_tema

NAVY = "#1E2A6B"
TINTE = "#F3F5FB"
LINEA = "#9FB0DA"

aplicar_tema()


def _lienzo(w: float, h: float):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def _caja(ax, x, y, w, h, titulo, sub=None, fc=TINTE, tc=NAVY, sc=TXT, fs=11, fs_sub=9, radio=0.09, ec="none", lw=0, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radio}", fc=fc, ec=ec, lw=lw, zorder=z))
    if sub:
        ax.text(x + w / 2, y + h * 0.66, titulo, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc, zorder=z + 1, linespacing=1.15)
        ax.text(x + w / 2, y + h * 0.29, sub, ha="center", va="center", fontsize=fs_sub, color=sc, zorder=z + 1, linespacing=1.2)
    else:
        ax.text(x + w / 2, y + h / 2, titulo, ha="center", va="center", fontsize=fs, fontweight="bold", color=tc, zorder=z + 1, linespacing=1.2)


def _flecha(ax, x0, y0, x1, y1, color=AZUL, lw=2.0, z=1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, shrinkA=0, shrinkB=0), zorder=z)


# --------------------------------------------------------------------------- #
def fig_kdd():
    fig, ax = _lienzo(9.6, 4.0)
    fases = [
        ("Selección", "Fase 1 · Sem. 1", ["ENOE 4T-2025\n(INEGI)", "Tablas SDEMT\n+ COE2T", "7 cifras oficiales\nvalidadas"]),
        ("Preprocesamiento", "Fase 2 · Sem. 4", ["Cobertura y\nfaltantes", "Calidad del ingreso\n(grupos A/B/C/D)", "Atípicos y\n15 pruebas"]),
        ("Transformación", "Fase 3 · Sem. 4·6·7", ["Variables\nderivadas", "ETL hacia\nSQLite", "Documentos\nMongoDB"]),
        ("Minería", "Fase 4 · Sem. 2·3·5", ["Diseño muestral\n(Rao-Wu)", "Spearman\ny Mincer", "Brecha y\nOaxaca-Blinder"]),
        ("Interpretación", "Fase 5 · Sem. 5", ["Hallazgos y\nmétricas", "Recomen-\ndaciones", "Límites del\nestudio"]),
    ]
    w, gap, x0 = 1.76, 0.1, 0.2
    for i, (nombre, sem, items) in enumerate(fases):
        x = x0 + i * (w + gap)
        pts = [(x, 2.9), (x + w - 0.3, 2.9), (x + w, 3.4), (x + w - 0.3, 3.9), (x, 3.9)]
        ax.add_patch(Polygon(pts, closed=True, fc=NAVY, ec="none", zorder=2))
        ax.text(x + 0.12, 3.54, nombre, ha="left", va="center", fontsize=10.5, fontweight="bold", color="white", zorder=3)
        ax.text(x + 0.12, 3.2, sem, ha="left", va="center", fontsize=8.3, color="#CADCFC", zorder=3)
        ax.add_patch(FancyBboxPatch((x, 0.5), w - 0.06, 2.15, boxstyle="round,pad=0,rounding_size=0.08", fc=TINTE, ec="none", zorder=2))
        for j, it in enumerate(items):
            ax.text(x + 0.12, 2.17 - j * 0.67, "• " + it.replace("\n", "\n   "), ha="left", va="center", fontsize=8.8, color=TXT, zorder=3, linespacing=1.25)
    return fig


def fig_arquitectura():
    fig, ax = _lienzo(9.6, 4.5)
    # fila superior
    _caja(ax, 0.15, 2.85, 1.5, 1.2, "Microdatos\nINEGI", "SDEMT · COE2T\n(CSV)", fs=10.5, fs_sub=8.5)
    _caja(ax, 1.95, 2.85, 2.0, 1.2, "Pipeline ETL", "extract · clean\ntransform · validate", fs=10.5, fs_sub=8.5)
    _caja(ax, 4.25, 2.85, 2.0, 1.2, "SQLite", "esquema en estrella\nPK · FK · CHECK", fc=NAVY, tc="white", sc="#CADCFC", fs=10.5, fs_sub=8.5)
    _caja(ax, 6.55, 2.85, 1.35, 1.2, "Análisis", "Rao-Wu\nmodelos", fs=10.5, fs_sub=8.5)
    _caja(ax, 8.2, 2.85, 1.25, 1.2, "Resultados", "CSV · figuras\ninformes", fs=10.5, fs_sub=8.5)
    for x0, x1 in [(1.65, 1.95), (3.95, 4.25), (6.25, 6.55), (7.9, 8.2)]:
        _flecha(ax, x0 + 0.02, 3.45, x1 - 0.02, 3.45)
    # fila inferior
    _caja(ax, 4.25, 1.0, 2.0, 1.2, "MongoDB", "documentos: entidades\npersonas · metadatos", fc=NAVY, tc="white", sc="#CADCFC", fs=10.5, fs_sub=8.5)
    _caja(ax, 6.55, 1.0, 2.0, 1.2, "Tablero", "HTML interactivo\n(ficha por entidad)", fs=10.5, fs_sub=8.5)
    _flecha(ax, 5.25, 2.85, 5.25, 2.2)
    _flecha(ax, 6.25, 1.6, 6.55, 1.6)
    ax.text(2.0, 1.6, "SQLite = fuente de verdad\n(análisis, integridad)", ha="left", va="center", fontsize=8.8, color=TXT2, linespacing=1.3)
    ax.text(2.0, 1.15, "MongoDB = vista de lectura\n(ficha por entidad)", ha="left", va="center", fontsize=8.8, color=TXT2, linespacing=1.3)
    ax.add_patch(FancyBboxPatch((0.15, 0.1), 9.3, 0.55, boxstyle="round,pad=0,rounding_size=0.08", fc="#FFFFFF", ec=LINEA, lw=1.0, zorder=2))
    ax.text(4.8, 0.375, "Garantías: 15 pruebas de datos  ·  34 pruebas de código  ·  una sola semilla  ·  SHA-256 de cada archivo  ·  ETL idempotente",
            ha="center", va="center", fontsize=8.8, color=TXT2, zorder=3)
    return fig


def fig_esquema_estrella():
    fig, ax = _lienzo(9.6, 5.0)
    _caja(ax, 3.2, 1.95, 3.2, 1.1, "fact_ocupado", "190,187 filas · una por persona ocupada", fc=NAVY, tc="white", sc="#CADCFC", fs=13)
    arriba = [("dim_entidad", "32 filas"), ("dim_sexo", "2 filas"), ("dim_nivel_instruccion", "5 filas"), ("dim_nivel_detalle", "5 filas"), ("dim_posicion_ocupacion", "4 filas")]
    abajo = [("dim_rama", "12 filas"), ("dim_tamano_localidad", "4 filas"), ("dim_ing7c", "7 filas"), ("dim_grupo_ingreso", "4 filas"), ("dim_upm", "21,194 filas")]
    w, gap = 1.7, 0.14
    x_ini = (9.6 - (5 * w + 4 * gap)) / 2
    anclas = np.linspace(3.55, 6.05, 5)
    for i, (n, f) in enumerate(arriba):
        x = x_ini + i * (w + gap)
        ax.plot([x + w / 2, anclas[i]], [3.95, 3.05], color=LINEA, lw=1.4, zorder=1)
        _caja(ax, x, 3.95, w, 0.8, n, f, fs=8.8, fs_sub=8.5)
    for i, (n, f) in enumerate(abajo):
        x = x_ini + i * (w + gap)
        ax.plot([x + w / 2, anclas[i]], [1.05, 1.95], color=LINEA, lw=1.4, zorder=1)
        _caja(ax, x, 0.25, w, 0.8, n, f, fs=8.8, fs_sub=8.5)
    ax.text(0.3, 2.5, "Cada dimensión\ndescribe a la persona\nmediante una llave\nforánea (FK).", ha="left", va="center", fontsize=8.5, color=MUTED)
    return fig


def fig_diseno_muestral():
    fig, ax = _lienzo(9.6, 3.9)
    items = [("Estrato", "724 estratos\n(713 tras fusionar los\nque tienen 1 sola UPM)"), ("UPM", "21,194 unidades primarias\nde muestreo (conjuntos\nde viviendas)"),
             ("Vivienda", "se entrevista hasta\n5 veces (panel rotativo,\nvariable n_ent)"), ("Persona", "419,038 residentes;\ncada una trae su\nfactor de expansión")]
    w, gap = 1.95, 0.45
    for i, (t, s) in enumerate(items):
        x = 0.2 + i * (w + gap)
        _caja(ax, x, 1.95, w, 1.55, t, s, fc=NAVY if i == 3 else TINTE, tc="white" if i == 3 else NAVY, sc="#CADCFC" if i == 3 else TXT, fs=13, fs_sub=9)
        if i < 3:
            _flecha(ax, x + w + 0.04, 2.72, x + w + gap - 0.04, 2.72)
    ax.add_patch(FancyBboxPatch((0.2, 0.2), 9.15, 1.45, boxstyle="round,pad=0,rounding_size=0.09", fc="#FFFFFF", ec=LINEA, lw=1.0, zorder=2))
    ax.text(0.45, 1.3, "fac_tri = a cuántas personas de la población representa cada persona de la muestra", ha="left", va="center", fontsize=10.5, fontweight="bold", color=NAVY, zorder=3)
    ax.text(0.45, 0.88, "La suma de fac_tri es 131.0 millones de personas (la población del país); los ocupados de 15+ años representan 59.8 millones.", ha="left", va="center", fontsize=9.2, color=TXT, zorder=3)
    ax.text(0.45, 0.5, "Ejemplo: una persona con fac_tri = 300 cuenta como 300 personas en cualquier promedio o porcentaje.", ha="left", va="center", fontsize=9.2, color=TXT, zorder=3)
    return fig


def fig_rao_wu(semilla: int = C.SEMILLA):
    fig, ax = _lienzo(9.6, 4.7)
    titulos = ["1. Un estrato con n = 4 UPM", "2. Se sortean n − 1 = 3 UPM\ncon reemplazo", "3. Se reescalan los pesos\n× n/(n − 1) = 4/3", "4. Se repite 1,000 veces"]
    xs = [0.2, 2.55, 4.9, 7.25]
    for x, t in zip(xs, titulos):
        ax.text(x + 1.05, 4.3, t, ha="center", va="center", fontsize=9.6, fontweight="bold", color=NAVY, linespacing=1.15)
    for letra, y in zip("ABCD", [3.3, 2.65, 2.0, 1.35]):
        _caja(ax, 0.75, y, 0.9, 0.5, f"UPM {letra}", fs=9, radio=0.06, fc=TINTE)
    ax.text(1.2, 0.95, "peso 1 cada una", ha="center", fontsize=8.5, color=MUTED)
    for letra, y in zip("BBD", [3.3, 2.65, 2.0]):
        _caja(ax, 3.05, y, 0.9, 0.5, f"salió {letra}", fs=9, radio=0.06, fc="#CADCFC")
    ax.text(3.5, 1.4, "veces que salió cada UPM:\nA = 0 · B = 2 · C = 0 · D = 1", ha="center", fontsize=8.5, color=TXT, linespacing=1.3)
    ax3 = fig.add_axes([5.15 / 9.6, 1.1 / 4.7, 1.6 / 9.6, 2.55 / 4.7])
    pesos = np.array([0, 2, 0, 1]) * 4 / 3
    ax3.bar(list("ABCD"), pesos, color=AZUL, width=0.6)
    for i, v in enumerate(pesos):
        ax3.text(i, v + 0.08, f"{v:.2f}", ha="center", fontsize=8.5, color=TXT2)
    ax3.set_ylim(0, 3.4)
    ax3.set_yticks([])
    ax3.grid(False)
    ax3.spines["left"].set_visible(False)
    ax3.tick_params(labelsize=8.5)
    ax.text(5.95, 0.55, "los pesos suman 4,\ncomo antes", ha="center", fontsize=8.5, color=MUTED, linespacing=1.3)
    ax4 = fig.add_axes([7.4 / 9.6, 1.1 / 4.7, 2.0 / 9.6, 2.55 / 4.7])
    rng = np.random.default_rng(semilla)
    reps = rng.normal(0, 1, 1000)
    ax4.hist(reps, bins=22, color=AZUL, alpha=0.9, edgecolor=SUP, linewidth=0.5)
    lo, hi = np.percentile(reps, [2.5, 97.5])
    for v in (lo, hi):
        ax4.axvline(v, color=NARANJA, lw=1.6)
    ax4.set_yticks([])
    ax4.set_xticks([lo, hi])
    ax4.set_xticklabels(["2.5 %", "97.5 %"], fontsize=8.5)
    ax4.spines["left"].set_visible(False)
    ax4.grid(False)
    ax.text(8.4, 0.55, "desviación estándar = error estándar\npercentiles 2.5 y 97.5 = IC 95 %", ha="center", fontsize=8.5, color=TXT, linespacing=1.3)
    ax.text(8.4, 3.95, "(distribución ilustrativa)", ha="center", fontsize=8, color=MUTED)
    for x0 in (2.3, 4.65, 7.0):
        _flecha(ax, x0 - 0.2, 2.5, x0 + 0.2, 2.5, lw=1.8)
    return fig


def fig_como_leer_ic(tabla_cuantiles: pd.DataFrame, tabla_brecha: pd.DataFrame, tabla_subgrupos: pd.DataFrame):
    """Tres intervalos reales para aprender a leerlos (uno claramente distinto de 0, uno límite y uno que incluye el 0)."""
    t = tabla_brecha.set_index("nivel").loc["Total"]
    c50 = tabla_cuantiles.set_index("percentil").loc[50]
    sur = tabla_subgrupos[(tabla_subgrupos["dimension"] == "Región") & (tabla_subgrupos["categoria"] == "Sur")].iloc[0]
    filas = [("Brecha por hora, total", t["brecha_hora_pct"], t["brecha_hora_inf"], t["brecha_hora_sup"], "El intervalo NO incluye el 0:\nhay brecha (p < 0.001)"),
             ("Brecha en la mediana", c50["brecha_pct"], c50["inf"], c50["sup"], "El intervalo toca el 0:\nevidencia débil (p = %.2f)" % c50["p"]),
             ("Brecha en la región Sur", sur["brecha_pct"], sur["inf"], sur["sup"], "El intervalo INCLUYE el 0:\nno hay brecha demostrable (p = %.2f)" % sur["p"])]
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    for i, (n, est, lo, hi, lectura) in enumerate(filas[::-1]):
        ax.plot([lo, hi], [i, i], color=AZUL, lw=3, solid_capstyle="round", zorder=2)
        ax.scatter([est], [i], s=80, color=AZUL, edgecolor=SUP, linewidth=1.6, zorder=3)
        ax.text(7.2, i, lectura, va="center", ha="left", fontsize=9.3, color=TXT2, linespacing=1.3)
        ax.text(-5.9, i + 0.28, n, va="center", ha="left", fontsize=9.8, fontweight="bold", color=TXT)
        ax.text(est, i - 0.32, f"{est:.1f} % [{lo:.1f}; {hi:.1f}]", ha="center", va="center", fontsize=8.8, color=TXT2)
    ax.axvline(0, color=NARANJA, lw=1.8, zorder=1)
    ax.text(0.15, 2.62, "0 = sin brecha", color=NARANJA, fontsize=9, ha="left", va="center")
    ax.set_xlim(-6, 12.5)
    ax.set_xticks([-4, -2, 0, 2, 4, 6, 8, 10])
    ax.set_ylim(-0.7, 2.9)
    ax.set_yticks([])
    ax.set_xlabel("% menos que ganan las mujeres por hora (IC 95 %)")
    ax.xaxis.set_major_formatter(plt.FormatStrFormatter("%.0f %%"))
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    fig.subplots_adjust(left=0.03, right=0.99, top=0.97, bottom=0.2)
    return fig


def fig_oaxaca_idea(ob: pd.DataFrame):
    d = ob[ob["especificacion"].str.startswith("Principal")].set_index("componente")["log_puntos"] * 100
    d.index = [i.strip(" ·") for i in d.index]
    total = d["Brecha total (log-puntos)"]
    exp = d["Explicada por características (referencia agrupada)"]
    noexp = d["No explicada (referencia agrupada)"]
    fig, ax = _lienzo(9.6, 4.3)
    _caja(ax, 0.3, 2.7, 2.5, 1.35, f"{total:+.1f}", "Brecha total por hora\n(hombres − mujeres)", fc=NAVY, tc="white", sc="#CADCFC", fs=22, fs_sub=9)
    ax.text(3.05, 3.37, "=", fontsize=26, ha="center", va="center", color=NAVY, fontweight="bold")
    _caja(ax, 3.3, 2.7, 2.9, 1.35, f"{exp:+.1f}", "EXPLICADA por características\n(escolaridad, edad, lugar, empleo, rama)", fc="#CADCFC", tc=NAVY, sc=TXT, fs=22, fs_sub=9)
    ax.text(6.45, 3.37, "+", fontsize=26, ha="center", va="center", color=NAVY, fontweight="bold")
    _caja(ax, 6.7, 2.7, 2.6, 1.35, f"{noexp:+.1f}", "NO EXPLICADA\n(pago distinto a las\nmismas características)", fc="#FBD9CB", tc="#9A3A14", sc=TXT, fs=22, fs_sub=9)
    ax.text(3.3 + 1.45, 2.4, "Las mujeres tienen mejores características\n(sobre todo más escolaridad): eso favorecería su ingreso", ha="center", va="top", fontsize=8.8, color=TXT, linespacing=1.3)
    ax.text(6.7 + 1.3, 2.4, "A igualdad de características, a las mujeres\nse les paga menos: ≈ 7 puntos de más", ha="center", va="top", fontsize=8.8, color=TXT, linespacing=1.3)
    comp = [("escolaridad", d["escolaridad"]), ("edad", d["edad / experiencia"]), ("entidad y localidad", d["entidad y tamaño de localidad"]),
            ("posición e informalidad", d["posición e informalidad"]), ("rama", d["rama de actividad"])]
    ax.text(0.3, 1.45, "Desglose de la parte explicada (puntos logarítmicos):", fontsize=9.2, fontweight="bold", color=NAVY, ha="left")
    anchos, sep = 1.7, 0.12
    for i, (n, v) in enumerate(comp):
        x = 0.3 + i * (anchos + sep)
        _caja(ax, x, 0.35, anchos, 0.85, f"{v:+.1f}", n, fc=TINTE, tc=AZUL if v < 0 else "#B3261E", sc=TXT, fs=15, fs_sub=8.5)
    return fig


def fig_spearman_ejemplo():
    """Ejemplo didáctico (seis personas ilustrativas): valores -> rangos -> correlación de los rangos."""
    esc = np.array([6, 9, 9, 12, 16, 18])
    sal = np.array([30, 45, 38, 60, 90, 85])
    rx, ry = stats.rankdata(esc), stats.rankdata(sal)
    rho = np.corrcoef(rx, ry)[0, 1]
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.6))
    ax = axs[0]
    ax.scatter(esc, sal, s=70, color=AZUL, edgecolor=SUP, linewidth=1.6, zorder=3)
    for e, s_ in zip(esc, sal):
        ax.annotate(f"${s_}", (e, s_), xytext=(6, 5), textcoords="offset points", fontsize=8.5, color=TXT2)
    ax.set_xlabel("Años de escolaridad")
    ax.set_ylabel("Ingreso por hora ($)")
    ax.set_title("Valores originales", fontsize=10.5, color=TXT2, loc="left")
    ax = axs[1]
    ax.scatter(rx, ry, s=70, color=NARANJA, edgecolor=SUP, linewidth=1.6, zorder=3)
    ax.set_xlabel("Lugar en escolaridad (1 = menos)")
    ax.set_ylabel("Lugar en ingreso (1 = menos)")
    ax.set_title(f"Rangos: Spearman = Pearson de los rangos = {rho:.2f}", fontsize=10.5, color=TXT2, loc="left")
    ax.set_xticks(range(1, 7))
    ax.set_yticks(range(1, 7))
    fig.subplots_adjust(left=0.08, right=0.99, top=0.88, bottom=0.17, wspace=0.28)
    return fig, rho, (esc, sal, rx, ry)
