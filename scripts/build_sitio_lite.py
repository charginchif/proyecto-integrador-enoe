"""Página interactiva y ligera del proyecto (sitio/index.html): pocas láminas, una gráfica interactiva por mensaje y casi sin texto.

    python scripts/build_sitio_lite.py                    # sitio/index.html
    python scripts/build_sitio_lite.py --fragmento RUTA   # además, la versión sin envoltura de documento (para publicarla como artefacto)

Sigue el punto 1 de la guía de la maestra (INEGI: radiografía socioeconómica de México): las tres preguntas de investigación, las tres métricas de éxito,
las siete competencias que menciona la guía (las seis de su lista, estadística, limpieza, transformación, visualización, ingeniería y NoSQL, más la selección de
datos de la semana 1), la reflexión final y solo los productos importantes. Todas las cifras salen de results/ y de la base SQLite (scripts/web_datos.py); la guía de estudio completa sigue
disponible en sitio/estudio.html (scripts/build_sitio.py).
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from web_datos import datos_web  # noqa: E402

ASSETS = Path(__file__).resolve().parent / "web_assets"
TITULO = "Radiografía socioeconómica de México"
REPO = "https://github.com/charginchif/proyecto-integrador-enoe"
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap">')
FUENTE_PIE = "INEGI, ENOE 2025-T4 · IC 95 % por bootstrap de Rao-Wu"


def e(t) -> str:
    return html.escape(str(t), quote=True)


def n_es(x, d: int = 0) -> str:
    return f"{x:,.{d}f}"


def pc(x, d: int = 1) -> str:
    return f"{x:.{d}f} %"


def escena(id_: str, titulo: str, cuerpo: str, quien: str, guion: str, clase: str = "") -> str:
    return (f'<section class="escena {clase}" id="{id_}" data-titulo="{e(titulo)}" data-quien="{e(quien)}" data-guion="{e(guion)}"><div class="cont">{cuerpo}</div></section>')


def etiqueta(texto: str, negrita: str = "") -> str:
    return f'<p class="etq">{"<b>" + e(negrita) + "</b> · " if negrita else ""}{e(texto)}</p>'


def tarjeta(titulo: str, subtitulo: str, vistas: list[tuple], pie_pista: str = "", ver_tabla: bool = True) -> str:
    """vistas: [(clave, etiqueta del botón, html de la vista, nota al pie de esa vista)]. Con una sola vista no hay botones; la nota al pie cambia con la vista."""
    seg = ""
    if len(vistas) > 1:
        seg = '<div class="seg" role="group" aria-label="Vista de la gráfica">' + "".join(
            f'<button type="button" data-vista="{v[0]}" aria-pressed="{"true" if i == 0 else "false"}">{e(v[1])}</button>' for i, v in enumerate(vistas)) + "</div>"
    def justificacion(v: tuple) -> str:
        return (f'<details class="porque"><summary>¿Por qué este gráfico?</summary><p>{e(v[4])}</p></details>' if len(v) > 4 and v[4] else "")
    cuerpos = "".join(f'<div class="vista" data-vista="{v[0]}"{" hidden" if i else ""} data-pista="{e(v[3] if len(v) > 3 else pie_pista)}">{v[2]}{justificacion(v)}</div>' for i, v in enumerate(vistas))
    pista_inicial = vistas[0][3] if len(vistas[0]) > 3 else pie_pista
    tabla = ('<button type="button" class="ver-tabla" aria-pressed="false">Ver tabla</button>' if ver_tabla else "")
    return (f'<figure class="tarjeta"><header class="tarjeta__cab"><div class="tarjeta__tit"><b>{e(titulo)}</b><span>{e(subtitulo)}</span></div>{seg}</header>'
            f'{cuerpos}<div class="tabla-vista" hidden></div>'
            f'<footer class="tarjeta__pie"><span class="pista">{e(pista_inicial)}</span><span>{tabla}</span></footer></figure>')


def viz(nombre: str) -> str:
    return f'<div class="viz" data-chart="{nombre}"></div>'


def cifra(valor: str, texto: str, nota: str = "") -> str:
    return f'<div class="cifra"><b>{e(valor)}</b><span>{e(texto)}</span>{"<small>" + e(nota) + "</small>" if nota else ""}</div>'


def chips(items: list[tuple[str, str]]) -> str:
    """items: [(texto, tipo)] con tipo '' | 'ok' | 'aviso'. Los fragmentos entre ** van en negrita."""
    def cuerpo(t: str) -> str:
        partes = e(t).split("**")
        return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(partes))
    return '<ul class="chips">' + "".join(f'<li class="chip{" chip--" + k if k else ""}">{cuerpo(t)}</li>' for t, k in items) + "</ul>"


def construir(d: dict) -> str:
    k, n = d["k"], d["n"]
    ret, g1, bh, bm = k["ret"], k["g1"], k["bh"], k["bm"]
    est = {x["n"]: x for x in d["estados"]}
    top3 = sorted(d["estados"], key=lambda x: -x["til"][0])[:3]
    umbral_til = int(min(x["til"][0] for x in top3))              # entero hacia abajo: Chiapas tiene 74.9 %, así que «superan 74 %»
    rq = {x["q"]: x for x in d["retorno_q"]}
    ret_max = max(d["estados"], key=lambda x: x["ret"][0])
    ret_min = min(d["estados"], key=lambda x: x["ret"][0])
    til_n = d["til_nivel"]
    reg = {x["n"]: x["v"] for x in d["til_region"]}
    calidad_total = d["calidad"][0]
    sec: list[str] = []

    # ------------------------------------------------------------------ 0 · portada
    sec.append(escena("e-portada", "Portada", f"""
<div class="portada-grid">
 <div>
  <p class="etq">Proyecto Integrador · Ciencia de Datos · Equipo 1</p>
  <h1>{e(TITULO)}</h1>
  <p class="sub">¿Cuánto rinde estudiar, cambia entre estados y qué brechas hay?</p>
  <p class="equipo">Juan Evelio Culin Grajeda · Angel Yireh Garcia Jara · Luis Andre Gutierrez Zuñia<br>UNE Plantel Centro · Datos: ENOE 2025-T4, INEGI</p>
 </div>
 <div><p class="mosaico-tit">Informalidad laboral por entidad (%)</p>{viz("mosaicoPortada")}</div>
</div>
<div class="kpis">
 <a class="kpi" href="#e-q1" data-ir="e-q1"><b>+{ret[0]:.1f} %</b><span>ingreso por hora por cada año de estudio</span><em>Pregunta 1 ▸</em></a>
 <a class="kpi" href="#e-q2" data-ir="e-q2"><b>{g1[0]:.1f} %</b><span>menos por hora ganan las mujeres con la misma escolaridad ({bm[0]:.1f} % por mes)</span><em>Pregunta 2 ▸</em></a>
 <a class="kpi" href="#e-q3" data-ir="e-q3"><b>{k["til"][0]:.0f} %</b><span>de las personas ocupadas está en empleo informal</span><em>Pregunta 3 ▸</em></a>
</div>""", "Juan Evelio",
        f"Presentamos la radiografía socioeconómica de México con la ENOE del cuarto trimestre de 2025: {n_es(n['universo'])} personas ocupadas. Tres preguntas: cuánto rinde estudiar y si cambia entre estados, "
        "si hay brecha de género con la misma escolaridad y dónde hay más informalidad. Cada tarjeta lleva a su respuesta.", "portada"))

    # ------------------------------------------------------------------ 1 · ruta KDD
    fases = [("01 · Sem. 1", "Selección", "Fuente y validación"), ("02 · Sem. 4", "Preprocesamiento", "Limpieza documentada"), ("03 · Sem. 4 · 6", "Transformación", "Variables y base de datos"),
             ("04 · Sem. 2 · 3 · 5", "Minería y análisis", "Estadística y gráficas"), ("05 · Sem. 5", "Interpretación", "Comunicar y recomendar")]
    comp = [("Sem. 1", "Selección", "7 de 7 cifras oficiales", "e-datos"), ("Sem. 2 · 3", "Estadística", "Rao-Wu, Spearman, Holm", "e-q1"), ("Sem. 4", "Limpieza", f"{n['pruebas_datos']} pruebas de calidad", "e-limpieza"), ("Sem. 4", "Transformación", f"{n['variables_derivadas']} variables derivadas", "e-ingenieria"),
            ("Sem. 5", "Visualización", "Más de 10 gráficas", "e-estados"), ("Sem. 6", "Ingeniería", "ETL a SQLite", "e-ingenieria"), ("Sem. 7", "NoSQL", "MongoDB por entidad", "e-ingenieria")]
    sec.append(escena("e-ruta", "Ruta del proyecto", etiqueta("ciclo KDD", "Marco metodológico") + '<h2 class="titular titular--ancho">Del dato crudo al hallazgo: cinco pasos y las siete competencias del curso</h2>'
        '<div class="kdd" role="group" aria-label="Fases del ciclo KDD">' + "".join(f'<button type="button" class="fase" aria-pressed="false"><small>{a}</small><b>{b}</b><span>{c}</span></button>' for a, b, c in fases) + "</div>"
        '<div class="fase-detalle" id="fase-detalle" aria-live="polite"></div>' + etiqueta("El proyecto evidencia las competencias que pide la guía") +
        '<div class="comp">' + "".join(f'<a href="#{i}" data-ir="{i}"><small>{s}</small><b>{t}</b><span>{x}</span></a>' for s, t, x, i in comp) + "</div>", "Juan Evelio",
        "El proyecto sigue el ciclo KDD y cubre las siete competencias del curso. Toquen cada fase para ver su evidencia: datos validados, limpieza con pruebas de calidad, base SQLite y MongoDB, análisis con Rao-Wu y las respuestas."))

    # ------------------------------------------------------------------ 2 · datos
    sec.append(escena("e-datos", "Datos reales y validados", etiqueta("dataset real, grande y verificable", "Selección · Sem. 1") +
        f'<h2 class="titular">{n_es(n["registros"] / 1000)} mil registros reales; reproducimos 7 de 7 cifras oficiales del INEGI</h2>'
        '<div class="cuerpo">' + tarjeta("De los registros crudos a la muestra de análisis", "cada regla elimina filas solo cuando está justificada",
            [("embudo", "Embudo de datos", viz("embudo"), "Barras desde cero · en azul intenso, las tres cifras clave · " + FUENTE_PIE, 'Barras horizontales porque comparan cantidades del mismo tipo (registros) y los nombres largos caben mejor. El eje parte de cero, así que la longitud de cada barra es proporcional a la cantidad.'),
             ("inegi", "Cifras del INEGI", viz("validacion"), "Mismos microdatos públicos, calculados con el factor de expansión")], FUENTE_PIE, True) +
        '<div class="lectura">' + cifra("7 de 7", "cifras oficiales del INEGI reproducidas con los microdatos", "PEA, participación, informalidad y tres estados") +
        chips([(f"**{n_es(n['registros'])}** → **{n_es(n['salarial'])}** observaciones salariales", ""), ("Huella SHA-256 de cada archivo", "ok"), ("Diccionario de datos documentado", "ok")]) + "</div></div>", "Juan Evelio",
        f"Partimos de {n_es(n['registros'])} registros reales. Cada paso del embudo elimina filas solo cuando está justificado. Como control externo reprodujimos las siete cifras que publicó el INEGI."))

    # ------------------------------------------------------------------ 3 · limpieza
    leyenda_cal = ('<div class="leyenda" role="group" aria-label="Categorías de declaración del ingreso">' + "".join(
        f'<button type="button" data-k="{c}"><i class="sw-s{i}"></i>{t}</button>' for i, (c, t) in enumerate([("A", "A · Monto exacto"), ("B", "B · Solo un rango de salarios mínimos"), ("C", "C · No recibe ingresos"), ("D", "D · No especificó")], 1)) + "</div>")
    sec.append(escena("e-limpieza", "Limpieza", etiqueta("limpieza documentada", "Preprocesamiento · Sem. 4") +
        f'<h2 class="titular">«Ingreso 0» no significa «no gana»: solo {calidad_total["C"]:.0f} % no recibe ingresos</h2>'
        '<div class="cuerpo">' + tarjeta("Cómo declaran su ingreso las personas ocupadas", "porcentaje por grupo; pasa el cursor sobre una categoría de la leyenda",
            [("cal", "", viz("calidad") + leyenda_cal, "Quien más estudió declara menos el monto exacto", 'Los cuatro grupos suman 100 %, así que se muestran como partes de un todo en barras apiladas. Cada barra es una población y todas llevan el porcentaje escrito; los colores se distinguen también en escala de grises.')], "", True) +
        '<div class="lectura">' + cifra(f"{calidad_total['C']:.0f} %", "de las personas ocupadas no recibe ingresos; el resto del «cero» es información incompleta", f"{calidad_total['B']:.0f} % da un rango · {calidad_total['D']:.0f} % no especifica") +
        chips([("99 años de escolaridad pasan a faltante", ""), ("0 horas pasan a faltante", ""), ("Atípicos: P0.5 a P99.5 por entidad", ""), (f"**{n['pruebas_datos']} de {n['pruebas_datos']}** pruebas de calidad", "ok")]) + "</div></div>", "Angel Yireh",
        f"El ingreso cero engaña: solo {calidad_total['C']:.0f} % no recibe ingresos; {calidad_total['B']:.0f} % da un rango de salarios mínimos y {calidad_total['D']:.0f} % no especifica. Quien más estudia declara menos el monto exacto, "
        "por eso contrastamos los resultados con imputación y con ponderación por no respuesta."))

    # ------------------------------------------------------------------ 4 · ingeniería y NoSQL
    nodos = [("Microdatos INEGI", "CSV · SDEMT y COE2T"), ("Pipeline ETL", "Python · reproducible"), ("SQLite", "esquema en estrella"), ("MongoDB", "un documento por entidad"), ("Tablero y página", "HTML interactivo")]
    arq = '<div class="arq" role="group" aria-label="Arquitectura de datos">' + '<span class="flecha" aria-hidden="true">→</span>'.join(f'<button type="button" class="nodo" aria-pressed="false"><b>{a}</b><span>{b}</span></button>' for a, b in nodos) + "</div>"
    ficha = ('<div class="ficha"><div><div class="caja-tit"><span>SQL · SQLite</span><span>para analizar</span></div><pre class="codigo" id="ficha-sql"></pre><div class="res-sql" id="ficha-res"></div></div>'
             '<div><div class="caja-tit"><span>MongoDB</span><span>para servir</span></div><pre class="codigo" id="ficha-mongo"></pre></div></div>')
    sec.append(escena("e-ingenieria", "Ingeniería y NoSQL", etiqueta("transformación e ingeniería de datos", "Sem. 4 · 6 · 7") +
        '<h2 class="titular">SQLite para analizar, MongoDB para servir: dos bases, dos usos</h2>' + arq + '<p class="mini" id="nodo-detalle" aria-live="polite"></p>' +
        '<figure class="tarjeta"><header class="tarjeta__cab"><div class="tarjeta__tit"><b>La misma pregunta en las dos bases</b><span>elige una entidad: una consulta con JOIN frente a una lectura por clave</span></div>'
        '<select class="sel" id="sel-ficha" aria-label="Entidad de la consulta"></select></header>' + ficha +
        '<footer class="tarjeta__pie"><span class="pista">Extracto del documento (valores redondeados)</span><span>Carga probada con mongomock (simulador); falta un servidor real</span></footer></figure>' +
        chips([(f"**{n_es(n['filas_fact'])}** filas × **{n['cols_fact']}** columnas", ""), ("10 dimensiones · 5 índices · 4 vistas", ""), ("32 documentos: uno por entidad", ""), ("Esquema de estrella con llaves y restricciones", "ok")]), "Angel Yireh",
        "Dos bases para dos usos. SQLite, en esquema de estrella, sirve para analizar con JOIN y agregaciones ponderadas. MongoDB sirve la ficha de cada entidad con una sola lectura. Elijan un estado y vean la misma pregunta en SQL y en MongoDB. "
        "La carga la probamos con un simulador; falta probarla en un servidor real."))

    # ------------------------------------------------------------------ 5 · pregunta 1: rinde estudiar
    leyenda_curva = '<div class="leyenda"><span><i class="l sw-s1"></i>Hombres</span><span><i class="l sw-s2"></i>Mujeres</span></div>'
    calc = ('<div class="calc"><label for="calc-rango">Si estudiara más años…</label><input type="range" id="calc-rango" min="1" max="8" value="4"><output id="calc-res" for="calc-rango"></output>'
            '<small id="calc-ic"></small></div>')
    sec.append(escena("e-q1", "Pregunta 1: ¿cuánto rinde estudiar?", etiqueta("escolaridad e ingreso", "Pregunta 1 · Estadística y visualización") +
        f'<h2 class="titular">Cada año de estudio sube el ingreso por hora {ret[0]:.1f} %; la licenciatura casi lo duplica</h2>'
        '<div class="cuerpo">' + tarjeta("¿Cuánto más gana quien estudia más?", "ingreso por hora, personas ocupadas de 15 a 65 años",
            [("anios", "Por años de estudio", viz("curva") + leyenda_curva, "Mediana ponderada · escala logarítmica · pasa el cursor sobre la curva", 'La escolaridad es una variable ordenada, así que se usa una línea. El eje del ingreso es logarítmico (y está rotulado así) porque el ingreso cambia en proporciones; solo se grafican celdas con al menos 60 observaciones y los colores son aptos para daltonismo.'),
             ("nivel", "Por nivel de estudios", viz("premio"), "Frente a no terminar la primaria · barras desde 0 · línea = IC 95 %", 'Las barras parten de cero porque el premio es una magnitud, y los niveles de estudio son una escala ordenada (de claro a oscuro). Cada barra lleva su intervalo de confianza.')], "", True) +
        '<div class="lectura">' + cifra(f"+{ret[0]:.1f} %", f"por cada año de escolaridad (IC 95 %: {ret[1]:.1f} a {ret[2]:.1f})", "modelo de Mincer con edad, sexo, entidad y localidad") + calc +
        chips([(f"Correlación de Spearman **{k['rho_nac'][0]:.2f}** (moderada)", ""), (f"Mujeres **{k['ret_m']:.1f} %** · Hombres **{k['ret_h']:.1f} %** por año", "")]) + "</div></div>", "Luis Andre",
        f"Cada año de estudio se asocia con {ret[0]:.1f} % más ingreso por hora y la licenciatura casi duplica el ingreso frente a no terminar la primaria. Es una asociación, no un efecto causal. "
        "Con el control deslizante se ve el efecto acumulado de varios años."))

    # ------------------------------------------------------------------ 6 · pregunta 1: estados ricos y pobres
    leyenda_q = ('<div class="leyenda"><span>Cuartil de ingreso del estado (rendimiento medio):</span>' + "".join(
        f'<span><i class="sw-q{q}"></i>Q{q}{" · más bajo" if q == 1 else " · más alto" if q == 4 else ""}: {rq[q]["v"]:.1f} %</span>' for q in (1, 2, 3, 4)) + "</div>")
    sec.append(escena("e-estados", "Pregunta 1: estados ricos y pobres", etiqueta("¿varía entre estados ricos y pobres?", "Pregunta 1 · Estadística") +
        '<h2 class="titular">Estudiar rinde parecido en estados ricos y pobres</h2>'
        '<div class="cuerpo">' + tarjeta("Aumento del ingreso por año de estudio en cada estado", "cada punto es una entidad; toca uno para resaltarlo en todas las gráficas",
            [("disp", "Frente al ingreso del estado", viz("dispEstados") + leyenda_q, "Línea vertical = IC 95 % · color = cuartil de ingreso del estado", 'Una dispersión muestra a la vez el ingreso del estado y el aumento por año de estudio; cada punto lleva su intervalo para que la incertidumbre sea parte del mensaje. Solo se rotulan los extremos. Es una relación entre estados, no un efecto individual.'),
             ("rank", "Ranking de correlación", viz("rankRho"), "Línea horizontal = IC 95 % · a la derecha, el lugar con su intervalo", 'Un punto con intervalo por entidad, ordenadas de mayor a menor. A la derecha se escribe el lugar de cada entidad con su propio intervalo, para que se vea que solo los extremos se distinguen.')], "", True) +
        '<div class="lectura">' + cifra("≈ 0", f"diferencia entre el cuarto de estados más rico y el más pobre (p = {k['dq'][3]:.2f})", "Q4 − Q1 en log-puntos del rendimiento") +
        chips([(f"De **{ret_min['ret'][0]:.1f} %** ({ret_min['n']}) a **{ret_max['ret'][0]:.1f} %** ({ret_max['n']})", ""), (f"Correlación ρ de **{k['rho_min'][1]:.2f}** ({k['rho_min'][0]}) a **{k['rho_max'][1]:.2f}** ({k['rho_max'][0]})", ""),
               ("Ranking defendible: solo los extremos se distinguen", "aviso")]) + "</div></div>", "Luis Andre",
        "La relación entre escolaridad e ingreso es parecida en estados ricos y pobres: la diferencia entre el cuarto más rico y el más pobre es prácticamente cero. "
        "El ranking de correlación solo distingue los extremos; los lugares centrales tienen intervalos muy amplios."))

    # ------------------------------------------------------------------ 7 · pregunta 2: brecha de género
    leyenda_oax = ('<div class="leyenda"><span><i class="sw-rojo"></i>Aumenta la brecha (desventaja de las mujeres)</span><span><i class="sw-s1"></i>Reduce la brecha (ventaja de las mujeres)</span></div>')
    sec.append(escena("e-q2", "Pregunta 2: brecha de género", etiqueta("brecha de género", "Pregunta 2 · Estadística") +
        f'<h2 class="titular">A igual escolaridad, las mujeres ganan {g1[0]:.1f} % menos por hora</h2>'
        '<div class="cuerpo">' + tarjeta("Brecha salarial: % menos que ganan las mujeres", "ingreso por hora, comparado con el de los hombres",
            [("esc", "Con controles", viz("escalera"), "Línea horizontal = IC 95 % · en gris, un modelo que no se interpreta (sesgo de división)", 'Muestra cómo cambia la estimación al agregar controles uno por uno: un punto con intervalo por modelo, todos en la misma escala. El último modelo (con horas) va en gris porque no se interpreta.'),
             ("niv", "Por nivel de estudios", viz("brechaNivel"), "Barras desde 0 · línea = IC 95 % · medias geométricas", 'Las barras parten de cero porque la brecha es una magnitud. Llevan su intervalo de confianza y los dos paneles (por hora y por mes) usan escalas rotuladas, así que no hay ejes duales ni trucos de escala.'),
             ("cuan", "Dónde se concentra", viz("cuantiles"), "Banda = IC 95 % · P10 = quien menos gana", 'Los percentiles son una secuencia ordenada, así que se usa una línea con una banda para el intervalo de confianza y una referencia en cero. Se ve de inmediato dónde la banda cruza el cero y la brecha deja de ser demostrable.'),
             ("oax", "Qué la explica", viz("oaxaca") + leyenda_oax, "Puntos logarítmicos ≈ % del ingreso por hora · línea = IC 95 %", 'Barras divergentes que parten de cero: las rojas aumentan la brecha y las azules la reducen. Cada una trae su intervalo de confianza y la leyenda dice qué significa cada color.')], "", True) +
        '<div class="lectura">' + cifra(f"{g1[0]:.1f} %", f"menos por hora con la misma escolaridad (IC 95 %: {g1[1]:.1f} a {g1[2]:.1f}; p < 0.001)", "prueba de hipótesis con α = 0.05") +
        chips([(f"Por mes: **{bm[0]:.1f} %**", ""), (f"Las mujeres trabajan **{k['menos_horas']:.0f} %** menos horas pagadas", ""), (f"Sin controles: **{bh[0]:.1f} %** · con todos: **{k['g5'][0]:.1f} %**", ""),
               ("La parte no explicada no prueba discriminación", "aviso")]) + "</div></div>", "Angel Yireh",
        f"Con la misma escolaridad las mujeres ganan {g1[0]:.1f} % menos por hora. Por mes la brecha es de {bm[0]:.1f} % porque trabajan {k['menos_horas']:.0f} % menos horas pagadas. "
        "La brecha se concentra en los percentiles bajos. La parte no explicada de la descomposición no prueba discriminación: incluye todo lo que no se mide."))

    # ------------------------------------------------------------------ 8 · pregunta 3: informalidad
    metricas = [("til", "Informalidad (TIL1)"), ("esc", "Años de escolaridad promedio"), ("ret", "Aumento por año de estudio"), ("mln", "Ingreso mediano por hora"), ("bh", "Brecha por hora")]
    controles_mapa = ('<div class="herr-mapa"><label for="sel-metrica">Indicador:</label> <select class="sel" id="sel-metrica">' + "".join(f'<option value="{v}">{t}</option>' for v, t in metricas) + "</select></div>")
    vista_mapa = controles_mapa + '<div class="par">' + viz("mosaicoQ3") + '<div><p class="mosaico-tit sub-tit">Informalidad por nivel de estudios (todo el país)</p>' + viz("tilNivel") + "</div></div>"
    sec.append(escena("e-q3", "Pregunta 3: informalidad", etiqueta("informalidad y escolaridad", "Pregunta 3 · Visualización") +
        f'<h2 class="titular titular--ancho">{top3[0]["n"]}, {top3[1]["n"]} y {top3[2]["n"]} superan {umbral_til} % de informalidad; a más estudio, menos informalidad</h2>'
        '<div class="cuerpo">' + tarjeta("Informalidad laboral por entidad", "cada estado ocupa la misma área; toca uno para ver su ficha",
            [("mapa", "Mapa y niveles", vista_mapa, "Mosaico: cada estado ocupa la misma área · barras desde 0, línea = IC 95 %", 'Un cartograma de mosaicos: cada estado ocupa la misma área, para que los estados grandes no dominen la vista. La escala es de un solo tono con el número escrito en cada mosaico. Las barras por nivel parten de cero y llevan su intervalo.'),
             ("disp", "Frente a la escolaridad", viz("dispTil"), "Cada punto es una entidad · línea vertical = IC 95 % · línea gris = tendencia", 'Dispersión con línea de tendencia: cada punto es una entidad. Sirve para ver la relación entre estados y se acompaña de la advertencia de que no es un efecto individual.')], "", True) +
        '<div class="lectura">' + cifra(f"{til_n[0]['v']:.0f} → {til_n[3]['v']:.0f} %", "informalidad con primaria incompleta frente a media superior o más") +
        chips([(f"Norte **{reg['Norte']:.0f} %** · Sur **{reg['Sur']:.0f} %**", ""), (f"Entre estados, ρ = **{str(k['rho_til']).replace('-', '−')}**", ""), ("Es una relación entre estados, no un efecto individual", "aviso")]) + "</div></div>", "Luis Andre",
        f"{top3[0]['n']}, {top3[1]['n']} y {top3[2]['n']} superan el {umbral_til} % de informalidad; Coahuila tiene {min(x['til'][0] for x in d['estados']):.0f} %. A mayor escolaridad, menos informalidad: de {til_n[0]['v']:.0f} % sin primaria completa "
        f"a {til_n[3]['v']:.0f} % con media superior o más. Entre estados la correlación es {str(k['rho_til']).replace('-', '−')}, pero no debe leerse como efecto individual."))

    # ------------------------------------------------------------------ 9 · respuestas y métricas
    resp = (
        f'<a href="#e-q1" data-ir="e-q1"><small>Pregunta 1</small><span class="q">¿Cuánto rinde estudiar y varía entre estados?</span><span class="a">+{ret[0]:.1f} %<span>por año de estudio, igual en estados ricos y pobres (p = {k["dq"][3]:.2f})</span></span>{viz("miniPremio")}</a>'
        f'<a href="#e-q2" data-ir="e-q2"><small>Pregunta 2</small><span class="q">¿Hay brecha de género con la misma escolaridad?</span><span class="a">{g1[0]:.1f} % menos<span>por hora, significativa (p &lt; 0.001); por mes, {bm[0]:.1f} %</span></span>{viz("miniEscalera")}</a>'
        f'<a href="#e-q3" data-ir="e-q3"><small>Pregunta 3</small><span class="q">¿Dónde hay más informalidad y cómo se relaciona con la escuela?</span><span class="a">{k["til"][0]:.0f} % informal<span>de {til_n[0]["v"]:.0f} % sin primaria a {til_n[3]["v"]:.0f} % con media superior o más</span></span>{viz("miniTil")}</a>')
    metr = (
        f'<a class="metrica" href="#e-q2" data-ir="e-q2"><i>✓</i><b>M1 · Brecha de género en % con su intervalo</b><span>{g1[0]:.1f} % (IC 95 %: {g1[1]:.1f} a {g1[2]:.1f}) controlando por escolaridad</span></a>'
        '<a class="metrica" href="#e-estados" data-ir="e-estados"><i>✓</i><b>M2 · Correlación por estado y ranking defendible</b><span>32 estados con intervalo; el ranking distingue solo los extremos</span></a>'
        '<a class="metrica" href="#e-q3" data-ir="e-q3"><i>✓</i><b>M3 · Tablero con 4 o más visualizaciones</b><span>Esta página y el tablero: más de 10 gráficas interactivas</span></a>')
    sec.append(escena("e-respuestas", "Respuestas y métricas", etiqueta("respuestas y métricas de éxito", "Interpretación · Sem. 5") +
        '<h2 class="titular titular--ancho">Tres preguntas, tres respuestas, tres métricas cumplidas</h2><div class="resp">' + resp + '</div><div class="metricas">' + metr + "</div>" +
        chips([("Son asociaciones, no efectos causales", "aviso"), ("Un solo trimestre (2025-T4)", "aviso"), ("MongoDB probado con un simulador", "aviso")]), "Juan Evelio",
        "Resumimos: tres preguntas contestadas y tres métricas cumplidas: la brecha con su intervalo, un ranking defendible y este tablero con más de cuatro visualizaciones. "
        "Reconocemos los límites: son asociaciones de un solo trimestre."))

    # ------------------------------------------------------------------ 10 · cierre: reflexión y productos
    reflexion = [
        ("¿Por qué le importa a alguien más allá de la calificación? ¿Quién usaría los hallazgos?",
         "Porque orienta decisiones públicas: becas y cobertura educativa, formalización del empleo e igualdad de género. Lo usarían las secretarías de educación y del trabajo, organizaciones civiles y cualquier estudiante que se pregunte si estudiar rinde."),
        ("¿Cuál fue el mayor reto técnico y en qué semana aprendimos a enfrentarlo?",
         "Calcular errores correctos con el diseño muestral complejo de la encuesta (bootstrap de Rao-Wu, semanas 2 y 3) y limpiar códigos e «ingreso 0» (semana 4)."),
        ("¿Cómo se repartió el trabajo para que todos practicaran las siete competencias?",
         "Hay cuatro roles: coordinación, ingeniería de datos, análisis estadístico y visualización y comunicación. Rotan entre los tres integrantes y cada quien presenta un bloque."),
    ]
    acordeon = '<div class="acordeon">' + "".join(f"<details{' open' if i == 0 else ''}><summary>{e(q)}</summary><p>{e(a)}</p></details>" for i, (q, a) in enumerate(reflexion)) + "</div>"
    productos = [("NB", "Cuaderno (Notebook)", "Pipeline y análisis ejecutados, con las mismas cifras", "cuaderno.html", ""), ("GH", "Repositorio en GitHub", "Código, pruebas y datos derivados", REPO, " target=\"_blank\" rel=\"noopener\""),
                 ("TB", "Tablero interactivo", "Ficha de cada entidad, mapa y ranking", "tablero.html", ""), ("PDF", "Informe técnico", "66 páginas: método, resultados y límites", "descargas/Informe_Final_Proyecto_ENOE.pdf", ""),
                 ("PPT", "Presentación completa", "48 diapositivas con guion", "descargas/Presentacion_Completa_Proyecto_ENOE.pdf", "")]
    prods = '<div class="productos">' + "".join(f'<a class="producto" href="{h}"{x}><i>{s}</i><b>{t}</b><span>{dd}</span></a>' for s, t, dd, h, x in productos) + "</div>"
    sec.append(escena("e-cierre", "Cierre", etiqueta("reflexión final y productos", "Cierre") + '<h2 class="titular">Lo que entregamos y lo que aprendimos</h2>'
        f'<div class="cierre"><div><p class="etq">Reflexión final del equipo</p>{acordeon}</div><div><p class="etq">Productos importantes (el informe visual es esta página)</p>{prods}</div></div>'
        f'<p class="pie">Datos: INEGI, ENOE 2025-T4 (microdatos públicos). Estimaciones ponderadas con el factor de expansión; IC 95 % por bootstrap de Rao-Wu con {n_es(k["B"])} réplicas. '
        f'Equipo 1 · UNE Plantel Centro · <a href="estudio.html">Guía de estudio ampliada ▸</a></p>', "Juan Evelio",
        "Respondemos las tres preguntas de reflexión y mostramos los productos: el cuaderno, el repositorio, el tablero, el informe y la presentación. Ajusten estas respuestas con su reparto real del trabajo."))

    return "\n".join(sec)


def pagina(cuerpo: str, datos_json: str, css: str, js: str, fragmento: bool) -> str:
    barra = (f'<header class="barra"><a class="marca" href="#e-portada" data-ir="e-portada">{e(TITULO)}<small>Equipo 1 · ENOE 2025-T4</small></a><nav class="puntos" id="puntos" aria-label="Láminas"></nav>'
             '<div class="controles"><span class="estado-chip" id="chip-estado"><span></span><button type="button" aria-label="Quitar la entidad elegida">×</button></span>'
             '<select class="sel" id="sel-estado" aria-label="Resaltar una entidad en todas las gráficas"></select>'
             '<button type="button" class="btn solo-ancho" id="btn-notas" aria-pressed="false" title="Notas del orador (N)">Notas</button>'
             '<button type="button" class="btn solo-ancho" id="btn-pantalla" title="Pantalla completa (F)">Pantalla completa</button>'
             '<button type="button" class="btn" id="btn-tema" aria-label="Cambiar entre tema claro y oscuro">Tema</button></div></header>')
    nav = ('<div class="nav"><button type="button" id="ant" aria-label="Lámina anterior">↑</button><span class="pos" id="pos">1 / 11</span><button type="button" id="sig" aria-label="Lámina siguiente">↓</button></div>'
           '<aside class="guion" id="guion" hidden aria-label="Notas del orador"><h4></h4><p></p></aside>')
    aviso = '<noscript><p style="padding:5rem 1.5rem 1rem">Esta página dibuja sus gráficas con JavaScript. Actívalo o abre la <a href="estudio.html">guía de estudio</a>.</p></noscript>'
    app = f"{barra}<main>{aviso}{cuerpo}</main>{nav}"
    datos = f'<script type="application/json" id="datos">{datos_json}</script>'
    if fragmento:
        return f'<title>{e(TITULO)}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n{FUENTES}\n<style>\n{css}\n</style>\n{app}\n{datos}\n<script>\n{js}\n</script>\n'
    return (f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>{e(TITULO)}</title>\n'
            f'<meta name="description" content="Proyecto Integrador de Ciencia de Datos con la ENOE 2025-T4 del INEGI: cuánto rinde estudiar, brechas de género e informalidad.">\n{FUENTES}\n'
            f'<style>\nhtml{{padding:0}}body{{margin:0}}\n{css}\n</style>\n</head>\n<body>\n{app}\n{datos}\n<script>\n{js}\n</script>\n</body>\n</html>\n')


def main() -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(RAIZ / "sitio" / "index.html"))
    ap.add_argument("--fragmento", default=None, help="ruta donde escribir la versión sin envoltura de documento")
    a = ap.parse_args()
    d = datos_web()
    datos_json = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    css = (ASSETS / "lite.css").read_text(encoding="utf-8-sig")        # utf-8-sig: ignora una marca BOM al inicio, que invalidaría el primer bloque de variables
    js = (ASSETS / "lite.js").read_text(encoding="utf-8-sig")
    cuerpo = construir(d)
    destino = Path(a.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina(cuerpo, datos_json, css, js, fragmento=False), encoding="utf-8")
    if a.fragmento:
        Path(a.fragmento).write_text(pagina(cuerpo, datos_json, css, js, fragmento=True), encoding="utf-8")
    print(f"Página escrita en {destino} ({destino.stat().st_size / 1e3:.0f} KB; 11 láminas)")
    return destino


if __name__ == "__main__":
    main()
