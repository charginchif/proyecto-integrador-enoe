"""Informe técnico · secciones 8 (discusión), 9 (conclusiones) y anexos (glosario, guía de ejecución, resultados por entidad, defensa, guion y referencias)."""
from __future__ import annotations

import pandas as pd
from docx.shared import Cm

from informe_datos import f1, n_es, pval
from informe_lib import Informe
from enoe import config as C

FIG = C.FIGURES


def ic(a: float, b: float, d: int = 1) -> str:
    return f"{a:.{d}f} a {b:.{d}f}"


def seccion8(inf: Informe, D) -> None:
    R, tot, rt = D.R, D.tot, D.rt
    inf.h1("8. Discusión")
    inf.h2("8.1 Hallazgos principales")
    inf.numerada([
        f"**Estudiar paga, y paga más en lo alto de la escalera.** Cada año de escolaridad se asocia con {f1(rt['nacional_pct']['est'])} % más ingreso por hora (IC 95 %: {ic(rt['nacional_pct']['ic_inf'], rt['nacional_pct']['ic_sup'])}) entre personas de igual edad, sexo, entidad y tamaño de localidad. "
        f"El beneficio no es lineal: terminar una licenciatura o un posgrado se asocia con {D.premio_por_nivel.iloc[3]['premio_pct']:.0f} % más ingreso por hora que no terminar la primaria, mientras que terminar la primaria agrega solo {D.premio_por_nivel.iloc[0]['premio_pct']:.0f} %.",
        f"**El rendimiento de estudiar es parecido en estados ricos y pobres.** La diferencia entre los estados del cuartil de mayor ingreso y los del menor es prácticamente cero (p = {D.dq['p']:.2f}). Los estados más escolarizados pagan más (Spearman entre estados = {rt['rho_estatal_esc_ingreso']['est']:.2f}), pero el aumento porcentual por año de estudio es similar.",
        f"**El ranking de entidades solo es defendible en los extremos.** La correlación escolaridad-ingreso va de {rt['rho_min']['rho_est']:.2f} ({rt['rho_min']['entidad']}) a {rt['rho_max']['rho_est']:.2f} ({rt['rho_max']['entidad']}), pero el lugar de las entidades intermedias tiene intervalos de decenas de lugares.",
        f"**La brecha salarial de género depende de qué se mida.** Por hora es de {f1(tot['brecha_hora_pct'])} % ({ic(tot['brecha_hora_inf'], tot['brecha_hora_sup'])}) y significativa en los cuatro niveles de instrucción tras la corrección de Holm; por mes, de {f1(tot['brecha_mens_pct'])} %. "
        f"La diferencia mensual se debe sobre todo a que las mujeres trabajan {f1(tot['menos_horas_mujeres_pct'])} % menos horas pagadas. Entre personas comparables la brecha por hora es de {D.g5['brecha_pct']:.1f} %.",
        "**La brecha por hora se concentra abajo y en el empleo informal.** Es de 8.2 % en el decil inferior y de 10.4 % en el cuartil inferior, desaparece en la mediana y se invierte levemente en el cuartil superior; y es significativa entre los trabajadores informales (4.3 %) pero no entre los formales (1.2 %).",
        f"**Las mujeres tienen mejores características, pero reciben menos pago a igualdad de ellas.** En la descomposición de Oaxaca-Blinder, las diferencias en escolaridad y ubicación favorecen a las mujeres; la parte no explicada (6.9 puntos logarítmicos) es mayor que la brecha total (3.8) y no debe leerse como discriminación probada.",
        f"**La informalidad es alta, desigual y baja con la escolaridad.** El {f1(D.nac['est'])} % de los ocupados es informal; de {D.mn_til['til1_est']:.0f} % ({D.mn_til['entidad']}) a {D.mx_til['til1_est']:.0f} % ({D.mx_til['entidad']}); "
        f"de {R['til1']['por_nivel']['1']:.0f} % entre quienes no terminaron la primaria a {R['til1']['por_nivel']['4']:.0f} % con preparatoria o más. Entre estados, la asociación es de {D.asoc.loc['rho_spearman_til_esc', 'est']:.2f} (Spearman).",
        f"**El ingreso «cero» es un problema de medición y no de pobreza extrema:** {D.cero_pond:.0f} % de los ocupados tiene `ingocup = 0`, pero solo {D.C_t:.0f} % no recibe ingresos. Quien más estudió declara con menos frecuencia el monto exacto, por lo que la muestra salarial subrepresenta a los más escolarizados."])

    inf.h2("8.2 Evaluación de las métricas de éxito")
    inf.tabla([["M1", "Brecha salarial de género (%) por nivel de instrucción, con IC 95 % y prueba de hipótesis", "Tabla de la sección 7.4: brecha por hora y mensual en los cuatro niveles, con IC por bootstrap de Rao-Wu y valores p ajustados con Holm; también pruebas de Welch y Mann-Whitney y *d* de Cohen.", "Cumplida"],
               ["M2", "Correlación escolaridad-ingreso (Spearman) en las 32 entidades, con IC por bootstrap y un ranking defendible", "Spearman ponderado para las 32 entidades con IC y con el intervalo del lugar de cada entidad (sección 7.3 y Anexo C). Se declara explícitamente que el ranking solo distingue los extremos.", "Cumplida"],
               ["M3", "Tablero con al menos cuatro visualizaciones interpretables, alimentado por un pipeline que carga a MongoDB consultable por entidad", "Tablero interactivo de un solo archivo con seis visualizaciones y la ficha de cada entidad (`tablero/tablero_enoe.html`); pipeline que construye y exporta los documentos y verifica que la agregación documental reproduce la vista SQL.", "Cumplida, con una salvedad: la carga a un servidor MongoDB real no se ejecutó"]],
              ["Métrica", "Exigencia del protocolo", "Evidencia", "Estado"], [1.7, 4.5, 6.9, 3.4], pie="Cumplimiento de las métricas de éxito del protocolo.", alinear=["centro", "izq", "izq", "izq"], fuente=9)

    inf.h2("8.3 Interpretación integrada")
    inf.p("Los resultados forman una historia coherente. **La educación paga**, y paga sobre todo cuando se llega a niveles altos, pero la ganancia porcentual por año de estudio es parecida en todo el país: lo que cambia entre estados es el *nivel* de ingreso, no el *rendimiento* de estudiar. "
          "**El mayor beneficio de estudiar parece pasar por el tipo de empleo**: al controlar por posición, informalidad y rama el rendimiento baja de 5.1 % a 3.8 %, y la informalidad cae de 87 % a 38 % conforme aumenta la escolaridad. Estudiar abre la puerta al empleo formal.", alinear="justificado")
    inf.p("**La desigualdad de género en el ingreso tiene dos componentes de naturaleza distinta.** Uno es de *tiempo*: las mujeres trabajan una cuarta parte menos horas remuneradas, lo que explica casi toda la brecha mensual. El otro es de *pago por hora*: entre personas comparables, las mujeres ganan alrededor de 8 % menos, con una desventaja concentrada en la parte baja de la distribución y en el empleo informal, es decir, donde hay menos protección salarial. "
          "Que la brecha por hora aumente al comparar personas con la misma escolaridad (de 3.7 % a 7.7 %) muestra que las mujeres obtienen menos ingreso a pesar de tener más estudios.", alinear="justificado")

    inf.h2("8.4 Implicaciones y recomendaciones")
    inf.p("Los resultados son asociaciones, no efectos causales; las siguientes implicaciones se formulan con esa cautela y como líneas de reflexión, no como evaluación de políticas.", alinear="justificado")
    inf.vinetas(["**Educación.** Como el mayor beneficio se concentra en completar la educación media superior y superior, las políticas que reduzcan el abandono entre la secundaria y la licenciatura (becas, cobertura, transporte) apuntan al tramo con mayor rendimiento asociado. La similitud del rendimiento entre estados sugiere que el beneficio de estudiar no es exclusivo de los estados ricos.",
                 "**Informalidad.** La asociación entre escolaridad e informalidad (de 87 % a 38 %) y su variación regional (de 33 % a 80 %) indican que cualquier estrategia para formalizar el empleo debe considerar tanto la oferta de personas con estudios como la generación de empleos formales en el Sur y Centro del país.",
                 "**Igualdad de género.** La brecha mensual depende sobre todo de las horas; reducirla pasa por medidas que amplíen las oportunidades de trabajo remunerado de jornada completa (servicios de cuidado, flexibilidad laboral). La concentración de la brecha por hora en la parte baja de la distribución y en el empleo informal sugiere prestar atención a los pisos salariales y a la formalización.",
                 f"**Medición.** El {D.cero_pond:.0f} % de los ocupados no da un monto exacto de ingreso y la no respuesta no es aleatoria. Mejorar su captación, o publicar ajustes por no respuesta, aumentaría la precisión de los estudios sobre ingreso."])

    inf.h2("8.5 Limitaciones")
    inf.tabla([["Correlación, no causalidad", "No se puede afirmar que estudiar un año más *cause* un aumento de 5 %: personas con más estudios pueden diferir en habilidad, redes o contexto familiar (sesgo de habilidad)."],
               ["Selección en el empleo", "Solo se observa el ingreso de quienes trabajan. Si las mujeres que trabajan son un grupo seleccionado (por ejemplo, con más escolaridad), la brecha estimada se distorsiona. No se modeló la participación laboral (corrección de Heckman, 1979)."],
               ["Selección en la declaración del ingreso", "Solo se usa a quienes dan monto exacto (61 %). La no respuesta no es aleatoria; se evaluó con imputación, IPW y asalariados, pero no se puede descartar un sesgo residual."],
               ["Medición del ingreso", "El ingreso es autorreportado, redondeado y se refiere al mes anterior; el ingreso por hora usa las horas de una sola semana, lo que introduce error de medición (sesgo de división)."],
               ["Un solo trimestre", "Los resultados describen el 4.º trimestre de 2025; no se puede hablar de tendencias ni de estacionalidad."],
               ["Falacia ecológica", "Las relaciones entre estados (por ejemplo, escolaridad promedio e ingreso mediano) no se pueden leer a nivel individual."],
               ["Precisión por entidad", "Con 1,900 a 5,900 observaciones salariales por estado, los intervalos son amplios; las diferencias entre entidades cercanas no son distinguibles. Las 32 brechas estatales no se corrigen por multiplicidad y son solo descriptivas."],
               ["Ocupación específica no observada", "No se controla por la ocupación detallada, la experiencia real, la antigüedad ni las interrupciones de carrera, por lo que la parte «no explicada» de Oaxaca-Blinder no equivale a discriminación."],
               ["Elementos por verificar", "Los códigos de `p6c` se infirieron de su correspondencia exacta con `ing7c`; las cifras del INEGI usadas para validar se consultaron mediante búsqueda web de los boletines; no se cargó a un servidor MongoDB real."]],
              ["Limitación", "Qué implica"], [4.4, 12.1], pie="Limitaciones del estudio.", alinear=["izq", "izq"], fuente=9, negrita_col0=True)

    inf.h2("8.6 Trabajo futuro")
    inf.vinetas(["Usar **varios trimestres** (el panel rotativo de la ENOE permite seguir hasta cinco veces a una misma persona) para estudiar tendencias y controlar características fijas no observadas.",
                 "Modelar la **participación laboral** (corrección de Heckman) para tratar la selección hacia el empleo, y las **horas de trabajo no remunerado** (Encuesta Nacional sobre Uso del Tiempo) para dimensionar la parte de la brecha asociada con los cuidados.",
                 "Agregar la **ocupación detallada** (SINCO) y regresiones cuantílicas para describir mejor la brecha a lo largo de la distribución.",
                 "Un mapa geográfico real con el Marco Geoestadístico del INEGI, **estimación en áreas pequeñas** para mejorar la precisión por entidad y la carga de los documentos en un servidor **MongoDB real** con una API de consulta."])


def seccion9(inf: Informe, D) -> None:
    R, tot, rt = D.R, D.tot, D.rt
    inf.h1("9. Conclusiones")
    inf.p("El proyecto cumple el ciclo KDD completo sobre datos reales y responde la pregunta planteada:", despues=2, keep=True)
    inf.numerada([f"**Rendimiento de la escolaridad:** +{f1(rt['nacional_pct']['est'])} % de ingreso por hora por año de estudio (IC 95 %: {ic(rt['nacional_pct']['ic_inf'], rt['nacional_pct']['ic_sup'])}), con un premio de {D.premio_por_nivel.iloc[3]['premio_pct']:.0f} % para quienes tienen licenciatura o posgrado; resultado estable ante siete especificaciones alternativas (de {D.robustez_retorno.retorno_pct.min():.1f} % a {D.robustez_retorno.retorno_pct.max():.1f} %).",
                  "**Entre entidades:** el rendimiento no es distinto entre los estados de mayor y menor ingreso; la correlación escolaridad-ingreso varía entre 0.21 y 0.49 y el ranking solo es defendible en los extremos.",
                  f"**Brecha salarial de género:** {f1(tot['brecha_hora_pct'])} % por hora y {f1(tot['brecha_mens_pct'])} % por mes. Es estadísticamente significativa en los cuatro niveles de instrucción, aunque pequeña en tamaño del efecto; la diferencia mensual es sobre todo de horas trabajadas ({f1(tot['menos_horas_mujeres_pct'])} % menos); entre personas comparables es de {D.g5['brecha_pct']:.1f} %.",
                  f"**Informalidad:** {f1(D.nac['est'])} % de los ocupados, de {D.mn_til['til1_est']:.0f} % a {D.mx_til['til1_est']:.0f} % según la entidad, y estrechamente asociada con la escolaridad ({R['til1']['por_nivel']['1']:.0f} % → {R['til1']['por_nivel']['4']:.0f} %).",
                  f"**Calidad de los datos:** el «ingreso cero» de la ENOE esconde información incompleta ({D.B_t:.0f} % solo da un rango de salarios mínimos y {D.D_t:.0f} % no especifica); la no respuesta es selectiva, y por eso las conclusiones se contrastaron con imputación, ponderación inversa y solo asalariados.",
                  "**Ingeniería de datos:** el proceso es reproducible de principio a fin (una semilla, una orden, 34 pruebas, 30 archivos de resultados idénticos en dos corridas), y la arquitectura relacional (SQLite) y documental (MongoDB) responde a patrones de acceso distintos.",
                  "**Alcance:** los resultados son asociaciones de un trimestre; su lectura causal requeriría otros diseños de investigación."])
    inf.recuadro("Mensaje final", ["Estudiar se asocia con un mayor ingreso y con menos informalidad en todo el país; la desigualdad de género en el ingreso mensual es, sobre todo, una desigualdad de horas, y la de pago por hora se concentra en quienes menos ganan."])


GLOSARIO = [("ACID", "Propiedades de una base de datos transaccional: atomicidad, consistencia, aislamiento y durabilidad. SQLite las cumple."),
      ("Asimetría", "Medida de qué tan desbalanceada está una distribución. Vale 0 si es simétrica; el ingreso por hora tiene 3.1 y su logaritmo, 0.06."),
      ("Bootstrap", "Técnica que estima la incertidumbre volviendo a muestrear los propios datos muchas veces."),
      ("Brecha salarial de género", "Porcentaje menos que ganan las mujeres que los hombres; aquí se calcula comparando medias geométricas de ingresos."),
      ("COE2T", "Tabla de la ENOE con el cuestionario de ocupación y empleo (parte 2); contiene el detalle de la captación del ingreso."),
      ("Cohen, d de", "Tamaño del efecto: diferencia de medias dividida entre la desviación estándar (0.2 pequeño, 0.5 mediano, 0.8 grande)."),
      ("Conglomerado", "Grupo de unidades parecidas entre sí (aquí, las viviendas de una UPM) que se muestrea como bloque."),
      ("Curtosis", "Peso de las colas de una distribución respecto a la normal; valor en exceso 0 = como la normal."),
      ("Dominio", "Subpoblación para la que se estima (un estado, un nivel de instrucción...). Se estima conservando todo el diseño muestral."),
      ("Efecto de diseño (deff)", "Razón entre la varianza real de un estimador con el diseño de la encuesta y la que tendría una muestra aleatoria simple del mismo tamaño."),
      ("ENOE", "Encuesta Nacional de Ocupación y Empleo del INEGI: principal fuente de información del mercado laboral mexicano."),
      ("Estrato", "Grupo de áreas parecidas a partir del cual se sortean las UPM."),
      ("ETL", "Extract-Transform-Load: proceso de extraer, transformar y cargar datos."),
      ("Factor de expansión (fac_tri)", "Número de personas de la población que representa cada persona de la muestra."),
      ("Falacia ecológica", "Error de atribuir a las personas una relación observada entre promedios de grupos (por ejemplo, entre estados)."),
      ("Heterocedasticidad", "Varianza de los errores de un modelo que no es constante."),
      ("Holm", "Corrección de valores p que controla la probabilidad de equivocarse al menos una vez en un conjunto de pruebas; es más potente que Bonferroni."),
      ("Hot-deck", "Imputación que toma el valor de «donantes» parecidos; aquí, la mediana de quienes declararon monto en el mismo rango."),
      ("Idempotencia", "Propiedad de un proceso que, si se repite, produce el mismo resultado sin duplicar efectos."),
      ("Imputación", "Sustituir un dato faltante por un valor plausible."),
      ("Informalidad laboral (TIL1)", "Porcentaje de ocupados en un empleo informal (sin protección laboral formal) respecto al total de ocupados de 15 años y más."),
      ("Ingreso por hora", "Ingreso mensual dividido entre las horas trabajadas al mes (horas semanales × 4.3)."),
      ("Intervalo de confianza", "Rango de valores plausibles para una cantidad poblacional; al 95 %, el procedimiento contiene al valor verdadero el 95 % de las veces."),
      ("IPW", "Ponderación por la probabilidad inversa de responder: da más peso a quienes se parecen a los que no respondieron."),
      ("KDD", "Knowledge Discovery in Databases: proceso completo de descubrimiento de conocimiento (selección, preprocesamiento, transformación, minería, interpretación)."),
      ("Linealización de Taylor", "Método analítico para calcular varianzas de estimadores complejos respetando estratos y UPM."),
      ("Logaritmo natural", "Transformación que acorta las colas largas; la diferencia de logaritmos equivale a una diferencia porcentual."),
      ("Logit", "Regresión para una variable sí/no; sus coeficientes se leen como razones de momios."),
      ("Media geométrica", "Exponencial del promedio de los logaritmos; resume mejor datos con cola larga."),
      ("Mincer, ecuación de", "Regresión del logaritmo del ingreso sobre los años de escolaridad y la experiencia; mide el rendimiento de la educación."),
      ("MongoDB", "Base de datos documental (NoSQL) que guarda documentos JSON."),
      ("NDJSON", "Formato con un documento JSON por línea; es el que usa `mongoimport`."),
      ("Oaxaca-Blinder", "Descomposición de la diferencia entre dos grupos en una parte explicada por características y otra no explicada."),
      ("Panel rotativo", "Diseño en el que cada vivienda se entrevista varias veces consecutivas (en la ENOE, cinco)."),
      ("Persistencia políglota", "Usar distintos tipos de bases de datos según el patrón de acceso."),
      ("Percentil", "Valor bajo el cual queda cierto porcentaje de las observaciones (P10: 10 %)."),
      ("Razón de momios (odds ratio)", "Cociente de los momios de un evento entre dos situaciones; 0.82 = 18 % menos momios."),
      ("Rao-Wu, bootstrap de", "Bootstrap para encuestas complejas que remuestrea UPM dentro de cada estrato y reescala los ponderadores."),
      ("Rango (Spearman)", "Lugar que ocupa un valor al ordenar todos los datos; los empates reciben el rango medio."),
      ("SDEMT", "Tabla de la ENOE con las variables sociodemográficas y laborales de cada persona, además del ponderador."),
      ("Sesgo de división", "Relación negativa mecánica entre el ingreso por hora y las horas trabajadas causada por el error de medición en las horas."),
      ("SQLite", "Base de datos relacional contenida en un solo archivo, sin servidor."),
      ("Salario mínimo (SM)", "Unidad en que la ENOE capta los rangos de ingreso; en 2025: $8,364 al mes (zona general) y $12,596 (frontera norte)."),
      ("UPM", "Unidad Primaria de Muestreo: conjunto de viviendas que se sortea en la primera etapa del diseño."),
      ("Valor p", "Probabilidad de observar una diferencia tan grande como la hallada si la hipótesis nula fuera cierta."),
      ("VIF", "Factor de inflación de la varianza: mide la multicolinealidad; valores menores que 5 se consideran aceptables."),
      ("WLS", "Mínimos cuadrados ponderados: regresión en la que cada observación pesa según su factor de expansión.")]


def preguntas_defensa(D) -> list:
    """Preguntas frecuentes de la defensa, agrupadas por tema: [(tema, [(pregunta, respuesta), ...]), ...]. Las cifras salen de D."""
    R, tot = D.R, D.tot
    re = D.retorno_entidad.set_index("cve_ent")
    cdmx, bcs = re[re.entidad == "Ciudad de México"].iloc[0], re[re.entidad == "Baja California Sur"].iloc[0]
    return [
        ("A. Conceptos", [
            ("¿Qué es el factor de expansión y por qué hay que usarlo?", "Es el número de personas de la población que representa cada persona de la muestra (`fac_tri`; su suma es 131 millones). Sin ponderar se describe a la muestra, no al país."),
            ("¿Qué es el efecto de diseño?", f"Cuánto más grande es la varianza real, por ser una muestra por conglomerados, que la de una muestra aleatoria simple. Aquí vale {D.deff.loc['TIL1 nacional', 'deff']:.1f} en la informalidad: 190 mil ocupados equivalen a unos 40 mil independientes."),
            ("¿Cómo se interpreta un intervalo de confianza del 95 %?", "Es un rango de valores plausibles: si se repitiera el estudio muchas veces, el 95 % de los intervalos construidos así contendría el valor real. Si no incluye el cero, la diferencia es significativa."),
            ("¿Qué diferencia hay entre «significativo» y «grande»?", f"El valor p dice si una diferencia puede deberse al azar; el tamaño del efecto dice si importa. Con 112 mil observaciones casi todo es significativo; por eso se reporta la d de Cohen (0.06 a 0.24, pequeña) y la brecha en %."),
            ("¿Por qué 4.3 semanas por mes?", "Es la convención del INEGI para construir `ing_x_hrs = ingocup / (hrsocup × 4.3)` (52 semanas ÷ 12 meses ≈ 4.33); nuestra variable coincide con la del INEGI con error relativo menor de 0.01 %.")]),
        ("B. Datos y limpieza", [
            ("¿Por qué ese conjunto de datos y cómo saben que está bien leído?", "ENOE 4T-2025 del INEGI: 419,038 registros, fuente oficial, con «suciedad» real y diccionario. Con la base oficial se reproducen **7 de 7 cifras publicadas** (PEA 61.3 M, participación 59.3 %, informales 32.9 M, TIL1 55.0 % y los TIL1 de Chiapas, Chihuahua y CDMX). Si se incluyeran los menores de 15 años, el TIL1 sería 55.27 % y no coincidiría."),
            ("¿Qué limpieza hicieron y por qué esas reglas?", "La cobertura (entrevista completa, residente habitual, 15+, ocupado) elimina filas; lo demás (faltantes codificados, calidad del ingreso, atípicos) **crea banderas** para poder hacer análisis de sensibilidad sin volver a limpiar. Cada regla es una función probada y queda en una bitácora (de 419 mil a 112 mil)."),
            ("«No hay nulos» en la ENOE, ¿entonces qué limpiaron?", "Los faltantes vienen **codificados como valores reales**: escolaridad 99 (610 casos), horas 0 (5,278 ocupados ausentes) u horas mayores de 112 (41 casos imposibles). Un `isna()` diría que todo está completo."),
            ("¿Qué es el «ingreso cero» y por qué importa?", f"El {D.cero_reg:.0f} % de los registros tiene `ingocup = 0`, pero no es «sin ingreso»: {D.B_t:.0f} % (ponderado) solo da un **rango de salarios mínimos**, {D.D_t:.0f} % no especifica y solo {D.C_t:.0f} % realmente no recibe ingresos. Además, quien más estudió declara menos el monto exacto ({D.A_n4:.0f} % frente a {D.A_n1:.0f} %): los datos faltan de forma no aleatoria. Por eso se contrastó con imputación por rango, IPW y solo asalariados."),
            ("¿Por qué recortan atípicos en P0.5-P99.5 por entidad?", f"El ingreso por hora va de ${D.ing_hora_min:.2f} a ${D.ing_hora_max:,.0f}. Recortar dentro de cada entidad respeta que los salarios difieren por estado. Es 1 % de la muestra y el resultado casi no cambia sin recorte (brecha {D.rob_tot.loc['S1 Sin recorte', 'brecha_pct']:.1f} % frente a {tot['brecha_hora_pct']:.1f} %; rendimiento {D.robr.loc['R1 Sin recorte', 'retorno_pct']:.1f} % frente a {D.robr.loc['R0 Base', 'retorno_pct']:.1f} %).")]),
        ("C. Estadística", [
            ("¿Por qué ponderan con `fac_tri` y por qué el bootstrap de Rao-Wu?", "Cada persona representa a `fac_tri` personas. Y como la ENOE es por conglomerados, los errores estándar «normales» serían demasiado pequeños: Rao-Wu remuestrea UPM dentro de estratos y reescala los ponderadores; se verificó que reproduce la varianza de Taylor."),
            ("¿Por qué el logaritmo del ingreso?", f"Porque el ingreso por hora tiene asimetría {D.dg['asimetria_ingreso_nivel']:.1f} y el logaritmo la vuelve simétrica ({D.dg['asimetria_ln_ingreso']:.2f}); además, una diferencia de logaritmos es una diferencia porcentual aproximada."),
            ("¿Spearman o Pearson?", "Spearman: mide asociación monótona, robusta a atípicos y a la forma de la relación; la escolaridad tiene muchos empates (se usan rangos medios ponderados). Con pesos iguales coincide con SciPy."),
            ("¿Qué significa «ranking defendible»?", f"Que se reporta con incertidumbre: cada estado tiene un intervalo del lugar que ocupa. La Ciudad de México es la primera con seguridad (lugar {int(cdmx.rho_rango_inf)} a {int(cdmx.rho_rango_sup)}), Baja California Sur está entre las últimas ({int(bcs.rho_rango_inf)} a {int(bcs.rho_rango_sup)}), pero los estados del centro del ranking tienen intervalos de 15 o más lugares y **no se pueden distinguir**."),
            ("¿Por qué Holm y no Bonferroni?", "Holm controla la misma tasa de error por familia pero es uniformemente más potente. Se aplica a las cuatro pruebas por nivel de instrucción."),
            ("¿Por qué hay Welch y Mann-Whitney *y* el método de diseño?", "El protocolo pedía las pruebas clásicas (sin ponderar) y coinciden en las conclusiones; pero la inferencia **correcta** para la población es la que usa el diseño. Se muestran las dos.")]),
        ("D. Resultados", [
            ("¿Cuánto rinde un año de escolaridad?", f"≈ **{f1(D.rt['nacional_pct']['est'])} %** más ingreso por hora (IC 95 %: {ic(D.rt['nacional_pct']['ic_inf'], D.rt['nacional_pct']['ic_sup'])}) controlando edad, sexo, entidad y localidad; ≈ {D.retorno_modelos.iloc[3]['retorno_pct']:.1f} % si además se controla el tipo de empleo (parte del beneficio pasa por conseguir un mejor empleo). Es **robusto**: {D.robustez_retorno.retorno_pct.min():.1f} a {D.robustez_retorno.retorno_pct.max():.1f} % en siete especificaciones. No es lineal: licenciatura o posgrado paga **+{D.premio_por_nivel.iloc[3]['premio_pct']:.0f} %** frente a no terminar primaria."),
            ("¿Estudiar rinde más en estados ricos?", f"No: la diferencia entre el cuarto cuartil y el primero es ≈ 0 (p = {D.dq['p']:.2f}). El *nivel* de ingreso sí difiere (los estados más escolarizados pagan más: ρ = {D.rt['rho_estatal_esc_ingreso']['est']:.2f} entre estados), pero el *rendimiento por año* es parecido."),
            ("¿Hay brecha de género?", f"Sí, **pero depende de qué se mide**: por hora {f1(tot['brecha_hora_pct'])} % (IC {ic(tot['brecha_hora_inf'], tot['brecha_hora_sup'])}, p < 0.001); por nivel {D.bn.loc['1. Primaria incompleta', 'brecha_hora_pct']:.1f} / {D.bn.loc['2. Primaria completa', 'brecha_hora_pct']:.1f} / {D.bn.loc['3. Secundaria completa', 'brecha_hora_pct']:.1f} / {D.bn.loc['4. Medio superior y superior', 'brecha_hora_pct']:.1f} %, las cuatro significativas tras Holm; por **mes {f1(tot['brecha_mens_pct'])} %**. La diferencia mensual es de **horas** (las mujeres trabajan {f1(tot['menos_horas_mujeres_pct'])} % menos), no de pago por hora. Entre personas comparables, {D.g5['brecha_pct']:.1f} %."),
            ("¿Qué es la parte «no explicada» de Oaxaca-Blinder?", "La parte de la brecha que **no** se explica por las características medidas (escolaridad, edad, lugar, empleo, rama). Aquí las mujeres tienen *mejores* características (más escolaridad) pero reciben menos, así que el residuo (6.9 puntos logarítmicos) es mayor que la brecha total (3.8). **No prueba discriminación**: incluye todo lo no observado."),
            ("¿Por qué no interpretan el modelo con horas (G6)?", f"Por el **sesgo de división**: el ingreso por hora es ingreso ÷ horas, así que un error en las horas crea una relación negativa mecánica y la brecha «sube» a {D.g6['brecha_pct']:.0f} % artificialmente. Se muestra por transparencia."),
            ("¿Por qué la imputación (S3) da 0.7 % si las demás dan más?", "Imputar el grupo B con la mediana del rango le asigna **el mismo ingreso a un hombre y a una mujer** del mismo rango y borra diferencias: sesga hacia cero por construcción y es una cota inferior. La conclusión honesta: la brecha por hora es positiva pero su tamaño depende de la muestra (de 0.7 % a 4.6 %); la ajustada (≈ 8 %) y la mensual (≈ 27 %) son sólidas."),
            ("¿Dónde está la brecha?", "Abajo: 8.2 % en el P10 y 10.4 % en el P25; en la mediana es 2.1 % (no significativa) y arriba es nula o favorece a las mujeres (un «piso pegajoso»). También se concentra en el empleo informal."),
            ("¿Qué hallazgo hay sobre informalidad?", f"TIL1 nacional {f1(D.nac['est'])} %; de {D.mn_til['til1_est']:.0f} % ({D.mn_til['entidad']}) a {D.mx_til['til1_est']:.0f} % ({D.mx_til['entidad']}); {R['til1']['por_nivel']['1']:.0f} % entre quienes no terminaron la primaria frente a {R['til1']['por_nivel']['4']:.0f} % con preparatoria o más. Entre estados ρ = {D.asoc.loc['rho_spearman_til_esc', 'est']:.2f}; a nivel individual cada año de escolaridad baja ≈ {abs(D.ind['ame_anios_esc_pp']):.1f} puntos la probabilidad; ser mujer suma ≈ {D.ind['ame_mujer_pp']:.0f} puntos."),
            ("¿Es causal?", "No. Es una asociación: hay sesgo de habilidad no observada y selección. Y las relaciones entre estados no deben leerse a nivel individual (falacia ecológica).")]),
        ("E. Ingeniería de datos y NoSQL", [
            ("¿Por qué SQLite y MongoDB?", "Persistencia políglota por **patrón de acceso**: análisis (agregaciones ponderadas, `JOIN`, integridad) en una base relacional; servir la ficha de una entidad (un documento por clave, esquema flexible) en una documental. SQLite es la fuente de verdad; MongoDB es una vista de lectura que se regenera."),
            ("¿Por qué embeben los indicadores en `entidades` pero no las personas?", "Los indicadores se leen siempre junto con la entidad (una lectura, sin `JOIN`). Las 190 mil personas no caben en un documento (límite de 16 MB de BSON) ni se leen con la entidad: son una colección aparte relacionada por `cve_ent`."),
            ("¿Cargaron a un servidor MongoDB real?", "No: en la máquina de desarrollo no hay servidor ni `pymongo`. Se exportaron los documentos (NDJSON listos para `mongoimport`) y se **verificó que la agregación de MongoDB reproduce la vista SQL** (diferencia máxima 0.005 puntos porcentuales). Con `pip install pymongo` y un servidor, `python scripts/run_mongo.py --uri …` los carga."),
            ("¿Cómo garantizan la reproducibilidad?", "Una sola semilla (20251231), versiones y huellas SHA-256 en `etl_meta.json`, ETL idempotente, 34 pruebas automáticas y un cuaderno que se reconstruye desde `results/` con aserciones que avisan si una conclusión deja de ser cierta.")]),
        ("F. Preguntas incómodas", [
            ("¿Qué limitaciones tiene su trabajo?", "Un trimestre; ingreso autorreportado con redondeo; ingreso por hora a partir de las horas de *una* semana; selección en el empleo; no causalidad; entre 1,900 y 5,900 observaciones por estado; y la redacción literal de los códigos de `p6c` se infirió de su correspondencia con `ing7c` (conviene confirmarla con el cuestionario)."),
            ("¿Qué harían con más tiempo?", "Usar varios trimestres (panel rotativo), modelar la participación laboral (corrección de Heckman), hacer un mapa geográfico real con el Marco Geoestadístico y estimaciones para áreas pequeñas."),
            ("¿Qué parte hiciste tú?", "*(La responden los integrantes.)* Roles propuestos: ingeniería de datos y pipeline; análisis estadístico; visualización y comunicación. Cada integrante debe poder explicar de principio a fin al menos una sección del cuaderno.")])]


def anexos(inf: Informe, D) -> None:
    R, tot = D.R, D.tot
    re = D.retorno_entidad.set_index("cve_ent")
    # ------------------------------------------------------------------ A. Glosario
    inf.h1("Anexo A. Glosario")
    inf.tabla([[t, d] for t, d in GLOSARIO], ["Término", "Significado"], [4.6, 11.9], pie="Glosario de términos.", alinear=["izq", "izq"], fuente=9, negrita_col0=True)

    # ------------------------------------------------------------------ B. Guía de ejecución
    inf.h1("Anexo B. Guía para reproducir el proyecto")
    inf.h2("B.1 Requisitos")
    inf.vinetas(["**Python 3.12**, la versión con la que se desarrolló y verificó el proyecto (los paquetes fijados en `requirements.txt` requieren una versión reciente de Python).",
                 "Los paquetes de `requirements.txt`: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `plotly` (solo para incrustar `plotly.js` en el tablero), `nbformat`, `nbconvert`, `ipykernel`, `jinja2`, `python-pptx` (presentaciones), `python-docx` y `pillow` (este informe).",
                 "Los **microdatos del INEGI** (≈ 300 MB), que no se incluyen en el proyecto: https://www.inegi.org.mx/programas/enoe/15ymas/ → Microdatos → CSV → 4.º trimestre de 2025. Se necesitan `ENOE_SDEMT425.csv` y `ENOE_COE2T425.csv`.",
                 "Opcional: un servidor MongoDB y `pymongo` para la carga real de los documentos."])
    inf.h2("B.2 Instalación y datos")
    inf.codigo("""pip install -r requirements.txt
# Opción 1: copiar los CSV a la carpeta data\\raw
# Opción 2: indicar su ubicación con una variable de entorno (PowerShell):
$env:ENOE_RAW_DIR = "C:\\ruta\\a\\enoe_2025_trim4_csv"
""")
    inf.h2("B.3 Ejecución")
    inf.codigo("""python scripts/run_all.py            # todo el proyecto, ~10 minutos
python scripts/run_all.py --rapido   # 100 réplicas, sin cuaderno, presentaciones ni informe

# o paso a paso:
python scripts/run_etl.py            # 10 s    limpia, valida y crea la base SQLite
python scripts/run_analysis.py       # ~5 min  1,000 réplicas Rao-Wu; escribe results/
python scripts/make_figures.py       # 17 figuras de datos + 8 diagramas en figures/
python scripts/run_mongo.py --exportar   # documentos NoSQL + verificación contra SQL
python scripts/build_dashboard.py    # tablero/tablero_enoe.html
python scripts/build_notebook.py     # cuaderno ejecutado (.ipynb y .html)
python scripts/build_deck.py         # presentación corta (24 diapositivas)
python scripts/build_deck_completa.py  # presentación completa explicada
python scripts/build_informe.py      # este informe (Word)
powershell -File scripts\\exportar_informe.ps1   # (Windows con Word) índice y PDF del informe
python -m unittest discover -s tests # 34 pruebas automáticas""")
    inf.h2("B.4 Qué produce cada paso")
    inf.tabla([["`run_etl.py`", "`data/processed/enoe_2025t4.sqlite`; `results/etl_*.csv`; `results/etl_meta.json`"],
               ["`run_analysis.py`", "30 tablas en `results/*.csv`, `results/resumen.json` y tablas `res_*` en la base"],
               ["`make_figures.py`", "`figures/01…17_*.png` y `figures/D01…D08_*.png`"],
               ["`run_mongo.py`", "`data/processed/mongo/` (entidades, personas, metadatos)"],
               ["`build_dashboard.py`", "`tablero/tablero_enoe.html` (funciona sin internet)"],
               ["`build_notebook.py`", "`notebooks/Proyecto_Integrador_ENOE.ipynb` y `.html`"],
               ["`build_deck*.py`", "`presentacion/Proyecto_Integrador_ENOE.pptx` y `presentacion/Presentacion_Completa_Proyecto_ENOE.pptx`"],
               ["`build_informe.py`", "`documento/Informe_Final_Proyecto_ENOE.docx`"]],
              ["Comando", "Archivos que genera"], [4.6, 11.9], pie="Salidas de cada paso de la ejecución.", alinear=["izq", "izq"], fuente=9, negrita_col0=True)
    inf.h2("B.5 Solución de problemas")
    inf.vinetas(["**`FileNotFoundError` con `ENOE_SDEMT425.csv`:** no se encontró la carpeta de datos; revise `ENOE_RAW_DIR` o copie los CSV a `data/raw`.",
                 "**Caracteres extraños al leer los CSV:** los archivos del INEGI están en codificación `latin-1`; el proyecto ya los lee así.",
                 "**Poca memoria:** el ETL carga solo 35 de las 115 columnas de SDEMT. Si el análisis agota la memoria, cierre otros programas o ejecute `python scripts/run_analysis.py --B 100`.",
                 "**Para una verificación rápida del análisis:** `python scripts/run_analysis.py --B 100`.",
                 "**Los resultados cambian de una corrida a otra:** no debería ocurrir (semilla fija). Revise que `etl_meta.json` registre la semilla 20251231 y las mismas versiones de las bibliotecas."])

    # ------------------------------------------------------------------ C. Resultados por entidad
    inf.h1("Anexo C. Resultados por entidad federativa")
    inf.p("Las tablas siguientes reúnen, para las 32 entidades, los indicadores que alimentan las métricas M2 y M3 y el tablero. Los intervalos son del bootstrap de Rao-Wu al 95 %; el lugar es el que ocupa la entidad en el ranking (1 = mayor valor) y su intervalo, en las 1,000 réplicas.", alinear="justificado")
    til = D.til1_entidad.set_index("cve_ent")
    filas = []
    for e in sorted(til.index):
        t, r = til.loc[e], re.loc[e]
        filas.append([t.entidad, t.region, f"{t.til1_est:.1f}", f"{t.til1_ic_inf:.1f} a {t.til1_ic_sup:.1f}", f"{int(t.til1_rango)} ({int(t.til1_rango_inf)}-{int(t.til1_rango_sup)})", f"{t.esc15_est:.1f}", f"{r.mln_est:.1f}", f"{r.mln_ic_inf:.1f} a {r.mln_ic_sup:.1f}"])
    inf.tabla(filas, ["Entidad", "Región", "TIL1 %", "IC 95 %", "Lugar (IC)", "Esc. media", "Mediana $/h", "IC 95 %"], [3.2, 2.0, 1.2, 2.3, 2.1, 1.3, 1.6, 2.7],
              pie="Informalidad (TIL1), escolaridad media de los ocupados e ingreso mediano por hora.", alinear=["izq", "izq", "der", "centro", "centro", "der", "der", "centro"], fuente=8)
    be = D.brecha_estados.set_index("cve_ent")
    filas = []
    for e in sorted(re.index):
        r, b = re.loc[e], be.loc[e]
        filas.append([r.entidad, f"{r.rho_est:.2f}", f"{r.rho_ic_inf:.2f} a {r.rho_ic_sup:.2f}", f"{int(r.rho_rango)} ({int(r.rho_rango_inf)}-{int(r.rho_rango_sup)})", f"{r.ret_est:.1f}", f"{r.ret_ic_inf:.1f} a {r.ret_ic_sup:.1f}",
                      f"{b.brecha_hora_est:.1f}", f"{b.brecha_hora_ic_inf:.1f} a {b.brecha_hora_ic_sup:.1f}"])
    inf.tabla(filas, ["Entidad", "ρ", "IC 95 %", "Lugar (IC)", "Rend. %", "IC 95 %", "Brecha %", "IC 95 %"], [3.2, 1.2, 2.3, 2.1, 1.4, 2.3, 1.6, 2.4],
              pie="Correlación de Spearman, rendimiento por año de escolaridad y brecha por hora en cada entidad.", alinear=["izq", "der", "centro", "centro", "der", "centro", "der", "centro"], fuente=8)

    # ------------------------------------------------------------------ D. Defensa
    inf.h1("Anexo D. Preguntas frecuentes de la defensa")
    inf.p("Respuestas cortas a las preguntas más probables. **Entiendan la lógica de cada respuesta; no las memoricen.** Las cifras proceden de `results/resumen.json`.", alinear="justificado")
    qa = preguntas_defensa(D)
    for bloque, preguntas in qa:
        inf.h3(bloque)
        for q, a in preguntas:
            inf.p(f"**{q}**", despues=1, keep=True)
            inf.p(a, alinear="justificado", despues=6)

    # ------------------------------------------------------------------ E. Guion
    inf.h1("Anexo E. Guion de exposición")
    inf.p("Propuesta de reparto de la exposición entre los tres integrantes del equipo. Hay dos versiones: la **presentación completa** (`Presentacion_Completa_Proyecto_ENOE.pptx`, 48 diapositivas que explican cada concepto y cada decisión; unos 50 minutos) y la **ruta corta** "
          "(las 18 diapositivas principales señaladas con ★ en la presentación completa, que también existen como presentación independiente de 24 diapositivas; unos 18 minutos). "
          "Las notas del orador de cada diapositiva incluyen el texto sugerido y el nombre de quien presenta, y el archivo está dividido en secciones por bloque.", alinear="justificado")
    inf.tabla([["A. Apertura", "Juan Evelio", "La pregunta, los objetivos, qué es el KDD y la hoja de ruta", "5", "2"],
               ["B. Datos y diseño muestral", "Juan Evelio", "ENOE, tablas, llave, diseño muestral, factor de expansión, validación con cifras oficiales", "5", "2"],
               ["C. Limpieza de datos", "Angel Yireh", "Embudo de filtros, códigos especiales, el ingreso cero, no respuesta, imputación, atípicos, 15 expectativas", "7", "2"],
               ["D. Ingeniería de datos", "Angel Yireh", "Arquitectura, esquema en estrella, SQL frente a MongoDB, reproducibilidad, pruebas, mapa del código", "6", "1"],
               ["E. Estadística explicada", "Luis Andre", "Diseño muestral y error, bootstrap de Rao-Wu, intervalos y valor p, Spearman, Mincer, brecha y Holm", "7", "2"],
               ["F1. Escolaridad e ingreso", "Luis Andre", "Rendimiento, estados ricos y pobres, ranking de entidades", "4", "3"],
               ["F2. Brecha de género", "Angel Yireh", "Brecha por hora y por mes, personas comparables, Oaxaca-Blinder, distribución, heterogeneidad y robustez", "6", "3"],
               ["F3. Informalidad, tablero y diagnóstico", "Luis Andre", "Informalidad y escolaridad, tablero interactivo, diagnóstico del modelo", "5", "1"],
               ["G. Cierre", "Juan Evelio", "Síntesis, métricas de éxito, limitaciones y cierre; al final (bloque H, respaldo) quedan el glosario y las preguntas difíciles", "4", "2"]],
              ["Bloque", "Presenta", "Contenido", "Min. (completa)", "Min. (ruta corta)"], [3.7, 2.2, 6.9, 1.9, 1.8], pie="Reparto sugerido de la exposición (49 minutos la versión completa; 18 minutos la ruta corta).", alinear=["izq", "izq", "izq", "centro", "centro"], fuente=9, negrita_col0=True)
    inf.h3("Tres mensajes que todo el equipo debe poder repetir")
    inf.numerada([f"Cada año de escolaridad se asocia con {f1(D.rt['nacional_pct']['est'])} % más ingreso por hora, con un beneficio mucho mayor en la licenciatura, y el rendimiento es parecido en estados ricos y pobres.",
                  f"La brecha de género es de {f1(tot['brecha_hora_pct'])} % por hora y de {f1(tot['brecha_mens_pct'])} % por mes: la diferencia mensual es sobre todo de horas trabajadas.",
                  "Los resultados son asociaciones, descritas con intervalos de confianza que respetan el diseño de la encuesta; el trabajo documenta qué se hizo, qué se verificó y qué no."])
    inf.h3("Consejos para la defensa")
    inf.vinetas(["Cuando se pregunte por una cifra, **responda primero con la idea** («cada año de estudio sube el ingreso 5 %») y después con el número y el intervalo.",
                 "Si no se sabe una respuesta, es válido decir qué se haría para averiguarla; **no inventar cifras**. Todas están en `results/resumen.json` y en el cuaderno.",
                 "Ante «¿es causal?», responder siempre que no, y explicar por qué (habilidad no observada, selección).",
                 "Tener abiertos el tablero y el cuaderno HTML para mostrar cualquier detalle a la audiencia.",
                 "Reconocer las limitaciones (anexo y sección 8.5) antes de que las pregunten: transmite rigor."])

    # ------------------------------------------------------------------ F. Referencias
    inf.h1("Anexo F. Referencias", salto=False)
    refs = ["Blau, F. D., y Kahn, L. M. (2017). The gender wage gap: Extent, trends, and explanations. *Journal of Economic Literature*, 55(3), 789-865.",
            "Blinder, A. S. (1973). Wage discrimination: Reduced form and structural estimates. *Journal of Human Resources*, 8(4), 436-455.",
            "Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2.ª ed.). Lawrence Erlbaum.",
            "Fayyad, U., Piatetsky-Shapiro, G., y Smyth, P. (1996). From data mining to knowledge discovery in databases. *AI Magazine*, 17(3), 37-54.",
            "Fortin, N., Lemieux, T., y Firpo, S. (2011). Decomposition methods in economics. En *Handbook of Labor Economics* (vol. 4A, pp. 1-102). Elsevier.",
            "Heckman, J. J. (1979). Sample selection bias as a specification error. *Econometrica*, 47(1), 153-161.",
            "Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65-70.",
            "INEGI. Encuesta Nacional de Ocupación y Empleo (ENOE), población de 15 años y más: metodología, descriptor de archivos y tabulados. https://www.inegi.org.mx/programas/enoe/15ymas/",
            "Jann, B. (2008). The Blinder-Oaxaca decomposition for linear regression models. *The Stata Journal*, 8(4), 453-479.",
            "Kish, L. (1965). *Survey Sampling*. Wiley.",
            "Little, R. J. A., y Rubin, D. B. (2019). *Statistical Analysis with Missing Data* (3.ª ed.). Wiley.",
            "Lumley, T. (2010). *Complex Surveys: A Guide to Analysis Using R*. Wiley.",
            "Mincer, J. (1974). *Schooling, Experience, and Earnings*. National Bureau of Economic Research.",
            "Neumark, D. (1988). Employers' discriminatory behavior and the estimation of wage discrimination. *Journal of Human Resources*, 23(3), 279-295.",
            "Oaxaca, R. (1973). Male-female wage differentials in urban labor markets. *International Economic Review*, 14(3), 693-709.",
            "Rao, J. N. K., y Wu, C. F. J. (1988). Resampling inference with complex survey data. *Journal of the American Statistical Association*, 83(401), 231-241.",
            "Rao, J. N. K., Wu, C. F. J., y Yue, K. (1992). Some recent work on resampling methods for complex surveys. *Survey Methodology*, 18(2), 209-217.",
            "Spearman, C. (1904). The proof and measurement of association between two things. *American Journal of Psychology*, 15(1), 72-101."]
    for r_ in refs:
        par = inf.p(r_, size=10, despues=4)
        par.paragraph_format.left_indent = Cm(1.0)
        par.paragraph_format.first_line_indent = Cm(-1.0)
