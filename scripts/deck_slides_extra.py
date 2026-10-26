"""Diapositivas nuevas de la presentación completa: explican los conceptos, el proceso de limpieza, la ingeniería de datos y la estadística.

Cada función construye una diapositiva en el Deck recibido (ver build_deck_completa.py para el orden). Las cifras salen de results/.
"""
from __future__ import annotations

import json

import numpy as np
from pptx.oxml.ns import qn

from deck_lib import *  # noqa: F401,F403

# ------------------------------- cifras adicionales ------------------------------- #
meta = json.loads((RES / "etl_meta.json").read_text(encoding="utf-8"))
imp = leer("etl_imputacion_rangos")
chi = leer("calidad_ingreso_chi2").set_index("variable")
lg = leer("no_respuesta_logit").set_index(["modelo", "variable"])
ex = leer("etl_expectativas")
rmod = leer("retorno_modelos")
sg = leer("brecha_subgrupos")
tc = leer("tests_clasicos").set_index("nivel")
dg = R["diagnosticos"]
ambar = "FFF7E6"
BLOQUES = {"A": "A · Apertura", "B": "B · Datos y diseño muestral", "C": "C · Limpieza de datos", "D": "D · Ingeniería de datos", "E": "E · Estadística explicada",
           "F1": "F1 · Escolaridad e ingreso", "F2": "F2 · Brecha de género", "F3": "F3 · Informalidad, tablero y diagnóstico", "G": "G · Cierre", "H": "H · Respaldo"}
PRESENTA = {"A": "Juan Evelio", "B": "Juan Evelio", "C": "Angel Yireh", "D": "Angel Yireh", "E": "Luis Andre", "F1": "Luis Andre", "F2": "Angel Yireh", "F3": "Luis Andre", "G": "Juan Evelio"}
MINUTOS = {"A": 5, "B": 5, "C": 7, "D": 6, "E": 7, "F1": 4, "F2": 6, "F3": 5, "G": 4}
MIN_CORTA = {"A": 2, "B": 2, "C": 2, "D": 1, "E": 2, "F1": 3, "F2": 3, "F3": 1, "G": 2}


def circulo_texto(s, x, y, dia, texto, nombre, size=14, fondo=TC.ACCENT_1):
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(dia), Inches(dia))
    c.name = nombre
    c.shadow.inherit = False
    c.line.fill.background()
    c.fill.solid()
    color(c.fill.fore_color, fondo)
    texto_en_forma(c, [[(texto, {"size": size, "bold": True, "spec": TC.BACKGROUND_1})]], margen=0, espacio=0)
    return c


def lectura(s, x, y, w, h, nombre, items, size=15, titulo_txt=None, vinetas=False, fondo=TC.BACKGROUND_2, espacio=8):
    """Tarjeta con texto (y título opcional) alineado a la izquierda."""
    tarjeta(s, x, y, w, h, nombre, fondo)
    _, tf = caja(s, x + 0.22, y + 0.12, w - 0.44, h - 0.24, nombre + " texto", MSO_ANCHOR.MIDDLE)
    filas = []
    if titulo_txt:
        filas.append([(titulo_txt, {"size": size + 3, "bold": True, "spec": TC.TEXT_2})])
    filas += items
    parrafos(tf, filas, size=size, espacio=espacio, vinetas=False)
    if vinetas:
        for p in list(tf.paragraphs)[1 if titulo_txt else 0:]:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(Inches(0.25)))
            pPr.set("indent", str(-Inches(0.25)))
            bu = etree.SubElement(pPr, "{%s}buChar" % NS["a"])
            bu.set("char", "•")


# =========================================================================== #
# A. Apertura
# =========================================================================== #
def s_agenda(d):
    s = d.nueva("Qué vamos a ver: nueve bloques y dos rutas", (
        "Esta presentación tiene dos versiones. La ruta corta son las 18 diapositivas con la marca de estrella, unos dieciocho minutos: portada, pregunta, ciclo KDD, validación, ingreso cero, embudo, arquitectura, diseño muestral, "
        "los cinco resultados principales, informalidad, conclusiones, límites y cierre. La ruta completa explica además cada concepto y cada decisión: qué es la encuesta, cómo se limpió, cómo se guardó, cómo se calcula cada estadístico y cómo se lee. "
        "El reparto de la exposición está en la tabla: Juan Evelio abre y cierra, Angel Yireh presenta la limpieza, la ingeniería de datos y la brecha de género, y Luis Andre presenta la estadística y los demás resultados."))
    orden = ["A", "B", "C", "D", "E", "F1", "F2", "F3", "G"]
    descr = {"A": "La pregunta, los objetivos y el ciclo KDD", "B": "La ENOE, el diseño muestral y la validación con cifras oficiales", "C": "Cobertura, faltantes, ingreso cero, imputación y atípicos",
             "D": "Arquitectura, esquema en estrella, SQL y MongoDB, reproducibilidad", "E": "Rao-Wu, intervalos, Spearman, Mincer, brecha y Holm", "F1": "Rendimiento de la escolaridad y ranking de entidades",
             "F2": "Brecha por hora y por mes, Oaxaca-Blinder, distribución y robustez", "F3": "Informalidad, tablero y diagnóstico del modelo", "G": "Síntesis, métricas de éxito, límites y cierre"}
    tarjeta(s, M, 1.62, 8.15, 5.2, "Agenda", fondo=TC.BACKGROUND_2)
    for i, k in enumerate(orden):
        y = 1.72 + i * 0.565
        circulo_texto(s, M + 0.18, y + 0.02, 0.46, k, f"Bloque {k}", size=13 if len(k) == 1 else 12)
        _, tf = caja(s, M + 0.8, y, 5.4, 0.52, f"Bloque {k} texto", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [[(BLOQUES[k].split(" · ", 1)[1] + "  ", {"size": 14, "bold": True, "spec": TC.TEXT_2}), (descr[k], {"size": 12, "spec": RGB["muted"]})]], espacio=0)
        _, tf = caja(s, M + 6.35, y, 1.7, 0.52, f"Bloque {k} presenta", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [[(PRESENTA[k], {"size": 12, "bold": True}), (f"  {MINUTOS[k]} min", {"size": 12, "spec": RGB["muted"]})]], espacio=0, alinear=PP_ALIGN.RIGHT)
    estadistica(s, 9.0, 1.62, 3.73, 1.7, "★ 18", "diapositivas de la ruta corta (≈ 18 min)", "Ruta corta", vsize=40, lsize=14, fondo=TC.TEXT_2, vspec=TC.BACKGROUND_1, lspec=TC.BACKGROUND_1)
    estadistica(s, 9.0, 3.47, 3.73, 1.7, "48", "diapositivas de la ruta completa (≈ 50 min)", "Ruta completa", vsize=40, lsize=14)
    lectura(s, 9.0, 5.32, 3.73, 1.5, "Notas", [[("El guion de cada diapositiva está en las ", {"size": 14}), ("notas del orador", {"size": 14, "bold": True}), (". Al final: glosario y preguntas de respaldo.", {"size": 14})]], size=14)


def s_por_que_importa(d):
    s = d.nueva("Por qué importa: educación, informalidad e igualdad de género", (
        "El contexto de la pregunta. La educación se considera la principal vía de movilidad social, pero el mercado laboral mexicano combina una informalidad muy alta con diferencias persistentes entre regiones y entre mujeres y hombres. "
        f"En el cuarto trimestre de 2025 hay {R['muestras']['ocupados_millones']:.1f} millones de personas ocupadas y {til1['nacional']['est']:.0f} de cada cien están en un empleo informal. "
        "Saber cuánto paga un año de estudio, si ese pago es parejo en el país y si mujeres y hombres con la misma preparación reciben lo mismo orienta decisiones de política educativa, laboral y de igualdad. "
        "La fuente es la ENOE del INEGI, la principal encuesta del mercado laboral, con microdatos públicos."))
    tarjetas = [(f"{R['muestras']['ocupados_millones']:.1f} M", "personas ocupadas de 15 años y más", "Educación: ¿cuánto rinde estudiar un año más?", "La escolaridad es la principal vía de movilidad social: ¿cuánto se paga cada año de estudio y cambia por entidad?"),
                (f"{til1['nacional']['est']:.0f} %", "de las personas ocupadas está en un empleo informal", "Informalidad: ¿dónde y para quién?", "La mitad del empleo carece de protección laboral formal; varía de 33 % a 80 % según la entidad."),
                (f"{bn.loc['Total', 'part_mujeres_pct']:.0f} %", "de la muestra salarial son mujeres", "Igualdad: ¿ganan lo mismo mujeres y hombres?", "Comparar a personas con la misma escolaridad separa la diferencia de preparación de la diferencia de pago.")]
    for i, (v, l, h, t) in enumerate(tarjetas):
        x = M + i * 4.1
        estadistica(s, x, 1.7, 3.95, 1.75, v, l, f"Dato {i + 1}", vsize=44, lsize=14)
        lectura(s, x, 3.6, 3.95, 2.25, f"Pregunta {i + 1}", [[(t, {"size": 14})]], size=14, titulo_txt=h)
    tarjeta(s, M, 6.05, 12.13, 0.75, "Mensaje", fondo=TC.TEXT_2)
    _, tf = caja(s, M + 0.3, 6.1, 11.5, 0.65, "Mensaje texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[("Fuente: ", {"size": 15, "bold": True, "spec": TC.BACKGROUND_1}), ("Encuesta Nacional de Ocupación y Empleo (ENOE) del INEGI, 4.º trimestre de 2025: microdatos públicos y anonimizados.", {"size": 15, "spec": TC.BACKGROUND_1})]], espacio=0)


# =========================================================================== #
# B. Datos y diseño muestral
# =========================================================================== #
def s_enoe(d):
    s = d.nueva("La ENOE: la encuesta que mide el mercado laboral de México", (
        "La Encuesta Nacional de Ocupación y Empleo es una encuesta continua del INEGI: cada trimestre se entrevista a cientos de miles de personas en viviendas de todo el país. "
        "Cada vivienda se entrevista hasta cinco veces consecutivas, que es el panel rotativo. El INEGI publica los microdatos en cinco tablas; nosotros usamos dos. "
        f"SDEMT trae una fila por persona, {419038:,} en este trimestre y 115 columnas, de las que leemos 35: sociodemográficas, laborales, el ponderador y el diseño muestral. "
        "COE2T trae el detalle de cómo se captó el ingreso, que nos permite entender qué significa el ingreso cero. Las unimos con una llave de once campos que verificamos que es única; la unión es uno a uno y el proceso se detiene si una persona ocupada no encuentra pareja."))
    lectura(s, M, 1.65, 5.55, 3.65, "Qué es la ENOE", [
        "Encuesta continua del INEGI en viviendas de todo el país",
        "Panel rotativo: cada vivienda se entrevista hasta 5 veces seguidas",
        "Microdatos públicos y anonimizados, en 5 tablas CSV (latin-1)",
        "Cada fila de SDEMT es una persona; fac_tri dice a cuántas personas representa"], size=15, titulo_txt="Qué es", vinetas=True)
    filas = [["SDEMT", "Sociodemográfica y laboral: una fila por persona", "Sí · 35 de 115 columnas"], ["COE2T", "Ocupación y empleo (parte 2): captación del ingreso", "Sí · 14 columnas"],
             ["COE1T", "Ocupación y empleo (parte 1)", "No"], ["HOGT", "Hogares", "No"], ["VIVT", "Viviendas", "No"]]
    tabla_nativa(s, 6.35, 1.65, [1.0, 3.55, 1.83], ["Tabla", "Contenido", "¿Se usa?"], filas, "Tablas de la ENOE", size=13, alto_fila=0.6, alinear=[PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.LEFT], negrita_col0=True, resaltar=(0, 1))
    for i, (v, l) in enumerate([("419,038", "personas en SDEMT"), ("344,166", "filas en COE2T"), (f"{n_u:,}", "ocupados unidos 1 a 1")]):
        estadistica(s, M + i * 4.1, 5.5, 3.95, 1.3, v, l, f"Dato {i + 1}", vsize=34, lsize=14)


def s_diseno_muestral(d):
    s = d.nueva("El diseño muestral: por qué cada persona pesa distinto", (
        "La ENOE no es una muestra aleatoria simple: sería carísimo recorrer el país. Es un diseño bietápico, estratificado y por conglomerados. Primero se agrupan áreas parecidas en estratos, hay 724; luego se sortean unidades primarias de muestreo, 21,194 en este trimestre, que son conjuntos de viviendas; "
        "dentro se eligen viviendas y personas. Cada persona trae un factor de expansión, fac_tri, que indica a cuántas personas de la población representa: la suma es 131 millones, la población del país, y la de los ocupados de 15 años y más es 59.8 millones. "
        f"Por eso todo está ponderado. Y como las personas de una misma unidad se parecen entre sí, el efecto de diseño es {deff.loc['TIL1 nacional', 'deff']:.1f}: los {n_u / 1000:.0f} mil ocupados valen como unos {deff.loc['TIL1 nacional', 'n_efectivo'] / 1000:.0f} mil independientes."))
    imagen(s, "D04_diseno_muestral.png", M, 1.62, 8.5, 3.55, "Diagrama de los niveles del diseño muestral: estrato, unidad primaria de muestreo, vivienda y persona, y el significado del factor de expansión")
    estadistica(s, 9.35, 1.65, 3.38, 1.05, "724 → 713", "estratos (11 fusionados)", "Estratos", vsize=28, lsize=13)
    estadistica(s, 9.35, 2.85, 3.38, 1.05, "21,194", "unidades primarias de muestreo", "UPM", vsize=28, lsize=13)
    estadistica(s, 9.35, 4.05, 3.38, 1.05, "131.0 M", "suma de fac_tri = población del país", "Factor de expansión", vsize=28, lsize=13)
    lectura(s, M, 5.35, 6.0, 1.45, "Ponderar", [[("Ponderar: ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("un promedio sin ponderar describiría a la muestra, no al país.", {"size": 15})]], size=15)
    lectura(s, 6.73, 5.35, 6.0, 1.45, "Efecto de diseño", [[("Efecto de diseño ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), (f"{deff.loc['TIL1 nacional', 'deff']:.1f}: ", {"size": 15, "bold": True}), (f"{n_u / 1000:.0f} mil ocupados equivalen a unos {deff.loc['TIL1 nacional', 'n_efectivo'] / 1000:.0f} mil independientes.", {"size": 15})]], size=15)


# =========================================================================== #
# C. Limpieza
# =========================================================================== #
def s_cobertura(d):
    s = d.nueva("La cobertura define el universo: cinco reglas, 190,187 personas", (
        "La limpieza empieza por definir a quién estudiamos. Partimos de 419,038 registros de la tabla SDEMT y aplicamos cinco reglas de cobertura, una por una, cada una registrada en una bitácora con cuántos registros quedaban antes y después. "
        "Primero, entrevista completa. Segundo, residente habitual: se excluyen los nuevos residentes, que no traen sexo ni edad. Tercero, 15 años o más con edad especificada; esto es lo que hace coincidir el proyecto con la definición oficial. "
        "Cuarto, personas ocupadas. Quinto, ponderador positivo: es una verificación y no excluye a nadie. El resultado son 190,187 personas ocupadas, el universo de estudio. "
        "El principio rector es marcar y no borrar: solo la cobertura elimina filas; los faltantes, la calidad del ingreso y los atípicos crean banderas."))
    reglas = [("L1", "Entrevista completa", "Entrevistas incompletas (r_def ≠ 0)"), ("L2", "Residente habitual", "Nuevos residentes (c_res = 2), sin sexo ni edad"),
              ("L3", "Edad de 15 a 98 años", "Menores de 15 años y edad no especificada"), ("L4", "Población ocupada", "Personas no ocupadas (clase2 ≠ 1)"), ("L5", "Ponderador positivo", "Nadie: es una verificación")]
    filas = [["L0", "Registros crudos de SDEMT", "—", f"{int(bit.loc['L0', 'n_antes']):,}", f"{int(bit.loc['L0', 'n_despues']):,}", "0"]]
    for k, a, b in reglas:
        filas.append([k, a, b, f"{int(bit.loc[k, 'n_antes']):,}", f"{int(bit.loc[k, 'n_despues']):,}", f"{int(bit.loc[k, 'afectados']):,}"])
    tabla_nativa(s, M, 1.65, [0.7, 3.2, 4.6, 1.2, 1.25, 1.18], ["Paso", "Regla", "Quién se excluye", "Antes", "Después", "Excluidos"], filas, "Embudo de cobertura", size=13, alto_fila=0.46,
                 alinear=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT], resaltar=(5,))
    lectura(s, M, 5.15, 7.2, 1.65, "Marcar, no borrar", [[("Marcar, no borrar. ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("Solo la cobertura elimina filas; los faltantes, la calidad del ingreso y los atípicos crean banderas, para cambiar una decisión y rehacer el análisis sin volver a limpiar.", {"size": 15})]], size=15)
    estadistica(s, 8.0, 5.15, 4.73, 1.65, f"{int(bit.loc['L5', 'n_despues']):,}", "personas ocupadas de 15+: el universo de estudio", "Universo", vsize=40, lsize=14, fondo=TC.TEXT_2, vspec=TC.BACKGROUND_1, lspec=TC.BACKGROUND_1)


def s_faltantes(d):
    s = d.nueva("Los faltantes vienen codificados como números reales", (
        "La ENOE no tiene celdas vacías. Un isna diría que todo está completo. Pero los datos desconocidos vienen codificados: 99 años de escolaridad significa que no se especificó, cero horas trabajadas significa que la persona está ocupada pero ausente esa semana, más de 112 horas semanales es una jornada imposible. "
        "Si tratáramos el 99 como un número real, los promedios saldrían absurdos. Por eso cada código se convierte explícitamente en faltante y se registra. "
        f"Son pocos casos: {int(bit.loc['M1', 'afectados'])} escolaridades, {int(bit.loc['M2', 'afectados']):,} jornadas de cero horas, {int(bit.loc['M3', 'afectados'])} jornadas imposibles y {int(bit.loc['M4', 'afectados'])} niveles no especificados. "
        "El caso importante no es este sino el ingreso, que sigue."))
    panel_codigo(s, M, 1.65, 5.6, 1.7, "Código isna", ["df.isna().sum().sum()", "→ 0     # «todo está completo»", "df['anios_esc'].max()", "→ 99    # no especificado"], size=15, titulo_txt="Lo que ve el código")
    lectura(s, 6.4, 1.65, 6.33, 1.7, "Por qué importa", [[("Un 99 tratado como número real distorsionaría los promedios. ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("Cada código se convierte en faltante y se registra; nadie se borra del universo.", {"size": 15})]], size=15)
    filas = [["M1", "anios_esc", "99 = no especificado", f"{int(bit.loc['M1', 'afectados']):,}", "Faltante: no entra al análisis de escolaridad"],
             ["M2", "hrsocup", "0 horas la semana pasada", f"{int(bit.loc['M2', 'afectados']):,}", "Faltante: ocupado pero ausente; no hay ingreso por hora"],
             ["M3", "hrsocup", "> 112 horas semanales", f"{int(bit.loc['M3', 'afectados']):,}", "Faltante: 16 h × 7 días es una jornada imposible"],
             ["M4", "niv_ins", "5 = no especificado", f"{int(bit.loc['M4', 'afectados']):,}", "Se excluye del análisis por nivel de instrucción"]]
    tabla_nativa(s, M, 3.6, [0.8, 1.8, 3.1, 1.2, 5.23], ["Marca", "Variable", "Código", "Registros", "Tratamiento"], filas, "Códigos especiales", size=14, alto_fila=0.52, alto_enc=0.48,
                 alinear=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.LEFT])
    _, tf = caja(s, M, 6.4, 12.13, 0.35, "Nota")
    parrafos(tf, [[("Menos de 3 % del universo en el peor caso (M2): el faltante importante es el del ingreso.", {"size": 13, "spec": RGB["muted"]})]], espacio=0)


def s_no_respuesta(d):
    s = d.nueva("La no respuesta del ingreso no es aleatoria: quien más estudia declara menos", (
        f"Una vez entendido el ingreso cero surge la pregunta de si quienes declaran el monto exacto son un subconjunto aleatorio. No lo son. "
        f"Con una regresión logística de la probabilidad de declarar el monto exacto, cada año de escolaridad reduce {100 * (1 - lg.loc[('A_vs_resto', 'anios_esc'), 'razon_momios']):.1f} por ciento los momios, y la proporción baja de {A_n1:.0f} a {A_n4:.0f} por ciento del nivel más bajo al más alto. "
        f"Los empleadores y los trabajadores por cuenta propia declaran menos, y las mujeres más. Las pruebas ji cuadrada confirman la asociación con la posición en la ocupación, V de Cramér {chi.loc['posición', 'v_cramer']:.2f}, y con la informalidad, {chi.loc['informalidad', 'v_cramer']:.2f}. "
        "La consecuencia es que la muestra salarial subrepresenta a los más escolarizados. Por eso cada resultado clave se contrasta con imputación por rangos, ponderación inversa y solo asalariados."))
    cats = [("Mujer", "mujer"), ("+1 año de escolaridad", "anios_esc"), ("Empleo informal", "informal"), ("Empleador", "pos_empleador"), ("Cuenta propia", "pos_cuenta_propia")]
    vals = [100 * (lg.loc[("A_vs_resto", v), "razon_momios"] - 1) for _, v in cats]
    cd = CategoryChartData()
    cd.categories = [c for c, _ in cats][::-1]
    cd.add_series("Cambio en los momios (%)", [float(v) for v in vals][::-1])
    _, tf = caja(s, M, 1.65, 7.4, 0.4, "Subtítulo de la gráfica")
    parrafos(tf, [[("Cambio en los momios de declarar el monto exacto (%)", {"size": 16, "bold": True, "spec": TC.TEXT_2})]], espacio=0)
    gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(M), Inches(2.1), Inches(7.4), Inches(4.7), cd)
    gf.name = "Gráfica de razones de momios"
    ch = gf.chart
    estilo_grafica(ch)
    ch.has_title = False
    ch.has_legend = False
    eje_valores(ch, '+0"%";"−"0"%"')
    from pptx.enum.chart import XL_TICK_LABEL_POSITION
    ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    pl = ch.plots[0]
    pl.gap_width = 60
    pl.has_data_labels = True
    pl.data_labels.number_format = '+0"%";"−"0"%"'
    pl.data_labels.number_format_is_linked = False
    pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    pl.data_labels.font.size = Pt(15)
    pl.data_labels.font.bold = True
    ser = pl.series[0]
    ser.invert_if_negative = False
    for i, v in enumerate(vals[::-1]):
        pt = ser.points[i]
        pt.format.fill.solid()
        color(pt.format.fill.fore_color, TC.ACCENT_1 if v >= 0 else TC.ACCENT_2)
        dpt = ser._element.get_or_add_dPt_for_point(i)       # sin esto PowerPoint pinta de blanco las barras negativas
        if dpt.find(qn("c:invertIfNegative")) is None:
            inv = etree.SubElement(dpt, qn("c:invertIfNegative"))
            inv.set("val", "0")
            dpt.remove(inv)
            dpt.insert(1, inv)
    estadistica(s, 8.3, 1.65, 4.43, 1.45, f"{A_n1:.0f} % → {A_n4:.0f} %", "declaran el monto exacto: de primaria incompleta a media superior o más", "Gradiente", vsize=32, lsize=13)
    estadistica(s, 8.3, 3.25, 4.43, 1.45, f"V = {chi.loc['posición', 'v_cramer']:.2f}", f"asociación χ² con la posición en la ocupación (informalidad {chi.loc['informalidad', 'v_cramer']:.2f}; nivel {chi.loc['nivel de instrucción', 'v_cramer']:.2f}; sexo {chi.loc['sexo', 'v_cramer']:.2f})", "V de Cramér", vsize=32, lsize=13)
    lectura(s, 8.3, 4.85, 4.43, 1.95, "Consecuencia", [[("Consecuencia: ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("la muestra salarial subrepresenta a los más escolarizados; se contrasta con imputación, IPW y solo asalariados.", {"size": 15})]], size=15)


def s_imputacion(d):
    r4 = imp[imp.p6c == 4].iloc[0]
    s = d.nueva("Imputación por rango: la mediana de quienes sí declararon", (
        "A las personas del grupo B, que solo dieron un rango de salarios mínimos, les asignamos un valor plausible para aprovechar su información en el análisis de sensibilidad. "
        "Calculamos la mediana ponderada de ingreso entre salario mínimo de quienes sí declararon un monto exacto dentro del mismo rango y la multiplicamos por el salario mínimo de la persona. No usamos el punto medio porque dentro del rango hay más personas cerca del límite inferior. "
        f"Ejemplo: alguien de la zona general que dijo entre dos y tres salarios mínimos recibe {r4.razon_mediana_sm:.2f} por 8,364 pesos, es decir {r4.razon_mediana_sm * 8364:,.0f} pesos al mes. "
        "Advertencia: asignar el mismo valor a todos los hombres y mujeres de un rango comprime las diferencias entre ellos y sesga la brecha hacia cero por construcción; por eso solo se usa como sensibilidad, con una muestra ampliada de 145,529 personas."))
    filas = [[r.rango, f"{int(r.n_referencia_A):,}", f"{r.razon_mediana_sm:.2f}", f"{int(r.n_B_imputados):,}"] for r in imp.itertuples()]
    tabla_nativa(s, M, 1.65, [3.0, 2.2, 2.0, 1.8], ["Rango declarado", "Referencia (grupo A)", "Mediana (× SM)", "Personas B"], filas, "Tabla de imputación", size=14, alto_fila=0.5,
                 alinear=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT], resaltar=(3,))
    _, tf = caja(s, M, 5.75, 9.0, 1.1, "Nota de la tabla")
    parrafos(tf, [[("SM = salario mínimo mensual de la zona de la persona. La mediana se usa en lugar del punto medio porque dentro de cada rango hay más personas cerca del límite inferior.", {"size": 13, "spec": RGB["muted"]})]], espacio=0)
    lectura(s, 9.9, 1.65, 2.83, 2.6, "Ejemplo", [[("Ejemplo", {"size": 15, "bold": True, "spec": TC.TEXT_2})], [("«Más de 2 a 3 SM»", {"size": 14})], [(f"{r4.razon_mediana_sm:.2f} × $8,364", {"size": 16, "bold": True})], [(f"= ${r4.razon_mediana_sm * 8364:,.0f} al mes", {"size": 16, "bold": True, "spec": TC.ACCENT_1})]], size=14, espacio=4)
    lectura(s, 9.9, 4.4, 2.83, 2.4, "Advertencia", [[("Sesga hacia cero", {"size": 15, "bold": True, "spec": TC.TEXT_2})], [("Mismo ingreso para hombres y mujeres del rango: solo sensibilidad (145,529 personas).", {"size": 13})]], size=13, fondo=ambar, espacio=4)


def s_atipicos(d):
    s = d.nueva("Atípicos y logaritmo: domar la cola larga del ingreso", (
        f"El ingreso por hora tiene una cola larga: la mayoría gana poco y unos pocos ganan muchísimo. Su asimetría es {R['diagnosticos']['asimetria_ingreso_nivel']:.1f}. Con el logaritmo natural la distribución se vuelve casi simétrica, asimetría {R['diagnosticos']['asimetria_ln_ingreso']:.2f}. "
        "Además, una diferencia de logaritmos es, aproximadamente, una diferencia porcentual: logaritmo de 110 menos logaritmo de 100 es 0.095, casi diez por ciento. "
        f"Para que unas pocas observaciones no dominen, excluimos el 0.5 por ciento más bajo y el 0.5 por ciento más alto del ingreso por hora dentro de cada entidad: {int(bit.loc['O1', 'afectados']):,} observaciones, uno por ciento. "
        "El corte es por entidad para no eliminar sistemáticamente a las entidades ricas o pobres. Probamos que sin recorte la brecha es 3.6 por ciento en lugar de 3.7."))
    imagen(s, "03_distribucion_ingreso.png", M, 1.6, 8.3, 4.15, "Dos histogramas del ingreso por hora: en pesos con cola larga a la derecha y en logaritmo natural casi simétrico", cortar=(0.62, 0.2))
    estadistica(s, 9.1, 1.65, 3.63, 1.45, f"{R['diagnosticos']['asimetria_ingreso_nivel']:.1f} → {R['diagnosticos']['asimetria_ln_ingreso']:.2f}", "asimetría: en pesos → en logaritmo", "Asimetría", vsize=32, lsize=13)
    estadistica(s, 9.1, 3.25, 3.63, 1.45, f"{int(bit.loc['O1', 'afectados']):,}", "atípicos (1.0 %) fuera de P0.5–P99.5 por entidad", "Atípicos", vsize=34, lsize=13)
    estadistica(s, 9.1, 4.85, 3.63, 1.45, "3.6 vs 3.7 %", "brecha sin recorte vs. con recorte", "Sensibilidad", vsize=30, lsize=13)
    lectura(s, M, 5.9, 8.3, 0.95, "Logaritmo", [[("Por qué el logaritmo: ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("una diferencia de logaritmos es una diferencia porcentual: ln(110) − ln(100) = 0.095 ≈ 10 %.", {"size": 15})]], size=15)


def s_quince_pruebas(d):
    s = d.nueva("15 pruebas automáticas de calidad: 15 de 15 cumplidas", (
        "Después de limpiar y transformar, el pipeline verifica quince expectativas sobre la base resultante. Son afirmaciones que deben ser verdaderas si los datos están bien: que la llave de persona es única, que están las 32 entidades, que las edades están entre 15 y 98, que los ponderadores son positivos, "
        "que el ingreso por hora que recalculamos coincide con el del INEGI, que el rango de ingreso de la tabla COE2T reproduce el de SDEMT, entre otras. Catorce son críticas: si una falla, el proceso se detiene con un error en lugar de continuar con datos dudosos. "
        "Es el equivalente de las pruebas unitarias pero aplicadas a los datos. Las quince se cumplen."))
    nombres = [str(e) for e in ex.expectativa]
    corto = {"ing7c consistente con ingocup/salario mínimo": "ing7c consistente con ingocup / salario mínimo", "ing_x_hrs = ingocup / (hrsocup x 4.3)": "ing_x_hrs = ingocup / (hrsocup × 4.3)",
             "p6c (COE2T) reproduce ing7c (SDEMT) en el grupo B": "p6c (COE2T) reproduce ing7c (SDEMT)", "ingocup == p6b2 (COE2T) en el grupo A": "ingocup = p6b2 (COE2T) en el grupo A"}
    ancho, alto = 3.95, 0.72
    for i, (nom, crit) in enumerate(zip(nombres, ex.critica)):
        col, fila = i // 5, i % 5
        x, y = M + col * 4.09, 1.68 + fila * 0.86
        tarjeta(s, x, y, ancho, alto, f"Prueba {i + 1}", TC.BACKGROUND_2)
        circulo_texto(s, x + 0.12, y + 0.14, 0.44, "✓", f"Prueba {i + 1} marca", size=16, fondo=TC.ACCENT_3)
        _, tf = caja(s, x + 0.68, y + 0.04, ancho - 0.78, alto - 0.08, f"Prueba {i + 1} texto", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [[(corto.get(nom, nom), {"size": 13, "bold": False})]], espacio=0)
    tarjeta(s, M, 6.05, 12.13, 0.75, "Mensaje pruebas", fondo=TC.TEXT_2)
    _, tf = caja(s, M + 0.3, 6.1, 11.5, 0.65, "Mensaje pruebas texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[(f"{int(ex.critica.sum())} críticas + {int((~ex.critica).sum())} informativa: ", {"size": 16, "bold": True, "spec": TC.BACKGROUND_1}), ("si una crítica falla, el ETL se detiene en lugar de continuar con datos dudosos.", {"size": 16, "spec": TC.BACKGROUND_1})]], espacio=0)


# =========================================================================== #
# D. Ingeniería de datos
# =========================================================================== #
def s_estrella(d):
    s = d.nueva("Esquema en estrella: una tabla de hechos y diez dimensiones", (
        "El modelo relacional que elegimos es un esquema en estrella. En el centro, la tabla de hechos con una fila por persona ocupada: 190,187 filas y 36 columnas. Alrededor, diez dimensiones pequeñas: entidad, sexo, nivel de instrucción, posición en la ocupación, rama, tamaño de localidad, rangos de ingreso, grupo de ingreso y las unidades primarias de muestreo. "
        "Ventajas: no repetimos textos largos en ciento noventa mil filas, un cambio en una descripción se hace en un solo lugar y las consultas son rápidas y legibles. "
        "Y el propio motor hace cumplir la calidad: llaves primarias, llaves foráneas y restricciones CHECK, como que el ponderador sea positivo o que la edad esté entre 15 y 98. Al cargar verificamos integrity_check igual a ok y cero violaciones de llave foránea."))
    imagen(s, "D03_esquema_estrella.png", M, 1.6, 8.5, 5.2, "Diagrama del esquema en estrella: la tabla de hechos fact_ocupado de 190,187 filas rodeada de diez tablas de dimensiones")
    lectura(s, 9.3, 1.65, 3.43, 5.15, "Qué garantiza", [
        "fact_ocupado: 190,187 filas · 36 columnas",
        "Llaves primarias y foráneas (foreign_keys = ON)",
        "CHECK: fac_tri > 0, eda 15–98, emp_ppal ∈ {1, 2}",
        "5 índices y 4 vistas (TIL1, escolaridad, calidad, muestra salarial)",
        "integrity_check = ok · 0 violaciones de FK"], size=15, titulo_txt="Qué garantiza", vinetas=True)


def s_sql_mongo(d):
    s = d.nueva("La misma pregunta en SQL y en MongoDB", (
        "Para mostrar por qué usamos dos modelos, la misma pregunta en los dos lenguajes: la tasa de informalidad ponderada por entidad. En SQL es una agregación con JOIN y GROUP BY; la ponderación se expresa directamente con la suma de fac_tri por informal. "
        "En MongoDB es un pipeline de agregación con group y project. Verificamos que el resultado de MongoDB, calculado con la misma lógica sobre los documentos exportados, reproduce la vista SQL con una diferencia máxima de cero punto cero cero cinco puntos porcentuales, el redondeo del SQL. "
        "Donde el modelo documental brilla es en servir la ficha completa de una entidad: una sola lectura por clave, sin JOIN. Aclaración honesta: no cargamos a un servidor MongoDB real porque no hay uno instalado; la carga completa se probó con mongomock, un simulador, y los documentos están listos para mongoimport."))
    panel_codigo(s, M, 1.65, 5.95, 3.55, "Código SQL", [
        "SELECT e.entidad,",
        "  ROUND(100.0 *",
        "    SUM(f.fac_tri * f.informal)",
        "    / SUM(f.fac_tri), 2) AS til1_pct",
        "FROM fact_ocupado f",
        "JOIN dim_entidad e USING (cve_ent)",
        "GROUP BY e.entidad",
        "ORDER BY til1_pct DESC;"], size=15, titulo_txt="SQL · vista v_til_entidad")
    panel_codigo(s, 6.78, 1.65, 5.95, 3.55, "Código MongoDB", [
        "db.personas.aggregate([",
        "  {$group: {_id: \"$cve_ent\",",
        "    ocupados: {$sum: \"$fac_tri\"},",
        "    informales: {$sum: {$cond: [",
        "      \"$trabajo.informal\",",
        "      \"$fac_tri\", 0]}}}},",
        "  {$project: {til1_pct: {$multiply: [",
        "    100, {$divide: [",
        "      \"$informales\", \"$ocupados\"]}]}}}",
        "])"], size=14, titulo_txt="MongoDB · pipeline de agregación")
    lectura(s, M, 5.4, 7.0, 1.4, "Ficha", [[("Ficha de una entidad: ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("SQL necesita varias consultas con JOIN; MongoDB, una lectura por clave: ", {"size": 15}), ("db.entidades.findOne({cve_ent: 20})", {"size": 14, "fuente": MONO})]], size=15)
    estadistica(s, 7.8, 5.4, 4.93, 1.4, "0.005 pp", "diferencia máxima entre ambas (redondeo del SQL)", "Equivalencia verificada", vsize=34, lsize=13)


def s_reproducibilidad(d):
    s = d.nueva(f"Reproducibilidad: una orden, una semilla, {sum(C.contar_pruebas().values())} pruebas", (
        "Un resultado científico solo vale si otra persona puede obtenerlo. Todo el proyecto se reproduce con una sola orden, run_all, que encadena diez pasos: el ETL, el análisis, las figuras, la base documental, el tablero, el cuaderno, las dos presentaciones, el informe en Word y las pruebas. Toma entre seis y diez minutos. "
        "Hay una única semilla, veinte millones doscientos cincuenta y un mil doscientos treinta y uno, para todo lo aleatorio; ejecutamos dos veces y los treinta archivos de resultados son idénticos. "
        "La base se recrea desde cero, así que correr el proceso dos veces no duplica datos. La tabla etl_run guarda las versiones de las bibliotecas, los parámetros y la huella SHA-256 de cada archivo de origen. "
        "Y hay treinta y cuatro pruebas automáticas: de limpieza, de estadística de encuestas, de modelos y una de integración con los datos reales."))
    panel_codigo(s, M, 1.65, 12.13, 0.62, "Orden única", ["python scripts/run_all.py            # todo el proyecto, de principio a fin, en ≈ 10 minutos"], size=15)
    pasos = ["ETL", "Análisis", "Figuras", "NoSQL", "Tablero", "Cuaderno", "Deck corto", "Deck completo", "Informe", "Pruebas"]
    ancho = (SW - 2 * M - 9 * 0.08) / 10
    for i, p in enumerate(pasos):
        x = M + i * (ancho + 0.08)
        sh = tarjeta(s, x, 2.5, ancho, 0.8, f"Paso {i + 1}", fondo=TC.TEXT_2, forma=MSO_SHAPE.PENTAGON)
        texto_en_forma(sh, [[(p, {"size": 12, "bold": True, "spec": TC.BACKGROUND_1})]], alinear=PP_ALIGN.LEFT, margen=0.08, espacio=0)
    datos = [("20251231", "semilla única para todo lo aleatorio"), ("30 de 30", "archivos de resultados idénticos en dos corridas"), (str(sum(C.contar_pruebas().values())), "pruebas automáticas (limpieza, encuestas, modelos, capa documental, integración)"), ("SHA-256", "huella de cada archivo de origen (tabla etl_run)")]
    for i, (v, l) in enumerate(datos):
        estadistica(s, M + i * 3.07, 3.55, 2.93, 1.75, v, l, f"Dato {i + 1}", vsize=30, lsize=13)
    lectura(s, M, 5.5, 12.13, 1.3, "Garantías", [[("Idempotente: ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("la base se recrea desde cero.  ", {"size": 15}), ("Auditable: ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("bitácora de cada regla.  ", {"size": 15}), ("Transparente: ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("todas las decisiones viven en config.py.", {"size": 15})]], size=15)


def s_mapa_codigo(d):
    s = d.nueva("Mapa del código: un módulo, una responsabilidad", (
        "El código está organizado como un paquete de Python, src enoe, con una responsabilidad por módulo, y scripts que lo ejecutan. Config concentra todos los parámetros y catálogos: ninguna decisión está escondida en el código. "
        "Extract lee los archivos y calcula las huellas. Clean aplica las reglas y las quince expectativas. Transform une las tablas, crea variables e imputa. Validacion compara con el INEGI. Load_sqlite y load_mongo cargan a los dos almacenes. "
        "Survey es la estadística de encuestas escrita desde cero: Rao-Wu, Taylor, Spearman ponderado, regresión y logit con diseño, Holm. Estimadores, modelos y analisis ejecutan todo el análisis, y viz genera las diecisiete figuras de datos y los ocho diagramas. "
        "Cada módulo tiene su docstring y sus pruebas."))
    mods = [("config.py", "Rutas, parámetros, catálogos y cifras de referencia: la única fuente de decisiones"), ("extract.py · validacion.py", "Lectura de los CSV (latin-1) con huella SHA-256; comparación con las cifras del INEGI"),
            ("clean.py", "Cobertura, faltantes, grupos de ingreso, atípicos, muestras y 15 expectativas"), ("transform.py", "Llave de persona, unión 1 a 1, variables derivadas e imputación"),
            ("pipeline.py", "Orquesta el ETL completo y escribe los metadatos y la bitácora"), ("load_sqlite.py · load_mongo.py", "Esquema en estrella con restricciones y documentos NoSQL"),
            ("survey.py", "Rao-Wu, Taylor, Spearman ponderado, WLS y logit con diseño, Holm"), ("datos · estimadores · modelos · analisis", "Todo el análisis estadístico: 30 tablas de resultados"),
            ("viz · viz_diagramas · figuras", "17 figuras de datos y 8 diagramas explicativos")]
    for i, (nom, desc) in enumerate(mods):
        col, fila = i % 3, i // 3
        x, y = M + col * 4.09, 1.65 + fila * 1.72
        tarjeta(s, x, y, 3.95, 1.58, f"Módulo {i + 1}", TC.BACKGROUND_2)
        _, tf = caja(s, x + 0.2, y + 0.1, 3.55, 1.38, f"Módulo {i + 1} texto", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [[(nom, {"size": 14, "bold": True, "spec": TC.TEXT_2, "fuente": MONO})], [(desc, {"size": 13})]], espacio=3)
    _, tf = caja(s, M, 6.85, 12.13, 0.3, "Nota módulos")
    parrafos(tf, [[(f"Paquete src/enoe/ (16 módulos) + scripts/ (ejecutables) + tests/ ({sum(C.contar_pruebas().values())} pruebas).", {"size": 12, "spec": RGB["muted"]})]], espacio=0)


# =========================================================================== #
# E. Estadística explicada
# =========================================================================== #
def s_rao_wu(d):
    s = d.nueva("El bootstrap de Rao–Wu, paso a paso", (
        "Para medir la incertidumbre hay que saber cuánto cambiaría el resultado si repitiéramos la encuesta. No se puede repetir, pero se puede simular: el bootstrap remuestrea los propios datos. Como la ENOE es por conglomerados, no se remuestrean personas sino unidades primarias completas, respetando los estratos. "
        "El método de Rao y Wu lo hace así: en cada estrato con n unidades se sortean n menos uno con reemplazo, y los ponderadores se multiplican por n entre n menos uno por el número de veces que salió su unidad. El ejemplo del diagrama es un estrato de cuatro unidades. "
        "Se repite mil veces con la misma semilla; la desviación estándar de las estimaciones replicadas es el error estándar, y los percentiles 2.5 y 97.5 son el intervalo de confianza. Verificamos con pruebas que la varianza bootstrap coincide con la de linealización de Taylor, dentro de ocho por ciento."))
    imagen(s, "D05_rao_wu.png", M, 1.6, 8.5, 4.2, "Diagrama en cuatro pasos del bootstrap de Rao-Wu con un estrato de cuatro unidades primarias de muestreo")
    pasos = ["En cada estrato con n UPM se sortean n − 1 con reemplazo", "Los pesos se reescalan: × n/(n − 1) × veces que salió la UPM", "Se repite 1,000 veces con la misma semilla", "Error estándar = desviación estándar; IC = percentiles 2.5 y 97.5"]
    for i, t in enumerate(pasos):
        y = 1.65 + i * 1.28
        tarjeta(s, 9.3, y, 3.43, 1.13, f"Paso {i + 1}", TC.BACKGROUND_2)
        punto_numerado(s, 9.4, y + 0.3, 0.5, i + 1, f"Número {i + 1}")
        _, tf = caja(s, 10.02, y + 0.06, 2.6, 1.0, f"Paso {i + 1} texto", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [t], size=13, espacio=0)
    lectura(s, M, 5.95, 8.5, 0.85, "Verificado", [[("Verificado con pruebas: ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("la varianza bootstrap coincide con la de linealización de Taylor (± 8 %).", {"size": 15})]], size=15)


def s_ic_p(d):
    p50 = cu.loc[50]
    sur = sg[(sg.dimension == "Región") & (sg.categoria == "Sur")].iloc[0]
    s = d.nueva("Cómo leer un intervalo de confianza y un valor p", (
        "Como trabajamos con una muestra, toda diferencia podría deberse al azar. El valor p es la probabilidad de observar una diferencia tan grande si en realidad no hubiera brecha; si es menor que cinco por ciento decimos que la diferencia es estadísticamente significativa. "
        "El intervalo de confianza del 95 por ciento es un rango de valores plausibles: si el estudio se repitiera muchas veces, el 95 por ciento de los intervalos construidos así contendría el valor verdadero. La regla práctica: si el intervalo no incluye el cero, hay una diferencia demostrable. "
        f"Tres casos reales de este proyecto: la brecha por hora total, {tot['brecha_hora_pct']:.1f} por ciento, no incluye el cero; la brecha en la mediana, {p50['brecha_pct']:.1f} por ciento, toca el cero, p igual a {p50['p']:.2f}, evidencia débil; la brecha en la región Sur, {sur['brecha_pct']:.1f} por ciento, incluye el cero, p igual a {sur['p']:.2f}, no se puede afirmar."))
    imagen(s, "D06_como_leer_ic.png", M, 1.6, 8.7, 3.4, "Tres intervalos de confianza reales del proyecto: uno que excluye el cero, uno que lo toca y uno que lo incluye")
    lectura(s, 9.5, 1.65, 3.23, 3.35, "Definiciones", [[("IC 95 %: ", {"size": 14, "bold": True, "spec": TC.TEXT_2}), ("rango de valores plausibles; si no incluye el 0, la diferencia es significativa.", {"size": 14})],
                                                       [("Valor p: ", {"size": 14, "bold": True, "spec": TC.TEXT_2}), ("probabilidad de ver una diferencia así si no hubiera brecha; p < 0.05 = significativa.", {"size": 14})]], size=14, espacio=10)
    casos = [("Excluye el 0", f"Brecha por hora total: {tot['brecha_hora_pct']:.1f} % ({tot['brecha_hora_inf']:.1f} a {tot['brecha_hora_sup']:.1f}). Hay brecha demostrable.", TC.ACCENT_3),
             ("Toca el 0", f"Brecha en la mediana: {p50['brecha_pct']:.1f} % (p = {p50['p']:.2f}). Evidencia débil.", TC.ACCENT_4),
             ("Incluye el 0", f"Brecha en la región Sur: {sur['brecha_pct']:.1f} % (p = {sur['p']:.2f}). No se puede afirmar.", TC.ACCENT_2)]
    for i, (h, t, c_) in enumerate(casos):
        x = M + i * 4.1
        tarjeta(s, x, 5.2, 3.95, 1.6, f"Caso {i + 1}", TC.BACKGROUND_2)
        circulo_texto(s, x + 0.18, 5.38, 0.4, str(i + 1), f"Caso {i + 1} número", size=14, fondo=c_)
        _, tf = caja(s, x + 0.7, 5.3, 3.1, 1.4, f"Caso {i + 1} texto", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [[(h, {"size": 15, "bold": True, "spec": TC.TEXT_2})], [(t, {"size": 13})]], espacio=3)


def s_spearman(d):
    s = d.nueva("Spearman: la correlación entre rangos", (
        "La correlación de Spearman mide si dos variables suben juntas, sin importar la forma exacta de la relación ni los valores extremos. Se reemplaza cada valor por su lugar, su rango, y se calcula la correlación de Pearson entre los rangos. Los empates reciben el rango medio. "
        "En este proyecto cada persona cuenta tantas veces como su factor de expansión: son rangos medios ponderados. El ejemplo del diagrama usa seis personas ilustrativas, y al pasar a rangos la correlación sale 0.93. "
        f"Va de menos uno a más uno; como referencia, 0.1 es débil, 0.3 moderada y 0.5 fuerte. La correlación nacional entre escolaridad e ingreso por hora es {rt['spearman_nacional']['est']:.2f}, moderada; por entidad va de {rho_min['rho_est']:.2f} a {rho_max['rho_est']:.2f}."))
    imagen(s, "D08_spearman_ejemplo.png", M, 1.6, 8.7, 3.4, "Ejemplo con seis personas: a la izquierda los valores originales y a la derecha sus rangos, donde el Spearman resulta 0.93")
    lectura(s, 9.5, 1.65, 3.23, 3.35, "Cómo se calcula", [[("1  ", {"size": 14, "bold": True, "spec": TC.ACCENT_1}), ("Ordenar cada variable", {"size": 14})], [("2  ", {"size": 14, "bold": True, "spec": TC.ACCENT_1}), ("Cambiar valores por rangos (empates: rango medio)", {"size": 14})],
                                                          [("3  ", {"size": 14, "bold": True, "spec": TC.ACCENT_1}), ("Pearson entre rangos, ponderado por fac_tri", {"size": 14})]], size=14, titulo_txt="Cómo se calcula", espacio=8)
    for i, (v, l, f_) in enumerate([("≈ 0.1", "débil", TC.BACKGROUND_2), ("≈ 0.3", "moderada", TC.BACKGROUND_2), ("≈ 0.5", "fuerte", TC.BACKGROUND_2), (f"{rt['spearman_nacional']['est']:.2f}", "escolaridad e ingreso por hora, nacional", TC.TEXT_2)]):
        oscuro = f_ == TC.TEXT_2
        estadistica(s, M + i * 3.07, 5.2, 2.93, 1.6, v, l, f"Escala {i + 1}", vsize=34, lsize=14, fondo=f_, vspec=TC.BACKGROUND_1 if oscuro else TC.TEXT_2, lspec=TC.BACKGROUND_1 if oscuro else TC.TEXT_1)


def s_mincer(d):
    m3 = rmod[rmod.modelo.str.startswith("M3")].iloc[0]
    s = d.nueva(f"La ecuación de Mincer: cómo se lee el {rt['nacional_pct']['est']:.1f} %", (
        "La ecuación de Mincer es el modelo clásico de la economía laboral para medir el rendimiento de la educación: se explica el logaritmo del ingreso por hora con los años de escolaridad, la edad y la edad al cuadrado, el sexo y efectos de entidad y localidad. "
        f"El coeficiente beta de escolaridad mide el aumento del logaritmo del ingreso por cada año de estudio; el aumento porcentual es cien por e elevado a beta menos uno. Con beta igual a {m3.coef:.4f}, un año más se asocia con {m3.retorno_pct:.1f} por ciento más ingreso por hora y dos años, con {100 * ((1 + m3.retorno_pct / 100) ** 2 - 1):.1f} por ciento. "
        "La tabla muestra cómo cambia al agregar controles: al agregar la posición en la ocupación y la informalidad baja a 3.8 por ciento, porque una parte del beneficio de estudiar actúa a través de conseguir un mejor empleo; por eso ese modelo no es el resultado principal."))
    tarjeta(s, M, 1.65, 12.13, 1.4, "Ecuación", fondo=TC.TEXT_2)
    _, tf = caja(s, M + 0.3, 1.7, 11.5, 1.3, "Ecuación texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[("ln(ingreso por hora) = α + β · escolaridad + γ₁ · edad + γ₂ · edad²", {"size": 20, "bold": True, "spec": TC.BACKGROUND_1})],
                  [("+ δ · mujer + efectos de entidad y de localidad + error", {"size": 20, "bold": True, "spec": TC.BACKGROUND_1})],
                  [("β = aumento del logaritmo del ingreso por año de estudio  →  rendimiento (%) = 100 × (e^β − 1)", {"size": 15, "spec": RGB["soft"]})]], espacio=3, alinear=PP_ALIGN.CENTER)
    filas = [[r.modelo, f"{r.coef:.4f}", f"{r.retorno_pct:.2f} % ({r.retorno_pct_inf:.2f} a {r.retorno_pct_sup:.2f})"] for r in rmod.iloc[:4].itertuples()]
    tabla_nativa(s, M, 3.3, [4.4, 1.3, 2.9], ["Modelo (controles acumulados)", "β", "Rendimiento por año (IC 95 %)"], filas, "Modelos de Mincer", size=13, alto_fila=0.52,
                 alinear=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT], resaltar=(2,))
    _, tf = caja(s, M, 6.0, 8.6, 0.8, "Nota modelos")
    parrafos(tf, [[("M3 (con entidad y localidad) es el resultado de referencia. M4 baja a 3.8 % porque parte del beneficio de estudiar actúa a través de conseguir un mejor empleo (formal, asalariado).", {"size": 13, "spec": RGB["muted"]})]], espacio=0)
    estadistica(s, 9.55, 3.3, 3.18, 1.45, f"+{m3.retorno_pct:.1f} %", "por cada año de estudio (M3)", "Un año", vsize=36, lsize=13)
    estadistica(s, 9.55, 4.9, 3.18, 1.45, f"+{100 * ((1 + m3.retorno_pct / 100) ** 2 - 1):.1f} %", "dos años: (1.051)² − 1", "Dos años", vsize=36, lsize=13)


def s_brecha_d_holm(d):
    s = d.nueva("Tres herramientas para leer la brecha: porcentaje, tamaño del efecto y Holm", (
        f"La brecha se define como uno menos el cociente del ingreso medio geométrico de las mujeres entre el de los hombres. Con los datos: los hombres ganan {tot['ing_hora_h']:.2f} pesos por hora y las mujeres {tot['ing_hora_m']:.2f}; uno menos el cociente es {tot['brecha_hora_pct']:.1f} por ciento. "
        "Con 112 mil observaciones casi toda diferencia es significativa, por eso medimos también el tamaño del efecto con la d de Cohen: la diferencia de medias entre la desviación estándar; 0.2 es pequeño, 0.5 mediano y 0.8 grande. La nuestra va de 0.06 a 0.24, un efecto pequeño. "
        "Y como hacemos cuatro pruebas, una por nivel de instrucción, aplicamos la corrección de Holm, que ordena los valores p y los compara con umbrales cada vez menos exigentes para controlar el error de todo el conjunto. Las cuatro siguen siendo significativas."))
    tarjetas = [("Brecha (%)", f"1 − ({tot['ing_hora_m']:.2f} ÷ {tot['ing_hora_h']:.2f}) = {tot['brecha_hora_pct']:.1f} %", "Las mujeres ganan 3.7 % menos por hora, comparando medias geométricas."),
                ("d de Cohen", "diferencia de medias ÷ desviación estándar", "0.2 pequeño · 0.5 mediano · 0.8 grande. Aquí: 0.06 a 0.24."),
                ("Corrección de Holm", "4 pruebas → p ordenados y umbrales crecientes", "Controla el error del conjunto; las 4 brechas siguen siendo significativas.")]
    for i, (h, f_, t) in enumerate(tarjetas):
        x = M + i * 4.1
        tarjeta(s, x, 1.65, 3.95, 2.45, f"Herramienta {i + 1}", TC.BACKGROUND_2)
        _, tf = caja(s, x + 0.2, 1.75, 3.55, 2.25, f"Herramienta {i + 1} texto", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [[(h, {"size": 18, "bold": True, "spec": TC.TEXT_2})], [(f_, {"size": 14, "bold": True, "spec": TC.ACCENT_1})], [(t, {"size": 14})]], espacio=6)
    filas = []
    for k in ["1. Primaria incompleta", "2. Primaria completa", "3. Secundaria completa", "4. Medio superior y superior"]:
        filas.append([k.split(". ", 1)[1], f"{bn.loc[k, 'brecha_hora_pct']:.1f} %", f"{bn.loc[k, 'brecha_hora_inf']:.1f} a {bn.loc[k, 'brecha_hora_sup']:.1f}", f"{tc.loc[k, 'd_cohen']:.2f}", "< 0.001" if bn.loc[k, 'p_hora_holm'] < 0.001 else f"{bn.loc[k, 'p_hora_holm']:.3f}"])
    filas.append(["Total", f"{tot['brecha_hora_pct']:.1f} %", f"{tot['brecha_hora_inf']:.1f} a {tot['brecha_hora_sup']:.1f}", f"{tc.loc['Total', 'd_cohen']:.2f}", "< 0.001"])
    tabla_nativa(s, M, 4.3, [3.0, 1.2, 1.9, 1.15, 1.15], ["Nivel de instrucción", "Brecha", "IC 95 %", "d de Cohen", "p (Holm)"], filas, "Brecha por nivel", size=13, alto_fila=0.42,
                 alinear=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.CENTER, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT], resaltar=(4,))
    lectura(s, 9.25, 4.3, 3.48, 2.52, "Lectura brecha", [[("Hay brecha en los cuatro niveles, pero el efecto es pequeño: hombres y mujeres se traslapan mucho.", {"size": 14})]], size=14, titulo_txt="Lectura", espacio=6)


# =========================================================================== #
# F. Resultados
# =========================================================================== #
def s_oaxaca_idea(d):
    ob = leer("oaxaca")
    ob["clave"] = [str(c).strip(" ·") for c in ob["componente"]]
    ob = ob[ob.especificacion.str.startswith("Principal")].set_index("clave")
    expl, noexp, total = ob.loc["Explicada por características (referencia agrupada)", "log_puntos"] * 100, ob.loc["No explicada (referencia agrupada)", "log_puntos"] * 100, ob.loc["Brecha total (log-puntos)", "log_puntos"] * 100
    s = d.nueva("Oaxaca–Blinder: separar lo explicado de lo no explicado", (
        "La descomposición de Oaxaca-Blinder separa la brecha en dos partes. La parte explicada es la que se debe a que mujeres y hombres difieren en sus características medidas: escolaridad, edad, lugar de residencia, tipo de empleo y rama. La parte no explicada es la que queda cuando se comparan personas con las mismas características: a iguales características, se les paga distinto. "
        f"Con nuestros datos la brecha total es {total:.1f} puntos logarítmicos; la parte explicada es {expl:.1f}, negativa, porque las mujeres tienen más escolaridad y viven en lugares de mayor ingreso, lo que favorecería su ingreso; y la no explicada es {noexp:.1f}. "
        "Es decir: si las mujeres fueran pagadas como los hombres con sus mismas características, ganarían más que ellos. Importante: la parte no explicada no prueba discriminación, incluye todo lo que no medimos, como la ocupación específica, la experiencia real y la negociación."))
    imagen(s, "D07_oaxaca_idea.png", M, 1.6, 8.7, 3.9, "Diagrama de la idea de Oaxaca-Blinder: brecha total igual a parte explicada más parte no explicada, con los componentes de la parte explicada")
    lectura(s, 9.5, 1.65, 3.23, 3.85, "Cómo leerla", [[("Explicada: ", {"size": 14, "bold": True, "spec": TC.TEXT_2}), ("difieren las características (escolaridad, edad, lugar, empleo, rama).", {"size": 14})],
                                                      [("No explicada: ", {"size": 14, "bold": True, "spec": TC.TEXT_2}), ("a iguales características, distinto pago.", {"size": 14})]], size=14, titulo_txt="Cómo leerla", espacio=8)
    lectura(s, M, 5.7, 8.7, 1.1, "Mensaje OB", [[("A iguales características, las mujeres reciben ", {"size": 15}), (f"{noexp:.1f} puntos logarítmicos (≈ 6.7 %) menos.", {"size": 15, "bold": True, "spec": TC.TEXT_2})]], size=15)
    lectura(s, 9.5, 5.7, 3.23, 1.1, "Aviso OB", [[("No prueba discriminación.", {"size": 14, "bold": True})]], size=14, fondo=ambar)


def s_heterogeneidad(d):
    g_ = lambda dim, cat: sg[(sg.dimension == dim) & (sg.categoria == cat)].iloc[0]  # noqa: E731
    inf, form = g_("Informalidad", "Informal"), g_("Informalidad", "Formal")
    s = d.nueva("La brecha por hora varía por grupo: es mayor en el empleo informal", (
        "Para ver dónde se concentra la brecha la calculamos dentro de subgrupos: informalidad, posición en la ocupación, región, tamaño de localidad, edad y nivel de instrucción detallado. Los puntos rellenos son las categorías significativas tras la corrección de Holm dentro de cada dimensión. "
        f"La brecha es de {inf.brecha_pct:.1f} por ciento entre trabajadores informales, significativa, y de {form.brecha_pct:.1f} entre formales, no significativa: la desigualdad se concentra en el empleo informal. "
        f"Por región va de {g_('Región', 'Sur').brecha_pct:.1f} en el Sur, no significativa, a {g_('Región', 'Centro-Norte').brecha_pct:.1f} en el Centro-Norte. Por edad es significativa de los 15 a los 64 años, con un máximo de {g_('Grupo de edad', '45-54').brecha_pct:.1f} entre los 45 y 54. "
        "Con intervalos tan amplios en algunos subgrupos hay que evitar conclusiones fuertes sobre diferencias pequeñas entre ellos."))
    imagen(s, "17_brecha_subgrupos.png", M, 1.55, 7.7, 5.3, "Gráfica de puntos con intervalos de la brecha por hora en subgrupos de informalidad, posición, región, tamaño de localidad y edad", cortar=(0.62, 0.24))
    estadistica(s, 8.6, 1.65, 4.13, 1.5, f"{inf.brecha_pct:.1f} % vs {form.brecha_pct:.1f} %", "informales (significativa) vs. formales (no significativa)", "Informalidad", vsize=30, lsize=13)
    estadistica(s, 8.6, 3.3, 4.13, 1.5, f"{g_('Región', 'Sur').brecha_pct:.1f} → {g_('Región', 'Centro-Norte').brecha_pct:.1f} %", "del Sur (no significativa) al Centro-Norte", "Región", vsize=30, lsize=13)
    estadistica(s, 8.6, 4.95, 4.13, 1.5, "25–64 años", f"significativa en todos los grupos de edad ({g_('Grupo de edad', '25-34').brecha_pct:.1f} % a {g_('Grupo de edad', '45-54').brecha_pct:.1f} %)", "Edad", vsize=30, lsize=13)


# =========================================================================== #
# G. Cierre y respaldo
# =========================================================================== #
def s_metricas(d):
    s = d.nueva("Métricas de éxito del protocolo: las tres se cumplen", (
        "Regresamos a las tres métricas que fijó el protocolo. M1: la brecha salarial por nivel de instrucción con intervalo de confianza y prueba de hipótesis; la tabla de resultados tiene la brecha por hora y por mes en los cuatro niveles, con intervalos de Rao-Wu y valores p ajustados con Holm. "
        "M2: la correlación de Spearman de las 32 entidades con intervalo por bootstrap y un ranking defendible; reportamos el intervalo del lugar de cada entidad y declaramos que el ranking solo distingue los extremos. "
        "M3: un tablero con al menos cuatro visualizaciones interpretables, alimentado por un pipeline que carga a una base NoSQL; el tablero tiene seis visualizaciones y la ficha de cada entidad. "
        "La salvedad honesta de M3: la carga a un servidor MongoDB real no se ejecutó; la carga completa se probó con un simulador (mongomock) y la agregación equivalente está verificada."))
    filas = [["M1", "Brecha salarial por nivel de instrucción, con IC 95 % y prueba de hipótesis", "Brecha por hora y por mes en los 4 niveles; IC de Rao-Wu; p con Holm; Welch, Mann-Whitney y d de Cohen", "Cumplida"],
             ["M2", "Spearman en las 32 entidades, con IC por bootstrap y ranking defendible", "ρ de 32 entidades con IC y con el intervalo del lugar; el ranking solo distingue los extremos", "Cumplida"],
             ["M3", "Tablero con ≥ 4 visualizaciones, alimentado por un pipeline a una base NoSQL consultable por entidad", "Tablero HTML con 6 visualizaciones y ficha por entidad; documentos MongoDB y agregación verificada contra SQL", "Cumplida*"]]
    tabla_nativa(s, M, 1.7, [0.8, 4.4, 5.4, 1.53], ["", "Qué pedía el protocolo", "Evidencia", "Estado"], filas, "Métricas de éxito", size=14, alto_fila=1.2, alto_enc=0.5,
                 alinear=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT, PP_ALIGN.CENTER], negrita_col0=True)
    lectura(s, M, 5.85, 12.13, 0.95, "Salvedad", [[("* Salvedad: ", {"size": 15, "bold": True, "spec": TC.TEXT_2}), ("la carga a un servidor MongoDB real no se ejecutó (no hay servidor instalado); se probó con mongomock (simulador), los documentos están listos para mongoimport y la agregación equivalente está verificada.", {"size": 14})]], size=14, fondo=ambar)


def s_glosario_1(d):
    _glosario(d, "Glosario (1/2): encuesta e inferencia", [
        ("ENOE", "Encuesta Nacional de Ocupación y Empleo del INEGI: principal fuente del mercado laboral."),
        ("Factor de expansión (fac_tri)", "A cuántas personas de la población representa cada persona de la muestra."),
        ("Estrato y UPM", "Estrato: grupo de áreas parecidas. UPM: conjunto de viviendas que se sortea."),
        ("Efecto de diseño", "Cuánto agranda la varianza el muestreo por conglomerados frente a una muestra simple."),
        ("Bootstrap de Rao–Wu", "Remuestreo de UPM dentro de estratos con pesos reescalados para medir la incertidumbre."),
        ("Intervalo de confianza", "Rango de valores plausibles; al 95 %, contiene el valor verdadero el 95 % de las veces."),
        ("Valor p", "Probabilidad de ver una diferencia así si no hubiera efecto; < 0.05 = significativa."),
        ("Corrección de Holm", "Ajusta los valores p cuando se hacen varias pruebas a la vez.")],
        "Glosario 1: ENOE, factor de expansión, estrato y UPM, efecto de diseño, bootstrap de Rao-Wu, intervalo de confianza, valor p y Holm.")


def s_glosario_2(d):
    _glosario(d, "Glosario (2/2): modelos y variables", [
        ("Spearman (ρ)", "Correlación entre los rangos de dos variables; mide asociación monótona."),
        ("Logaritmo natural", "Transformación que acorta la cola larga; sus diferencias son diferencias porcentuales."),
        ("Ecuación de Mincer", "Regresión del logaritmo del ingreso sobre escolaridad y experiencia."),
        ("Brecha salarial", "Porcentaje menos que ganan las mujeres que los hombres (medias geométricas)."),
        ("d de Cohen", "Tamaño del efecto: 0.2 pequeño, 0.5 mediano, 0.8 grande."),
        ("Oaxaca–Blinder", "Divide la brecha en parte explicada por características y parte no explicada."),
        ("IPW", "Ponderación por la probabilidad inversa de responder para corregir la no respuesta."),
        ("TIL1", "Tasa de informalidad laboral: ocupados informales ÷ ocupados de 15 años y más.")],
        "Glosario 2: Spearman, logaritmo natural, ecuación de Mincer, brecha salarial, d de Cohen, Oaxaca-Blinder, IPW y TIL1.")


def _glosario(d, titulo_txt, terminos, notas):
    s = d.nueva(titulo_txt, notas)
    for col in range(2):
        for k in range(4):
            t, desc = terminos[col * 4 + k]
            x, y = M + col * 6.15, 1.65 + k * 1.3
            tarjeta(s, x, y, 5.98, 1.18, f"Término {col * 4 + k + 1}", TC.BACKGROUND_2)
            _, tf = caja(s, x + 0.22, y + 0.08, 5.55, 1.02, f"Término {col * 4 + k + 1} texto", MSO_ANCHOR.MIDDLE)
            parrafos(tf, [[(t, {"size": 16, "bold": True, "spec": TC.TEXT_2})], [(desc, {"size": 13})]], espacio=3)


def s_preguntas(d):
    s = d.nueva("Preguntas difíciles y respuestas cortas", (
        "Respaldo para la sesión de preguntas. Seis de las preguntas más probables con una respuesta corta. ¿Es causal? No: son asociaciones. ¿Por qué ponderan y usan Rao-Wu? Porque la encuesta es por conglomerados y los errores normales serían demasiado pequeños. "
        "¿Hay brecha de género? Sí, pero depende de qué se mide. ¿Por qué no interpretan el modelo con horas? Por el sesgo de división. ¿Cargaron a MongoDB real? No, y lo decimos con claridad. ¿Qué limita los resultados? Un trimestre, ingreso autorreportado, selección y pocas observaciones por estado. "
        "La guía de defensa en la carpeta docs y el anexo D del informe tienen muchas respuestas más."))
    qa = [("¿Es causal?", "No: son asociaciones. Hay habilidad no observada y selección, y las relaciones entre estados no se leen a nivel individual."),
          ("¿Por qué ponderan y usan Rao–Wu?", f"fac_tri representa personas y la encuesta es por conglomerados: los errores «normales» serían demasiado pequeños (efecto de diseño {deff.loc['TIL1 nacional', 'deff']:.1f})."),
          ("¿Hay brecha de género?", f"Sí, depende de qué se mida: {tot['brecha_hora_pct']:.1f} % por hora, {tot['brecha_mens_pct']:.1f} % por mes (horas: −{tot['menos_horas_mujeres_pct']:.0f} %) y {g5['brecha_pct']:.1f} % entre personas comparables."),
          ("¿Por qué no interpretan el modelo con horas?", "Sesgo de división: un error en las horas crea una relación negativa mecánica y la brecha «sube» a 16 %."),
          ("¿Cargaron a un MongoDB real?", "No hay servidor. La carga completa se probó con mongomock (simulador) y la agregación reproduce la vista SQL (0.005 pp); con un servidor, run_mongo.py --uri la repite."),
          ("¿Qué limita los resultados?", "Un trimestre, ingreso autorreportado y con redondeo, selección en el empleo y entre 1,900 y 5,900 observaciones por estado.")]
    for i, (q, a) in enumerate(qa):
        col, fila = i % 2, i // 2
        x, y = M + col * 6.15, 1.65 + fila * 1.72
        tarjeta(s, x, y, 5.98, 1.6, f"Pregunta {i + 1}", TC.BACKGROUND_2)
        _, tf = caja(s, x + 0.22, y + 0.08, 5.55, 1.44, f"Pregunta {i + 1} texto", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [[(q, {"size": 16, "bold": True, "spec": TC.TEXT_2})], [(a, {"size": 13})]], espacio=4)
