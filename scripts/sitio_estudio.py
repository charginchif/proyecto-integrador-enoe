"""Contenido del sitio, parte C: herramientas para estudiar, plan de exposición y descargas."""
from __future__ import annotations

import json

from deck_slides_extra import BLOQUES, MIN_CORTA, MINUTOS, PRESENTA
from informe_datos import contar_pruebas, f1, n_es
from informe_s4 import GLOSARIO, preguntas_defensa
from sitio_lib import Raw, e, lista, md, nota, p, tabla, tarjeta


def numeros_clave(D) -> list[tuple[str, str, str]]:
    R, tot, rt = D.R, D.tot, D.rt
    prem92 = float(D.premio_por_nivel.iloc[3]["premio_pct"])
    return [
        ("Registros crudos de SDEMT", "419,038", "tabla sociodemográfica y laboral"), ("Universo: ocupados de 15+", n_es(D.n_u), "entrevista completa, residente habitual"), ("Ventana de 15 a 65 años", n_es(D.n_v), "edades del protocolo"),
        ("Muestra salarial", n_es(D.n_s), f"{R['muestras']['salarial_poblacion_millones']:.1f} millones de personas"), ("Estratos y UPM", "713 y 21,194", "11 estratos con una UPM se fusionaron"),
        ("Suma de fac_tri", "131.0 millones", "población; ocupados de 15+: 59.8 millones"), ("Efecto de diseño de la informalidad", f"{D.deff.loc['TIL1 nacional', 'deff']:.1f}", "190 mil ocupados valen como unos 40 mil"),
        ("Cifras del INEGI reproducidas", "7 de 7", "PEA, participación, informalidad nacional y de tres estados"), ("Ingreso 0 en los registros", f"{D.cero_reg:.0f} %", f"{D.cero_pond:.0f} % de la población ponderada"),
        ("Grupos de ingreso A, B, C, D", f"{D.A_t:.0f}, {D.B_t:.0f}, {D.C_t:.0f}, {D.D_t:.0f} %", "monto exacto, solo rango, no recibe, no especifica"), ("Rendimiento por año de escolaridad", f"{f1(rt['nacional_pct']['est'])} %", f"IC 95 %: {f1(rt['nacional_pct']['ic_inf'])} a {f1(rt['nacional_pct']['ic_sup'])}"),
        ("Premio de licenciatura o posgrado", f"+{prem92:.0f} %", "frente a no terminar la primaria"), ("Diferencia de rendimiento Q4 − Q1", f"≈ 0 (p = {D.dq['p']:.2f})", "estados ricos frente a pobres"),
        ("Spearman nacional", f"{rt['spearman_nacional']['est']:.2f}", f"por entidad de {rt['rho_min']['rho_est']:.2f} a {rt['rho_max']['rho_est']:.2f}"),
        ("Brecha por hora", f"{f1(tot['brecha_hora_pct'])} %", f"IC 95 %: {f1(tot['brecha_hora_inf'])} a {f1(tot['brecha_hora_sup'])}"), ("Brecha mensual", f"{f1(tot['brecha_mens_pct'])} %", f"mujeres con {f1(tot['menos_horas_mujeres_pct'])} % menos horas"),
        ("Brecha entre personas comparables", f"{D.g5['brecha_pct']:.1f} %", "modelo G5, sin horas"), ("Brecha en P10, P25, P50", f"{D.cu.loc[10, 'brecha_pct']:.1f}, {D.cu.loc[25, 'brecha_pct']:.1f}, {D.cu.loc[50, 'brecha_pct']:.1f} %", "se concentra abajo"),
        ("Oaxaca-Blinder (log-puntos × 100)", f"{D.ob.loc['Brecha total (log-puntos)', 'log_puntos'] * 100:.1f} = {D.ob.loc['Explicada por características (referencia agrupada)', 'log_puntos'] * 100:.1f} + {D.ob.loc['No explicada (referencia agrupada)', 'log_puntos'] * 100:.1f}", "total = explicada + no explicada"),
        ("Rango de la brecha por hora en la robustez", f"{D.hora_specs['brecha_pct'].min():.1f} a {D.hora_specs['brecha_pct'].max():.1f} %", "sin controles; con controles, 8.2 %"), ("Informalidad nacional", f"{f1(D.nac['est'])} %", f"de {D.mn_til['til1_est']:.0f} % ({D.mn_til['entidad']}) a {D.mx_til['til1_est']:.0f} % ({D.mx_til['entidad']})"),
        ("Informalidad por escolaridad", f"{R['til1']['por_nivel']['1']:.0f} % → {R['til1']['por_nivel']['4']:.0f} %", "de primaria incompleta a media superior o más"), ("Spearman entre estados (informalidad y escolaridad)", f"{D.asoc.loc['rho_spearman_til_esc', 'est']:.2f}", f"pendiente {D.asoc.loc['pendiente_til_esc', 'est']:.1f} pp por año"),
        ("Réplicas bootstrap y semilla", f"{R['B']:,} · {D.meta['semilla']}", "una sola semilla para todo"), ("Pruebas automáticas y expectativas de datos", f"{sum(contar_pruebas().values())} y 15", "todas cumplidas"),
    ]


def preguntas_quiz(D) -> list[dict]:
    R, tot = D.R, D.tot
    prem92 = float(D.premio_por_nivel.iloc[3]["premio_pct"])
    ret = f1(D.rt["nacional_pct"]["est"])
    return [
        dict(q="¿Cuánto aumenta, en promedio, el ingreso por hora por cada año adicional de escolaridad?", o=["0.5 %", f"{ret} %", "15 %", f"{prem92:.0f} %"], c=1,
             e=f"El rendimiento de Mincer es {ret} % por año (IC 95 %: {f1(D.rt['nacional_pct']['ic_inf'])} a {f1(D.rt['nacional_pct']['ic_sup'])}). El {prem92:.0f} % es el premio de una licenciatura o posgrado frente a no terminar la primaria, no el efecto de un año."),
        dict(q=f"El efecto de diseño de la tasa de informalidad es {D.deff.loc['TIL1 nacional', 'deff']:.1f}. ¿Qué significa?", o=["Que la tasa de informalidad es 4.8 %", "Que la varianza real es casi cinco veces la de una muestra aleatoria simple: 190 mil ocupados valen como unos 40 mil",
                                                                                                                  "Que hay 4.8 réplicas por estrato", "Que el factor de expansión promedio es 4.8"], c=1,
             e="Las personas de una misma UPM se parecen, así que aportan menos información independiente. Ignorar el diseño haría los errores estándar casi la mitad de lo que deben ser."),
        dict(q="Un intervalo de confianza del 95 % de la brecha va de −0.4 a 1.8. ¿Qué se concluye?", o=["Que la brecha es significativa", "Que no se puede afirmar que exista brecha, porque el intervalo incluye el 0", "Que la brecha es exactamente 0.7", "Que las mujeres ganan más"], c=1,
             e="Si el intervalo incluye el 0, los datos son compatibles con que no haya diferencia. Es el caso de la brecha con rangos imputados (0.7 %, de −0.4 a 1.8) y de la región Sur."),
        dict(q=f"¿Por qué la brecha mensual ({f1(tot['brecha_mens_pct'])} %) es mucho mayor que la brecha por hora ({f1(tot['brecha_hora_pct'])} %)?", o=["Porque los hombres tienen más escolaridad", f"Porque las mujeres trabajan en promedio {f1(tot['menos_horas_mujeres_pct'])} % menos horas pagadas",
                                                                                                                                                       "Porque el ingreso mensual tiene más atípicos", "Porque la brecha mensual no está ponderada"], c=1,
             e="En logaritmos, brecha mensual = brecha por hora + brecha de horas. Casi toda la diferencia mensual es de tiempo trabajado, no de pago por hora."),
        dict(q="¿Qué esconde el «ingreso cero» de la ENOE?", o=["Personas que no trabajan", f"Sobre todo información incompleta: {D.B_t:.0f} % da solo un rango de salarios mínimos y {D.D_t:.0f} % no especifica; solo {D.C_t:.0f} % no recibe ingresos",
                                                                "Errores de captura que se eliminan sin problema", "Trabajadores del sector formal"], c=1,
             e="`ingocup` guarda solo el monto exacto y vale 0 cuando no lo hay. Además, quien más estudió declara menos el monto exacto, por lo que «solo casos completos» sesga el análisis."),
        dict(q="¿Por qué no se interpreta el modelo que controla por horas trabajadas (G6)?", o=["Porque tiene demasiados parámetros", "Por el sesgo de división: un error en las horas crea una relación negativa mecánica con el ingreso por hora", "Porque las horas no son significativas", "Porque lo prohíbe el INEGI"], c=1,
             e=f"El ingreso por hora es ingreso entre horas; si las horas traen error, la brecha «sube» artificialmente de {D.g5['brecha_pct']:.1f} % a {D.g6['brecha_pct']:.1f} %."),
        dict(q="En Oaxaca-Blinder, ¿qué puede decirse de la parte «no explicada»?", o=["Que prueba discriminación", "Es la diferencia de pago a iguales características medidas, y no prueba discriminación porque incluye todo lo no observado", "Es la diferencia en escolaridad", "Siempre es menor que la brecha total"], c=1,
             e="Aquí es mayor que la brecha total (6.9 frente a 3.8 puntos logarítmicos) porque las características de las mujeres (más escolaridad) las favorecen."),
        dict(q="¿Para qué sirve la corrección de Holm?", o=["Para eliminar atípicos", "Para controlar el error cuando se hacen varias pruebas a la vez", "Para estimar el tamaño del efecto", "Para ponderar por no respuesta"], c=1,
             e="Con varias pruebas, alguna saldría «significativa» solo por azar. Holm ordena los valores p y los compara con umbrales crecientes; es más potente que Bonferroni."),
        dict(q="¿Por qué el proyecto usa SQLite y MongoDB?", o=["Porque MongoDB es más rápido en todo", "Por el patrón de acceso: SQLite para analizar (agregaciones ponderadas, uniones, integridad) y MongoDB para servir la ficha de cada entidad", "Porque el INEGI lo exige", "Porque los datos de la ENOE son semiestructurados"], c=1,
             e="Es persistencia políglota. Los datos de la ENOE son una tabla rectangular; la elección responde al patrón de acceso y no al volumen."),
        dict(q="¿Qué entidades tienen la mayor informalidad laboral?", o=["Coahuila, Nuevo León y Chihuahua", "Oaxaca, Guerrero y Chiapas", "Ciudad de México, Jalisco y Nuevo León", "Baja California, Sonora y Sinaloa"], c=1,
             e=f"Oaxaca ({D.mx_til['til1_est']:.0f} %), Guerrero y Chiapas (más de 74 %); las de menor informalidad son Coahuila ({D.mn_til['til1_est']:.0f} %), Nuevo León y Chihuahua."),
        dict(q="¿Cómo se lee el ranking de Spearman por entidad?", o=["Todas las posiciones son confiables", "Solo los extremos se distinguen: los lugares centrales tienen intervalos de 15 o más posiciones", "El ranking no tiene incertidumbre", "Solo importa el último lugar"], c=1,
             e="Cada entidad tiene un intervalo del lugar que ocupa. Un ranking defendible reporta esa incertidumbre y solo afirma los extremos."),
        dict(q="¿Se puede afirmar que estudiar un año más CAUSA 5 % más de ingreso?", o=["Sí, porque el intervalo no incluye el 0", "No: es una asociación; puede haber habilidad no observada y selección", "Sí, porque se controló por edad y sexo", "Solo en los estados ricos"], c=1,
             e="El diseño es observacional de un trimestre. Que el intervalo excluya el 0 habla de precisión, no de causalidad."),
    ]


def reflexion(D) -> list[tuple[str, str]]:
    return [
        ("¿Por qué este problema le importa a alguien más allá de la calificación? ¿Quién usaría sus hallazgos?",
         f"Porque el ingreso, la informalidad y la igualdad de género orientan decisiones públicas. Las secretarías de educación pueden usar el rendimiento de estudiar y la diferencia entre estados para decidir dónde ampliar el acceso y la permanencia escolar; "
         f"las dependencias laborales y los institutos de las mujeres, la brecha de horas y de ingresos bajos y la informalidad ({f1(D.nac['est'])} % de los ocupados); y el INEGI, el hallazgo de que {D.cero_pond:.0f} % de los ocupados no da un monto exacto de ingreso. También sirve a cualquier estudiante para dimensionar cuánto rinde un año más de estudio."),
        ("¿Cuál será el mayor reto técnico del proyecto y en qué semana del curso aprendieron a enfrentarlo?",
         "El diseño muestral complejo: la ENOE es por conglomerados, y tratarla como muestra aleatoria simple haría los errores casi la mitad de lo debido; se resolvió con bootstrap de Rao-Wu (Semanas 2 y 3, inferencia). "
         "El segundo reto fue el «ingreso cero» y los faltantes codificados, que obligaron a diseñar la limpieza (Semana 4). La carga a SQLite y MongoDB exigió decidir el modelo de datos (Semanas 6 y 7)."),
        ("¿Cómo se repartirán el trabajo para que todos los integrantes practiquen las siete competencias?",
         "Con roles que rotan (coordinación, ingeniería de datos, análisis estadístico, visualización y comunicación), de modo que cada integrante explique de principio a fin al menos una sección del cuaderno y presente un bloque de la exposición. "
         "La propuesta de reparto está en la sección Exponer; ajústenla con sus propias palabras."),
    ]


def estudiar(D) -> str:
    # --- glosario ---
    gl = "".join(f'<article class="term"><h3>{md(t)}</h3><p class="def">{md(d)}</p></article>' for t, d in GLOSARIO)
    # --- números clave ---
    nums = "".join(f'<button type="button" class="nm"><span>{e(a)}</span><b>{e(v)}</b><small>{md(h)}</small></button>' for a, v, h in numeros_clave(D))
    # --- preguntas ---
    qa = ""
    for tema, preguntas in preguntas_defensa(D):
        qa += f"<h3>{e(tema)}</h3>" + "".join(f'<details><summary>{md(q)}</summary><div class="resp"><p>{md(a)}</p></div></details>' for q, a in preguntas)
    # --- reflexión ---
    ref = ""
    for i, (q, a) in enumerate(reflexion(D), start=1):
        ref += (f'<p class="refl-p">{i}. {e(q)}</p><textarea class="refl" id="refl{i}" data-guardar="refl{i}" aria-label="Respuesta a la pregunta {i}">{e(a)}</textarea>'
                f'<p><button type="button" class="btn btn--chico btn--ghost" data-restablecer="refl{i}">Restablecer el borrador</button></p>')
    quiz = json.dumps(preguntas_quiz(D), ensure_ascii=False)
    return f"""<section class="seccion estudio no-pres" id="estudiar"><div class="cont">
<p class="etq"><span>Estudiar</span></p><h2 class="titular">Herramientas para estudiar</h2>
<p class="lead">Todo sale de las mismas cifras de la página. Lo que escribas en la reflexión se guarda solo en este navegador.</p>
<div class="tabs" role="tablist" aria-label="Herramientas de estudio">
<button role="tab" id="t-gl" aria-controls="p-gl" aria-selected="true">Glosario</button><button role="tab" id="t-nm" aria-controls="p-nm" aria-selected="false" tabindex="-1">Números clave</button>
<button role="tab" id="t-qa" aria-controls="p-qa" aria-selected="false" tabindex="-1">Preguntas de defensa</button><button role="tab" id="t-qz" aria-controls="p-qz" aria-selected="false" tabindex="-1">Autoevaluación</button>
<button role="tab" id="t-rf" aria-controls="p-rf" aria-selected="false" tabindex="-1">Reflexión del equipo</button></div>
<div class="panel" id="p-gl" role="tabpanel" aria-labelledby="t-gl"><div class="herr"><input type="search" id="gl-buscar" placeholder="Buscar un término" aria-label="Buscar un término"><button type="button" class="btn btn--chico btn--ghost" id="gl-auto" aria-pressed="false">Autoevaluación: ocultar definiciones</button></div><div class="glos" id="glosario">{gl}</div><p class="vacio" id="gl-vacio" hidden>Ningún término coincide con la búsqueda.</p></div>
<div class="panel" id="p-nm" role="tabpanel" aria-labelledby="t-nm" hidden><div class="herr"><button type="button" class="btn btn--chico btn--ghost" id="nm-tapar" aria-pressed="false">Autoevaluación: tapar los números</button></div><div class="nums" id="numeros">{nums}</div></div>
<div class="panel" id="p-qa" role="tabpanel" aria-labelledby="t-qa" hidden><div class="herr"><input type="search" id="qa-buscar" placeholder="Buscar en las preguntas" aria-label="Buscar en las preguntas"><button type="button" class="btn btn--chico btn--ghost" id="qa-todo" aria-pressed="false">Expandir todo</button></div><div class="qa" id="qa">{qa}</div><p class="vacio" id="qa-vacio" hidden>Ninguna pregunta coincide con la búsqueda.</p></div>
<div class="panel" id="p-qz" role="tabpanel" aria-labelledby="t-qz" hidden><p>Doce preguntas con explicación. Las opciones cambian de orden cada vez.</p><div id="quiz"></div><p class="quiz-res" id="quiz-res" aria-live="polite"></p><p><button type="button" class="btn btn--chico" id="quiz-otra">Empezar de nuevo</button></p></div>
<div class="panel" id="p-rf" role="tabpanel" aria-labelledby="t-rf" hidden><p>La guía de la maestra cierra con tres preguntas de reflexión. Aquí hay un borrador de respuesta para cada una; edítenlo con sus propias palabras.</p>{ref}</div>
<script type="application/json" id="datos-quiz">{quiz.replace("</", "<\\/")}</script></div></section>"""


def exponer(D) -> str:
    desc = {"A": "La pregunta, los objetivos y el ciclo KDD", "B": "La ENOE, el diseño muestral y la validación con cifras oficiales", "C": "Cobertura, faltantes, ingreso cero, imputación y atípicos", "D": "Arquitectura, esquema en estrella, SQL y MongoDB, reproducibilidad",
            "E": "Rao-Wu, intervalos, Spearman, Mincer, brecha y Holm", "F1": "Rendimiento de la escolaridad y ranking de entidades", "F2": "Brecha por hora y por mes, Oaxaca-Blinder, distribución y robustez", "F3": "Informalidad, tablero y diagnóstico del modelo", "G": "Síntesis, métricas de éxito, límites y cierre"}
    filas = [[BLOQUES[k].split(" · ", 1)[1], PRESENTA[k], desc[k], str(MINUTOS[k]), str(MIN_CORTA[k])] for k in ["A", "B", "C", "D", "E", "F1", "F2", "F3", "G"]]
    filas.append(["**Total**", "", "", f"**{sum(MINUTOS.values())}**", f"**{sum(MIN_CORTA.values())}**"])
    tabla_h = tabla(["Bloque", "Presenta (propuesta)", "Qué cubre", "Min. completa", "Min. ruta corta"], filas, num=(3, 4), destacar=(len(filas) - 1,),
                    pie="Reparto sugerido: es una propuesta; ajústenlo con el equipo. La presentación completa tiene 48 diapositivas y la ruta corta, las 18 marcadas con ★.")
    chk = [("ensayo", "Cada integrante ensayó su bloque con cronómetro."), ("idea", "Todos pueden decir primero la idea y después la cifra y el intervalo."), ("causal", "Todos saben responder «¿es causal?»: no, es una asociación."),
           ("abiertos", "Están a la mano la presentación, el tablero y el cuaderno (y el PDF de respaldo)."), ("equipo", "Probaron el proyector o la pantalla y el modo presentación de esta página."), ("limites", "Conocen las limitaciones y las dicen antes de que las pregunten."),
           ("mongo", "Saben decir con claridad que la carga a MongoDB real no se ejecutó, y qué sí se verificó.")]
    chk_h = '<ul class="chk">' + "".join(f'<li><label><input type="checkbox" data-chk="{k}"> <span>{e(t)}</span></label></li>' for k, t in chk) + "</ul>"
    teclas = lista(["**Flecha derecha, Re Pág o espacio:** siguiente escena; **flecha izquierda o Av Pág:** anterior.", "**N:** mostrar u ocultar el guion de la escena. **R:** cambiar entre ruta completa y ruta corta.",
                    "**Inicio / Fin:** primera o última escena. **Esc:** salir del modo presentación.", "El reloj arranca al entrar y se marca en rojo si pasa del tiempo de la ruta elegida."])
    consejos = lista(["Cuando pregunten por una cifra, **primero la idea** («cada año de estudio sube el ingreso 5 %») y después el número y el intervalo.", "Si no saben una respuesta, es válido decir qué harían para averiguarla; **no inventen cifras**.",
                      "Ante «¿es causal?», responder siempre que no y por qué: habilidad no observada y selección.", "Reconocer las limitaciones antes de que las pregunten transmite rigor."])
    return f"""<section class="seccion no-pres" id="exponer"><div class="cont">
<p class="etq"><span>Exponer</span></p><h2 class="titular">Plan para la exposición del jueves</h2>
<p class="lead">Dos rutas: la completa explica cada concepto y cada decisión; la corta cuenta la historia en las diapositivas marcadas con ★.</p>
<p><button type="button" class="btn" data-presentar="corta">Presentar la ruta corta ★ ({sum(MIN_CORTA.values())} min)</button> <button type="button" class="btn btn--ghost" data-presentar="completa">Presentar la ruta completa ({sum(MINUTOS.values())} min)</button></p>
<p><span class="chip">También se entra agregando #presentar-corta o #presentar al final de la dirección de esta página</span></p>
{tabla_h}
<div class="dos dos--igual"><div><p class="tit-c">Antes del jueves</p>{chk_h}</div><div><p class="tit-c">Cómo responder</p>{consejos}<p class="tit-c">Teclas del modo presentación</p>{teclas}</div></div>
{nota("Guion", "Cada escena de la página tiene su guion al final (sección «Guion para exponer»). Es el mismo texto de las notas del orador de la presentación completa.", "sencillo")}
</div></section>"""


def descargas() -> str:
    cards = [("Informe técnico (PDF)", "67 páginas: marco conceptual, datos, limpieza, ingeniería, metodología, resultados, discusión y anexos.", "descargas/Informe_Final_Proyecto_ENOE.pdf", "PDF"),
             ("Presentación completa (PDF)", "48 diapositivas; la versión editable está en la carpeta del proyecto.", "descargas/Presentacion_Completa_Proyecto_ENOE.pdf", "PDF"),
             ("Cuaderno ejecutado", "El notebook con código, tablas y gráficas, exportado a HTML.", "cuaderno.html", "HTML"),
             ("Tablero interactivo", "Ficha de cada entidad con mapa, ranking y gráficas (funciona sin internet).", "tablero.html", "HTML")]
    h = '<div class="descargas">' + "".join(f'<a class="tarjeta" href="{u}" target="_blank" rel="noopener"><h3>{e(t)}</h3><p>{e(d)}</p><small>{k} · se abre en otra pestaña</small></a>' for t, d, u, k in cards) + "</div>"
    return f"""<section class="seccion no-pres" id="descargas"><div class="cont">
<p class="etq"><span>Descargas</span></p><h2 class="titular">Documentos del proyecto</h2>{h}
{p("En la carpeta del proyecto también están el informe en Word, las presentaciones en PowerPoint, el código (`src/` y `scripts/`), las pruebas (`tests/`) y la documentación (`docs/`).")}
</div></section>"""
