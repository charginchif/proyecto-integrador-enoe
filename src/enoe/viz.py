"""Gráficas del proyecto (matplotlib) con una paleta validada para daltonismo.

Reglas aplicadas (guía de visualización):
  * Color por función: hombres = azul, mujeres = naranja (par validado, CVD ΔE > 24); magnitud = rampa
    secuencial de un solo tono azul; polaridad = azul/rojo con medio gris; niveles ordenados = rampa ordinal.
  * Un solo eje por gráfica (nunca ejes duales); barras desde una línea base con cero visible.
  * Marcas delgadas, rejilla hairline sólida y recesiva, anillo de color de superficie en los puntos.
  * Etiquetas directas selectivas (extremos), leyenda siempre que hay >= 2 series; el texto nunca usa el color de la serie.
  * Cada figura tiene su tabla equivalente en el cuaderno (vista de tabla accesible).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib import colors as mcolors
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from . import config as C
from .survey import cuantil_ponderado

# --- tokens de color (modo claro) ---
SUP, TXT, TXT2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASE, MEDIO = "#e1e0d9", "#c3c2b7", "#f0efec"
AZUL, NARANJA, AQUA, AMARILLO, ROJO = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e34948"
SEQ_PASOS = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf",
             "#1c5cab", "#184f95", "#104281", "#0d366b"]
ORDINAL_4 = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]       # pasos 250, 400, 550, 700 (el más claro >= paso 250)
CMAP_SEQ = mcolors.LinearSegmentedColormap.from_list("azul_seq", SEQ_PASOS)
FUENTE = "Fuente: INEGI, ENOE 2025-T4 (SDEMT y COE2T). Estimaciones ponderadas con fac_tri; IC 95 % por bootstrap de Rao-Wu."


def aplicar_tema() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SUP, "axes.facecolor": SUP, "savefig.facecolor": SUP,
        "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10.5,
        "text.color": TXT, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": BASE, "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.axisbelow": True, "axes.labelsize": 10, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
        "legend.frameon": False, "legend.fontsize": 9.5, "figure.dpi": 110, "savefig.dpi": 200,
        "axes.unicode_minus": False,
    })


aplicar_tema()


# --------------------------------------------------------------------------- #
# utilidades
# --------------------------------------------------------------------------- #
def n_es(x: float, d: int = 0) -> str:
    return f"{x:,.{d}f}"


def encabezado(fig, titulo: str, subtitulo: str = "", y: float = 0.985) -> None:
    fig.text(0.012, y, titulo, fontsize=14, fontweight="bold", color=TXT, va="top", ha="left")
    if subtitulo:
        fig.text(0.012, y - 0.052, subtitulo, fontsize=10.5, color=TXT2, va="top", ha="left")


def pie(fig, texto: str = FUENTE, y: float = 0.008) -> None:
    fig.text(0.012, y, texto, fontsize=8, color=MUTED, va="bottom", ha="left")


def guardar(fig, nombre: str, carpeta: Path | None = None) -> Path:
    carpeta = carpeta or C.FIGURES
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}.png"
    fig.savefig(ruta, dpi=200, facecolor=SUP)
    return ruta


def _color_texto(hex_color: str) -> str:
    r, g, b = mcolors.to_rgb(hex_color)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#ffffff" if lum < 0.5 else TXT


def _punto(ax, x, y, color, s=46, z=3):
    ax.scatter(x, y, s=s, color=color, edgecolor=SUP, linewidth=1.5, zorder=z)


def _ejes_limpios(ax, xgrid=True, ygrid=False):
    ax.grid(axis="x", visible=xgrid)
    ax.grid(axis="y", visible=ygrid)


# --------------------------------------------------------------------------- #
# 1. Calidad y flujo de datos
# --------------------------------------------------------------------------- #
def fig_embudo(bit: pd.DataFrame, embudo: pd.DataFrame):
    b = bit.set_index("id")
    etapas = [
        ("Registros de la tabla SDEMT (todas las edades)", b.loc["L0", "n_despues"]),
        ("Entrevista completa", b.loc["L1", "n_despues"]),
        ("Residente habitual", b.loc["L2", "n_despues"]),
        ("Personas de 15 años y más", b.loc["L3", "n_despues"]),
        ("Ocupados (universo del estudio)", b.loc["L4", "n_despues"]),
        ("Ocupados de 15 a 65 años", b.loc["L6", "n_despues"]),
        ("… con monto exacto de ingreso", embudo.set_index("id").loc["W1", "n"]),
        ("… con horas trabajadas válidas", embudo.set_index("id").loc["W2", "n"]),
        ("… con escolaridad especificada", embudo.set_index("id").loc["W3", "n"]),
        ("Muestra salarial (sin atípicos)", embudo.set_index("id").loc["W4", "n"]),
    ]
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    y = np.arange(len(etapas))[::-1]
    vals = np.array([v for _, v in etapas], float)
    ax.barh(y, vals, height=0.52, color=AZUL, zorder=3)
    for yi, (et, v) in zip(y, etapas):
        ax.text(v + vals.max() * 0.012, yi, n_es(v), va="center", fontsize=9.5, color=TXT2)
    ax.set_yticks(y, [e for e, _ in etapas])
    ax.set_xlim(0, vals.max() * 1.13)
    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v / 1000:,.0f} mil" if v else "0"))
    _ejes_limpios(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    encabezado(fig, f"De {vals[0] / 1000:,.0f} mil registros a {vals[-1] / 1000:,.0f} mil observaciones salariales",
               "Cada regla elimina filas solo cuando está justificada; lo demás se marca con banderas para el análisis de sensibilidad")
    pie(fig)
    fig.subplots_adjust(left=0.33, right=0.97, top=0.86, bottom=0.09)
    return fig


def fig_calidad_ingreso(cal: pd.DataFrame):
    pobs = ["Total", "Hombres", "Mujeres"] + [f"Nivel {k}. {C.NIV_INS[k]}" for k in (1, 2, 3, 4)]
    cols = {"A": AZUL, "B": NARANJA, "C": AQUA, "D": AMARILLO}
    etq = {"A": "A · monto exacto", "B": "B · solo rango de salarios mínimos", "C": "C · no recibe ingresos", "D": "D · no especificó"}
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    y = np.arange(len(pobs))[::-1]
    izq = np.zeros(len(pobs))
    for g in "ABCD":
        v = np.array([cal[(cal["grupo"] == g) & (cal["poblacion"] == p)]["pct"].iloc[0] for p in pobs])
        ax.barh(y, v, left=izq, height=0.56, color=cols[g], edgecolor=SUP, linewidth=1.6, label=etq[g], zorder=3)
        for yi, l, w in zip(y, izq, v):
            if w >= 6.5:
                ax.text(l + w / 2, yi, f"{w:.0f} %", ha="center", va="center", fontsize=9, color=_color_texto(cols[g]))
        izq += v
    ax.set_yticks(y, [p.replace("Nivel ", "") for p in pobs])
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(decimals=0))
    _ejes_limpios(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.45, -0.2), fontsize=8.8, handlelength=1.2, columnspacing=1.2)
    g = lambda x, p: float(cal[(cal["grupo"] == x) & (cal["poblacion"] == p)]["pct"].iloc[0])
    a1, a4 = g("A", "Nivel 1. " + C.NIV_INS[1]), g("A", "Nivel 4. " + C.NIV_INS[4])
    encabezado(fig, "El «ingreso cero» no es un solo fenómeno",
               f"Solo {g('A', 'Total'):.0f} % declara monto exacto; {g('B', 'Total'):.0f} % da solo un rango y {g('D', 'Total'):.0f} % no especifica. "
               f"Quien más estudió declara menos el monto exacto ({a4:.0f} % vs. {a1:.0f} %)")
    pie(fig)
    fig.subplots_adjust(left=0.27, right=0.97, top=0.84, bottom=0.2)
    return fig


def fig_distribucion_ingreso(W: pd.DataFrame, diag: dict | None = None):
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.4))
    w = W["fac_tri"].to_numpy()
    x = W["ing_hora"].to_numpy()
    lim = np.quantile(x, 0.99)
    ax = axs[0]
    h, e = np.histogram(x[x <= lim], bins=60, weights=w[x <= lim])
    ax.bar(e[:-1], h / 1e6, width=np.diff(e), align="edge", color=AZUL, edgecolor=SUP, linewidth=0.4, zorder=3)
    ax.set_title("Pesos por hora (hasta el percentil 99)", fontsize=10.5, color=TXT2, loc="left")
    ax.set_xlabel("Ingreso por hora ($)")
    ax.set_ylabel("Millones de personas")
    ax.text(0.97, 0.93, f"asimetría = {pd.Series(x).skew():.1f}", transform=ax.transAxes, ha="right", fontsize=9.5, color=TXT2)
    ax = axs[1]
    z = W["ln_ing_hora"].to_numpy()
    h, e = np.histogram(z, bins=60, weights=w)
    ax.bar(e[:-1], h / 1e6, width=np.diff(e), align="edge", color=AZUL, edgecolor=SUP, linewidth=0.4, zorder=3)
    ax.set_title("Logaritmo natural del ingreso por hora", fontsize=10.5, color=TXT2, loc="left")
    ax.set_xlabel("ln(ingreso por hora)")
    ax.text(0.97, 0.93, f"asimetría = {pd.Series(z).skew():.2f}", transform=ax.transAxes, ha="right", fontsize=9.5, color=TXT2)
    for a in axs:
        a.grid(axis="x", visible=False)
    encabezado(fig, "El logaritmo vuelve simétrica una distribución muy sesgada",
               "Por eso el análisis se hace sobre ln(ingreso por hora): diferencias de ln ≈ diferencias porcentuales")
    pie(fig, "Muestra salarial (n = %s). Histogramas ponderados con fac_tri." % n_es(len(W)))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.8, bottom=0.17, wspace=0.18)
    return fig


# --------------------------------------------------------------------------- #
# 2. Escolaridad e ingreso
# --------------------------------------------------------------------------- #
def fig_ingreso_por_escolaridad(W: pd.DataFrame, minimo: int = 60):
    filas = []
    for (a, s), g in W.groupby(["anios_esc", "mujer"]):
        if len(g) >= minimo:
            filas.append((a, s, cuantil_ponderado(g["ing_hora"].to_numpy(), g["fac_tri"].to_numpy(), 0.5), len(g)))
    t = pd.DataFrame(filas, columns=["anios", "mujer", "mediana", "n"])
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    for s, color, nombre in [(0, AZUL, "Hombres"), (1, NARANJA, "Mujeres")]:
        d = t[t["mujer"] == s].sort_values("anios")
        ax.plot(d["anios"], d["mediana"], color=color, lw=2, solid_capstyle="round", zorder=3, label=nombre)
        _punto(ax, d["anios"], d["mediana"], color, s=34)
    ax.set_yscale("log")
    ax.set_yticks([20, 30, 40, 60, 80, 120, 180])
    ax.get_yaxis().set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.yaxis.set_minor_formatter(mpl.ticker.NullFormatter())
    ax.set_xticks([0, 3, 6, 9, 12, 16, 18, 21])
    ax.set_xlabel("Años de escolaridad")
    ax.set_ylabel("Mediana del ingreso por hora (escala logarítmica)")
    ax.legend(loc="upper left")
    _ejes_limpios(ax, xgrid=False, ygrid=True)
    for anios, txt in [(6, "primaria"), (9, "secundaria"), (12, "media sup."), (16, "licenciatura")]:
        ax.text(anios, ax.get_ylim()[0] * 1.04, txt, fontsize=8.5, color=MUTED, ha="center", va="bottom")
    encabezado(fig, "El ingreso por hora sube con la escolaridad, sobre todo al llegar a la licenciatura",
               "Mediana ponderada del ingreso por hora según años de escolaridad (celdas con al menos %d observaciones)" % minimo)
    pie(fig)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.85, bottom=0.17)
    return fig


def fig_retorno_estados(ret: pd.DataFrame, ret_nac: float):
    d = ret.sort_values("ret_est").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.0, 7.6))
    y = np.arange(len(d))
    for i, r in d.iterrows():
        c = ORDINAL_4[int(r["cuartil_ingreso"]) - 1]
        ax.plot([r["ret_ic_inf"], r["ret_ic_sup"]], [i, i], color=c, lw=1.6, solid_capstyle="round", zorder=2)
        _punto(ax, r["ret_est"], i, c, s=52)
    ax.axvline(ret_nac, color=MUTED, lw=1, zorder=1)
    ax.text(ret_nac, len(d) - 0.2, f"nacional {ret_nac:.1f} %", fontsize=8.8, color=TXT2, ha="center", va="bottom")
    ax.set_yticks(y, d["entidad"])
    ax.set_xlabel("Aumento del ingreso por hora por cada año adicional de escolaridad (%)")
    ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.0f %%"))
    ax.set_ylim(-0.8, len(d) + 0.4)
    _ejes_limpios(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    handles = [Line2D([0], [0], marker="o", color="none", markerfacecolor=ORDINAL_4[k], markeredgecolor=SUP, markersize=8) for k in range(4)]
    ax.legend(handles, ["Q1 (ingreso más bajo)", "Q2", "Q3", "Q4 (ingreso más alto)"], title="Cuartil de ingreso mediano por hora del estado",
              loc="lower right", fontsize=8.8, title_fontsize=8.8)
    lo, hi = d.iloc[0], d.iloc[-1]
    encabezado(fig, f"Un año más de estudio rinde de {lo['ret_est']:.1f} % ({lo['entidad']}) a {hi['ret_est']:.1f} % ({hi['entidad']})",
               "Rendimiento por año de escolaridad con IC 95 %, controlando edad y sexo; el color indica el ingreso mediano del estado")
    pie(fig)
    fig.subplots_adjust(left=0.19, right=0.97, top=0.9, bottom=0.095)
    return fig


def fig_spearman_estados(ret: pd.DataFrame, rho_nac: float):
    d = ret.sort_values("rho_est").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.0, 7.6))
    for i, r in d.iterrows():
        ax.plot([r["rho_ic_inf"], r["rho_ic_sup"]], [i, i], color=AZUL, lw=1.6, solid_capstyle="round", zorder=2)
        _punto(ax, r["rho_est"], i, AZUL, s=52)
        ax.text(1.015, i, f"{int(r['rho_rango']):>2d}  [{int(r['rho_rango_inf'])}–{int(r['rho_rango_sup'])}]", transform=ax.get_yaxis_transform(),
                fontsize=8.6, color=TXT2, va="center")
    ax.text(1.015, len(d) - 0.1, "Lugar [IC 95 %]", transform=ax.get_yaxis_transform(), fontsize=8.8, color=TXT2, fontweight="bold", va="bottom")
    ax.axvline(rho_nac, color=MUTED, lw=1, zorder=1)
    ax.text(rho_nac, -1.6, f"nacional {rho_nac:.2f}", fontsize=8.8, color=TXT2, ha="center", va="bottom")
    ax.set_yticks(np.arange(len(d)), d["entidad"])
    ax.set_xlabel("Correlación de Spearman entre años de escolaridad e ingreso por hora")
    ax.set_ylim(-1.8, len(d) + 0.4)
    _ejes_limpios(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    encabezado(fig, "Ranking de estados por la fuerza del vínculo escolaridad-ingreso",
               "Spearman ponderado con IC 95 % y lugar en el ranking con su intervalo (los extremos sí se distinguen; el centro no)")
    pie(fig)
    fig.subplots_adjust(left=0.19, right=0.84, top=0.9, bottom=0.095)
    return fig


def _etiquetas_selectivas(ax, x, y, nombres, idx, fs=8.6):
    """Etiqueta solo los puntos de ``idx`` eligiendo, para cada uno, la posición que no choque con puntos ni otras etiquetas."""
    from matplotlib.transforms import Bbox

    fig = ax.figure
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    pts = ax.transData.transform(np.column_stack([x, y]))
    ocupados = [(k, Bbox.from_extents(p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9)) for k, p in enumerate(pts)]
    ax_bb = ax.get_window_extent()
    candidatas = [(7, 5, "left"), (7, -14, "left"), (-7, 5, "right"), (-7, -14, "right"), (0, 13, "center"), (0, -19, "center")]
    for i in sorted(idx, key=lambda k: y[k]):
        elegida = None
        for dx, dy, ha in candidatas:
            t = ax.annotate(nombres[i], (x[i], y[i]), xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=fs, color=TXT2)
            bb = t.get_window_extent(r)
            fuera = bb.x0 < ax_bb.x0 or bb.x1 > ax_bb.x1 + 2 or bb.y0 < ax_bb.y0 or bb.y1 > ax_bb.y1
            choca = any(bb.overlaps(o) for k, o in ocupados if k != i)
            if not fuera and not choca:
                elegida = (t, bb)
                break
            t.remove()
        if elegida is None:                       # último recurso: la primera posición que quede dentro del eje
            dx, dy, ha = candidatas[2] if pts[i][0] > ax_bb.x0 + 0.7 * ax_bb.width else candidatas[0]
            t = ax.annotate(nombres[i], (x[i], y[i]), xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=fs, color=TXT2)
            elegida = (t, t.get_window_extent(r))
        ocupados.append((-1, elegida[1]))


def fig_dispersion_estatal(ret: pd.DataFrame, rho: float | None = None):
    d = ret.reset_index(drop=True)
    x, y = d["esc_sal_est"].to_numpy(), d["mln_est"].to_numpy()
    fig, ax = plt.subplots(figsize=(9.0, 5.8))
    b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min() - 0.1, x.max() + 0.1, 50)
    ax.plot(xs, np.polyval(b, xs), color=BASE, lw=1.6, zorder=1)
    _punto(ax, x, y, AZUL, s=60)
    resid = y - np.polyval(b, x)
    idx = set(np.argsort(y)[:3]) | set(np.argsort(y)[-4:]) | set(np.argsort(x)[:2]) | set(np.argsort(x)[-2:]) | set(np.argsort(resid)[:2]) | set(np.argsort(resid)[-2:])
    _etiquetas_selectivas(ax, x, y, d["entidad"].to_numpy(), idx)
    ax.set_xlabel("Años de escolaridad promedio de los trabajadores del estado")
    ax.set_ylabel("Mediana del ingreso por hora ($)")
    ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("$%.0f"))
    _ejes_limpios(ax, True, True)
    if rho is not None:
        ax.text(0.03, 0.95, f"Spearman entre estados = {rho:.2f}", transform=ax.transAxes, fontsize=9.8, color=TXT2, va="top")
    encabezado(fig, "Los estados más escolarizados pagan más por hora",
               "Cada punto es una entidad; la línea es el ajuste lineal (relación entre estados, no causal)")
    pie(fig)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.86, bottom=0.12)
    return fig


def fig_cajas_nivel_sexo(W: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    centros = np.arange(4)
    for s, color, desp in [(0, AZUL, -0.19), (1, NARANJA, 0.19)]:
        for k in range(4):
            g = W[(W["niv_ins"] == k + 1) & (W["mujer"] == s)]
            xx, ww = g["ing_hora"].to_numpy(), g["fac_tri"].to_numpy()
            q = cuantil_ponderado(xx, ww, np.array([0.10, 0.25, 0.5, 0.75, 0.90]))
            x0 = centros[k] + desp
            ax.plot([x0, x0], [q[0], q[1]], color=color, lw=1.4, zorder=2)      # bigotes solo fuera de la caja
            ax.plot([x0, x0], [q[3], q[4]], color=color, lw=1.4, zorder=2)
            ax.add_patch(Rectangle((x0 - 0.15, q[1]), 0.30, q[3] - q[1], facecolor=color, edgecolor=SUP, linewidth=1.2, zorder=3))
            ax.plot([x0 - 0.15, x0 + 0.15], [q[2], q[2]], color=SUP, lw=2.2, zorder=4)
    ax.set_yscale("log")
    ax.set_ylim(12, 200)
    ax.set_yticks([15, 20, 30, 40, 60, 80, 120, 160])
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.yaxis.set_minor_formatter(mpl.ticker.NullFormatter())
    ax.set_xticks(centros, [C.NIV_INS[k + 1].replace(" y ", " y\n").replace("completa", "completa") for k in range(4)])
    ax.set_xlim(-0.6, 3.6)
    ax.set_ylabel("Ingreso por hora (escala logarítmica)")
    ax.legend(handles=[Patch(facecolor=AZUL, label="Hombres"), Patch(facecolor=NARANJA, label="Mujeres")], loc="upper left")
    _ejes_limpios(ax, False, True)
    encabezado(fig, "Distribución del ingreso por hora según nivel de instrucción y sexo",
               "Caja: percentiles 25-75; raya blanca: mediana; bigotes: percentiles 10-90 (todo ponderado)")
    pie(fig, "Muestra salarial (n = %s). Percentiles ponderados con fac_tri." % n_es(len(W)))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.85, bottom=0.14)
    return fig


# --------------------------------------------------------------------------- #
# 3. Brecha de género
# --------------------------------------------------------------------------- #
def fig_brecha_nivel(bn: pd.DataFrame):
    d = bn.copy()
    corto = {"Primaria incompleta": "Primaria\nincompleta", "Primaria completa": "Primaria\ncompleta",
             "Secundaria completa": "Secundaria\ncompleta", "Medio superior y superior": "Medio sup.\ny superior"}
    etiquetas = [corto[n.split(". ", 1)[-1]] if n != "Total" else "Total" for n in d["nivel"]]
    fig, axs = plt.subplots(1, 2, figsize=(9.8, 4.8), sharey=True)
    for ax, (col, titulo) in zip(axs, [("hora", "Ingreso por hora"), ("mens", "Ingreso mensual")]):
        v, lo, hi = d[f"brecha_{col}_pct"].to_numpy(), d[f"brecha_{col}_inf"].to_numpy(), d[f"brecha_{col}_sup"].to_numpy()
        x = np.arange(len(d))
        ax.bar(x, v, width=0.5, color=AZUL, zorder=3)
        ax.errorbar(x, v, yerr=[v - lo, hi - v], fmt="none", ecolor=TXT2, elinewidth=1.1, capsize=3, zorder=4)
        for xi, vi, hi_i in zip(x, v, hi):
            ax.text(xi, hi_i + 0.9, f"{vi:.1f} %", ha="center", fontsize=9, color=TXT2)
        ax.axhline(0, color=BASE, lw=1)
        ax.set_title(titulo, fontsize=10.5, color=TXT2, loc="left")
        ax.set_xticks(x, etiquetas, rotation=0, fontsize=8.5)
        ax.grid(axis="x", visible=False)
        ax.axvline(3.5, color=GRID, lw=1)
    axs[0].set_ylabel("% menos que ganan las mujeres que los hombres")
    axs[0].yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.0f %%"))
    tot = d[d["nivel"] == "Total"].iloc[0]
    encabezado(fig, f"Por hora la brecha es de {tot['brecha_hora_pct']:.1f} %; por mes, de {tot['brecha_mens_pct']:.1f} %",
               "Brecha = 1 − (ingreso medio geométrico de mujeres / de hombres), con IC 95 %; misma escala en ambos paneles")
    pie(fig, FUENTE + " Muestra: ocupados 15-65 con monto exacto.")
    fig.subplots_adjust(left=0.085, right=0.985, top=0.83, bottom=0.14, wspace=0.05)
    return fig


def fig_escalera(esc: pd.DataFrame):
    d = esc.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.2, 4.9))
    for i, r in d.iterrows():
        ax.plot([r["brecha_pct_inf"], r["brecha_pct_sup"]], [i, i], color=AZUL, lw=1.7, solid_capstyle="round", zorder=2)
        _punto(ax, r["brecha_pct"], i, AZUL, s=60)
        ax.text(r["brecha_pct_sup"] + 0.6, i, f"{r['brecha_pct']:.1f} %", va="center", fontsize=9, color=TXT2)
    ax.axvline(0, color=BASE, lw=1.2, zorder=1)
    ax.set_yticks(np.arange(len(d)), d["modelo"])
    ax.set_xlabel("% menos que ganan las mujeres por hora (coeficiente de 'mujer', IC 95 %)")
    ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(4))
    ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.0f %%"))
    _ejes_limpios(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    g0, g5 = esc.iloc[0]["brecha_pct"], esc.iloc[5]["brecha_pct"]
    encabezado(fig, f"Al comparar personas parecidas, la brecha por hora pasa de {g0:.1f} % a {g5:.1f} %",
               "Brecha por hora al agregar controles; G6 (horas) es sensible al sesgo de división y no se interpreta")
    pie(fig)
    fig.subplots_adjust(left=0.33, right=0.96, top=0.85, bottom=0.14)
    return fig


def fig_oaxaca(ob: pd.DataFrame):
    d = ob[ob["especificacion"].str.startswith("Principal")].copy()
    orden = ["Brecha total (log-puntos)", "Explicada por características (referencia agrupada)", "  · escolaridad",
             "  · edad / experiencia", "  · entidad y tamaño de localidad", "  · posición e informalidad",
             "  · rama de actividad", "No explicada (referencia agrupada)"]
    d = d.set_index("componente").loc[orden].reset_index()
    nombres = ["Brecha total", "Explicada por características", "   escolaridad", "   edad / experiencia", "   entidad y localidad",
               "   posición e informalidad", "   rama de actividad", "No explicada"]
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    y = np.arange(len(d))[::-1]
    v = 100 * d["log_puntos"].to_numpy()
    lo, hi = 100 * d["ic_inf"].to_numpy(), 100 * d["ic_sup"].to_numpy()
    colores = [AZUL if x < 0 else ROJO for x in v]
    ax.barh(y, v, height=0.5, color=colores, zorder=3)
    ax.errorbar(v, y, xerr=[v - lo, hi - v], fmt="none", ecolor=TXT2, elinewidth=1.1, capsize=3, zorder=4)
    for yi, vi, lo_i, hi_i in zip(y, v, lo, hi):
        if vi >= 0:
            ax.text(hi_i + 0.25, yi, f"{vi:+.1f}", va="center", ha="left", fontsize=9.2, color=TXT2)
        else:
            ax.text(lo_i - 0.25, yi, f"{vi:+.1f}", va="center", ha="right", fontsize=9.2, color=TXT2)
    ax.axvline(0, color=BASE, lw=1.2, zorder=1)
    ax.set_yticks(y, nombres)
    ax.set_xlim(-5.2, 8.8)
    ax.set_xlabel("Puntos logarítmicos ≈ puntos porcentuales de ingreso por hora (hombres − mujeres)")
    _ejes_limpios(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(handles=[Patch(facecolor=ROJO, label="Aumenta la brecha (desventaja de las mujeres)"),
                       Patch(facecolor=AZUL, label="Reduce la brecha (ventaja de las mujeres)")],
              loc="upper center", bbox_to_anchor=(0.45, -0.17), ncol=2, fontsize=8.8)
    encabezado(fig, "Las mujeres tienen características «favorables», pero un residuo desfavorable",
               "Descomposición de Oaxaca-Blinder (referencia agrupada de Neumark) de la brecha por hora, IC 95 %")
    pie(fig)
    fig.subplots_adjust(left=0.27, right=0.96, top=0.85, bottom=0.22)
    return fig


def fig_cuantiles(cu: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    x = cu["percentil"].to_numpy()
    ax.fill_between(x, cu["inf"], cu["sup"], color=AZUL, alpha=0.12, linewidth=0, zorder=1)
    ax.plot(x, cu["brecha_pct"], color=AZUL, lw=2, solid_capstyle="round", zorder=3)
    _punto(ax, x, cu["brecha_pct"], AZUL, s=52)
    ax.axhline(0, color=BASE, lw=1.2)
    for xi, vi in zip(x, cu["brecha_pct"]):
        ax.text(xi, vi + 1.3, f"{vi:.1f} %", ha="center", fontsize=9, color=TXT2)
    ax.set_xticks(x, [f"P{k}" for k in x])
    ax.set_xlabel("Posición en la distribución del ingreso por hora (P10 = quien gana menos)")
    ax.set_ylabel("% menos que ganan las mujeres")
    ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(5))
    ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.0f %%"))
    _ejes_limpios(ax, False, True)
    encabezado(fig, "La brecha se concentra en la parte baja de la distribución del ingreso",
               "Diferencia de percentiles ponderados del ingreso por hora (hombres vs. mujeres), IC 95 %; arriba es nula o favorece a las mujeres")
    pie(fig)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.85, bottom=0.16)
    return fig


def fig_robustez(rob: pd.DataFrame):
    d = rob[rob["grupo"] == "Total"].copy().iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    for i, r in d.iterrows():
        mensual = r["especificacion"].startswith("S6")
        c = AZUL if not mensual else MUTED
        ax.plot([r["inf"], r["sup"]], [i, i], color=c, lw=1.7, solid_capstyle="round", zorder=2)
        _punto(ax, r["brecha_pct"], i, c, s=58)
        ax.text(r["sup"] + 0.5, i, f"{r['brecha_pct']:.1f} %", va="center", fontsize=9, color=TXT2)
    ax.axvline(0, color=BASE, lw=1.2, zorder=1)
    ax.set_yticks(np.arange(len(d)), [e.split(" ", 1)[0] + "  " + e.split(" ", 1)[1] for e in d["especificacion"]])
    ax.set_xlabel("% menos que ganan las mujeres (IC 95 %)")
    ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.0f %%"))
    _ejes_limpios(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    hora = d[~d["especificacion"].str.startswith(("S6", "S8", "S9"))]
    encabezado(fig, f"La brecha por hora es positiva en todas las muestras, pero su tamaño va de {hora['brecha_pct'].min():.1f} % a {hora['brecha_pct'].max():.1f} %",
               "Brecha total bajo distintas decisiones metodológicas (gris: ingreso mensual, otro estimando; S3 sesga hacia cero por construcción)")
    pie(fig)
    fig.subplots_adjust(left=0.31, right=0.96, top=0.86, bottom=0.12)
    return fig


def fig_brecha_subgrupos(sub: pd.DataFrame):
    """Brecha por hora en subgrupos (informalidad, posición, región, localidad, edad) con IC; círculo vacío = no significativa."""
    dims = ["Informalidad", "Posición en la ocupación", "Región", "Tamaño de localidad", "Grupo de edad"]
    d = sub[sub["dimension"].isin(dims)].copy()
    d = d[~((d["dimension"] == "Grupo de edad") & (d["categoria"] == "65+"))]
    filas = []
    for dim in dims:
        filas.append(("H", dim))
        for r in d[d["dimension"] == dim].itertuples():
            filas.append(("C", r))
    fig, ax = plt.subplots(figsize=(9.4, 6.6))
    n = len(filas)
    ticks, etiquetas = [], []
    for k, (tipo, v) in enumerate(filas):
        y = n - k
        if tipo == "H":
            ax.text(-0.015, y, v, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=10, fontweight="bold", color=TXT)
            continue
        sig = v.p_holm_dimension < 0.05
        ax.plot([v.inf, v.sup], [y, y], color=AZUL, lw=1.7, solid_capstyle="round", zorder=2)
        ax.scatter([v.brecha_pct], [y], s=62, facecolor=AZUL if sig else SUP, edgecolor=AZUL, linewidth=1.8, zorder=3)
        ticks.append(y)
        etiquetas.append(v.categoria)
        ax.text(max(v.sup, 0) + 0.7, y, f"{v.brecha_pct:.1f} %", va="center", fontsize=9, color=TXT2)
    ax.set_yticks(ticks, etiquetas)
    ax.axvline(0, color=BASE, lw=1.2, zorder=1)
    ax.set_ylim(0.2, n + 0.8)
    ax.set_xlim(-2.5, 18)
    ax.set_xlabel("% menos que ganan las mujeres por hora (IC 95 %)")
    ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.0f %%"))
    ax.tick_params(axis="y", length=0, labelsize=9.2)
    _ejes_limpios(ax)
    ax.spines["left"].set_visible(False)
    ax.legend([Line2D([0], [0], marker="o", color="none", markerfacecolor=AZUL, markeredgecolor=AZUL, markersize=8),
               Line2D([0], [0], marker="o", color="none", markerfacecolor=SUP, markeredgecolor=AZUL, markeredgewidth=1.8, markersize=8)],
              ["significativa (Holm, p < 0.05)", "no significativa"], loc="lower right", fontsize=9)
    encabezado(fig, "La brecha por hora no es igual en todos los grupos",
               "Mayor entre empleadores, informales y localidades medianas; sin brecha demostrable entre formales y en el Sur")
    pie(fig)
    fig.subplots_adjust(left=0.3, right=0.96, top=0.89, bottom=0.105)
    return fig


# --------------------------------------------------------------------------- #
# 4. Informalidad
# --------------------------------------------------------------------------- #
def fig_mapa_informalidad(til: pd.DataFrame):
    d = til.copy()
    col = {k: v[4] for k, v in C.ENTIDADES.items()}
    fila = {k: v[5] for k, v in C.ENTIDADES.items()}
    vmin, vmax = d["til1_est"].min(), d["til1_est"].max()
    norm = mcolors.Normalize(vmin=vmin - 3, vmax=vmax + 3)
    fig, ax = plt.subplots(figsize=(9.6, 5.5))
    for _, r in d.iterrows():
        cx, cy = col[r["cve_ent"]], fila[r["cve_ent"]]
        c = CMAP_SEQ(norm(r["til1_est"]))
        ax.add_patch(Rectangle((cx + 0.04, -cy + 0.04), 0.92, 0.92, facecolor=c, edgecolor="none", zorder=2))
        tc = _color_texto(mcolors.to_hex(c))
        ax.text(cx + 0.5, -cy + 0.6, r["abreviatura"], ha="center", va="center", fontsize=9.5, fontweight="bold", color=tc, zorder=3)
        ax.text(cx + 0.5, -cy + 0.28, f"{r['til1_est']:.0f}", ha="center", va="center", fontsize=9, color=tc, zorder=3)
    ax.set_xlim(-0.1, 11.1)
    ax.set_ylim(-5.1, 1.1)
    ax.set_aspect("equal")
    ax.axis("off")
    cax = fig.add_axes([0.06, 0.19, 0.27, 0.025])
    cb = mpl.colorbar.ColorbarBase(cax, cmap=CMAP_SEQ, norm=norm, orientation="horizontal")
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=8.5)
    cb.set_label("Tasa de informalidad laboral (TIL1, %)", fontsize=9, color=TXT2)
    mx, mn = d.loc[d["til1_est"].idxmax()], d.loc[d["til1_est"].idxmin()]
    encabezado(fig, f"Informalidad laboral: de {mn['til1_est']:.0f} % en {mn['entidad']} a {mx['til1_est']:.0f} % en {mx['entidad']}",
               "Cartograma de mosaicos: cada estado ocupa la misma área para que ninguno domine por su tamaño")
    pie(fig, "Fuente: INEGI, ENOE 2025-T4; TIL1 = ocupados en empleo informal / ocupados de 15+. Ponderado con fac_tri.")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.85, bottom=0.07)
    return fig


def fig_informalidad_vs_escolaridad(til: pd.DataFrame, rho: float | None = None):
    d = til.reset_index(drop=True)
    x, y = d["esc15_est"].to_numpy(), d["til1_est"].to_numpy()
    fig, ax = plt.subplots(figsize=(9.0, 5.6))
    b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min() - 0.1, x.max() + 0.1, 50)
    ax.plot(xs, np.polyval(b, xs), color=BASE, lw=1.6, zorder=1)
    _punto(ax, x, y, AZUL, s=60)
    resid = y - np.polyval(b, x)
    idx = set(np.argsort(y)[:3]) | set(np.argsort(y)[-4:]) | set(np.argsort(x)[-2:]) | set(np.argsort(resid)[:2]) | set(np.argsort(resid)[-2:])
    _etiquetas_selectivas(ax, x, y, d["entidad"].to_numpy(), idx)
    ax.set_xlabel("Años de escolaridad promedio de los ocupados del estado")
    ax.set_ylabel("Tasa de informalidad laboral (%)")
    ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.0f %%"))
    _ejes_limpios(ax, True, True)
    txt = f"pendiente = {b[0]:.1f} puntos por año"
    if rho is not None:
        txt = f"Spearman entre estados = {rho:.2f}\n" + txt
    ax.text(0.97, 0.95, txt, transform=ax.transAxes, ha="right", va="top", fontsize=9.8, color=TXT2)
    encabezado(fig, "Donde se estudia más hay menos informalidad",
               "Cada punto es una entidad (32). Relación entre estados: no implica causalidad individual")
    pie(fig)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.86, bottom=0.12)
    return fig


def fig_diagnosticos(residuos: np.ndarray, ajustados: np.ndarray):
    from scipy import stats as st

    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.4))
    ax = axs[0]
    rng = np.random.default_rng(C.SEMILLA)
    sel = rng.choice(len(residuos), 20000, replace=False)
    ax.hexbin(ajustados[sel], residuos[sel], gridsize=45, cmap=CMAP_SEQ, mincnt=1, linewidths=0)
    ax.axhline(0, color=TXT2, lw=1)
    ax.set_xlabel("Valores ajustados")
    ax.set_ylabel("Residuos")
    ax.set_title("Residuos vs. ajustados", fontsize=10.5, color=TXT2, loc="left")
    ax = axs[1]
    z = (residuos - residuos.mean()) / residuos.std()
    q = np.sort(z[sel])
    teo = st.norm.ppf((np.arange(1, len(q) + 1) - 0.5) / len(q))
    ax.plot(teo, q, ".", color=AZUL, ms=2.5, zorder=3)
    lim = [-4.5, 4.5]
    ax.plot(lim, lim, color=TXT2, lw=1)
    ax.set_xlabel("Cuantiles normales teóricos")
    ax.set_ylabel("Cuantiles de los residuos estandarizados")
    ax.set_title("Gráfico Q-Q de normalidad", fontsize=10.5, color=TXT2, loc="left")
    encabezado(fig, "Diagnóstico del modelo G6: varianza no constante y colas algo pesadas",
               "Por eso la inferencia usa errores estándar robustos de diseño, no supuestos de normalidad ni de homocedasticidad")
    pie(fig, "Muestra aleatoria de 20 mil residuos del modelo OLS con todos los controles.")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.8, bottom=0.17, wspace=0.2)
    return fig
