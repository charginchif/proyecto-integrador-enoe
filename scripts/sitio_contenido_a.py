"""Contenido del sitio, parte A: inicio, selección, preprocesamiento y transformación e ingeniería de datos (capítulos 0 a 3)."""
from __future__ import annotations

from enoe import config as C
from informe_datos import f1, n_es
from sitio_lib import (Ctx, Raw, barras, cifras, codigo, color_rampa, dos, e, fig, lista, md, nota, p, pasos, si_no, tabla, tarjeta)
from sitio_textos import ALT, PORQUE


def F(nombre: str, pie: str) -> str:
    """Figura con su texto alternativo y, si es un gráfico de datos, la justificación y la fuente."""
    return fig(nombre, ALT[nombre], pie, PORQUE.get(nombre), fuente=not nombre.startswith("D"))


def ir(id: str, texto: str) -> Raw:
    return Raw(f'<a href="#{id}">{e(texto)}</a>')


def mosaico(D, con_info: bool = True) -> str:
    """Cartograma de mosaicos de la informalidad (TIL1): cada estado ocupa la misma área; interactivo."""
    til = D.til1_entidad.set_index("cve_ent")
    vmin, vmax = float(til.til1_est.min()), float(til.til1_est.max())
    tiles = []
    for cve, (nombre, _oficial, abrev, _region, col, fila) in C.ENTIDADES.items():
        r = til.loc[cve]
        fondo, texto = color_rampa((float(r.til1_est) - vmin) / (vmax - vmin))
        tiles.append(f'<button type="button" class="tile" style="grid-column:{col + 1};grid-row:{fila + 1};--c:{fondo};--t:{texto}" data-n="{e(nombre)}" data-v="{r.til1_est:.1f}" '
                     f'data-i="{r.til1_ic_inf:.1f} a {r.til1_ic_sup:.1f}" data-l="{int(r.til1_rango)}" aria-label="{e(nombre)}: {r.til1_est:.1f} % de informalidad">{e(abrev)}<small>{r.til1_est:.0f}</small></button>')
    info = '<p class="mapa-info" aria-live="polite">Pasa el cursor o toca un mosaico para ver el dato de ese estado.</p>' if con_info else ""
    return (f'<div class="mapa-marco"><div class="mosaico" role="group" aria-label="Informalidad laboral por entidad federativa, un mosaico por estado">{"".join(tiles)}</div>'
            f'<div class="leyenda"><span>{vmin:.0f} %</span><i></i><span>{vmax:.0f} %</span></div>{info}</div>')


def construir(ctx: Ctx) -> list[str]:
    D = ctx.D
    R, tot, rt = D.R, D.tot, D.rt
    esc = ctx.escena
    out: list[str] = []
    prem92 = float(D.premio_por_nivel.iloc[3]["premio_pct"])
    ret = f1(rt["nacional_pct"]["est"])
    ic_ret = f"{f1(rt['nacional_pct']['ic_inf'])} a {f1(rt['nacional_pct']['ic_sup'])}"
    deff = float(D.deff.loc["TIL1 nacional", "deff"])
    nefec = float(D.deff.loc["TIL1 nacional", "n_efectivo"])
    bit = D.bit

    # ================================================================= 0 · INICIO
    # ---- portada ----
    textos, quien, corta = ctx.G.de(("Radiografía socioeconómica de México",))
    atr = ctx.atributos("portada", 0, "Portada", quien, corta)
    out.append(
        f'<header class="escena hero" {atr}><div class="cont"><div class="hero__grid"><div>'
        f'<p class="etq">Proyecto Integrador de Ciencia de Datos · Equipo 1</p>'
        f'<h1>Radiografía socioeconómica de México</h1>'
        f'<p class="hero__sub">Escolaridad, ingreso y brecha de género con la Encuesta Nacional de Ocupación y Empleo (INEGI, 4.º trimestre de 2025)</p>'
        f'<p class="hero__meta">Juan Evelio Culin Grajeda · Angel Yireh Garcia Jara · Luis Andre Gutierrez Zuñiga<br>'
        f'Universidad de Especialidades UNE · Plantel Centro · Optativa III: Ciencia de Datos · 9.º semestre</p>'
        f'<div class="hero__acc"><a class="btn btn--sol" href="#historia">Leer la historia</a><button type="button" class="btn" data-presentar>Modo presentación</button>'
        f'<a class="btn" href="#estudiar">Estudiar</a></div></div>'
        f'<div><p class="etq" style="margin-bottom:.5rem">Informalidad laboral por entidad (TIL1, %)</p>{mosaico(D)}</div></div>'
        + cifras([(f"+{ret} %", "ingreso por hora por cada año de escolaridad"), (f"{f1(tot['brecha_hora_pct'])} vs {f1(tot['brecha_mens_pct'])} %", "brecha de género por hora frente a por mes"),
                  (f"{f1(D.nac['est'])} %", "de las personas ocupadas está en empleo informal"), ("7 de 7", "cifras oficiales del INEGI reproducidas")])
        + f'{ctx.guion_html(textos, quien)}</div></header>')

    # ---- la historia en cinco frases ----
    pas = [
        Raw(md("**Los datos son confiables.** Con la base oficial reproducimos **7 de 7** cifras que publicó el INEGI (población económicamente activa, participación, informalidad nacional y de tres estados). ") + '<a href="#validacion">Ver la validación</a>'),
        Raw(md(f"**El «ingreso cero» engaña.** {D.cero_pond:.0f} % de los ocupados no da un monto exacto, pero solo {D.C_t:.0f} % no recibe ingresos: {D.B_t:.0f} % da un rango de salarios mínimos y {D.D_t:.0f} % no especifica. Quien más estudió declara menos. ") + '<a href="#ingreso0">Ver el hallazgo</a>'),
        Raw(md(f"**Estudiar paga.** Cada año de escolaridad sube el ingreso por hora {ret} % (IC 95 %: {ic_ret}); una licenciatura o un posgrado, {prem92:.0f} % más que no terminar la primaria. Rinde parecido en estados ricos y pobres. ") + '<a href="#rendimiento">Ver el resultado</a>'),
        Raw(md(f"**La brecha de género es sobre todo de horas.** {f1(tot['brecha_hora_pct'])} % por hora y {f1(tot['brecha_mens_pct'])} % por mes; unos {D.g5['brecha_pct']:.0f} % entre personas comparables, concentrados en los ingresos bajos y en el empleo informal. ") + '<a href="#brechahm">Ver la brecha</a>'),
        Raw(md(f"**La informalidad cae con la escolaridad.** {f1(D.nac['est'])} % a nivel nacional, de {D.mn_til['til1_est']:.0f} % ({D.mn_til['entidad']}) a {D.mx_til['til1_est']:.0f} % ({D.mx_til['entidad']}); "
               f"{R['til1']['por_nivel']['1']:.0f} % entre quienes no terminaron la primaria contra {R['til1']['por_nivel']['4']:.0f} % con preparatoria o más. ") + '<a href="#informalidad">Ver el mapa</a>'),
    ]
    out.append(esc("historia", 0, "La historia en cinco frases", (pasos(pas) + nota("Cuidado", "Todo lo anterior son **asociaciones**, no efectos causales: estudiar un año más no *causa* por sí solo un aumento de 5 %.", "cuidado")),
                   lead="Si solo hay un minuto, esto es lo que hay que contar.", g=(),
                   guion=("Esta es la historia completa en cinco frases. Uno: los datos son confiables, reproducimos siete cifras oficiales. Dos: el ingreso cero engaña, casi cuatro de cada diez ocupados no dan un monto exacto, pero solo cuatro de cada cien no reciben ingresos. "
                          "Tres: estudiar paga alrededor de cinco por ciento por año y la licenciatura casi duplica el ingreso. Cuatro: la brecha de género es de tres punto siete por ciento por hora y de veintisiete por ciento por mes, porque las mujeres trabajan menos horas pagadas. "
                          "Cinco: la informalidad baja con la escolaridad. Y siempre con la advertencia de que son asociaciones y no causalidad.")))

    # ---- la pregunta ----
    izq = ('<aside class="nota nota--sencillo"><span class="nota__t">Pregunta de investigación</span><p style="font-size:1.12rem;font-weight:600;max-width:none">'
           '¿Cuánto aumenta el ingreso laboral por cada año adicional de escolaridad, cómo cambia esa relación entre entidades federativas y existe una brecha salarial significativa '
           'entre hombres y mujeres con la misma escolaridad?</p></aside>'
           '<p class="tit-c">Objetivos</p>' + pasos(["Estimar la correlación y el rendimiento de la escolaridad en cada una de las 32 entidades, comparando estados de mayor y menor ingreso.",
                                                      "Probar si hay una diferencia significativa de ingreso por hora entre hombres y mujeres con el mismo nivel de instrucción.",
                                                      "Identificar las entidades con más informalidad y medir su relación con la escolaridad."]))
    der = ('<p class="tit-c">Por qué importa</p>' + cifras([(f"{R['muestras']['ocupados_millones']:.1f} M", "personas ocupadas de 15 años y más"), (f"{f1(D.nac['est'])} %", "en un empleo informal"),
                                                           (f"{D.bn.loc['Total', 'part_mujeres_pct']:.0f} %", "de la muestra salarial son mujeres")])
           + p("La educación se considera la principal vía de movilidad social, pero el mercado laboral combina una informalidad muy alta con diferencias persistentes entre regiones y entre mujeres y hombres. "
               "Las respuestas orientan decisiones de política educativa, laboral y de igualdad de género.")
           + '<p class="tit-c">Métricas de éxito</p><ul class="chips"><li class="chip">M1 · brecha por nivel con IC y prueba</li><li class="chip">M2 · Spearman de 32 entidades con IC y ranking</li><li class="chip">M3 · tablero con 4+ gráficas sobre NoSQL</li></ul>')
    out.append(esc("pregunta", 0, "La pregunta: ¿cuánto rinde estudiar, y para quién?", dos(izq, der, "dos--igual"), g=("La pregunta: ¿cuánto rinde estudiar", "Por qué importa:")))

    # ---- protocolo ----
    cards = [
        ("1 · Portada", p("Radiografía socioeconómica de México. Equipo 1: Juan Evelio Culin Grajeda, Angel Yireh Garcia Jara y Luis Andre Gutierrez Zuñiga. UNE Plantel Centro, Optativa III: Ciencia de Datos.")
         + p("Roles: coordinación, ingeniería de datos (pipeline), análisis estadístico y visualización y comunicación; pueden rotar.")),
        ("2 · Problema y justificación", p("¿Cuánto rinde un año más de estudio, cambia entre estados y hay brecha de género con la misma escolaridad?")
         + p("Importa porque orienta política educativa, laboral y de igualdad, y la ENOE es la fuente oficial del mercado laboral.")),
        ("3 · Dataset", p(f"ENOE 4T-2025 del INEGI: tablas SDEMT y COE2T. {n_es(R['muestras']['universo'])} ocupados de 15+ en 419,038 registros de SDEMT; 115 variables (se usan 35).")
         + p("Estado: necesita limpieza real (ingreso 0 en 36 % de los registros, códigos de «no especificado», atípicos).")),
        ("4 · Objetivos", p("**General:** cuantificar la relación entre escolaridad e ingreso laboral y la brecha salarial de género en México, por entidad.")
         + lista(["Estimar correlación y rendimiento por entidad.", "Probar la brecha de ingreso por hora con la misma escolaridad.", "Identificar las entidades con más informalidad y su relación con la escolaridad."])),
        ("5 · Métricas de éxito", lista(["M1: brecha de género (%) por nivel de instrucción con IC 95 % y prueba (p < 0.05).", "M2: Spearman escolaridad-ingreso de las 32 entidades con IC por bootstrap y ranking defendible.",
                                          "M3: tablero con al menos cuatro visualizaciones alimentado por un pipeline a una base NoSQL."])),
        ("6 · Plan por fases KDD", lista(["Selección: ENOE 4T-2025 (SDEMT y COE2T) validada contra cifras oficiales.", "Preprocesamiento: cobertura, faltantes codificados, calidad del ingreso, atípicos y 15 pruebas.",
                                          "Transformación: variables, imputación por rango, SQLite y MongoDB.", "Minería: Rao-Wu, Mincer, brecha con controles, Oaxaca-Blinder, cuantiles e informalidad.",
                                          "Interpretación: hallazgos, métricas, recomendaciones y límites."])),
        ("7 · Evidencia de validación", p("Los dos archivos se descargaron, se abrieron y se contaron: 419,038 filas en SDEMT y 344,166 en COE2T, cada uno con su huella SHA-256.")
         + p("Con la base oficial se reproducen 7 de 7 cifras publicadas por el INEGI. ") + f'<p>{ir("validacion", "Ver la tabla de validación")}</p>'),
    ]
    out.append(esc("protocolo", 0, "Protocolo: el contrato del proyecto", '<div class="rejilla">' + "".join(tarjeta(t, b) for t, b in cards) + "</div>",
                   lead="Las siete partes que pide la guía del protocolo, resumidas.",
                   guion=("El protocolo es el contrato del proyecto: dice qué haremos, con qué datos y cómo sabremos si funcionó. Tiene siete partes: portada con integrantes y roles, el problema y su justificación, el dataset con su estado, los objetivos, las métricas de éxito, "
                          "el plan por fases del ciclo KDD y la evidencia de que abrimos y validamos los datos. Todo lo que sigue en esta página cumple ese contrato.")))

    # ---- mapa: qué pide la maestra y dónde está ----
    ta = tabla(["Requisito del dataset", "Qué hay", "Dónde"], [
        ["Público y de gran escala (decenas de miles de registros o más)", f"419,038 registros en SDEMT y 344,166 en COE2T; {n_es(R['muestras']['universo'])} ocupados de 15+", ir("enoe", "La ENOE")],
        ["Fuente verificable (oficial o reconocida)", "INEGI, ENOE 4T-2025; huella SHA-256 de cada archivo; 7 de 7 cifras publicadas reproducidas", ir("validacion", "Validación")],
        ["Con «suciedad» real", f"Ingreso 0 en {D.cero_reg:.0f} % de los registros, faltantes codificados (99 años, 0 horas) y atípicos", ir("ingreso0", "Ingreso cero")],
        ["Documentado", "Descriptor de archivos del INEGI y diccionario del proyecto (`docs/diccionario_de_datos.md`)", ir("descargas", "Descargas")]])
    tb = tabla(["El proyecto debe evidenciar", "Qué pide la guía", "Evidencia en el proyecto", "Dónde"], [
        ["**Estadística** (Sem. 2-3)", "Descriptiva, inferencia o pruebas de hipótesis", "Bootstrap de Rao-Wu con 1,000 réplicas; pruebas de la brecha con Holm; Welch y Mann-Whitney; Spearman; Mincer; Oaxaca-Blinder", ir("raowu", "Estadística")],
        ["**Limpieza** (Sem. 4)", "Pipeline de preprocesamiento documentado", f"Bitácora de {len(D.etl_bitacora)} pasos y 15 pruebas automáticas de calidad de datos", ir("cobertura", "Limpieza")],
        ["**Transformación** (Sem. 4)", "Variables, codificación o normalización", "13 variables derivadas, logaritmo del ingreso por hora, imputación por rango y banderas de muestra", ir("variables", "Variables")],
        ["**Visualización** (Sem. 5)", "Al menos cuatro gráficos justificados y honestos", "17 figuras, cada una con su justificación, y un tablero interactivo con 6 visualizaciones", ir("rendimiento", "Resultados")],
        ["**Ingeniería** (Sem. 6)", "Pipeline de carga a una base", "ETL idempotente que carga a SQLite con llaves, restricciones, vistas y auditoría", ir("arquitectura", "Arquitectura")],
        ["**NoSQL** (Sem. 7)", "Justificación del modelo de datos elegido", "Persistencia políglota: SQLite para analizar, MongoDB para servir la ficha de cada entidad", ir("sqlmongo", "SQL y MongoDB")]])
    tc = tabla(["Entregable de cierre", "Qué es", "Dónde"], [
        ["Informe visual con hallazgos (storytelling)", "Esta página, que cuenta la historia por capítulos, y el informe técnico en Word y PDF", ir("historia", "La historia")],
        ["Notebook", "Cuaderno ejecutado de principio a fin, con las mismas cifras", Raw('<a href="cuaderno.html">Abrir el cuaderno</a>')],
        ["Exposición", "Presentación completa (48 diapositivas, ruta corta de 18) y el modo presentación de esta página", ir("exponer", "Exponer")],
        ["Protocolo (primer entregable)", "Plantilla completada con el dataset validado", ir("protocolo", "Protocolo")]])
    out.append(esc("mapa", 0, "Qué pide la maestra y dónde está", ta + tb + tc, lead="Cada requisito de su guía, con la evidencia y el lugar donde verla.",
                   guion=("Este es el mapa para defender el proyecto. La guía de la maestra pide cuatro cosas del dataset, seis competencias que el proyecto debe evidenciar y los entregables de cierre. "
                          "Ante cualquier pregunta del tipo ¿dónde están las gráficas?, ¿dónde justificaron el modelo de datos?, se señala la fila correspondiente y se muestra la evidencia.")))

    # ---- ciclo KDD ----
    fases = [("1 · Selección", "Sem. 1", "ENOE 4T-2025; validación contra cifras del INEGI", "enoe"), ("2 · Preprocesamiento", "Sem. 4", "Faltantes codificados, calidad del ingreso, atípicos y 15 pruebas", "cobertura"),
             ("3 · Transformación", "Sem. 4 · 6 · 7", "Variables derivadas, ETL, SQLite y MongoDB", "variables"), ("4 · Minería", "Sem. 2 · 3 · 5", "Diseño muestral complejo, regresión y Oaxaca-Blinder", "diseno"),
             ("5 · Interpretación", "Sem. 5", "Hallazgos, recomendaciones y límites", "conclusiones")]
    kdd = '<ol class="kdd">' + "".join(f'<li><a href="#{a}"><b>{e(t)}</b><span>{e(s)}</span><small>{e(d)}</small></a></li>' for t, s, d, a in fases) + "</ol>"
    out.append(esc("kdd", 0, "Un ciclo KDD completo sobre datos reales y masivos", kdd + cifras([("419,038", "registros de la tabla SDEMT"), (n_es(R["muestras"]["salarial"]), "observaciones salariales"),
                                                                                                  ("21,194", "UPM en 713 estratos"), ("7 de 7", "cifras oficiales reproducidas")]),
                   g=("Un ciclo KDD completo",)))

    # ================================================================= 1 · SELECCIÓN
    izq = (p("La **Encuesta Nacional de Ocupación y Empleo (ENOE)** es una encuesta continua del INEGI: cada trimestre entrevista a cientos de miles de personas en viviendas de todo el país. "
             "Cada vivienda se entrevista hasta cinco veces seguidas (panel rotativo) y los microdatos son públicos y anónimos.")
           + tabla(["Tabla", "Contenido", "¿Se usa?"], [["SDEMT", "Sociodemográfica y laboral: una fila por persona (419,038 filas, 115 columnas)", "Sí · 35 columnas"], ["COE2T", "Ocupación y empleo, parte 2: cómo se captó el ingreso (344,166 filas)", "Sí · 14 columnas"],
                                                       ["COE1T, HOGT, VIVT", "Otras partes del cuestionario, hogares y viviendas", "No"]])
           + p("La unión entre SDEMT y COE2T usa una llave de 11 campos que se comprobó única; es uno a uno y el proceso se detiene si una persona ocupada no encuentra pareja."))
    der = (cifras([("724 → 713", "estratos (11 con una sola UPM se fusionan)"), ("21,194", "unidades primarias de muestreo"), ("131.0 M", "suma de fac_tri = población del país"), (f"{deff:.1f}", f"efecto de diseño: {n_es(R['muestras']['universo'])} ocupados valen como {nefec / 1000:.0f} mil")])
           + nota("En palabras sencillas", "Cada persona encuestada es un «representante» de cientos de personas que no fueron entrevistadas, así que hay que contarla tantas veces como personas representa (ponderar). "
                  "Y como los representantes de una misma zona se parecen, tener 190 mil entrevistas equivale a unas 40 mil opiniones independientes.", "sencillo"))
    out.append(esc("enoe", 1, "La ENOE y su diseño muestral: por qué cada persona pesa distinto", dos(izq, der, "dos--igual")
                   + F("D04_diseno_muestral.png", "Niveles del diseño muestral y significado del factor de expansión (fac_tri)."),
                   g=("La ENOE: la encuesta", "El diseño muestral: por qué")))

    val = D.etl_validacion_externa
    filas = [[r.indicador, f"{r.estimado_proyecto:,.2f}", f"{r.oficial_inegi:,.1f}", si_no(bool(r.coincide))] for r in val.itertuples()]
    ef = D.meta["efecto_base_menores_15"]
    arch = [[a["tabla"], a["archivo"], f"{a['filas']:,}", str(a["columnas_leidas"]), f"{a['bytes'] / 1e6:.0f} MB", f"`{a['sha256'][:16]}…`"] for a in D.meta["archivos_origen"]]
    cuerpo = (dos(tabla(["Indicador", "Proyecto", "INEGI", "¿Coincide?"], filas, num=(1, 2), centro=(3,), pie="Con la base oficial: ocupados de 15+ años, entrevista completa, residentes habituales y fac_tri."),
                  cifras([("7 de 7", "cifras del INEGI reproducidas al redondear a su precisión")]) + nota("Por qué solo 15 años o más",
                                                                                                           f"Con los {ef['menores_de_15_ocupados_en_muestra']:,} menores de 15 años ocupados, el TIL1 sería {ef['til1_con_menores_de_15']:.2f} % en lugar de {ef['til1_base_15_y_mas']:.2f} % y dejaría de coincidir con el oficial."))
              + '<p class="tit-c">Evidencia de que los archivos se abrieron y se verificaron</p>'
              + tabla(["Tabla", "Archivo", "Filas", "Columnas leídas", "Tamaño", "SHA-256 (inicio)"], arch, num=(2, 3, 4))
              + nota("Nota de transparencia", "Las cifras oficiales de referencia se obtuvieron de los boletines del INEGI para el 4T-2025 mediante una búsqueda web; conviene contrastarlas con el PDF oficial antes de exponer.", "cuidado"))
    out.append(esc("validacion", 1, "Los filtros y ponderadores reproducen las cifras oficiales del INEGI", cuerpo, g=("Los filtros y ponderadores",)))

    # ================================================================= 2 · PREPROCESAMIENTO
    reglas = [("L1", "Entrevista completa", "Entrevistas incompletas (r_def distinto de 0)"), ("L2", "Residente habitual", "Nuevos residentes (c_res = 2), sin sexo ni edad"), ("L3", "Edad de 15 a 98 años", "Menores de 15 años y edad no especificada"),
              ("L4", "Población ocupada", "Personas no ocupadas (clase2 distinto de 1)"), ("L5", "Ponderador positivo", "Nadie: es una verificación")]
    filas = [["L0", "Registros crudos de SDEMT", "—", n_es(bit.loc["L0", "n_antes"]), n_es(bit.loc["L0", "n_despues"]), "0"]]
    for k, a, b in reglas:
        filas.append([k, a, b, n_es(bit.loc[k, "n_antes"]), n_es(bit.loc[k, "n_despues"]), n_es(bit.loc[k, "afectados"])])
    out.append(esc("cobertura", 2, "La cobertura define el universo: cinco reglas, 190,187 personas", tabla(["Paso", "Regla", "Quién se excluye", "Antes", "Después", "Excluidos"], filas, num=(3, 4, 5), destacar=(5,))
                   + nota("Marcar, no borrar", "Solo la cobertura elimina filas. Los faltantes, la calidad del ingreso y los atípicos crean **banderas**, para cambiar una decisión y rehacer el análisis sin volver a limpiar.", "sencillo")
                   + cifras([(n_es(bit.loc["L5", "n_despues"]), "personas ocupadas de 15+: el universo de estudio")]), g=("La cobertura define el universo",)))

    cod = "df.isna().sum().sum()      # 0     → «todo está completo»\ndf['anios_esc'].max()       # 99    → código de «no especificado»"
    filas = [["M1", "`anios_esc`", "99 = no especificado", n_es(bit.loc["M1", "afectados"]), "Faltante: no entra al análisis de escolaridad"],
             ["M2", "`hrsocup`", "0 horas la semana pasada", n_es(bit.loc["M2", "afectados"]), "Faltante: ocupado pero ausente; no hay ingreso por hora"],
             ["M3", "`hrsocup`", "más de 112 horas semanales", n_es(bit.loc["M3", "afectados"]), "Faltante: 16 h × 7 días es una jornada imposible"],
             ["M4", "`niv_ins`", "5 = no especificado", n_es(bit.loc["M4", "afectados"]), "Se excluye del análisis por nivel de instrucción"]]
    out.append(esc("faltantes", 2, "Los faltantes vienen codificados como números reales", dos(codigo(cod, "python"), nota("Por qué importa", "Un 99 tratado como número real distorsionaría los promedios. Cada código se convierte en faltante y se registra; nadie se borra del universo."))
                   + tabla(["Marca", "Variable", "Código", "Registros", "Tratamiento"], filas, num=(3,)) + p("Es menos de 3 % del universo en el peor caso (M2). El faltante importante es el del ingreso."), g=("Los faltantes vienen codificados",)))

    cifras_ing = cifras([(f"{D.A_t:.0f} %", "declara el monto exacto (A)"), (f"{D.B_t:.0f} %", "da solo un rango de salarios mínimos (B)"), (f"{D.C_t:.0f} %", "no recibe ingresos (C)"), (f"{D.D_t:.0f} %", "no especifica su ingreso (D)")])
    out.append(esc("ingreso0", 2, "El «ingreso cero» esconde tres fenómenos distintos",
                   p(f"`ingocup` vale 0 en {D.cero_reg:.0f} % de los registros ({D.cero_pond:.0f} % de la población ponderada). No son personas que ganen cero: solo el grupo C no recibe ingresos. "
                     "Al cruzar el monto con el rango de salarios mínimos (`ing7c`) salen cuatro grupos que suman 100 %.")
                   + cifras_ing + F("02_calidad_ingreso.png", "Calidad del ingreso por grupo de declaración: composición total, por sexo y por nivel de instrucción.")
                   + nota("Lo que hay que recordar", f"Quien más estudió declara menos el monto exacto ({D.A_n4:.0f} % frente a {D.A_n1:.0f} %). Los datos faltan de forma no aleatoria, por eso cada resultado clave se contrasta con tres correcciones: imputar el rango, ponderar por no respuesta y usar solo asalariados.", "cuidado"),
                   g=("El «ingreso cero» esconde",)))

    lg = D.no_respuesta_logit.set_index(["modelo", "variable"])
    chi = D.calidad_ingreso_chi2.set_index("variable")
    cats = [("Mujer", "mujer"), ("Un año más de escolaridad", "anios_esc"), ("Empleo informal", "informal"), ("Empleador", "pos_empleador"), ("Cuenta propia", "pos_cuenta_propia")]
    items = []
    for nombre, v in cats:
        x = 100 * (float(lg.loc[("A_vs_resto", v), "razon_momios"]) - 1)
        items.append((nombre, x, f"{x:+.0f} %".replace("-", "−")))
    chi_f = [[k.capitalize(), f"{chi.loc[k, 'chi2']:,.0f}", f"{chi.loc[k, 'v_cramer']:.2f}"] for k in ["sexo", "nivel de instrucción", "informalidad", "posición"]]
    out.append(esc("norespuesta", 2, "La no respuesta del ingreso no es aleatoria: quien más estudia declara menos",
                   dos('<p class="tit-c">Cambio en los momios de declarar el monto exacto</p>' + barras(items, div=True, escala=50.0), '<p class="tit-c">Asociación con el grupo de ingreso (χ²)</p>' + tabla(["Variable", "χ²", "V de Cramér"], chi_f, num=(1, 2)))
                   + nota("Cómo leerlo", "Un valor de +26 % significa que las mujeres tienen 26 % más momios de declarar el monto exacto. La **V de Cramér** (0 = sin asociación, 1 = perfecta) dice qué tan grande es la asociación: mínima con el sexo, fuerte con la posición en la ocupación.", "sencillo")
                   + nota("Consecuencia", "La muestra salarial subrepresenta a los más escolarizados; por eso se contrasta con imputación por rango, ponderación inversa (IPW) y solo asalariados."), g=("La no respuesta del ingreso",)))

    imp = D.etl_imputacion_rangos
    r4 = imp[imp.p6c == 4].iloc[0]
    filas = [[r.rango, n_es(r.n_referencia_A), f"{r.razon_mediana_sm:.2f}", n_es(r.n_B_imputados)] for r in imp.itertuples()]
    out.append(esc("imputacion", 2, "Imputación por rango: la mediana de quienes sí declararon",
                   dos(tabla(["Rango declarado", "Referencia (grupo A)", "Mediana (× SM)", "Personas del grupo B"], filas, num=(1, 2, 3), destacar=(3,), pie="SM = salario mínimo mensual de la persona."),
                       nota("Ejemplo", f"Alguien de la zona general que declaró «más de 2 a 3 salarios mínimos» recibe {r4.razon_mediana_sm:.2f} × $8,364 = **${r4.razon_mediana_sm * 8364:,.0f} al mes**.", "sencillo")
                       + nota("Advertencia", "Asignar el mismo valor a todos los hombres y mujeres de un rango comprime las diferencias entre ellos y **sesga la brecha hacia cero** por construcción. Solo se usa como sensibilidad, con la muestra ampliada de 145,529 personas.", "cuidado"))
                   + p("Se usa la mediana observada y no el punto medio del rango porque dentro de cada rango hay más personas cerca del límite inferior."), g=("Imputación por rango",)))

    out.append(esc("atipicos", 2, "Atípicos y logaritmo: domar la cola larga del ingreso",
                   F("03_distribucion_ingreso.png", "Distribución del ingreso por hora: en pesos (cola larga) y en logaritmo natural (casi simétrica).")
                   + cifras([(f"{D.dg['asimetria_ingreso_nivel']:.1f} → {D.dg['asimetria_ln_ingreso']:.2f}", "asimetría: en pesos y en logaritmo"), (n_es(bit.loc["O1", "afectados"]), "atípicos (1.0 %) fuera de P0.5 a P99.5 por entidad"),
                             (f"{D.rob_tot.loc['S1 Sin recorte', 'brecha_pct']:.1f} % vs {tot['brecha_hora_pct']:.1f} %", "brecha sin recorte frente a con recorte")])
                   + nota("En palabras sencillas", "El logaritmo acorta la cola larga, y una diferencia de logaritmos es una diferencia porcentual: ln(110) − ln(100) = 0.095, casi 10 %. El recorte se hace **dentro de cada entidad** para no eliminar sistemáticamente a las entidades ricas o pobres.", "sencillo"),
                   g=("Atípicos y logaritmo",)))

    out.append(esc("embudo", 2, "De 419 mil registros a 112 mil observaciones, paso a paso",
                   F("01_embudo_datos.png", "Embudo de datos: del registro crudo al universo y a las muestras de análisis.")
                   + lista(["La cobertura elimina filas; todo lo demás crea banderas.", f"{n_es(bit.loc['M1', 'n_despues'])} escolaridades iguales a 99 y {n_es(bit.loc['M2', 'n_despues'])} jornadas de 0 horas se recodifican como faltantes.",
                            f"{n_es(bit.loc['O1', 'n_despues'])} ingresos por hora atípicos (P0.5 a P99.5 por entidad).", "15 de 15 expectativas de calidad cumplidas.", "ETL idempotente: 10 segundos, una sola semilla y SHA-256 de cada archivo."]), g=("De 419 mil registros",)))

    ex = D.etl_expectativas
    nom = {"ing7c consistente con ingocup/salario mínimo": "ing7c consistente con ingocup y salario mínimo", "ing_x_hrs = ingocup / (hrsocup x 4.3)": "ing_x_hrs = ingocup / (hrsocup × 4.3)",
           "p6c (COE2T) reproduce ing7c (SDEMT) en el grupo B": "p6c (COE2T) reproduce ing7c (SDEMT)", "ingocup == p6b2 (COE2T) en el grupo A": "ingocup = p6b2 (COE2T) en el grupo A"}
    li = '<ul class="quince">' + "".join(f"<li>{e(nom.get(str(x), str(x)))}</li>" for x in ex.expectativa) + "</ul>"
    out.append(esc("pruebas", 2, "15 pruebas automáticas de calidad: 15 de 15 cumplidas", li + nota("Cómo funcionan", f"{int(ex.critica.sum())} son críticas y {int((~ex.critica).sum())} informativa. Si una crítica falla, el ETL se detiene con un error en lugar de continuar con datos dudosos: es el equivalente de las pruebas unitarias, pero aplicadas a los datos.", "sencillo"),
                   g=("15 pruebas automáticas",)))

    # ================================================================= 3 · TRANSFORMACIÓN E INGENIERÍA
    filas = [["`mujer`", "1 si `sex = 2`, 0 si hombre", "Variable binaria para regresiones y la brecha de género"], ["`edad2`", "`eda² / 100`", "Término cuadrático: el ingreso sube con la experiencia y luego se aplana"],
             ["`grupo_edad`", "15-24, 25-34, 35-44, 45-54, 55-64, 65+", "Heterogeneidad por edad"], ["`informal`", "1 si `emp_ppal = 1`, 0 si formal", "Variable de informalidad (TIL1)"],
             ["`niv_det`", "Nivel 4 dividido: medio superior (4) y superior (5, con 16+ años)", "Premio salarial por nivel"], ["`entidad`, `region`", "Nombre y región (Norte, Centro-Norte, Centro, Sur)", "Etiquetas y análisis regional"],
             ["`log_horas`", "ln(`hrsocup`)", "Control de horas trabajadas"], ["`grupo_ingreso`", "A, B, C o D según `ingocup` e `ing7c`", "Calidad del ingreso"],
             ["`ing_hora`", "`ingocup / (hrsocup × 4.3)` (grupo A, horas válidas)", "Ingreso por hora; se verifica contra el del INEGI"], ["`ln_ing_hora`", "ln(`ing_hora`)", "Variable dependiente de los modelos"],
             ["`ing_mensual_imp`, `ing_hora_imp`", "Imputación por rango para el grupo B", "Solo en análisis de sensibilidad"], ["`persona_id`", "Llave de 11 campos concatenados", "Llave primaria legible"]]
    out.append(esc("variables", 3, "Variables derivadas: de los códigos del INEGI a variables de análisis", tabla(["Variable", "Definición", "Para qué sirve"], filas)
                   + p(f"Siete banderas (`en_ventana_15_65`, `anios_esc_valido`, `horas_validas`, `nivel_especificado`, `outlier_ing_hora`, `en_muestra_salarial` y `en_muestra_salarial_ext`) definen las muestras. La tabla de hechos guarda {D.n_cols_fact} columnas."),
                   guion=("La transformación convierte los códigos del INEGI en variables que los modelos entienden. El ingreso por hora se calcula con la misma fórmula del INEGI, ingreso mensual entre horas por cuatro punto tres, y se trabaja en logaritmo. "
                          "La imputación por rango solo se usa para sensibilidad. Siete banderas definen qué registros entran a cada muestra: así cambiar una decisión no obliga a volver a limpiar.")))

    out.append(esc("arquitectura", 3, "Arquitectura: SQLite para analizar, MongoDB para servir",
                   F("D02_arquitectura.png", "De los microdatos del INEGI a los resultados, el tablero y la base documental.")
                   + '<div class="rejilla">' + tarjeta("Relacional (SQLite): analizar", p("Datos tabulares de esquema fijo; agregaciones ponderadas y uniones; integridad por restricciones; es la fuente de verdad."))
                   + tarjeta("Documental (MongoDB): servir", p("Una ficha por entidad (*embedding*); el esquema crece sin migraciones; lectura por clave; es una vista que se regenera.")) + "</div>", g=("Arquitectura: SQLite",)))

    out.append(esc("estrella", 3, "Esquema en estrella: una tabla de hechos y diez dimensiones",
                   F("D03_esquema_estrella.png", "La tabla de hechos fact_ocupado (190,187 filas) rodeada de diez dimensiones.")
                   + nota("Qué garantiza", [f"`fact_ocupado`: {n_es(D.n_u)} filas y {D.n_cols_fact} columnas. Llaves primarias y foráneas (`foreign_keys = ON`).", "Restricciones CHECK: `fac_tri > 0`, `eda` entre 15 y 98, `emp_ppal` en {1, 2}.",
                                            "5 índices y 4 vistas (TIL1, escolaridad, calidad del ingreso y muestra salarial). `integrity_check = ok` y 0 violaciones de llave foránea."], "sencillo"), g=("Esquema en estrella",)))

    sql = ("SELECT e.entidad,\n       ROUND(100.0 * SUM(f.fac_tri * f.informal)\n             / SUM(f.fac_tri), 2) AS til1_pct\nFROM fact_ocupado f\nJOIN dim_entidad e USING (cve_ent)\nGROUP BY e.entidad\nORDER BY til1_pct DESC;")
    mongo = ('db.personas.aggregate([\n  {$group: {_id: "$cve_ent",\n    ocupados: {$sum: "$fac_tri"},\n    informales: {$sum: {$cond: [\n      "$trabajo.informal", "$fac_tri", 0]}}}},\n  {$project: {til1_pct: {$multiply: [\n    100, {$divide: ["$informales", "$ocupados"]}]}}}\n])')
    out.append(esc("sqlmongo", 3, "La misma pregunta en SQL y en MongoDB",
                   dos('<p class="tit-c">SQL · vista v_til_entidad</p>' + codigo(sql, "sql"), '<p class="tit-c">MongoDB · pipeline de agregación</p>' + codigo(mongo, "javascript"), "dos--igual")
                   + cifras([("0.005 pp", "diferencia máxima entre ambas (el redondeo del SQL)")])
                   + nota("Ficha de una entidad", "SQL necesita varias consultas con JOIN; MongoDB, una lectura por clave: `db.entidades.findOne({cve_ent: 20})`.", "sencillo")
                   + nota("Alcance honesto", "No se cargó a un servidor MongoDB real porque no hay uno instalado. La carga completa se probó con mongomock (un simulador) y la agregación ejecutada en el motor reproduce la vista SQL; los archivos están listos para `mongoimport`.", "cuidado"),
                   g=("La misma pregunta en SQL",)))

    mapa = [["`config.py`", "Rutas, parámetros, catálogos y cifras de referencia: la única fuente de decisiones"], ["`extract.py`, `validacion.py`", "Lectura de los CSV con huella SHA-256; comparación con las cifras del INEGI"], ["`clean.py`", "Cobertura, faltantes, grupos de ingreso, atípicos, muestras y 15 expectativas"],
            ["`transform.py`", "Llave de persona, unión 1 a 1, variables derivadas e imputación"], ["`pipeline.py`", "Orquesta el ETL completo y escribe metadatos y bitácora"], ["`load_sqlite.py`, `load_mongo.py`", "Esquema en estrella con restricciones y documentos NoSQL"],
            ["`survey.py`", "Rao-Wu, Taylor, Spearman ponderado, WLS y logit con diseño, Holm"], ["`datos.py`, `estimadores.py`, `modelos.py`, `analisis.py`", "Todo el análisis estadístico: 30 tablas de resultados"], ["`viz.py`, `viz_diagramas.py`, `figuras.py`", "17 figuras de datos y 8 diagramas explicativos"]]
    out.append(esc("reprod", 3, f"Reproducibilidad: una orden, una semilla, {sum(C.contar_pruebas().values())} pruebas",
                   codigo("python scripts/run_all.py   # ETL → análisis → figuras → NoSQL → tablero → cuaderno → presentaciones → informe → pruebas (≈ 10 min)", "bash")
                   + cifras([("20251231", "semilla única para todo lo aleatorio"), ("30 de 30", "archivos de resultados idénticos en dos corridas"), (str(sum(C.contar_pruebas().values())), "pruebas automáticas (limpieza, encuestas, modelos, capa documental, integración)"), ("SHA-256", "huella de cada archivo de origen")])
                   + lista(["**Idempotente:** la base se recrea desde cero.", "**Auditable:** bitácora de cada regla y tabla `etl_run` con versiones y parámetros.", "**Transparente:** todas las decisiones viven en `config.py`."])
                   + '<details class="guion"><summary>Mapa del código</summary>' + tabla(["Módulo", "Qué contiene"], mapa) + "</details>", g=("Reproducibilidad: una orden", "Mapa del código")))
    return out
