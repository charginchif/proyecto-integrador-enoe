"""Tesina web del proyecto (sitio/index.html): el informe técnico completo como un documento académico para leer en pantalla.

    python scripts/build_tesina.py                    # sitio/index.html
    python scripts/build_tesina.py --fragmento RUTA   # además, la versión sin envoltura de documento (para publicarla como artefacto)

El texto, las tablas y las figuras salen de las mismas funciones que arman el informe en Word (informe_s1 a informe_s4), con un «backend» HTML
(informe_html.InformeHTML); aquí se agregan la portada, el resumen en inglés, los hallazgos clave, el índice, la bibliografía enlazada, los componentes
interactivos y la envoltura de la página. Las figuras de datos se dibujan en el navegador con las gráficas compartidas con la presentación
(web_assets/charts.js) a partir de los resultados (scripts/web_datos.py); cada una conserva la imagen original para ampliarla.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import informe_s1 as s1  # noqa: E402
import informe_s2 as s2  # noqa: E402
import informe_s3 as s3  # noqa: E402
import informe_s4 as s4  # noqa: E402
from informe_datos import cargar, f1, n_es  # noqa: E402
from informe_html import InformeHTML, e, md, slug  # noqa: E402
from sitio_textos import ALT, PORQUE  # noqa: E402
from web_datos import datos_web  # noqa: E402
from web_ruta_corta import ruta_corta_html  # noqa: E402

ASSETS = Path(__file__).resolve().parent / "web_assets"
SITIO = RAIZ / "sitio"
TITULO = "Radiografía socioeconómica de México"
SUBTITULO = "Escolaridad, ingreso y brecha de género a partir de la Encuesta Nacional de Ocupación y Empleo (ENOE), 4.º trimestre de 2025"
REPO = "https://github.com/charginchif/proyecto-integrador-enoe"
URL = "https://charginchif.github.io/proyecto-integrador-enoe/"
AUTORES = ["Juan Evelio Culin Grajeda", "Angel Yireh Garcia Jara", "Luis Andre Gutierrez Zuñiga"]
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400'
           '&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400..700&display=swap">')

# figura de datos -> gráfica interactiva (las demás figuras son diagramas o gráficas sin datos en la página y se muestran como imagen)
VIZ = {
    "01_embudo_datos.png": "embudo", "02_calidad_ingreso.png": "calidad", "04_ingreso_por_escolaridad.png": "curva", "05_retorno_estados.png": "retornoEstados",
    "06_spearman_estados.png": "rankRho", "07_escolaridad_vs_ingreso_estatal.png": "escIngreso", "09_brecha_por_nivel.png": "brechaNivel",
    "10_escalera_controles.png": "escalera", "11_oaxaca_blinder.png": "oaxacaCompleto", "12_brecha_cuantiles.png": "cuantiles", "13_robustez_brecha.png": "robustez",
    "14_mapa_informalidad.png": "mosaicoTil", "15_informalidad_vs_escolaridad.png": "dispTil", "17_brecha_subgrupos.png": "subgrupos",
}

# las dos ecuaciones del texto, compuestas con HTML (variables en cursiva, subíndices y una fracción de verdad)
ECUACIONES = {
    "ln(ingreso por hora) = α + β · años de escolaridad + γ₁ · edad + γ₂ · edad² + δ · mujer + efectos de entidad y de localidad + error":
        '<span class="eq-l"><span class="fn">ln</span>(<i>ingreso por hora</i>) = <i>α</i> + <i>β</i> · <i>años de escolaridad</i> + <i>γ</i><sub>1</sub> · <i>edad</i> + <i>γ</i><sub>2</sub> · <i>edad</i><sup>2</sup></span>'
        '<span class="eq-l">+ <i>δ</i> · <i>mujer</i> + <i>efectos de entidad y de localidad</i> + <i>error</i></span>',
    "brecha (%) = 100 × [ 1 − (ingreso medio geométrico de las mujeres ÷ ingreso medio geométrico de los hombres) ]":
        '<i>brecha</i> (%) = 100 × <span class="corch">[</span> 1 − <span class="frac"><span>ingreso medio geométrico de las mujeres</span><span>ingreso medio geométrico de los hombres</span></span> <span class="corch">]</span>',
}

# términos del glosario que se marcan (solo la primera vez que aparecen en cada capítulo) para mostrar su definición al pasar el cursor
TERMINOS = [
    (r"factor(?:es)? de expansión", "Factor de expansión (fac_tri)"), (r"efecto de diseño", "Efecto de diseño (deff)"), (r"UPM", "UPM"),
    (r"bootstrap de Rao-Wu", "Rao-Wu, bootstrap de"), (r"bootstrap", "Bootstrap"), (r"intervalos? de confianza", "Intervalo de confianza"), (r"valor(?:es)? p", "Valor p"),
    (r"Holm", "Holm"), (r"Oaxaca-Blinder", "Oaxaca-Blinder"), (r"TIL1", "Informalidad laboral (TIL1)"), (r"KDD", "KDD"), (r"ETL", "ETL"), (r"hot-deck", "Hot-deck"), (r"IPW", "IPW"),
    (r"logit", "Logit"), (r"WLS", "WLS"), (r"VIF", "VIF"), (r"d de Cohen", "Cohen, d de"), (r"heterocedasticidad", "Heterocedasticidad"), (r"falacia ecológica", "Falacia ecológica"),
    (r"persistencia políglota", "Persistencia políglota"), (r"idempotencia", "Idempotencia"), (r"sesgo de división", "Sesgo de división"),
    (r"razón(?:es)? de momios", "Razón de momios (odds ratio)"), (r"media geométrica", "Media geométrica"), (r"linealización de Taylor", "Linealización de Taylor"),
    (r"imputación", "Imputación"), (r"SDEMT", "SDEMT"), (r"COE2T", "COE2T"), (r"NDJSON", "NDJSON"), (r"ACID", "ACID"), (r"SQLite", "SQLite"), (r"MongoDB", "MongoDB"),
    (r"conglomerados?", "Conglomerado"), (r"estratos?", "Estrato"), (r"dominios?", "Dominio"), (r"panel rotativo", "Panel rotativo"), (r"curtosis", "Curtosis"), (r"asimetría", "Asimetría"),
    (r"ENOE", "ENOE"),
]
# citas de la bibliografía que aparecen en el texto: (autor, año, id de la referencia); se enlaza el año
CITAS = [("Mincer", "1974", "ref-mincer1974"), ("Holm", "1979", "ref-holm1979"), ("Rao y Wu", "1988", "ref-rao1988"), ("Neumark", "1988", "ref-neumark1988"),
         ("Heckman", "1979", "ref-heckman1979")]
SALTAR = {"a", "code", "pre", "h2", "h3", "h4", "figcaption", "summary", "button", "script", "style", "dt", "abbr", "label", "option", "select"}


# --------------------------------------------------------------------------- #
# procesamiento del HTML ya generado: enlaces entre secciones, citas y términos del glosario
# --------------------------------------------------------------------------- #
_ETIQUETA = re.compile(r"(<[^>]+>)")


_VACIAS = {"img", "br", "hr", "input", "col", "meta", "link", "source", "wbr", "path", "circle", "line", "rect", "polygon"}
_CLASES_SALTAR = ("cap-etq", "cap-meta", "nota__tit", "portada__", "prelim-t", "claves", "clave", "cifra-p", "ruta__", "interactivo__tit", "fig__", "tabla-filtro")


def por_texto(fragmento: str, funcion) -> str:
    """Aplica ``funcion`` solo al texto que no está dentro de enlaces, código, títulos, pies de figura, etiquetas ni controles."""
    salida, pila = [], []
    for parte in _ETIQUETA.split(fragmento):
        if parte.startswith("<"):
            m = re.match(r"<(/?)([a-zA-Z0-9]+)", parte)
            if m and m.group(2).lower() not in _VACIAS and not parte.endswith("/>"):
                etiqueta = m.group(2).lower()
                if m.group(1):                                              # cierre: se saca de la pila el elemento abierto más reciente con ese nombre
                    for k in range(len(pila) - 1, -1, -1):
                        if pila[k][0] == etiqueta:
                            del pila[k:]
                            break
                else:
                    clase = re.search(r'class="([^"]*)"', parte)
                    omitir = etiqueta in SALTAR or bool(clase and any(c in clase.group(1) for c in _CLASES_SALTAR))
                    pila.append((etiqueta, omitir))
            salida.append(parte)
        else:
            salida.append(funcion(parte) if parte.strip() and not any(o for _, o in pila) else parte)
    return "".join(salida)


_SEC_REF = re.compile(r"\b([Ss]ecci[oó]n(?:es)?)\s+(\d+(?:\.\d+)?(?:(?:\s*,\s*|\s+y\s+|\s+a\s+|\s+e\s+)\d+(?:\.\d+)?)*)")
_NUM = re.compile(r"\d+(?:\.\d+)?")


def enlazar_secciones(fragmento: str, ids: set[str]) -> str:
    def numero(m: re.Match) -> str:
        n = m.group(0)
        destino = "sec-" + n.replace(".", "-") if "." in n else "cap-" + n
        return f'<a class="ref-int" href="#{destino}">{n}</a>' if destino in ids else n

    def sec(m: re.Match) -> str:
        return m.group(1) + " " + _NUM.sub(numero, m.group(2))

    def anexo(m: re.Match) -> str:
        destino = "anexo-" + m.group(1).lower()
        return f'<a class="ref-int" href="#{destino}">Anexo {m.group(1)}</a>' if destino in ids else m.group(0)

    def texto(t: str) -> str:
        return re.sub(r"\bAnexo ([A-F])\b", anexo, _SEC_REF.sub(sec, t))

    return por_texto(fragmento, texto)


def enlazar_citas(fragmento: str, ids: set[str], refs: dict[str, str]) -> str:
    for autor, anio, ref in CITAS:
        if ref not in ids:
            continue
        a, titulo = re.escape(autor), e(refs.get(ref, ""))
        fragmento = re.sub(rf"({a}(?:</strong>|</em>)? \()({anio})(\))", rf'\1<a class="cita" href="#{ref}" title="{titulo}">\2</a>\3', fragmento)
        fragmento = re.sub(rf"({a}, )({anio})(\))", rf'\1<a class="cita" href="#{ref}" title="{titulo}">\2</a>\3', fragmento)
    return fragmento


def unir_porcentajes(fragmento: str) -> str:
    return por_texto(fragmento, lambda t: re.sub(r"(\d) %", "\\1&nbsp;%", t))


def marcar_terminos(fragmento: str, glosario: dict[str, str]) -> str:
    """Envuelve la primera aparición de cada término del glosario en <abbr class="termino">; la definición sale del anexo A."""
    usados: set[str] = set()
    patrones = [(re.compile(rf"(?<![\w-])({p})(?![\w-])", re.I if p[0].islower() else 0), clave) for p, clave in TERMINOS]

    def texto(t: str) -> str:
        marcas: list[tuple[int, int, str, str]] = []
        for rx, clave in patrones:
            if clave in usados:
                continue
            m = rx.search(t)
            if m and not any(a < m.end() and m.start() < b for a, b, _, _ in marcas):
                marcas.append((m.start(), m.end(), clave, m.group(1)))
        if not marcas:
            return t
        salida, pos = [], 0
        for a, b, clave, vista in sorted(marcas):
            usados.add(clave)
            salida.append(t[pos:a])
            salida.append(f'<abbr class="termino" tabindex="0" data-g="{glosario[clave]}">{vista}</abbr>')
            pos = b
        salida.append(t[pos:])
        return "".join(salida)

    return por_texto(fragmento, texto)


# --------------------------------------------------------------------------- #
# piezas de la página
# --------------------------------------------------------------------------- #
def icono(nombre: str) -> str:
    trazos = {
        "menu": '<path d="M3 6h18M3 12h18M3 18h18"/>',
        "buscar": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
        "tema": '<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/>',
        "flecha": '<path d="M12 19V5M5 12l7-7 7 7"/>',
        "pres": '<rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M8 20h8M12 16v4"/>',
    }
    return f'<svg class="ic-svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{trazos[nombre]}</svg>'


def portada(d: dict, D) -> str:
    k = d["k"]
    cifras = [(f"+{k['ret'][0]:.1f} %", "ingreso por hora por cada año de estudio", "#sec-7-2"), (f"{k['g1'][0]:.1f} %", "menos por hora ganan las mujeres con la misma escolaridad", "#sec-7-5"),
              (f"{k['til'][0]:.1f} %", "de las personas ocupadas está en empleo informal", "#sec-7-10"), ("7 de 7", "cifras oficiales del INEGI reproducidas con los microdatos", "#sec-3-4")]
    cifras_html = "".join(f'<a class="cifra-p" href="{h}"><b>{v}</b><span>{t}</span></a>' for v, t, h in cifras)
    autores = "".join(f"<li>{e(a)}</li>" for a in AUTORES)
    return f"""<header class="portada" id="portada">
 <div class="portada__fondo" aria-hidden="true"></div>
 <div class="portada__cont">
  <div class="portada__inst"><p class="inst-1">Universidad de Especialidades UNE · Plantel Centro</p><p class="inst-2">Ingeniería en Computación · Optativa III: Ciencia de Datos · 9.º semestre</p></div>
  <div class="portada__grid">
   <div class="portada__texto">
    <p class="portada__etq">Tesina · Proyecto Integrador de Ciencia de Datos</p>
    <h1>{e(TITULO)}</h1>
    <p class="portada__sub">{e(SUBTITULO)}</p>
    <div class="portada__autores"><p class="eq">Equipo 1</p><ul>{autores}</ul></div>
    <p class="portada__fecha">Octubre de 2026</p>
    <p class="portada__acc"><a class="btn btn--sol" href="#resumen">Leer el resumen</a><a class="btn" href="#indice-general">Ver el índice</a><a class="btn" href="#cap-7">Ir a los resultados</a><button type="button" class="btn" data-abrir-pres>Presentación breve · 18 min</button></p>
   </div>
   <figure class="portada__fig"><div class="viz" data-chart="mosaicoPortada" role="group" aria-label="Mosaico de las 32 entidades con su tasa de informalidad laboral"></div>
    <figcaption>Informalidad laboral por entidad (TIL1, %): cada mosaico es un estado y todos ocupan la misma área. Pasa el cursor para ver el dato; un clic lo resalta en las figuras del documento.</figcaption></figure>
  </div>
  <div class="portada__cifras">{cifras_html}</div>
 </div>
</header>"""


def resumen_ingles(D, k: dict) -> str:
    R, tot, rt = D.R, D.tot, D.rt
    return f"""<section class="prelim" id="abstract" lang="en"><h2 class="prelim-t">Abstract</h2>
<p class="j">This work documents a complete knowledge-discovery (KDD) cycle applied to Mexico’s National Survey of Occupation and Employment (ENOE, INEGI), fourth quarter of 2025 ({n_es(D.bit.loc['L0', 'n_despues'])} records).
It asks how much labor income rises with each additional year of schooling, how that relationship varies across the 32 states, and whether men and women with the same schooling earn significantly different hourly wages.</p>
<p class="j">The data were cleaned with documented and tested rules, validated against seven official INEGI figures (all seven match), stored in a relational (SQLite) and a document (MongoDB) model, and analyzed with methods that respect the survey’s complex design (Rao–Wu bootstrap, {R['B']:,} replicates).
Each year of schooling is associated with a {f1(rt['nacional_pct']['est'])} % increase in hourly income (95 % CI: {f1(rt['nacional_pct']['ic_inf'])} to {f1(rt['nacional_pct']['ic_sup'])}), with virtually no difference between richer and poorer states (p = {D.dq['p']:.2f}).
The gender gap is {f1(tot['brecha_hora_pct'])} % per hour and {f1(tot['brecha_mens_pct'])} % per month; the monthly difference comes mostly from women working {f1(tot['menos_horas_mujeres_pct'])} % fewer paid hours, while among comparable workers the hourly gap is about {D.g5['brecha_pct']:.0f} %, concentrated at the bottom of the distribution and in informal jobs.
Informal employment reaches {f1(D.nac['est'])} % of employed people, ranges from {D.mn_til['til1_est']:.0f} % to {D.mx_til['til1_est']:.0f} % across states and falls from {R['til1']['por_nivel']['1']:.0f} % to {R['til1']['por_nivel']['4']:.0f} % as schooling increases.
The results describe associations, not causal effects.</p>
<p class="claves"><span>Keywords</span><b>ENOE</b><b>schooling</b><b>hourly income</b><b>gender wage gap</b><b>informal employment</b><b>complex survey design</b><b>Rao–Wu bootstrap</b><b>Oaxaca–Blinder</b><b>SQLite</b><b>MongoDB</b></p></section>"""


def hallazgos(d: dict, D) -> str:
    k, rt, tot = d["k"], D.rt, D.tot
    est = {x["n"]: x for x in d["estados"]}
    tarjetas = [
        (f"+{k['ret'][0]:.1f} %", f"más ingreso por hora por cada año de escolaridad (IC 95 %: {k['ret'][1]:.1f} a {k['ret'][2]:.1f}); la licenciatura o el posgrado pagan {D.premio_por_nivel.iloc[3]['premio_pct']:.0f} % más que no terminar la primaria", "7.2", "sec-7-2"),
        ("≈ 0", f"diferencia del rendimiento entre los estados de mayor y menor ingreso (p = {k['dq'][3]:.2f}): estudiar rinde parecido en estados ricos y pobres", "7.2", "sec-7-2"),
        (f"{k['rho_min'][1]:.2f} a {k['rho_max'][1]:.2f}", f"correlación escolaridad-ingreso por entidad (Spearman), de {k['rho_min'][0]} a {k['rho_max'][0]}; el ranking solo es defendible en los extremos", "7.3", "sec-7-3"),
        (f"{k['bh'][0]:.1f} % · {k['bm'][0]:.1f} %", f"brecha de género por hora y por mes; la diferencia mensual se debe sobre todo a que las mujeres trabajan {k['menos_horas']:.0f} % menos horas pagadas", "7.4", "sec-7-4"),
        (f"{k['g1'][0]:.1f} % · {k['g5'][0]:.1f} %", "brecha por hora con la misma escolaridad y entre personas comparables (escolaridad, edad, lugar, empleo y rama)", "7.5", "sec-7-5"),
        (f"{k['til'][0]:.1f} %", f"de los ocupados está en empleo informal: de {D.mn_til['til1_est']:.0f} % ({D.mn_til['entidad']}) a {D.mx_til['til1_est']:.0f} % ({D.mx_til['entidad']}), y baja de {D.R['til1']['por_nivel']['1']:.0f} % a {D.R['til1']['por_nivel']['4']:.0f} % con la escolaridad", "7.10", "sec-7-10"),
    ]
    items = "".join(f'<a class="clave" href="#{h}"><b>{v}</b><span>{t}</span><em>Sección {s}</em></a>' for v, t, s, h in tarjetas)
    return f'<section class="prelim prelim--ancho" id="hallazgos"><h2 class="prelim-t">Hallazgos clave</h2><div class="clave-grid">{items}</div><p class="peq nota-pie">Cada tarjeta lleva a la sección donde se explica el resultado. Todos son asociaciones, no efectos causales.</p></section>'


def ficha_tecnica(D, d: dict) -> str:
    R, m = D.R, D.meta
    filas = [
        ("Fuente", "INEGI, Encuesta Nacional de Ocupación y Empleo (ENOE), 4.º trimestre de 2025; tablas SDEMT y COE2T (microdatos públicos)"),
        ("Datos", f"{n_es(d['n']['registros'])} registros; universo de estudio: {n_es(D.n_u)} personas ocupadas de 15 años o más; muestra salarial: {n_es(D.n_s)} personas ({R['muestras']['salarial_poblacion_millones']:.1f} millones ponderadas)"),
        ("Diseño muestral", f"{m['n_estratos_originales']} estratos ({m['n_estratos_colapsados']} tras fusionar los de una sola UPM) y {n_es(m['n_upm'])} UPM; efecto de diseño de {d['k']['deff']:.1f} en la tasa de informalidad"),
        ("Inferencia", f"Bootstrap de Rao-Wu con {R['B']:,} réplicas y una sola semilla ({m['semilla']}); intervalos de confianza del 95 %; errores de diseño por linealización de Taylor en los modelos"),
        ("Almacenamiento", f"SQLite con esquema en estrella (fact_ocupado: {n_es(D.n_u)} filas × {D.n_cols_fact} columnas y 10 dimensiones) y MongoDB (32 documentos de entidad; carga probada con mongomock)"),
        ("Calidad", f"15 expectativas de datos cumplidas, {D.n_pruebas} pruebas automáticas y 30 tablas de resultados idénticas en dos corridas"),
        ("Programas", f"Python {m['python']} · pandas {m['pandas']} · NumPy {m['numpy']} · SQLite {m['sqlite']}"),
        ("Código", f'<a href="{REPO}" rel="noopener">{REPO.removeprefix("https://")}</a>'),
    ]
    cuerpo = "".join(f"<div><dt>{e(a)}</dt><dd>{b if a == 'Código' else e(b)}</dd></div>" for a, b in filas)
    return f'<section class="prelim" id="ficha"><h2 class="prelim-t">Ficha técnica</h2><dl class="ficha-t">{cuerpo}</dl></section>'


def rutas_lectura() -> str:
    rutas = [("5 minutos", "Lo esencial", "Resumen, hallazgos clave y conclusiones.", [("resumen", "Resumen"), ("hallazgos", "Hallazgos"), ("cap-9", "Conclusiones")]),
             ("20 minutos", "Método y resultados", "Cómo se midió y qué se encontró, sin el marco conceptual ni la ingeniería.", [("cap-6", "Metodología"), ("cap-7", "Resultados"), ("cap-8", "Discusión")]),
             ("Lectura completa", "Todo el documento", "Los nueve capítulos, la bibliografía y los anexos.", [("cap-1", "Introducción"), ("cap-2", "Marco conceptual"), ("anexo-c", "Resultados por entidad")]),
             ("18 minutos", "Presentación breve", "La ruta corta, diapositiva por diapositiva, con el guion de quien expone y un reloj.", None)]
    tarjetas = "".join(f'<div class="ruta"><p class="ruta__t">{e(t)}</p><p class="ruta__n">{e(n)}</p><p class="ruta__d">{e(d)}</p><p class="ruta__l">'
                       + (" · ".join(f'<a href="#{i}">{e(x)}</a>' for i, x in enlaces) if enlaces else '<button type="button" class="btn btn--chico" data-abrir-pres>Iniciar la presentación</button>') + "</p></div>" for t, n, d, enlaces in rutas)
    return f'<section class="prelim prelim--ancho" id="rutas"><h2 class="prelim-t">Rutas de lectura</h2><div class="rutas">{tarjetas}</div></section>'


def como_citar() -> str:
    cita = (f"Culin Grajeda, J. E., Garcia Jara, A. Y., y Gutierrez Zuñiga, L. A. (2026). {TITULO}: escolaridad, ingreso y brecha de género [Tesina del Proyecto Integrador de Ciencia de Datos]. "
            f"Universidad de Especialidades UNE, Plantel Centro. {URL}")
    return (f'<section class="prelim" id="citar"><h2 class="prelim-t">Cómo citar</h2><div class="cita-caja"><p id="cita-texto">{e(cita)}</p>'
            '<button type="button" class="btn btn--chico" id="btn-copiar-cita">Copiar cita</button></div></section>')


def indice_general(res: dict) -> str:
    capitulos = [c for c in res["capitulos"]]

    def item(c: dict) -> str:
        subs = "".join(f'<li><a href="#{i}"><span class="n">{n}</span><span class="t">{md(t)}</span></a></li>' for i, n, t in c["secciones"])
        num = c["num"] if c["tipo"] != "otro" else ""
        etq = f'<span class="n">{e(c["num"]) if c["tipo"] == "capitulo" else ("Anexo " + c["num"] if c["tipo"] == "anexo" else "")}</span>'
        return (f'<li class="toc-cap"><a href="#{c["id"]}">{etq}<span class="t">{md(c["titulo"])}</span><span class="m">{c["minutos"]} min</span></a>' + (f"<ol>{subs}</ol>" if subs else "") + "</li>")

    figs = "".join(f'<li><a href="#{f["id"]}"><span class="n">Figura {f["n"]}</span><span class="t">{e(f["pie"])}</span></a></li>' for f in res["figuras"])
    tabs = "".join(f'<li><a href="#{t["id"]}"><span class="n">Tabla {t["n"]}</span><span class="t">{e(t["pie"])}</span></a></li>' for t in res["tablas"])
    return (f'<section class="prelim prelim--ancho" id="indice-general"><h2 class="prelim-t">Índice general</h2><ol class="toc-gen">{"".join(item(c) for c in capitulos)}</ol>'
            f'<details class="listas"><summary>Índice de figuras ({len(res["figuras"])})</summary><ol class="toc-lista">{figs}</ol></details>'
            f'<details class="listas"><summary>Índice de tablas ({len(res["tablas"])})</summary><ol class="toc-lista">{tabs}</ol></details></section>')


def indice_lateral(res: dict) -> str:
    pre = [("resumen", "Resumen"), ("abstract", "Abstract"), ("hallazgos", "Hallazgos clave"), ("ficha", "Ficha técnica"), ("rutas", "Rutas de lectura"), ("indice-general", "Índice general")]
    out = ['<nav class="indice" id="indice" aria-label="Índice de la tesina"><div class="indice__cab"><p class="indice__tit">Contenido</p><button type="button" class="btn-ic indice__cerrar" id="btn-cerrar-indice" aria-label="Cerrar el índice">×</button></div>'
           '<button type="button" class="indice__pres" data-abrir-pres>Presentación breve · 18 min</button>'
           '<label class="indice__ent">Resaltar una entidad<select class="sel" data-sel-estado aria-label="Resaltar una entidad en todas las figuras interactivas"></select></label>'
           '<ol class="indice__lista"><li class="grupo">Preliminares</li>' + "".join(f'<li class="pre"><a href="#{i}" data-id="{i}">{e(t)}</a></li>' for i, t in pre)]
    previo = None
    for c in res["capitulos"]:
        grupo = "Anexos" if c["tipo"] == "anexo" else ("Cuerpo" if c["tipo"] == "capitulo" else None)
        if grupo and grupo != previo:
            out.append(f'<li class="grupo">{"Capítulos" if grupo == "Cuerpo" else "Anexos"}</li>')
            previo = grupo
        num = c["num"] if c["tipo"] == "capitulo" else ("Anexo " + c["num"] if c["tipo"] == "anexo" else "")
        subs = "".join(f'<li><a href="#{i}" data-id="{i}"><span class="n">{n}</span>{md(t)}</a></li>' for i, n, t in c["secciones"])
        out.append(f'<li class="cap" data-cap="{c["id"]}"><a href="#{c["id"]}" data-id="{c["id"]}"><span class="n">{e(num)}</span>{md(c["titulo"])}</a>' + (f'<ol class="subs">{subs}</ol>' if subs else "") + "</li>")
    out.append("</ol>"
               '<div class="indice__enlaces"><p class="grupo">Otras versiones</p><a href="presentacion.html">Presentación interactiva (11 láminas)</a><a href="estudio.html">Guía de estudio</a><a href="cuaderno.html">Cuaderno</a><a href="tablero.html">Tablero</a>'
               '<a href="descargas/Informe_Final_Proyecto_ENOE.pdf">Informe técnico (PDF)</a><a href="descargas/Presentacion_Completa_Proyecto_ENOE.pdf" title="Presentación completa: 48 diapositivas con guion">Presentación (PDF)</a>'
               '<a href="descargas/Proyecto_Integrador_ENOE.pdf" title="Presentación corta: 24 diapositivas (18 principales y 5 de respaldo)">presentacion2 (PDF)</a>'
               f'<a href="{REPO}" rel="noopener">Código en GitHub</a></div></nav>')
    return "".join(out)


def pie_pagina() -> str:
    enlaces = [("Presentación interactiva (11 láminas)", "presentacion.html"), ("Guía de estudio", "estudio.html"), ("Cuaderno", "cuaderno.html"), ("Tablero", "tablero.html"),
               ("Informe técnico (PDF)", "descargas/Informe_Final_Proyecto_ENOE.pdf"), ("Código", REPO)]
    return (f'<footer class="pie"><p>Proyecto Integrador de Ciencia de Datos · Equipo 1 ({", ".join(AUTORES)}) · Universidad de Especialidades UNE, Plantel Centro · Octubre de 2026.</p>'
            '<p>Datos: INEGI, Encuesta Nacional de Ocupación y Empleo, 4.º trimestre de 2025 (microdatos públicos). Material académico: los resultados son asociaciones y no efectos causales.</p>'
            '<ul class="pie__enlaces">' + "".join(f'<li><a href="{h}">{t}</a></li>' for t, h in enlaces) + "</ul></footer>")


def barra() -> str:
    return (f'<header class="barra" id="barra"><button type="button" class="btn-ic btn-indice" id="btn-indice" aria-label="Abrir el índice" aria-controls="indice" aria-expanded="false">{icono("menu")}</button>'
            f'<a class="marca" href="#portada">{e(TITULO)}<small>Tesina · ENOE 2025-T4</small></a><p class="miga" id="miga"></p>'
            '<div class="barra__acc"><span class="estado-chip" id="chip-estado"><span></span><button type="button" aria-label="Quitar la entidad elegida">×</button></span>'
            '<select class="sel sel--barra" id="sel-estado" data-sel-estado aria-label="Resaltar una entidad en todas las figuras interactivas"></select>'
            f'<button type="button" class="btn-ic btn-pres" data-abrir-pres title="Presentación breve: ruta corta de 18 diapositivas (tecla P)">{icono("pres")}<span>Presentar</span></button>'
            f'<button type="button" class="btn-ic" id="btn-buscar" aria-label="Buscar en la tesina (tecla /)">{icono("buscar")}<span>Buscar</span></button>'
            f'<button type="button" class="btn-ic" id="btn-tema" aria-label="Cambiar entre tema claro y oscuro">{icono("tema")}<span>Tema</span></button></div>'
            '<div class="progreso" aria-hidden="true"><i id="progreso"></i></div></header>')


def extras(D, d: dict) -> str:
    return (ruta_corta_html(D, d) + '<div class="dock" id="dock" hidden role="status" aria-live="polite"></div>'
            '<div class="buscador" id="buscador" hidden role="dialog" aria-modal="true" aria-label="Buscar en la tesina"><div class="buscador__caja">'
            '<input type="search" id="buscar-texto" placeholder="Buscar en la tesina (por ejemplo: Rao-Wu, informalidad, brecha…)" autocomplete="off" aria-label="Texto que se busca">'
            '<ol id="buscar-res" aria-live="polite"></ol><p class="buscador__pie">Enter abre el primer resultado · Esc cierra</p></div></div>'
            '<div class="visor" id="visor" hidden role="dialog" aria-modal="true" aria-label="Figura ampliada"><button type="button" class="btn btn--chico" id="visor-cerrar">Cerrar</button>'
            '<img id="visor-img" alt=""><p id="visor-pie"></p></div>'
            f'<button type="button" class="arriba" id="arriba" aria-label="Volver al inicio" hidden>{icono("flecha")}</button>')


# --------------------------------------------------------------------------- #
# componentes interactivos que se insertan en el texto
# --------------------------------------------------------------------------- #
CALCULADORA = ('<aside class="interactivo" id="calculadora"><p class="interactivo__tit">Interactivo · ¿Cuánto sube el ingreso por hora con más estudios?</p>'
               '<label for="calc-rango">Años adicionales de estudio: <output id="calc-n">4</output></label><input id="calc-rango" type="range" min="1" max="12" value="4" aria-describedby="calc-ic">'
               '<p class="calc__res"><output id="calc-res" aria-live="polite"></output></p><p class="calc__nota" id="calc-ic"></p></aside>')

EXPLORADOR = ('<aside class="interactivo" id="explorador"><p class="interactivo__tit">Interactivo · La misma consulta en SQL y en MongoDB</p>'
              '<label for="sel-ficha">Entidad <select class="sel" id="sel-ficha"></select></label>'
              '<div class="ficha"><div><p class="caja-tit">SQL · SQLite</p><div class="codigo"><pre><code id="ficha-sql"></code></pre></div><p class="res-sql" id="ficha-res"></p></div>'
              '<div><p class="caja-tit">MongoDB · colección entidades</p><div class="codigo"><pre><code id="ficha-mongo"></code></pre></div></div></div>'
              '<p class="calc__nota">Los dos motores devuelven el mismo dato: la ficha de la entidad. En el documento de MongoDB los indicadores van anidados y se leen con una sola operación.</p></aside>')


def construir(D, d: dict) -> tuple[str, dict]:
    inf = InformeHTML(viz=VIZ, alts=ALT, porque=PORQUE, ecuaciones=ECUACIONES, img_dir=SITIO / "img", ganchos=[
        ("tabla", "Rendimiento por año de escolaridad según el modelo", CALCULADORA),
        ("tabla", "Consultas equivalentes", EXPLORADOR),
    ])
    s1.resumen(inf, D)
    s1.seccion1(inf, D)
    s1.seccion2(inf, D)
    s1.seccion3(inf, D)
    s2.seccion4(inf, D)
    s2.seccion5(inf, D)
    s3.seccion6(inf, D)
    s3.seccion7(inf, D)
    s4.seccion8(inf, D)
    s4.seccion9(inf, D)
    s4.anexo_referencias(inf, "Referencias")
    s4.anexo_glosario(inf, D)
    s4.anexo_guia(inf, D)
    s4.anexo_entidades(inf, D)
    s4.anexo_defensa(inf, D)
    res = inf.finalizar()

    # --- glosario: términos -> id (para las definiciones emergentes)
    glos = {t: "gl-" + slug(t) for t, _ in s4.GLOSARIO}
    faltan = [c for _, c in TERMINOS if c not in glos]
    assert not faltan, f"términos sin definición en el glosario: {faltan}"
    ids = {i for c in res["capitulos"] for i in re.findall(r' id="([^"]+)"', c["html"])}
    for c in res["capitulos"]:
        h = enlazar_secciones(c["html"], ids)
        h = enlazar_citas(h, ids, res["refs"])
        h = unir_porcentajes(h)
        if c["id"] not in ("anexo-a", "referencias"):
            h = marcar_terminos(h, glos)
        c["html"] = h

    # --- navegación entre capítulos
    seq = res["capitulos"]
    for i, c in enumerate(seq):
        ant = seq[i - 1] if i else None
        sig = seq[i + 1] if i + 1 < len(seq) else None
        nombre = lambda x: ((x["etq"] + ". ") if x["tipo"] == "capitulo" else (x["etq"] + ". " if x["tipo"] == "anexo" else "")) + re.sub(r"\*", "", x["titulo"])
        nav = ('<nav class="cap-nav" aria-label="Navegación entre capítulos">' + (f'<a class="ant" href="#{ant["id"]}"><small>Anterior</small>{e(nombre(ant))}</a>' if ant else "<span></span>")
               + (f'<a class="sig" href="#{sig["id"]}"><small>Siguiente</small>{e(nombre(sig))}</a>' if sig else '<a class="sig" href="#portada"><small>Fin</small>Volver al inicio</a>') + "</nav>")
        c["html"] = c["html"][:-len("</section>")] + nav + "</section>"
    return "".join(c["html"] for c in res["capitulos"]), res


def pagina(cuerpo: str, res: dict, datos_json: str, css: str, js: str, fragmento: bool, D, d: dict) -> str:
    prelim = {p["id"]: p for p in res["prelim"]}
    resumen = f'<section class="prelim" id="resumen"><h2 class="prelim-t">Resumen</h2>{prelim["resumen"]["html"]}</section>'
    k = d["k"]
    principal = (resumen + resumen_ingles(D, k) + hallazgos(d, D) + ficha_tecnica(D, d) + rutas_lectura() + como_citar() + indice_general(res) + cuerpo + pie_pagina())
    aviso = '<noscript><p class="aviso-js">Las figuras interactivas necesitan JavaScript; sin él se muestran como imágenes. El texto y las tablas se leen igual.</p></noscript>'
    app = (f'<a class="saltar" href="#contenido">Saltar al contenido</a>{barra()}{portada(d, D)}<div class="marco">{indice_lateral(res)}'
           f'<main id="contenido" class="tesina">{aviso}{principal}</main></div>{extras(D, d)}')
    datos = f'<script type="application/json" id="datos">{datos_json}</script>'
    if fragmento:
        return f'<title>{e(TITULO)}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n{FUENTES}\n<style>\n{css}\n</style>\n{app}\n{datos}\n<script>\n{js}\n</script>\n'
    meta = (f'<meta name="description" content="Tesina del Proyecto Integrador de Ciencia de Datos: cuánto rinde estudiar en México, brecha salarial de género e informalidad laboral con la ENOE 2025-T4 del INEGI.">\n'
            f'<meta name="author" content="{e(", ".join(AUTORES))}">\n<meta name="citation_title" content="{e(TITULO)}">\n'
            + "".join(f'<meta name="citation_author" content="{e(a)}">\n' for a in AUTORES)
            + '<meta name="citation_publication_date" content="2026/10">\n<meta property="og:type" content="article">\n'
            f'<meta property="og:title" content="{e(TITULO)}">\n<meta property="og:description" content="{e(SUBTITULO)}">\n<meta name="theme-color" content="#1e2a6b">\n'
            '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%276%27 fill=%27%231e2a6b%27/%3E%3Cpath d=%27M7 22l5-7 4 4 8-11%27 fill=%27none%27 stroke=%27%23ffd166%27 stroke-width=%273%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27/%3E%3C/svg%3E">\n')
    return (f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>{e(TITULO)}</title>\n{meta}{FUENTES}\n'
            f'<style>\nhtml{{padding:0}}body{{margin:0}}\n{css}\n</style>\n</head>\n<body>\n{app}\n{datos}\n<script>\n{js}\n</script>\n</body>\n</html>\n')


def main() -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(SITIO / "index.html"))
    ap.add_argument("--fragmento", default=None, help="ruta donde escribir la versión sin envoltura de documento")
    a = ap.parse_args()
    if any(not (SITIO / "img" / nombre).exists() for nombre in VIZ):               # las figuras recortadas las prepara build_sitio.py; si faltan, se preparan aquí
        from build_sitio import preparar_imagenes
        preparar_imagenes(SITIO)
    D = cargar()
    d = datos_web(extra=True)
    datos_json = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    leer = lambda nombre: (ASSETS / nombre).read_text(encoding="utf-8-sig")        # utf-8-sig: ignora una marca BOM al inicio, que invalidaría el primer bloque de variables
    css = leer("charts.css") + "\n" + leer("tesina.css")
    js = ("(function () {\n  'use strict';\n  document.documentElement.setAttribute('data-alto-fijo', '');          // las gráficas de la tesina tienen altura fija\n"
          + leer("charts.js") + "\n" + leer("tesina.js") + "\n})();")
    cuerpo, res = construir(D, d)
    destino = Path(a.salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina(cuerpo, res, datos_json, css, js, fragmento=False, D=D, d=d), encoding="utf-8")
    if a.fragmento:
        Path(a.fragmento).write_text(pagina(cuerpo, res, datos_json, css, js, fragmento=True, D=D, d=d), encoding="utf-8")
    palabras = sum(c["palabras"] for c in res["capitulos"])
    print(f"Tesina escrita en {destino} ({destino.stat().st_size / 1e3:.0f} KB; {len(res['capitulos'])} capítulos y anexos, {len(res['figuras'])} figuras, {len(res['tablas'])} tablas, ≈ {palabras:,} palabras)")
    return destino


if __name__ == "__main__":
    main()
