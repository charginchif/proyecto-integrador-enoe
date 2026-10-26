"""Presentación breve de la tesina web: la «ruta corta» de la presentación completa (las 18 diapositivas con ★, unos 18 minutos).

``ruta_corta_html(D, d)`` devuelve el HTML de la presentación (diapositivas y controles). Los títulos y el guion de cada diapositiva salen de las notas del orador de
presentacion/Presentacion_Completa_Proyecto_ENOE.pptx (quien presenta incluido); las cifras y las gráficas, de los resultados del proyecto, las mismas de la tesina.
La página la abre con el botón «Presentación breve» o con la dirección ``#presentacion-breve``; el comportamiento (teclas, reloj, guion) está en web_assets/tesina.js.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from deck_slides_extra import BLOQUES, MIN_CORTA, PRESENTA
from informe_html import e, md
from sitio_lib import Guiones

RAIZ = Path(__file__).resolve().parents[1]
PPTX = RAIZ / "presentacion" / "Presentacion_Completa_Proyecto_ENOE.pptx"


def _guiones() -> list[dict]:
    """Notas del orador de la presentación completa. Si el archivo está abierto en PowerPoint (bloqueado) se lee la versión guardada en git."""
    try:
        return Guiones(PPTX).items
    except (PermissionError, OSError):
        import tempfile
        copia = Path(tempfile.gettempdir()) / "completa_desde_git.pptx"
        datos = subprocess.run(["git", "show", "HEAD:presentacion/Presentacion_Completa_Proyecto_ENOE.pptx"], cwd=RAIZ, capture_output=True).stdout
        if not datos:
            return []
        copia.write_bytes(datos)
        return Guiones(copia).items


# ---------------------------------------------------------------------------------------------------------------------------------
# piezas de una diapositiva
# ---------------------------------------------------------------------------------------------------------------------------------
def viz(nombre: str, alt: str) -> str:
    return f'<div class="viz" data-chart="{nombre}" role="group" aria-label="{e(alt)}"></div>'


def cifra(valor: str, texto: str) -> str:
    return f'<div class="cifra-g"><b>{e(valor)}</b><span>{e(texto)}</span></div>'


def lista(items: list[str], clase: str = "") -> str:
    return f'<ul class="lista-g {clase}">' + "".join(f"<li>{md(i)}</li>" for i in items) + "</ul>"


def zona(visual: str, lado: str = "", clase: str = "") -> str:
    return f'<div class="dia__zona {clase}"><div class="dia__visual">{visual}</div><div class="dia__lado">{lado}</div></div>'


def imagen(nombre: str, alt: str) -> str:
    return f'<img class="dia__img" src="img/{nombre}" alt="{e(alt)}" loading="lazy" decoding="async">'


def f1(x: float) -> str:
    return f"{x:.1f}"


# ---------------------------------------------------------------------------------------------------------------------------------
# las 18 diapositivas: (clave, bloque, prefijo del título en la presentación completa, título de respaldo)
# ---------------------------------------------------------------------------------------------------------------------------------
RUTA = [
    ("portada", "A", "Radiografía socioeconómica", "Radiografía socioeconómica de México"),
    ("pregunta", "A", "La pregunta", "La pregunta: ¿cuánto rinde estudiar, y para quién?"),
    ("kdd", "A", "Un ciclo KDD completo", "Un ciclo KDD completo sobre datos reales y masivos"),
    ("validacion", "B", "Los filtros y ponderadores", "Los filtros y ponderadores reproducen las cifras oficiales del INEGI"),
    ("ingreso0", "C", "El «ingreso cero»", "El «ingreso cero» esconde tres fenómenos distintos"),
    ("embudo", "C", "De 419 mil registros", "De 419 mil registros a 112 mil observaciones, paso a paso"),
    ("arquitectura", "D", "Arquitectura:", "Arquitectura: SQLite para analizar, MongoDB para servir"),
    ("diseno", "E", "Ignorar el diseño muestral", "Ignorar el diseño muestral subestimaría el error a la mitad"),
    ("rendimiento", "F1", "Cada año de estudio", "Cada año de estudio eleva el ingreso por hora 5.1 %, y la licenciatura casi lo duplica"),
    ("estados", "F1", "Estudiar rinde parecido", "Estudiar rinde parecido en estados ricos y pobres"),
    ("ranking", "F1", "Un ranking defendible", "Un ranking defendible distingue solo los extremos"),
    ("brechahm", "F2", "Por hora la brecha", "Por hora la brecha es de 3.7 %; por mes, de 26.9 %"),
    ("comparables", "F2", "Entre personas comparables", "Entre personas comparables, la brecha por hora ronda 8 %"),
    ("cuantiles", "F2", "La brecha se concentra", "La brecha se concentra en la parte baja de la distribución"),
    ("informalidad", "F3", "La informalidad cae", "La informalidad cae con la escolaridad: de 87 % a 38 %"),
    ("conclusiones", "G", "Estudiar paga en todas partes", "Estudiar paga en todas partes; la brecha de género es de horas"),
    ("limites", "G", "Qué no podemos afirmar", "Qué no podemos afirmar, y qué haríamos después"),
    ("cierre", "G", "Gracias", "Gracias"),
]


def cuerpos(D, d: dict) -> dict[str, str]:
    """HTML del cuerpo de cada diapositiva; todas las cifras salen de los resultados."""
    k, n = d["k"], d["n"]
    est = d["estados"]
    mx_ret, mn_ret = max(est, key=lambda x: x["ret"][0]), min(est, key=lambda x: x["ret"][0])
    mx_til, mn_til = max(est, key=lambda x: x["til"][0]), min(est, key=lambda x: x["til"][0])
    rho_hi, rho_lo = max(est, key=lambda x: x["rho"][0]), min(est, key=lambda x: x["rho"][0])
    cal = d["calidad"]
    total, n1, n4 = cal[0], cal[3], cal[6]
    til_niv = d["til_nivel"]
    sur = next(x["v"] for x in d["til_region"] if x["n"] == "Sur")
    cuant = {q["p"]: q for q in d["cuantiles"]}
    robustez = (D.robustez_retorno.retorno_pct.min(), D.robustez_retorno.retorno_pct.max())
    ed = d["efecto_diseno"]
    c = {}

    c["portada"] = zona(
        '<p class="dia__sub">Escolaridad, ingreso y brecha de género</p><p class="dia__txt">Encuesta Nacional de Ocupación y Empleo (ENOE), 4.º trimestre de 2025 · INEGI</p>'
        '<p class="dia__equipo">Equipo 1 · Juan Evelio Culin Grajeda · Angel Yireh Garcia Jara · Luis Andre Gutierrez Zuñiga</p><p class="dia__txt">Proyecto Integrador de Ciencia de Datos · Ingeniería en Computación, 9.º semestre · UNE Plantel Centro</p>'
        '<div class="cifras-g">' + cifra(f"{n['registros']:,}", "registros") + cifra(f"{n['universo']:,}", "ocupados de 15+") + cifra("32", "entidades") + cifra(f"{k['B']:,}", "réplicas bootstrap") + "</div>",
        viz("mosaicoPortada", "Mosaico de las 32 entidades con su tasa de informalidad laboral"), "dia--portada")

    c["pregunta"] = zona(
        '<blockquote class="dia__pregunta">¿Cuánto aumenta el ingreso laboral por cada año adicional de escolaridad, cómo cambia esa relación entre entidades federativas y existe una brecha salarial '
        'significativa entre hombres y mujeres con la misma escolaridad?</blockquote>'
        '<ol class="obj-g"><li>Estimar la correlación y el rendimiento de la escolaridad en cada una de las 32 entidades</li>'
        '<li>Probar si hay brecha de ingreso por hora entre hombres y mujeres con el mismo nivel de instrucción</li>'
        '<li>Identificar las entidades con más informalidad y su relación con la escolaridad</li></ol>',
        '<p class="dia__etq2">Métricas de éxito del protocolo</p><ul class="chips-g"><li><b>M1</b> Brecha por nivel con IC 95 % y prueba de hipótesis</li>'
        '<li><b>M2</b> Spearman de las 32 entidades con IC y ranking</li><li><b>M3</b> Tablero con ≥ 4 gráficas sobre una base NoSQL</li></ul>', "dia--texto")

    c["kdd"] = zona(imagen("D01_kdd.png", "Las cinco fases del ciclo KDD: selección, preprocesamiento, transformación, minería e interpretación"),
                    '<div class="cifras-g cifras-g--col">' + cifra(f"{n['registros']:,}", "registros de la tabla SDEMT") + cifra(f"{n['salarial']:,}", "observaciones salariales")
                    + cifra("21,194", "UPM en 713 estratos") + cifra("7 de 7", "cifras oficiales reproducidas") + "</div>", "dia--ancha")

    c["validacion"] = zona(viz("validacion", "Cifras del proyecto frente a las publicadas por el INEGI"),
                           cifra("7 de 7", "cifras del INEGI reproducidas al redondear a su precisión")
                           + '<p class="dia__nota"><b>Por qué solo 15+:</b> con los 1,078 menores de 15 años ocupados, el TIL1 sería 55.27 % y dejaría de coincidir con el oficial.</p>')

    c["ingreso0"] = zona(viz("calidad", "Composición del ingreso por grupo de declaración, por población"),
                         '<div class="cifras-g cifras-g--col">' + cifra(f"{total['A']:.0f} %", "declara el monto exacto") + cifra(f"{total['B']:.0f} %", "da solo un rango de salarios mínimos")
                         + cifra(f"{total['D']:.0f} %", "no especifica su ingreso") + "</div>"
                         + f'<p class="dia__nota">Más escolaridad, menos monto exacto ({n4["A"]:.0f} % frente a {n1["A"]:.0f} %). Solo {total["C"]:.0f} % no recibe ingresos.</p>')

    c["embudo"] = zona(viz("embudo", "Embudo de registros: de 419,038 a 111,958 observaciones salariales"),
                       lista(["La cobertura elimina filas; todo lo demás **crea banderas**", "610 escolaridades = 99 y 5,278 jornadas de 0 h recodificadas",
                              "1,133 ingresos por hora atípicos (P0.5–P99.5 por entidad)", "**15 de 15** expectativas de calidad cumplidas", "ETL idempotente: 10 s, una sola semilla y SHA-256 de cada archivo"]))

    c["arquitectura"] = zona(imagen("D02_arquitectura.png", "Arquitectura del proyecto: microdatos, ETL, SQLite, análisis, resultados, MongoDB y tablero"),
                             '<div class="just-g"><p class="dia__etq2">Relacional (SQLite): analizar</p><p>Datos tabulares de esquema fijo · agregaciones ponderadas y JOIN · integridad por restricciones · fuente de verdad</p></div>'
                             '<div class="just-g"><p class="dia__etq2">Documental (MongoDB): servir</p><p>Una ficha por entidad (embedding) · el esquema crece sin migraciones · lectura por clave · vista que se regenera</p></div>', "dia--ancha")

    c["diseno"] = zona(viz("efectoDiseno", "Error estándar al ignorar el diseño muestral, como porcentaje del error real"),
                       '<div class="cifras-g cifras-g--col">' + cifra(f"×{k['deff']:.1f}", "efecto de diseño en la informalidad")
                       + cifra(f"{round(k['n_efectivo'], -3) / 1000:.0f} mil", f"observaciones efectivas de {n['universo'] // 1000} mil")
                       + cifra(f"{k['B']:,}", "réplicas de Rao-Wu · 713 estratos · 21,194 UPM") + "</div>")

    c["rendimiento"] = zona(viz("premio", "Premio salarial por nivel de estudios frente a primaria incompleta"),
                            cifra(f"+{k['ret'][0]:.1f} %", f"por año de escolaridad (IC 95 %: {k['ret'][1]:.1f} a {k['ret'][2]:.1f})")
                            + lista([f"Mujeres {k['ret_m']:.1f} % frente a hombres {k['ret_h']:.1f} % por año", f"Robusto: {robustez[0]:.1f} %–{robustez[1]:.1f} % en 7 especificaciones",
                                     f"Spearman nacional ρ = {k['rho_nac'][0]:.2f}"]))

    c["estados"] = zona(viz("dispEstados", "Aumento del ingreso por año de estudio frente al ingreso mediano de cada estado"),
                        '<div class="cifras-g cifras-g--col">' + cifra("≈ 0", f"diferencia de rendimiento entre estados ricos (Q4) y pobres (Q1): {k['dq'][0]:+.3f} log-puntos, p = {k['dq'][3]:.2f}")
                        + cifra(f"{mn_ret['ret'][0]:.1f}–{mx_ret['ret'][0]:.1f} %", f"rango entre estados: de {mn_ret['n']} a {mx_ret['n']}")
                        + cifra(f"{k['ret_m']:.1f} vs. {k['ret_h']:.1f} %", "rendimiento por año de mujeres frente a hombres") + "</div>")

    c["ranking"] = zona(viz("rankRho", "Correlación de Spearman entre escolaridad e ingreso por entidad, con intervalo y lugar"),
                        '<div class="cifras-g cifras-g--col">' + cifra(f"{k['rho_nac'][0]:.2f}", "Spearman nacional: asociación positiva y moderada")
                        + cifra(f"{rho_hi['rho'][0]:.2f} → {rho_lo['rho'][0]:.2f}", f"de {rho_hi['n']} (lugar {rho_hi['rho'][4]}–{rho_hi['rho'][5]}) a {rho_lo['n']} ({rho_lo['rho'][4]}–{rho_lo['rho'][5]})") + "</div>"
                        + '<p class="dia__nota">Los lugares centrales abarcan 15 o más posiciones: no son estadísticamente distinguibles.</p>')

    c["brechahm"] = zona(viz("brechaNivel", "Brecha por hora y por mes según el nivel de estudios"),
                         '<div class="cifras-g cifras-g--col">' + cifra(f"{k['bh'][0]:.1f} %", f"por hora (IC {k['bh'][1]:.1f}–{k['bh'][2]:.1f})") + cifra(f"{k['bm'][0]:.1f} %", "por mes")
                         + cifra(f"−{k['menos_horas']:.0f} %", f"horas pagadas: {k['horas_m']:.1f} frente a {k['horas_h']:.1f} h por semana") + "</div>"
                         + '<p class="dia__nota">Brecha = 1 − (ingreso medio geométrico de las mujeres ÷ el de los hombres), con IC 95 %.</p>')

    c["comparables"] = zona(viz("escalera", "Brecha por hora al agregar controles sucesivos"),
                            '<div class="cifras-g cifras-g--col">' + cifra(f"{d['escalera'][0]['v']:.1f} %", "sin controles") + cifra(f"{k['g5'][0]:.1f} %", "con escolaridad, edad, lugar, empleo y rama")
                            + cifra(f"{d['oaxaca_full'][-1]['v']:.1f} pts", "log-puntos no explicados (Oaxaca-Blinder); no prueban discriminación") + "</div>"
                            + '<p class="dia__nota">Cada fila agrega controles al anterior; la última (horas) no se interpreta por el sesgo de división.</p>')

    c["cuantiles"] = zona(viz("cuantiles", "Brecha por hora en los percentiles 10 a 90 del ingreso por hora"),
                          '<div class="cifras-g cifras-g--col">' + cifra(f"{cuant[10]['v']:.0f}–{cuant[25]['v']:.0f} %", "en el 10 %–25 % que menos gana") + cifra(f"{cuant[50]['v']:.1f} %", "en la mediana (no significativa)")
                          + cifra("≈ 0", "en el 25 % que más gana") + "</div>")

    c["informalidad"] = zona(viz("mosaicoPortada", "Mosaico de las 32 entidades con su tasa de informalidad laboral"),
                             '<div class="cifras-g cifras-g--col">' + cifra(f"{k['til'][0]:.1f} %", "informalidad nacional (TIL1)") + cifra(f"{mn_til['til'][0]:.0f} → {mx_til['til'][0]:.0f} %", f"de {mn_til['n']} a {mx_til['n']}")
                             + cifra(f"{til_niv[0]['v']:.0f} → {til_niv[3]['v']:.0f} %", "de primaria incompleta a media superior o más")
                             + cifra(f"{D.ind['ame_anios_esc_pp']:.1f} pp".replace("-", "−"), "por cada año de escolaridad (individual)") + "</div>"
                             + f'<p class="dia__nota">Entre estados, Spearman = {str(k["rho_til"]).replace("-", "−")}. TIL1 = ocupados en empleo informal ÷ ocupados de 15+ (definición del INEGI); las mujeres suman +{D.ind["ame_mujer_pp"]:.0f} puntos a igual escolaridad, edad y lugar.</p>')

    c["conclusiones"] = zona(
        '<p class="dia__etq2">Qué encontramos</p>' + lista([f"Estudiar rinde ≈ {k['ret'][0]:.1f} % por año y la licenciatura casi duplica el ingreso", f"El rendimiento es igual en estados ricos y pobres (p = {k['dq'][3]:.2f})",
                                                              f"Brecha de {k['bh'][0]:.1f} % por hora y {k['bm'][0]:.1f} % por mes: es de horas", f"Informalidad: {til_niv[0]['v']:.0f} % → {til_niv[3]['v']:.0f} % con la escolaridad"])
        + '<p class="dia__etq2">Qué recomendamos</p>' + lista([f"Ampliar acceso y permanencia escolar, sobre todo en el Sur (informalidad {sur:.0f} %)", "Políticas de cuidados y horarios flexibles de tiempo completo para cerrar la brecha de horas",
                                                                  "Atender el «piso pegajoso»: salario mínimo y formalización en los percentiles bajos", "Publicar ingresos imputados por rango y corregir por no respuesta"]),
        '<p class="dia__etq2">Métricas de éxito</p><ul class="chips-g chips-g--ok"><li><b>M1 ✓</b> Brecha por nivel con IC y prueba: cumplida</li><li><b>M2 ✓</b> Spearman de 32 entidades con IC y ranking: cumplida</li>'
        '<li><b>M3 ✓</b> Tablero ≥ 4 gráficas sobre base NoSQL: cumplida *</li></ul><p class="dia__nota">* La carga a un servidor MongoDB real no se ejecutó; se probó con mongomock.</p>', "dia--texto")

    c["limites"] = zona(
        '<p class="dia__etq2">Límites</p>' + lista(["Asociación, no causalidad (habilidad no observada; falacia ecológica entre estados)", "Solo vemos el ingreso de quien trabaja y lo declara (selección)",
                                                     "Ingreso autorreportado, con redondeo; horas de una sola semana", "Un trimestre; 1,900–5,900 observaciones por estado", "MongoDB: probado con mongomock; carga a servidor real pendiente"]),
        '<p class="dia__etq2">Con más tiempo</p>' + lista(["Varios trimestres (panel rotativo de la ENOE)", "Corrección de selección (Heckman) para la participación laboral", "Mapa geográfico real con el Marco Geoestadístico",
                                                           "Estimaciones para áreas pequeñas (municipios)", "Contrastar los códigos de rangos con el cuestionario oficial"]), "dia--texto")

    c["cierre"] = zona(
        '<p class="dia__sub">¿Preguntas o comentarios?</p><p class="dia__txt">Todo el trabajo está en esta misma página: el documento completo, la bibliografía y los anexos, y en las otras versiones del sitio.</p>'
        '<p class="dia__enlaces"><a href="#cap-7" data-cerrar-pres>Resultados (capítulo 7)</a><a href="#anexo-d" data-cerrar-pres>Preguntas frecuentes (anexo D)</a><a href="cuaderno.html">Cuaderno</a><a href="tablero.html">Tablero</a>'
        '<a href="descargas/Informe_Final_Proyecto_ENOE.pdf">Informe técnico (PDF)</a></p>',
        '<p class="dia__etq2">Reproducir todo</p><div class="codigo codigo--g"><pre><code>python scripts/run_etl.py\npython scripts/run_analysis.py\npython scripts/make_figures.py\npython scripts/build_notebook.py</code></pre></div>'
        '<p class="dia__nota">Código, pruebas y datos derivados: carpeta Proyecto_ENOE y repositorio de GitHub.</p>', "dia--texto")
    return c


def ruta_corta_html(D, d: dict) -> str:
    items = [x for x in _guiones() if x["estrella"]]
    cu = cuerpos(D, d)
    dias, minutos_total = [], sum(MIN_CORTA.values())
    for i, (clave, bloque, prefijo, titulo_resp) in enumerate(RUTA):
        g = items[i] if i < len(items) else None
        if g is not None and not g["titulo"].replace("–", "-").startswith(prefijo.replace("–", "-")):
            raise SystemExit(f"La diapositiva {i + 1} de la ruta corta es «{g['titulo']}», no «{prefijo}…»: revisa web_ruta_corta.RUTA")
        titulo = g["titulo"] if g else titulo_resp
        quien = (g["quien"] if g and g["quien"] else PRESENTA.get(bloque, ""))
        guion = g["notas"] if g else ""
        nombre_bloque = BLOQUES[bloque]
        dias.append(f'<section class="dia" id="dia-{i + 1}" data-clave="{clave}" data-bloque="{bloque}" data-bloque-nombre="{e(nombre_bloque)}" data-quien="{e(quien)}" data-min="{MIN_CORTA[bloque]}" '
                    f'data-titulo="{e(titulo)}" data-guion="{e(guion)}" hidden aria-label="Diapositiva {i + 1} de {len(RUTA)}">'
                    f'<p class="dia__etq">{e(nombre_bloque)} · {e(quien)}</p><h2 class="dia__titulo">{md(titulo)}</h2>{cu[clave]}</section>')
    bloques, vistos = [], []
    for _, b, _, _ in RUTA:
        if b not in vistos:
            vistos.append(b)
            bloques.append((b, BLOQUES[b].split(" · ", 1)[1], MIN_CORTA[b]))
    marcas = "".join(f'<li data-b="{b}" title="{e(nombre)} · {m} min"><span>{b}</span></li>' for b, nombre, m in bloques)
    return ('<div class="pres" id="pres" role="dialog" aria-modal="true" aria-label="Presentación breve: ruta corta de 18 diapositivas" hidden tabindex="-1">'
            '<header class="pres__cab"><div class="pres__marca"><b>Presentación breve</b><span>ruta corta · ' + str(len(RUTA)) + f' diapositivas · {minutos_total} min</span></div>'
            f'<ol class="pres__bloques" aria-label="Bloques de la presentación">{marcas}</ol>'
            '<div class="pres__acc"><button type="button" class="pres__reloj" id="pres-reloj" title="Iniciar o pausar el reloj (T); doble clic para reiniciar">▶ 00:00 / ' + f'{minutos_total}:00</button>'
            '<button type="button" class="btn-ic" id="pres-notas-btn" aria-pressed="false" title="Guion de quien expone (N)">Guion</button>'
            '<button type="button" class="btn-ic" id="pres-pantalla" title="Pantalla completa (F)">Pantalla completa</button>'
            '<button type="button" class="btn-ic" id="pres-salir" title="Salir (Esc)">Salir</button></div></header>'
            f'<div class="pres__marco" id="pres-marco">{"".join(dias)}</div>'
            '<footer class="pres__pie"><button type="button" class="pres__flecha" id="pres-ant" aria-label="Diapositiva anterior">←</button>'
            '<div class="pres__centro"><span id="pres-pos">1 / ' + str(len(RUTA)) + '</span><span class="pres__tiempo" id="pres-tiempo"></span><div class="pres__progreso"><i id="pres-barra"></i></div></div>'
            '<button type="button" class="pres__flecha" id="pres-sig" aria-label="Diapositiva siguiente">→</button></footer>'
            '<aside class="pres__notas" id="pres-notas" hidden aria-label="Guion de la diapositiva"><h3></h3><p></p></aside></div>')
