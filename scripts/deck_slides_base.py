"""Diapositivas de la presentación corta (24). Cada función construye una diapositiva en el Deck recibido; la usan build_deck.py y build_deck_completa.py."""
from deck_lib import *  # noqa: F401,F403


def s_portada(d):
    # =========================================================================== #
    # 1. Portada
    # =========================================================================== #
    s = d.nueva("Radiografía socioeconómica de México", (
        "Presentación del equipo. El proyecto responde a una pregunta simple —¿cuánto rinde estudiar y para quién?— con un ciclo KDD completo sobre la ENOE 2025-T4 del INEGI: "
        f"{n_u:,} ocupados, 32 entidades, limpieza documentada, dos almacenes de datos, estadística con el diseño muestral de la encuesta y un tablero. "
        "Pidan a cada integrante que se presente y diga qué parte explicará."), oscuro=True, con_pie=False)
    t = s.shapes.title
    t.top, t.height = Inches(1.6), Inches(1.3)
    t.text_frame.paragraphs[0].runs[0].font.size = Pt(48)
    _, tf = caja(s, M, 3.05, 10.5, 1.0, "Subtítulo")
    parrafos(tf, [[("Escolaridad, ingreso y brecha de género", {"size": 28, "spec": RGB["soft"]})],
                  [("Encuesta Nacional de Ocupación y Empleo (ENOE), 4.º trimestre de 2025 · INEGI", {"size": 18, "spec": TC.BACKGROUND_1})]], espacio=6)
    _, tf = caja(s, M, 4.45, 11.5, 1.2, "Equipo")
    parrafos(tf, [[("Equipo 1: ", {"size": 18, "bold": True, "spec": TC.BACKGROUND_1}),
                   ("Juan Evelio Culin Grajeda · Angel Yireh Garcia Jara · Luis Andre Gutierrez Zuñia", {"size": 18, "spec": TC.BACKGROUND_1})],
                  [("Proyecto Integrador de Ciencia de Datos · Ingeniería en Computación, 9.º semestre · UNE Plantel Centro · 18 de octubre de 2026", {"size": 14, "spec": RGB["soft"]})]], espacio=6)
    for i, (v, l) in enumerate([(f"{419038:,}", "registros"), (f"{n_u:,}", "ocupados de 15+"), ("32", "entidades"), (f"{R['B']:,}", "réplicas bootstrap")]):
        x = M + i * 3.0
        sh = tarjeta(s, x, 5.95, 2.8, 0.95, f"Dato {i + 1}", fondo=RGB["navy2"])
        texto_en_forma(sh, [[(v, {"size": 24, "bold": True, "spec": TC.BACKGROUND_1})], [(l, {"size": 13, "spec": RGB["soft"]})]], alinear=PP_ALIGN.CENTER, espacio=0)


def s_pregunta(d):

    # =========================================================================== #
    # 2. Pregunta y objetivos
    # =========================================================================== #
    s = d.nueva("La pregunta: ¿cuánto rinde estudiar, y para quién?", (
        "Esta es la pregunta del protocolo. Tiene tres partes que corresponden a los tres objetivos: el rendimiento de un año de escolaridad por entidad, la brecha de género con la misma escolaridad y la informalidad. "
        "Las tres métricas de éxito del protocolo son: M1, brecha por nivel de instrucción con intervalo y prueba; M2, Spearman por entidad con intervalo y ranking; M3, un tablero con al menos cuatro visualizaciones sobre una base NoSQL. "
        "Al final de la presentación regresamos a ellas para ver si se cumplieron."))
    c = tarjeta(s, M, 1.7, 5.7, 3.7, "Pregunta de investigación")
    _, tf = caja(s, M + 0.3, 1.9, 5.1, 3.3, "Pregunta", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[("¿Cuánto aumenta el ingreso laboral por cada año adicional de escolaridad, cómo cambia esa relación entre entidades federativas y existe una brecha salarial significativa entre hombres y mujeres con la misma escolaridad?", {"size": 22, "bold": True, "spec": TC.TEXT_2})]], espacio=0)
    objetivos = ["Estimar la correlación y el rendimiento de la escolaridad en cada una de las 32 entidades",
                 "Probar si hay brecha de ingreso por hora entre hombres y mujeres con el mismo nivel de instrucción",
                 "Identificar las entidades con más informalidad y su relación con la escolaridad"]
    for i, o in enumerate(objetivos):
        y = 1.7 + i * 1.28
        tarjeta(s, 6.6, y, 6.13, 1.12, f"Objetivo {i + 1}")
        punto_numerado(s, 6.8, y + 0.22, 0.68, i + 1, f"Número {i + 1}")
        _, tf = caja(s, 7.7, y + 0.1, 4.85, 0.92, f"Objetivo {i + 1} texto", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [o], size=16, espacio=0)
    for i, (m, txt) in enumerate([("M1", "Brecha por nivel con IC 95 % y prueba de hipótesis"), ("M2", "Spearman de las 32 entidades con IC y ranking"), ("M3", "Tablero con ≥ 4 gráficas sobre una base NoSQL")]):
        x = M + i * 4.1
        sh = tarjeta(s, x, 5.75, 3.95, 0.95, f"Métrica {m}", fondo=TC.TEXT_2)
        texto_en_forma(sh, [[(f"{m}  ", {"size": 18, "bold": True, "spec": TC.BACKGROUND_1}), (txt, {"size": 14, "spec": TC.BACKGROUND_1})]], alinear=PP_ALIGN.LEFT, margen=0.2)


def s_kdd(d):

    # =========================================================================== #
    # 3. Ciclo KDD
    # =========================================================================== #
    s = d.nueva("Un ciclo KDD completo sobre datos reales y masivos", (
        "El ciclo KDD estructura todo el trabajo y cada fase corresponde a semanas del curso. Selección: elegimos la ENOE y la validamos contra cifras oficiales. "
        "Preprocesamiento: la ENOE no tiene celdas vacías, los faltantes vienen codificados, y encontramos que el ingreso cero esconde tres fenómenos. Transformación: variables, un ETL y dos almacenes. "
        "Minería: estadística con el diseño muestral, regresión y descomposición. Interpretación: hallazgos y límites. Abajo, el tamaño de los datos."))
    fases = [("1 Selección", "Sem. 1", "ENOE 4T-2025; validación contra cifras del INEGI"),
             ("2 Preprocesamiento", "Sem. 4", "Faltantes codificados, calidad del ingreso, atípicos, 15 pruebas de datos"),
             ("3 Transformación", "Sem. 4 · 6 · 7", "Variables derivadas, ETL, SQLite y MongoDB"),
             ("4 Minería", "Sem. 2 · 3 · 5", "Diseño muestral complejo, regresión, Oaxaca-Blinder"),
             ("5 Interpretación", "Sem. 5", "Hallazgos, recomendaciones y límites")]
    ancho = (SW - 2 * M - 4 * 0.12) / 5
    for i, (f, sem, detalle) in enumerate(fases):
        x = M + i * (ancho + 0.12)
        sh = tarjeta(s, x, 1.75, ancho, 1.05, f"Fase {i + 1}", fondo=TC.TEXT_2, forma=MSO_SHAPE.PENTAGON)
        num, nombre_fase = f.split(" ", 1)
        texto_en_forma(sh, [[(nombre_fase, {"size": 15, "bold": True, "spec": TC.BACKGROUND_1})], [(f"Fase {num} · {sem}", {"size": 12, "spec": RGB["soft"]})]], alinear=PP_ALIGN.LEFT, margen=0.12, espacio=0)
        _, tf = caja(s, x, 2.95, ancho - 0.1, 1.5, f"Fase {i + 1} detalle")
        parrafos(tf, [detalle], size=15, espacio=0)
    datos_s = [(f"{419038:,}", "registros de la tabla SDEMT"), (f"{R['muestras']['salarial']:,}", "observaciones salariales"), ("21,194", "UPM en 713 estratos"), ("7 de 7", "cifras oficiales reproducidas")]
    for i, (v, l) in enumerate(datos_s):
        estadistica(s, M + i * 3.07, 4.85, 2.93, 1.55, v, l, f"Dato {i + 1}", vsize=34)


def s_validacion(d):

    # =========================================================================== #
    # 4. Validación externa
    # =========================================================================== #
    s = d.nueva("Los filtros y ponderadores reproducen las cifras oficiales del INEGI", (
        "Antes de analizar nada comprobamos que estamos leyendo bien los datos. Con la base oficial —ocupados de 15 años y más, entrevista completa, residentes habituales, ponderador fac_tri— "
        "reproducimos siete cifras que publicó el INEGI para este trimestre: la PEA, la tasa de participación, la ocupación informal, la tasa de informalidad nacional y la de tres estados. "
        "Un detalle: si hubiéramos incluido a los 1,078 menores de 15 años que trabajan, la informalidad subiría a 55.27 % y ya no coincidiría. Esto valida los códigos de clase, informalidad y los factores de expansión."))
    filas = len(ext) + 1
    tabla = s.shapes.add_table(filas, 4, Inches(M), Inches(1.75), Inches(8.1), Inches(0.5 * filas)).table
    for j, (h, w) in enumerate(zip(["Indicador", "Proyecto", "INEGI", "¿Coincide?"], [3.8, 1.5, 1.3, 1.5])):
        tabla.columns[j].width = Inches(w)
        c = tabla.cell(0, j)
        c.fill.solid()
        color(c.fill.fore_color, TC.TEXT_2)
        c.text_frame.text = ""
        r = c.text_frame.paragraphs[0].add_run()
        r.text = h
        estilo_run(r, 14, True, TC.BACKGROUND_1)
        c.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
    for i, f in enumerate(ext.itertuples(index=False), start=1):
        tabla.rows[i].height = Inches(0.5)
        for j, val in enumerate([f.indicador, f"{f.estimado_proyecto:,.2f}", f"{f.oficial_inegi:,.1f}", "Sí" if f.coincide else "No"]):
            c = tabla.cell(i, j)
            c.fill.solid()
            color(c.fill.fore_color, TC.BACKGROUND_2 if i % 2 == 0 else TC.BACKGROUND_1)
            c.text_frame.text = ""
            r = c.text_frame.paragraphs[0].add_run()
            r.text = val
            estilo_run(r, 14, j == 3, TC.TEXT_1)
            c.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
        tabla.rows[0].height = Inches(0.5)
    estadistica(s, 9.2, 1.75, 3.53, 2.1, "7 de 7", "cifras del INEGI reproducidas al redondear a su precisión", "Validación", vsize=54, lsize=15)
    tarjeta(s, 9.2, 4.05, 3.53, 2.0, "Nota menores de 15")
    _, tf = caja(s, 9.4, 4.2, 3.13, 1.7, "Nota menores de 15 texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[("Por qué solo 15+: ", {"bold": True, "size": 15}), ("con los 1,078 menores de 15 años ocupados, el TIL1 sería 55.27 % y dejaría de coincidir con el oficial.", {"size": 15})]], espacio=0)


def s_ingreso_cero(d):

    # =========================================================================== #
    # 5. Calidad del ingreso
    # =========================================================================== #
    s = d.nueva("El «ingreso cero» esconde tres fenómenos distintos", (
        "Este es el hallazgo de calidad de datos más importante. El archivo trae ingreso cero para el 36 por ciento de los registros, y la lectura ingenua es que no reciben ingresos. Falso. "
        f"Ponderado, solo {A_t:.0f} por ciento declara el monto exacto; {B_t:.0f} por ciento da únicamente un rango de salarios mínimos, {D_t:.0f} por ciento no especifica y apenas {C_t:.0f} por ciento realmente no recibe ingresos. "
        f"Y hay un patrón: la proporción que declara monto exacto baja con la escolaridad, de {A_n1:.0f} a {A_n4:.0f} por ciento. Los datos faltan de forma no aleatoria. "
        "Por eso el análisis principal usa a quienes declararon monto, pero cada resultado clave se contrasta con tres correcciones: imputar el rango, ponderar por no respuesta y usar solo asalariados."))
    imagen(s, "02_calidad_ingreso.png", M, 1.6, 8.4, 5.05, "Barras apiladas por población (total, sexo y nivel de instrucción) con el porcentaje que declara monto exacto (A), solo rango (B), no recibe ingresos (C) o no especificó (D)", cortar=(0.62, 0.2))
    estadistica(s, 9.3, 1.65, 3.43, 1.35, f"{A_t:.0f} %", "declara el monto exacto", "Grupo A", vsize=36)
    estadistica(s, 9.3, 3.15, 3.43, 1.35, f"{B_t:.0f} %", "da solo un rango de salarios mínimos", "Grupo B", vsize=36)
    estadistica(s, 9.3, 4.65, 3.43, 1.35, f"{D_t:.0f} %", "no especifica su ingreso", "Grupo D", vsize=36)
    _, tf = caja(s, 9.3, 6.12, 3.43, 0.6, "Mensaje")
    parrafos(tf, [[(f"Más escolaridad, menos monto exacto ({A_n4:.0f} % vs. {A_n1:.0f} %)", {"size": 13, "bold": True, "spec": TC.TEXT_2})]], espacio=0)


def s_embudo(d):

    # =========================================================================== #
    # 6. Limpieza / embudo
    # =========================================================================== #
    s = d.nueva("De 419 mil registros a 112 mil observaciones, paso a paso", (
        "La limpieza es una cascada de reglas, cada una es una función con nombre, probada con datos sintéticos y registrada en una bitácora. Solo las reglas de cobertura eliminan filas; "
        "los faltantes codificados, la calidad del ingreso y los atípicos crean banderas, así que podemos cambiar una decisión y rehacer el análisis sin volver a limpiar. "
        "Un punto técnico: la ENOE no tiene nulos explícitos, un isna diría que todo está completo; los faltantes vienen como 99 en escolaridad o cero horas trabajadas. "
        "Al final, el pipeline verifica quince expectativas de calidad y se detiene si una crítica falla."))
    imagen(s, "01_embudo_datos.png", M, 1.6, 8.0, 5.05, "Gráfica de barras del embudo de registros: de 419,038 registros a 111,958 observaciones salariales", cortar=(0.62, 0.2))
    _, tf = caja(s, 8.95, 1.75, 3.78, 4.9, "Reglas")
    parrafos(tf, ["La cobertura elimina filas; todo lo demás crea banderas",
                  f"{int(bit.loc['M1', 'n_despues']):,} escolaridades = 99 y {int(bit.loc['M2', 'n_despues']):,} jornadas de 0 h recodificadas",
                  f"{int(bit.loc['O1', 'n_despues']):,} ingresos por hora atípicos (P0.5–P99.5 por entidad)",
                  "15 de 15 expectativas de calidad cumplidas",
                  "ETL idempotente: 10 s, una sola semilla y SHA-256 de cada archivo"], size=16, espacio=10, vinetas=True)


def s_arquitectura(d):

    # =========================================================================== #
    # 7. Arquitectura
    # =========================================================================== #
    s = d.nueva("Arquitectura: SQLite para analizar, MongoDB para servir", (
        "Aquí está la ingeniería de datos y la justificación del modelo. Los microdatos entran a un pipeline en Python que extrae, limpia, transforma y valida, y carga a SQLite con esquema en estrella, con llaves primarias, foráneas y restricciones CHECK. "
        "Los datos de la ENOE son tabulares, así que para analizar el modelo relacional es el adecuado. Pero para servir la ficha de una entidad a un tablero conviene un modelo documental: un documento por entidad con los indicadores anidados, sin joins, con esquema flexible. "
        "SQLite es la fuente de verdad y MongoDB es una vista de lectura que se regenera. Aclaración honesta: verificamos que la agregación de Mongo reproduce la vista SQL, pero no cargamos a un servidor real porque no hay uno instalado; los documentos están listos para mongoimport."))
    cajas = [("Microdatos INEGI", "SDEMT · COE2T", 0.6, 1.75, 2.3), ("Pipeline ETL (Python)", "extract · clean · transform · validate", 3.5, 1.75, 3.0),
             ("SQLite · esquema en estrella", "PK · FK · CHECK · vistas · auditoría", 7.1, 1.75, 2.7), ("Análisis estadístico", "Rao-Wu · modelos · Oaxaca-Blinder", 10.4, 1.75, 2.33),
             ("MongoDB · documentos", "entidades · personas · metadatos", 7.1, 3.55, 2.7), ("Tablero interactivo", "HTML · 6 gráficas · ficha por entidad", 10.4, 3.55, 2.33)]
    for i, (a, b, x, y, w) in enumerate(cajas):
        sh = tarjeta(s, x, y, w, 1.3, f"Caja {i + 1}", fondo=TC.TEXT_2 if i in (2, 4) else TC.BACKGROUND_2)
        claro = i in (2, 4)
        texto_en_forma(sh, [[(a, {"size": 16, "bold": True, "spec": TC.BACKGROUND_1 if claro else TC.TEXT_2})], [(b, {"size": 13, "spec": RGB["soft"] if claro else TC.TEXT_1})]], espacio=2)
    for x, y in [(2.95, 2.2), (6.55, 2.2), (9.85, 2.2), (9.85, 4.0)]:
        f = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(0.5), Inches(0.4))
        f.name = "Flecha"
        f.shadow.inherit = False
        f.line.fill.background()
        f.fill.solid()
        color(f.fill.fore_color, TC.ACCENT_1)
    f = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(8.25), Inches(3.1), Inches(0.4), Inches(0.42))
    f.name = "Flecha abajo"
    f.shadow.inherit = False
    f.line.fill.background()
    f.fill.solid()
    color(f.fill.fore_color, TC.ACCENT_1)
    for i, (t_, d_) in enumerate([("Relacional (SQLite): analizar", "Datos tabulares de esquema fijo · agregaciones ponderadas y JOIN · integridad por restricciones · fuente de verdad"),
                                   ("Documental (MongoDB): servir", "Una ficha por entidad (embedding) · el esquema crece sin migraciones · lectura por clave · vista que se regenera")]):
        x = M + i * 6.2
        tarjeta(s, x, 5.1, 5.93, 1.6, f"Justificación {i + 1}")
        _, tf = caja(s, x + 0.25, 5.2, 5.43, 1.4, f"Justificación {i + 1} texto", MSO_ANCHOR.MIDDLE)
        parrafos(tf, [[(t_, {"size": 17, "bold": True, "spec": TC.TEXT_2})], [(d_, {"size": 14})]], espacio=4)


def s_diseno_complejo(d):

    # =========================================================================== #
    # 8. Diseño complejo
    # =========================================================================== #
    s = d.nueva("Ignorar el diseño muestral subestimaría el error a la mitad", (
        "La ENOE es una encuesta por conglomerados y estratos: las personas de una misma unidad primaria se parecen entre sí. Si tratáramos los datos como una muestra aleatoria simple, los errores estándar saldrían demasiado pequeños. "
        f"Medimos el efecto de diseño: {deff.loc['TIL1 nacional', 'deff']:.1f} para la informalidad, es decir, los {n_u:,} ocupados valen como unas {deff.loc['TIL1 nacional', 'n_efectivo'] / 1000:.0f} mil observaciones independientes. "
        "Por eso usamos el bootstrap de Rao y Wu con mil réplicas: remuestrea unidades dentro de estratos. Probamos que reproduce la varianza de linealización de Taylor, y que los dominios conservan todas las unidades del diseño."))
    cd = CategoryChartData()
    cd.categories = ["TIL1 nacional (puntos porcentuales)", "Brecha por hora (puntos logarítmicos)"]
    cd.add_series("Si fuera muestra aleatoria simple", (100 * deff.loc["TIL1 nacional", "ee_mas"], 100 * deff.loc["Brecha por hora total (log-puntos)", "ee_mas"]))
    cd.add_series("Con el diseño complejo (Rao-Wu)", (100 * deff.loc["TIL1 nacional", "ee_diseno"], 100 * deff.loc["Brecha por hora total (log-puntos)", "ee_diseno"]))
    _, tf = caja(s, M, 1.65, 7.6, 0.4, "Subtítulo de la gráfica")
    parrafos(tf, [[("Error estándar de dos estimaciones clave", {"size": 16, "bold": True, "spec": TC.TEXT_2})]], espacio=0)
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(M), Inches(2.1), Inches(7.6), Inches(4.5), cd)
    gf.name = "Gráfica de errores estándar"
    ch = gf.chart
    estilo_grafica(ch)
    ch.has_title = False
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.BOTTOM
    ch.legend.include_in_layout = False
    ch.legend.font.size = Pt(14)
    eje_valores(ch, "0.0")
    pl = ch.plots[0]
    pl.gap_width = 90
    pl.overlap = -10
    pl.has_data_labels = True
    pl.data_labels.number_format = "0.00"
    pl.data_labels.number_format_is_linked = False
    pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    pl.data_labels.font.size = Pt(14)
    pl.series[0].format.fill.solid()
    pl.series[0].format.fill.fore_color.rgb = rgb("A9A8A0")
    pl.series[1].format.fill.solid()
    color(pl.series[1].format.fill.fore_color, TC.ACCENT_1)
    estadistica(s, 8.6, 1.65, 4.13, 1.5, f"×{deff.loc['TIL1 nacional', 'deff']:.1f}", "efecto de diseño en la informalidad", "Efecto de diseño", vsize=38)
    estadistica(s, 8.6, 3.3, 4.13, 1.5, f"{deff.loc['TIL1 nacional', 'n_efectivo'] / 1000:.0f} mil", f"observaciones efectivas de {n_u / 1000:.0f} mil", "Observaciones efectivas", vsize=38)
    estadistica(s, 8.6, 4.95, 4.13, 1.5, f"{R['B']:,}", "réplicas de Rao-Wu · 713 estratos · 21,194 UPM", "Réplicas", vsize=38)


def s_rendimiento(d):

    # =========================================================================== #
    # 9. Rendimiento de la escolaridad
    # =========================================================================== #
    s = d.nueva(f"Cada año de estudio eleva el ingreso por hora {rt['nacional_pct']['est']:.1f} %, y la licenciatura casi lo duplica", (
        f"Resultado central del objetivo uno. Con la ecuación de Mincer, controlando edad, sexo, entidad y tamaño de localidad, cada año adicional de escolaridad eleva el ingreso por hora {rt['nacional_pct']['est']:.1f} por ciento, con un intervalo de {rt['nacional_pct']['ic_inf']:.1f} a {rt['nacional_pct']['ic_sup']:.1f}. "
        f"No es lineal: terminar licenciatura o posgrado paga {prem.loc['Licenciatura o posgrado (16+ años)', 'premio_pct']:.0f} por ciento más que no terminar la primaria. Las mujeres obtienen un rendimiento mayor, {rt['mujeres_pct']['est']:.1f} contra {rt['hombres_pct']['est']:.1f} por ciento. "
        f"Y es robusto: va de {robr['retorno_pct'].min():.1f} a {robr['retorno_pct'].max():.1f} por ciento en siete especificaciones, incluyendo imputar el ingreso faltante y ponderar por no respuesta."))
    cd = CategoryChartData()
    cd.categories = ["Primaria completa", "Secundaria completa", "Media superior", "Licenciatura o posgrado"]
    cd.add_series("Premio salarial (%)", [float(prem.loc[k, "premio_pct"]) for k in ["Primaria completa", "Secundaria completa", "Media superior / superior trunca (12-15 años)", "Licenciatura o posgrado (16+ años)"]])
    _, tf = caja(s, M, 1.65, 7.6, 0.4, "Subtítulo de la gráfica")
    parrafos(tf, [[("Premio salarial frente a no terminar primaria (%, con IC en el cuaderno)", {"size": 16, "bold": True, "spec": TC.TEXT_2})]], espacio=0)
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(M), Inches(2.1), Inches(7.6), Inches(4.5), cd)
    gf.name = "Gráfica del premio por nivel"
    ch = gf.chart
    estilo_grafica(ch)
    ch.has_title = False
    ch.has_legend = False
    eje_valores(ch, '0"%"')
    pl = ch.plots[0]
    pl.gap_width = 70
    pl.has_data_labels = True
    pl.data_labels.number_format = '0"%"'
    pl.data_labels.number_format_is_linked = False
    pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    pl.data_labels.font.size = Pt(16)
    pl.data_labels.font.bold = True
    pl.series[0].format.fill.solid()
    color(pl.series[0].format.fill.fore_color, TC.ACCENT_1)
    estadistica(s, 8.6, 1.65, 4.13, 1.75, f"+{rt['nacional_pct']['est']:.1f} %", f"por año de escolaridad (IC 95 %: {rt['nacional_pct']['ic_inf']:.1f} a {rt['nacional_pct']['ic_sup']:.1f})", "Rendimiento", vsize=44)
    tarjeta(s, 8.6, 3.55, 4.13, 3.05, "Detalles del rendimiento")
    _, tf = caja(s, 8.85, 3.7, 3.65, 2.75, "Detalles del rendimiento texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [f"Mujeres {rt['mujeres_pct']['est']:.1f} % vs. hombres {rt['hombres_pct']['est']:.1f} % por año",
                  f"Robusto: {robr['retorno_pct'].min():.1f} %–{robr['retorno_pct'].max():.1f} % en 7 especificaciones",
                  f"Spearman nacional ρ = {R['retorno']['spearman_nacional']['est']:.2f}"], size=16, espacio=10, vinetas=True)


def s_estados(d):

    # =========================================================================== #
    # 10. Estados
    # =========================================================================== #
    s = d.nueva("Estudiar rinde parecido en estados ricos y pobres", (
        f"Para el objetivo uno comparamos estados de mayor y menor ingreso. Agrupamos las 32 entidades en cuartiles de ingreso mediano por hora —el agrupamiento se recalcula en cada réplica para no ignorar su incertidumbre— y comparamos el rendimiento medio del cuartil más rico con el del más pobre. "
        f"La diferencia es prácticamente cero: {dq['est']:.3f} log-puntos, con p igual a {dq['p']:.2f}. No hay evidencia de que estudiar rinda más o menos según la riqueza del estado. "
        f"Lo que sí cambia entre estados es el nivel de ingreso. Y cada estado individual va de {ret_min['ret_est']:.1f} por ciento en {ret_min['entidad']} a {ret_max['ret_est']:.1f} en {ret_max['entidad']}, con intervalos amplios. Advertencia: son relaciones entre estados, no efectos causales individuales."))
    imagen(s, "05_retorno_estados.png", M, 1.5, 7.3, 5.45, "Gráfica de puntos con intervalos de confianza del rendimiento por año de escolaridad en cada entidad, coloreados por cuartil de ingreso estatal", cortar=(0.74, 0.2))
    estadistica(s, 8.2, 1.65, 4.53, 1.55, "≈ 0", f"diferencia de rendimiento entre estados ricos (Q4) y pobres (Q1): {dq['est']:+.3f} log-puntos, p = {dq['p']:.2f}", "Q4 menos Q1", vsize=40, lsize=14)
    estadistica(s, 8.2, 3.35, 4.53, 1.55, f"{ret_min['ret_est']:.1f}–{ret_max['ret_est']:.1f} %", f"rango entre estados: de {ret_min['entidad']} a {ret_max['entidad']}", "Rango", vsize=36, lsize=14)
    estadistica(s, 8.2, 5.05, 4.53, 1.55, f"{rt['mujeres_pct']['est']:.1f} vs. {rt['hombres_pct']['est']:.1f} %", "rendimiento por año de mujeres vs. hombres", "Por sexo", vsize=36, lsize=14)


def s_ranking(d):

    # =========================================================================== #
    # 11. Spearman
    # =========================================================================== #
    s = d.nueva("Un ranking defendible distingue solo los extremos", (
        f"Métrica dos. Para cada entidad calculamos el Spearman ponderado entre años de escolaridad e ingreso por hora, con su intervalo por bootstrap. A la derecha de la gráfica está el lugar de cada estado con su propio intervalo, porque el ranking también es incierto. "
        f"La Ciudad de México encabeza con {rho_max['rho_est']:.2f} y su lugar es uno o dos con seguridad. {rho_min['entidad']} tiene el menor vínculo, {rho_min['rho_est']:.2f}. Pero los estados del centro del ranking tienen intervalos de lugar de quince o más posiciones: no se pueden distinguir. "
        "Un ranking defendible es el que reporta esa incertidumbre; por eso solo afirmamos los extremos."))
    imagen(s, "06_spearman_estados.png", M, 1.5, 7.6, 5.45, "Gráfica de puntos con intervalos de confianza del Spearman por entidad y su lugar en el ranking con intervalo", cortar=(0.74, 0.2))
    estadistica(s, 8.5, 1.65, 4.23, 1.55, f"{R['retorno']['spearman_nacional']['est']:.2f}", "Spearman nacional: asociación positiva y moderada", "Nacional", vsize=40)
    estadistica(s, 8.5, 3.35, 4.23, 1.55, f"{rho_max['rho_est']:.2f} → {rho_min['rho_est']:.2f}", f"de {rho_max['entidad']} (lugar 1–2) a {rho_min['entidad']} (23–32)", "Extremos", vsize=34, lsize=14)
    tarjeta(s, 8.5, 5.05, 4.23, 1.55, "Interpretación del ranking")
    _, tf = caja(s, 8.7, 5.15, 3.85, 1.35, "Interpretación del ranking texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[("Los lugares centrales abarcan 15 o más posiciones: ", {"bold": True, "size": 15}), ("no son estadísticamente distinguibles.", {"size": 15})]], espacio=0)


def s_brecha_hora_mes(d):

    # =========================================================================== #
    # 12. Brecha hora vs mes
    # =========================================================================== #
    s = d.nueva(f"Por hora la brecha es de {tot['brecha_hora_pct']:.1f} %; por mes, de {tot['brecha_mens_pct']:.1f} %", (
        f"Métrica uno. La brecha se define como uno menos el cociente del ingreso medio geométrico de las mujeres entre el de los hombres. Por hora es {tot['brecha_hora_pct']:.1f} por ciento, con intervalo de {tot['brecha_hora_inf']:.1f} a {tot['brecha_hora_sup']:.1f} y p menor a 0.001. "
        f"Por nivel de instrucción va de {bn.iloc[3]['brecha_hora_pct']:.1f} a {bn.iloc[1]['brecha_hora_pct']:.1f} por ciento y las cuatro son significativas incluso con el ajuste de Holm; las pruebas clásicas de Welch y Mann-Whitney coinciden. "
        f"El tamaño de efecto es pequeño, la d de Cohen va de 0.06 a 0.24. Pero por mes la brecha es de {tot['brecha_mens_pct']:.1f} por ciento. La diferencia viene de las horas: las mujeres trabajan {tot['menos_horas_mujeres_pct']:.0f} por ciento menos horas pagadas. "
        "En logaritmos la identidad es exacta: brecha mensual igual a brecha por hora más brecha de horas."))
    imagen(s, "09_brecha_por_nivel.png", M, 1.6, 8.7, 4.55, "Dos paneles de barras con intervalos: brecha de género por hora y por mes, por nivel de instrucción y total", cortar=(0.62, 0.2))
    _, tf = caja(s, M, 6.25, 8.7, 0.6, "Definición de la brecha")
    parrafos(tf, [[("Brecha = 1 − (ingreso medio geométrico de las mujeres ÷ el de los hombres), con IC 95 %; misma escala en ambos paneles.", {"size": 13, "spec": RGB["muted"]})]], espacio=0)
    estadistica(s, 9.55, 1.65, 3.18, 1.5, f"{tot['brecha_hora_pct']:.1f} %", "por hora (IC 2.3–5.0)", "Brecha por hora", vsize=36, lsize=14)
    estadistica(s, 9.55, 3.3, 3.18, 1.5, f"{tot['brecha_mens_pct']:.1f} %", "por mes", "Brecha mensual", vsize=36, lsize=14)
    estadistica(s, 9.55, 4.95, 3.18, 1.5, f"−{tot['menos_horas_mujeres_pct']:.0f} %", f"horas pagadas: {tot['horas_m']:.1f} vs. {tot['horas_h']:.1f} h por semana", "Horas", vsize=36, lsize=14)


def s_comparables(d):

    # =========================================================================== #
    # 13. Comparables y abajo
    # =========================================================================== #
    s = d.nueva("Entre personas comparables, la brecha por hora ronda 8 %", (
        f"Para saber qué pasa con personas comparables fuimos agregando controles: la brecha sube de {esc.iloc[0]['brecha_pct']:.1f} a {g5['brecha_pct']:.1f} por ciento. Primero sube porque las mujeres de la muestra tienen más escolaridad, lo que ocultaba parte de la brecha. "
        "El último modelo, con horas trabajadas, da 16 por ciento pero no se interpreta: hay un sesgo de división, porque el ingreso por hora es ingreso entre horas y un error en las horas crea una relación negativa mecánica. "
        "La descomposición de Oaxaca-Blinder, que está en el anexo, dice lo mismo: la parte explicada es negativa —las mujeres tienen mejores características— y la no explicada es de unos siete puntos."))
    imagen(s, "10_escalera_controles.png", M, 1.6, 8.5, 4.5, "Gráfica de puntos con intervalos de la brecha por hora al agregar controles sucesivos", cortar=(0.62, 0.2))
    _, tf = caja(s, M, 6.25, 8.5, 0.6, "Lectura de la escalera")
    parrafos(tf, [[("Cada fila agrega controles al anterior; la última (horas) no se interpreta por el sesgo de división.", {"size": 13, "spec": RGB["muted"]})]], espacio=0)
    estadistica(s, 9.4, 1.65, 3.33, 1.5, f"{esc.iloc[0]['brecha_pct']:.1f} %", "sin controles", "Sin controles", vsize=36, lsize=14)
    estadistica(s, 9.4, 3.3, 3.33, 1.5, f"{g5['brecha_pct']:.1f} %", "con escolaridad, edad, lugar, empleo y rama", "Ajustada", vsize=36, lsize=14)
    estadistica(s, 9.4, 4.95, 3.33, 1.5, "≈ 7 pts", "parte no explicada (Oaxaca-Blinder)", "No explicada", vsize=32, lsize=14)


def s_cuantiles(d):

    s = d.nueva("La brecha se concentra en la parte baja de la distribución", (
        f"La brecha no está repartida parejo. Comparamos los percentiles del ingreso por hora de hombres y mujeres: en el percentil diez la brecha es de {cu.loc[10, 'brecha_pct']:.1f} por ciento y en el veinticinco de {cu.loc[25, 'brecha_pct']:.1f}, ambas significativas. "
        f"En la mediana baja a {cu.loc[50, 'brecha_pct']:.1f} por ciento y ya no es significativa, y en los percentiles setenta y cinco y noventa es nula o incluso favorece ligeramente a las mujeres. "
        "Es un patrón de piso pegajoso: la desventaja pesa más donde el salario es bajo —informalidad, servicio doméstico, comercio—, así que políticas como el salario mínimo y la formalización pueden incidir más en la brecha que las que apuntan a puestos directivos. "
        "Nota: las medianas de ingreso tienen redondeo en cifras exactas, por eso los intervalos son discretos."))
    imagen(s, "12_brecha_cuantiles.png", M, 1.6, 8.5, 4.6, "Gráfica de líneas con intervalo de la brecha de género en los percentiles 10 a 90 del ingreso por hora", cortar=(0.55, 0.2))
    estadistica(s, 9.4, 1.65, 3.33, 1.5, f"{cu.loc[10, 'brecha_pct']:.0f}–{cu.loc[25, 'brecha_pct']:.0f} %", "en el 10 %–25 % que menos gana", "Abajo", vsize=36, lsize=14)
    estadistica(s, 9.4, 3.3, 3.33, 1.5, f"{cu.loc[50, 'brecha_pct']:.1f} %", "en la mediana (no significativa)", "Mediana", vsize=36, lsize=14)
    estadistica(s, 9.4, 4.95, 3.33, 1.5, "≈ 0", "en el 25 % que más gana", "Arriba", vsize=36, lsize=14)


def s_informalidad(d):

    # =========================================================================== #
    # 14. Informalidad
    # =========================================================================== #
    s = d.nueva(f"La informalidad cae con la escolaridad: de {til1['por_nivel']['1']:.0f} % a {til1['por_nivel']['4']:.0f} %", (
        f"Objetivo tres. La informalidad laboral nacional es {til1['nacional']['est']:.1f} por ciento, que coincide con la cifra oficial. El cartograma de mosaicos da la misma área a cada estado para que ninguno domine por su tamaño: va de {mn['til1_est']:.0f} por ciento en {mn['entidad']} a {mx['til1_est']:.0f} en {mx['entidad']}. "
        f"Por escolaridad, {til1['por_nivel']['1']:.0f} por ciento entre quienes no terminaron la primaria contra {til1['por_nivel']['4']:.0f} con medio superior o superior. Entre estados, el Spearman entre escolaridad promedio e informalidad es {R['til1_vs_escolaridad_estatal']['rho_spearman_til_esc']['est']:.2f}. "
        f"A nivel individual, cada año de escolaridad reduce {abs(ind['ame_anios_esc_pp']):.1f} puntos la probabilidad de informalidad, y ser mujer la aumenta {ind['ame_mujer_pp']:.1f} puntos a igual escolaridad, edad y lugar. Cuidado con la falacia ecológica: la relación entre estados no es un efecto individual."))
    imagen(s, "14_mapa_informalidad.png", M, 1.6, 7.6, 4.4, "Cartograma de mosaicos de México con la tasa de informalidad laboral de cada entidad en una escala de azules", cortar=(0.62, 0.2))
    estadistica(s, 8.5, 1.65, 4.23, 1.0, f"{til1['nacional']['est']:.1f} %", "informalidad nacional (TIL1)", "Nacional", vsize=30, lsize=13)
    estadistica(s, 8.5, 2.8, 4.23, 1.0, f"{mn['til1_est']:.0f} → {mx['til1_est']:.0f} %", f"de {mn['entidad']} a {mx['entidad']}", "Rango estatal", vsize=30, lsize=13)
    estadistica(s, 8.5, 3.95, 4.23, 1.0, f"{til1['por_nivel']['1']:.0f} → {til1['por_nivel']['4']:.0f} %", "de primaria incompleta a media superior o más", "Por escolaridad", vsize=30, lsize=13)
    estadistica(s, 8.5, 5.1, 4.23, 1.0, f"{ind['ame_anios_esc_pp']:+.1f} pp", "por cada año de escolaridad (individual)", "Efecto individual", vsize=30, lsize=13)
    _, tf = caja(s, M, 6.1, 7.6, 0.8, "Lectura")
    parrafos(tf, [[(f"Entre estados, Spearman = {R['til1_vs_escolaridad_estatal']['rho_spearman_til_esc']['est']:.2f}. ", {"bold": True, "size": 15, "spec": TC.TEXT_2}), ("TIL1 = ocupados en empleo informal ÷ ocupados de 15+ (definición del INEGI); las mujeres suman +6 puntos a igual escolaridad, edad y lugar.", {"size": 15})]], espacio=0)


def s_conclusiones(d):

    # =========================================================================== #
    # 15. Conclusiones
    # =========================================================================== #
    s = d.nueva("Estudiar paga en todas partes; la brecha de género es de horas", (
        "Cierre de los resultados. Tres mensajes. Uno: estudiar paga alrededor de cinco por ciento por año y casi se duplica el ingreso con licenciatura, y rinde parecido en todos los estados, así que ampliar el acceso y la permanencia rinde en todas las regiones. "
        "Dos: la desigualdad de género mensual es sobre todo de horas pagadas, no de salario por hora; las políticas de cuidados y la atención a los percentiles bajos son las palancas. "
        "Tres: la informalidad se concentra donde se estudia menos, sobre todo en el Sur. A la derecha, el estatus de las métricas del protocolo: las tres se cumplen. "
        "Y la advertencia que no hay que olvidar: son asociaciones, no causalidad."))
    tarjeta(s, M, 1.65, 6.0, 4.0, "Qué encontramos")
    _, tf = caja(s, M + 0.25, 1.78, 5.5, 3.8, "Qué encontramos texto")
    parrafos(tf, [[("Qué encontramos", {"size": 20, "bold": True, "spec": TC.TEXT_2})],
                  f"Estudiar rinde ≈ {rt['nacional_pct']['est']:.1f} % por año y la licenciatura casi duplica el ingreso",
                  f"El rendimiento es igual en estados ricos y pobres (p = {dq['p']:.2f})",
                  f"Brecha de {tot['brecha_hora_pct']:.1f} % por hora y {tot['brecha_mens_pct']:.1f} % por mes: es de horas",
                  f"Informalidad: {til1['por_nivel']['1']:.0f} % → {til1['por_nivel']['4']:.0f} % con la escolaridad"], size=18, espacio=10)
    tarjeta(s, 6.85, 1.65, 5.88, 4.0, "Qué recomendamos")
    _, tf = caja(s, 7.1, 1.78, 5.4, 3.8, "Qué recomendamos texto")
    parrafos(tf, [[("Qué recomendamos", {"size": 20, "bold": True, "spec": TC.TEXT_2})],
                  "Ampliar acceso y permanencia escolar, sobre todo en el Sur (informalidad 69 %)",
                  "Políticas de cuidados y horarios flexibles de tiempo completo para cerrar la brecha de horas",
                  "Atender el «piso pegajoso»: salario mínimo y formalización en los percentiles bajos",
                  "Publicar ingresos imputados por rango y corregir por no respuesta"], size=18, espacio=10)
    for i, (m, txt) in enumerate([("M1", "Brecha por nivel con IC y prueba: cumplida"), ("M2", "Spearman de 32 entidades con IC y ranking: cumplida"), ("M3", "Tablero ≥ 4 gráficas sobre base NoSQL: cumplida")]):
        x = M + i * 4.1
        sh = tarjeta(s, x, 5.9, 3.95, 0.85, f"Métrica {m} cumplida", fondo=TC.TEXT_2)
        texto_en_forma(sh, [[(f"{m} ✓  ", {"size": 18, "bold": True, "spec": TC.BACKGROUND_1}), (txt, {"size": 13, "spec": TC.BACKGROUND_1})]], alinear=PP_ALIGN.LEFT, margen=0.18)


def s_limitaciones(d):

    # =========================================================================== #
    # 16. Limitaciones
    # =========================================================================== #
    s = d.nueva("Qué no podemos afirmar, y qué haríamos después", (
        "Es importante ser honestos con los límites. Son asociaciones y no causalidad: el rendimiento de estudiar mezcla el efecto de la escolaridad con habilidad no observada. Solo vemos el ingreso de quien trabaja y lo declara, así que hay selección; la mitigamos con ponderación por no respuesta e imputación por rangos, pero no la eliminamos. "
        "El ingreso por hora se calcula con las horas de una sola semana. Es un solo trimestre. Y por estado tenemos entre mil novecientas y cinco mil novecientas observaciones, por eso reportamos intervalos. "
        "Dos aclaraciones técnicas: no cargamos los documentos a un servidor MongoDB real porque no hay uno instalado, y el significado literal de los códigos de rangos de salarios mínimos lo inferimos de su correspondencia exacta con otra variable. "
        "Con más tiempo: varios trimestres con el panel rotativo, corrección por selección de Heckman, un mapa geográfico real y estimaciones para áreas pequeñas."))
    tarjeta(s, M, 1.65, 6.0, 5.05, "Límites")
    _, tf = caja(s, M + 0.25, 1.8, 5.5, 4.8, "Límites texto")
    parrafos(tf, [[("Límites", {"size": 20, "bold": True, "spec": TC.TEXT_2})],
                  "Asociación, no causalidad (habilidad no observada; falacia ecológica entre estados)",
                  "Solo vemos el ingreso de quien trabaja y lo declara (selección)",
                  "Ingreso autorreportado, con redondeo; horas de una sola semana",
                  "Un trimestre; 1,900–5,900 observaciones por estado",
                  "MongoDB: documentos verificados, carga a servidor real pendiente"], size=18, espacio=10, vinetas=False)
    tarjeta(s, 6.85, 1.65, 5.88, 5.05, "Próximos pasos")
    _, tf = caja(s, 7.1, 1.8, 5.4, 4.8, "Próximos pasos texto")
    parrafos(tf, [[("Con más tiempo", {"size": 20, "bold": True, "spec": TC.TEXT_2})],
                  "Varios trimestres (panel rotativo de la ENOE)",
                  "Corrección de selección (Heckman) para la participación laboral",
                  "Mapa geográfico real con el Marco Geoestadístico",
                  "Estimaciones para áreas pequeñas (municipios)",
                  "Contrastar los códigos de rangos con el cuestionario oficial"], size=18, espacio=10)


def s_gracias(d):

    # =========================================================================== #
    # 17. Cierre
    # =========================================================================== #
    s = d.nueva("Gracias", (
        "Cierre. Todo está reproducible: el cuaderno ejecutado, el tablero interactivo, el pipeline, las pruebas y la documentación están en la carpeta del proyecto. "
        "Abran el espacio para preguntas; la guía de defensa en la carpeta docs tiene las preguntas más probables con sus respuestas."), oscuro=True, con_pie=False)
    t = s.shapes.title
    t.top, t.height = Inches(1.9), Inches(1.3)
    t.text_frame.paragraphs[0].runs[0].font.size = Pt(54)
    _, tf = caja(s, M, 3.35, 11.5, 0.7, "Preguntas")
    parrafos(tf, [[("¿Preguntas?", {"size": 30, "spec": RGB["soft"]})]], espacio=0)
    tarjeta(s, M, 4.45, 12.13, 1.9, "Dónde está todo", fondo=RGB["navy2"])
    _, tf = caja(s, M + 0.3, 4.6, 11.5, 1.6, "Dónde está todo texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[("Carpeta Proyecto_ENOE: ", {"size": 16, "bold": True, "spec": TC.BACKGROUND_1}),
                   ("cuaderno (notebooks/) · tablero interactivo (tablero/) · código (src/ y scripts/) · documentación y guía de defensa (docs/) · pruebas (tests/)", {"size": 16, "spec": TC.BACKGROUND_1})],
                  [("Reproducir todo: ", {"size": 16, "bold": True, "spec": TC.BACKGROUND_1}), ("python scripts/run_etl.py → run_analysis.py → make_figures.py → build_notebook.py", {"size": 16, "spec": RGB["soft"]})]], espacio=8)


def s_anexos(d):

    # =========================================================================== #
    # Anexos
    # =========================================================================== #
    s = d.nueva("Anexos", "Diapositivas de respaldo para responder preguntas: robustez de la brecha, descomposición de Oaxaca-Blinder, informalidad vs. escolaridad, el tablero y los diagnósticos del modelo.", oscuro=True, con_pie=False)
    t = s.shapes.title
    t.top, t.height = Inches(2.9), Inches(1.3)
    t.text_frame.paragraphs[0].runs[0].font.size = Pt(54)
    _, tf = caja(s, M, 4.2, 11.5, 1.0, "Contenido de anexos")
    parrafos(tf, [[("Robustez de la brecha · Oaxaca-Blinder · Informalidad vs. escolaridad · Tablero interactivo · Diagnósticos", {"size": 20, "spec": RGB["soft"]})]], espacio=0)


def s_robustez(d):

    # A1 robustez
    s = d.nueva(f"La brecha por hora es positiva en todas las muestras, pero su tamaño va de {hora_specs['brecha_pct'].min():.1f} % a {hora_specs['brecha_pct'].max():.1f} %", (
        "Respaldo. Probamos la brecha bajo diez especificaciones. El signo es siempre positivo, pero el tamaño depende de a quién se incluya: de 0.7 por ciento si imputamos el grupo que solo dio rango —que sesga hacia cero por construcción, porque asigna el mismo ingreso a un hombre y a una mujer del mismo rango— a 4.6 sin ponderar. "
        "La estimación más robusta de personas comparables es 8.2 por ciento, sin horas. La brecha mensual, 26.9, es indiscutible."))
    imagen(s, "13_robustez_brecha.png", M, 1.6, 8.3, 5.1, "Gráfica de puntos con intervalos de la brecha total bajo diez especificaciones", cortar=(0.62, 0.2))
    tarjeta(s, 9.1, 1.65, 3.63, 5.0, "Lectura de la robustez")
    _, tf = caja(s, 9.3, 1.8, 3.23, 4.7, "Lectura de la robustez texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[("S3 sesga hacia cero: ", {"bold": True, "size": 15}), ("imputar el rango asigna el mismo ingreso a hombres y mujeres.", {"size": 15})],
                  [("S4 (IPW) la sube a ", {"size": 15}), (f"{rob_tot.loc['S4 Ajuste por no respuesta', 'brecha_pct']:.1f} %", {"bold": True, "size": 15}), (".", {"size": 15})],
                  [("Ajustada sin horas: ", {"bold": True, "size": 15}), (f"{g5['brecha_pct']:.1f} %", {"size": 15}), (". Con horas hay sesgo de división.", {"size": 15})]], espacio=12)


def s_oaxaca(d):

    # A2 Oaxaca
    s = d.nueva("Oaxaca-Blinder: las mujeres tienen mejores características, pero un residuo desfavorable", (
        "Respaldo. Descomponemos la brecha por hora con la referencia agrupada de Neumark. La parte explicada es negativa: las características medibles de las mujeres, sobre todo su mayor escolaridad, favorecerían un ingreso por hora más alto. "
        "La parte no explicada es de unos siete puntos logarítmicos: si las mujeres fueran pagadas como los hombres con las mismas características, ganarían alrededor de siete por ciento más por hora. "
        "No prueba discriminación: incluye ocupación específica, experiencia real, negociación y selección. Con los coeficientes de hombres o mujeres como referencia la conclusión es la misma."))
    imagen(s, "11_oaxaca_blinder.png", M, 1.6, 8.5, 5.1, "Barras con intervalos de la descomposición de Oaxaca-Blinder: brecha total, parte explicada por componentes y parte no explicada", cortar=(0.62, 0.2))
    tarjeta(s, 9.3, 1.65, 3.43, 5.0, "Lectura de Oaxaca")
    _, tf = caja(s, 9.5, 1.8, 3.03, 4.7, "Lectura de Oaxaca texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[("Explicada: ", {"bold": True, "size": 15}), ("negativa; la mayor escolaridad de las mujeres favorecería su ingreso.", {"size": 15})],
                  [("No explicada: ", {"bold": True, "size": 15}), ("≈ 7 puntos; no prueba discriminación.", {"size": 15})],
                  [("Con horas ", {"size": 15}), ("el residuo sube a 14 puntos por el sesgo de división.", {"size": 15})]], espacio=12)


def s_inf_vs_escolaridad(d):

    # A3 informalidad vs escolaridad
    s = d.nueva("Donde se estudia más hay menos informalidad (relación entre estados)", (
        f"Respaldo. Cada punto es una entidad. El Spearman entre escolaridad promedio e informalidad es {R['til1_vs_escolaridad_estatal']['rho_spearman_til_esc']['est']:.2f} y la pendiente es de {R['til1_vs_escolaridad_estatal']['pendiente_til_esc']['est']:.1f} puntos porcentuales por año de escolaridad promedio. "
        "Es una relación entre estados, no un efecto individual; el efecto individual lo estimamos aparte con un logit ponderado: la razón de momios por año es 0.82."))
    imagen(s, "15_informalidad_vs_escolaridad.png", M, 1.6, 8.3, 5.1, "Dispersión de la escolaridad promedio contra la tasa de informalidad de las 32 entidades con su recta de ajuste", cortar=(0.62, 0.2))
    estadistica(s, 9.1, 1.65, 3.63, 1.5, f"{R['til1_vs_escolaridad_estatal']['rho_spearman_til_esc']['est']:.2f}", "Spearman entre estados", "Spearman estatal", vsize=40)
    estadistica(s, 9.1, 3.3, 3.63, 1.5, f"{R['til1_vs_escolaridad_estatal']['pendiente_til_esc']['est']:.1f}", "puntos porcentuales por año de escolaridad promedio", "Pendiente", vsize=40, lsize=13)
    estadistica(s, 9.1, 4.95, 3.63, 1.5, "0.82", "razón de momios individual por año de escolaridad", "Razón de momios", vsize=40, lsize=13)


def s_tablero(d):

    # A4 tablero
    s = d.nueva("Tablero interactivo: la ficha de cada entidad", (
        "Respaldo para la métrica tres. El tablero es un único archivo HTML que funciona sin internet. Lo alimenta la colección de entidades exportada para MongoDB. Tiene un selector de entidad y un selector de indicador: el mapa de mosaicos y el ranking cambian con el indicador, dos dispersiones, las brechas por nivel, la calidad del ingreso y una vista de tabla accesible con las 32 entidades. "
        "También muestra el documento JSON de la entidad elegida, para ver cómo se guarda y se consulta."))
    ruta_t = ROOT / "presentacion" / "img" / "tablero.jpg"
    if ruta_t.exists():
        imagen(s, "tablero.jpg", M, 1.6, 7.4, 5.15, "Captura del tablero interactivo con KPIs, mapa de mosaicos y ranking de las entidades", ruta=ruta_t, cortar=dict(caja_px=(0, 0, 800, 692)))
    tarjeta(s, 8.5, 1.65, 4.23, 5.0, "Qué incluye el tablero")
    _, tf = caja(s, 8.75, 1.8, 3.75, 4.7, "Qué incluye el tablero texto", MSO_ANCHOR.MIDDLE)
    parrafos(tf, [[("Qué incluye", {"size": 18, "bold": True, "spec": TC.TEXT_2})],
                  "Selector de entidad e indicador",
                  "Mapa de mosaicos y ranking con IC",
                  "Dos dispersiones y brechas por nivel",
                  "Calidad del ingreso por entidad",
                  "Tabla accesible y documento JSON de la entidad"], size=15, espacio=8, vinetas=False)


def s_diagnosticos(d):

    # A5 diagnósticos
    dg = R["diagnosticos"]
    s = d.nueva("Diagnóstico del modelo: varianza no constante y colas pesadas, por eso errores robustos", (
        f"Respaldo. En el modelo con todos los controles hay heterocedasticidad —Breusch-Pagan rechaza— y colas algo pesadas, curtosis en exceso de {dg['curtosis_exceso_residuos']:.1f}. Por eso toda la inferencia usa errores estándar robustos de diseño y no supuestos de normalidad. "
        f"No hay multicolinealidad, el VIF máximo es {dg['vif_max_variables_clave']:.1f}, ni observaciones influyentes: la distancia de Cook máxima es {dg['cook_max']:.4f}, y el coeficiente de mujer casi no cambia si quitamos el 0.1 por ciento más influyente."))
    imagen(s, "16_diagnosticos_modelo.png", M, 1.6, 8.5, 4.6, "Gráficas de residuos contra ajustados y de cuantiles contra cuantiles normales del modelo con todos los controles", cortar=(0.62, 0.2))
    estadistica(s, 9.3, 1.65, 3.43, 1.4, f"{dg['vif_max_variables_clave']:.1f}", "VIF máximo: sin multicolinealidad", "VIF", vsize=36, lsize=13)
    estadistica(s, 9.3, 3.2, 3.43, 1.4, f"{dg['cook_max']:.4f}", "distancia de Cook máxima: sin influyentes", "Cook", vsize=30, lsize=13)
    estadistica(s, 9.3, 4.75, 3.43, 1.4, f"{dg['curtosis_exceso_residuos']:.1f}", "curtosis en exceso de los residuos", "Curtosis", vsize=36, lsize=13)


ORDEN_CORTA = [s_portada, s_pregunta, s_kdd, s_validacion, s_ingreso_cero, s_embudo, s_arquitectura, s_diseno_complejo, s_rendimiento, s_estados, s_ranking, s_brecha_hora_mes, s_comparables, s_cuantiles, s_informalidad, s_conclusiones, s_limitaciones, s_gracias, s_anexos, s_robustez, s_oaxaca, s_inf_vs_escolaridad, s_tablero, s_diagnosticos]
