"""Informe técnico · secciones 4 (preprocesamiento) y 5 (transformación e ingeniería de datos)."""
from __future__ import annotations

import ast
import re

from docx.shared import RGBColor

from informe_datos import f1, n_es, pval
from informe_lib import Informe
from enoe import config as C

FIG = C.FIGURES


def seccion4(inf: Informe, D) -> None:
    bit, R = D.bit, D.R
    inf.h1("4. Preprocesamiento (KDD fase 2: limpieza)")
    inf.p("Los datos crudos nunca están listos para analizarse: traen personas que no corresponden a la población de estudio, códigos que significan «no sabe» y no cantidades, jornadas imposibles y, sobre todo en esta encuesta, "
          "un ingreso que vale cero por razones muy distintas. Esta sección explica cada decisión de limpieza, cuántos registros afectó y por qué se tomó. El principio rector es **marcar, no borrar**: "
          "el universo completo se conserva en la base de datos y cada análisis elige, mediante banderas, qué registros usa.", alinear="justificado")

    # ------------------------------------------------------------------ 4.1
    inf.h2("4.1 Bitácora de limpieza: del archivo crudo al universo de estudio")
    inf.p("Cada regla se registra en una bitácora (`etl_bitacora`, tabla del modelo relacional) con el número de registros antes y después. Así cualquier persona puede auditar cuántos registros se perdieron en cada paso y por qué.", alinear="justificado")
    pasos = {"L0": "Registros crudos (todas las personas del hogar)", "L1": "Entrevista completa (`r_def = 0`)", "L2": "Residente habitual (`c_res` ∈ {1, 3})",
             "L3": "Edad válida de 15 a 98 años", "L4": "Población ocupada (`clase2 = 1`)", "L5": "Ponderador positivo (`fac_tri > 0`)"}
    filas = [[k, v, n_es(bit.loc[k, "n_antes"]), n_es(bit.loc[k, "n_despues"]), n_es(bit.loc[k, "afectados"])] for k, v in pasos.items()]
    inf.tabla(filas, ["Paso", "Regla", "Antes", "Después", "Excluidos"], [1.3, 7.7, 2.6, 2.6, 2.3], pie="Embudo de filtros que define el universo de estudio (SDEMT, 4T-2025).", alinear=["centro", "izq", "der", "der", "der"])
    inf.figura(FIG / "01_embudo_datos.png", 15.8, "Embudo de datos: de 419,038 registros crudos a 190,187 personas ocupadas (universo), y de ahí a las muestras de análisis.")
    inf.vinetas(["**L1 (892 excluidos).** Solo se usan entrevistas completas; las incompletas no tienen datos laborales confiables.",
                 "**L2 (10,047).** Se excluyen los «nuevos residentes» (`c_res = 2`), que el INEGI no considera parte de la población residente habitual y para quienes no se captan sexo ni edad.",
                 "**L3 (84,732).** Se conservan las personas de 15 años o más con edad especificada. Esta restricción es la que hace coincidir el proyecto con la definición oficial de población ocupada.",
                 "**L4 (133,180).** Se conservan las personas ocupadas, que son el objeto de estudio.",
                 "**L5 (0).** Se comprueba que todos los ponderadores sean positivos; es una verificación, no excluye a nadie."])

    # ------------------------------------------------------------------ 4.2
    inf.h2("4.2 Datos faltantes y códigos especiales")
    inf.p("En los archivos del INEGI, un dato desconocido casi nunca aparece vacío: aparece como un **código especial** (99 años de escolaridad, nivel «no especificado», 0 horas...). Si se tratara ese 99 como un número real, "
          "se obtendrían promedios absurdos. Por eso cada código se convierte explícitamente en valor faltante y se registra:", alinear="justificado")
    filas = [["M1", "`anios_esc`", "99 = no especificado", n_es(bit.loc["M1", "afectados"]), "Se convierte en faltante; esa persona no entra al análisis de escolaridad."],
             ["M2", "`hrsocup`", "0 horas trabajadas la semana pasada", n_es(bit.loc["M2", "afectados"]), "Faltante: están ocupadas pero ausentes de su trabajo esa semana; no se puede calcular el ingreso por hora."],
             ["M3", "`hrsocup`", "> 112 horas semanales", n_es(bit.loc["M3", "afectados"]), "Faltante: 112 h equivale a 16 h diarias los 7 días; se considera un error de captura."],
             ["M4", "`niv_ins`", "5 = no especificado", n_es(bit.loc["M4", "afectados"]), "Se excluye del análisis por nivel de instrucción."]]
    inf.tabla(filas, ["Marca", "Variable", "Código", "Registros", "Tratamiento"], [1.2, 2.2, 3.9, 1.9, 7.3], pie="Códigos especiales convertidos en valores faltantes.", alinear=["centro", "izq", "izq", "der", "izq"], fuente=9)
    inf.p("Los faltantes son una fracción muy pequeña del universo (menos de 3 % en el peor caso), por lo que una eliminación simple no cambia las conclusiones. El caso importante no es este sino el del ingreso, que se trata en la siguiente sección.", alinear="justificado")

    # ------------------------------------------------------------------ 4.3
    inf.h2("4.3 El problema del «ingreso cero»")
    inf.p(f"La variable de ingreso mensual (`ingocup`) vale **cero en {D.cero_reg:.0f} % de los registros ({D.cero_pond:.0f} % de la población ponderada)**. Tomarla literalmente sería un error grave: no son personas que ganen cero. "
          "El INEGI capta el ingreso en dos pasos: primero se pregunta el monto exacto y, si la persona no lo da, se le ofrece una lista de rangos en salarios mínimos. `ingocup` solo guarda el monto exacto, "
          "y vale 0 cuando no lo hay. Para entender por qué vale 0 se cruza con el rango (`ing7c`) y se obtienen cuatro grupos mutuamente excluyentes y exhaustivos:", alinear="justificado")
    cal = D.calidad_ingreso
    def pct(g):
        r = cal[(cal.grupo == g) & (cal.poblacion == "Total")].iloc[0]
        return f"{r.pct:.1f} % ({r.inf:.1f}–{r.sup:.1f})"
    filas = [["A", "Monto exacto declarado (`ingocup > 0`)", n_es(bit.loc["QA", "afectados"]), pct("A"), "Es la única con ingreso conocido. Constituye la muestra salarial."],
             ["B", "Solo rango de salarios mínimos (`ingocup = 0`, `ing7c` 1 a 5)", n_es(bit.loc["QB", "afectados"]), pct("B"), "Ingreso acotado entre dos valores; se imputa en el análisis de sensibilidad."],
             ["C", "No recibe ingresos (`ing7c = 6`)", n_es(bit.loc["QC", "afectados"]), pct("C"), "Cero verdadero: 77 % son trabajadores sin pago. Se excluye del análisis salarial."],
             ["D", "No especificó (`ing7c = 7`)", n_es(bit.loc["QD", "afectados"]), pct("D"), "Ingreso desconocido; se excluye y se estudia como no respuesta."]]
    inf.tabla(filas, ["Grupo", "Qué significa", "Registros", "% ponderado (IC 95 %)", "Tratamiento"], [1.3, 5.2, 1.9, 3.3, 4.8], pie="Los cuatro grupos de calidad del ingreso (ocupados de 15 a 65 años).",
              alinear=["centro", "izq", "der", "der", "izq"], fuente=9)
    inf.recuadro("En palabras sencillas", [f"Cuando una persona dice «gano más o menos entre dos y tres salarios mínimos» pero no quiere decir cuánto exactamente, el archivo guarda un 0 en el ingreso. "
                                           f"Si no se corrige, parecería que {D.cero_pond:.0f} de cada 100 personas ocupadas no ganan nada. En realidad, solo el grupo C (alrededor de {D.C_t:.0f} de cada 100) no recibe ingreso."])
    inf.figura(FIG / "02_calidad_ingreso.png", 15.8, "Calidad del ingreso por grupo de declaración: composición total, por sexo y por nivel de instrucción.")
    inf.h3("¿Quiénes pertenecen a cada grupo?")
    pf = D.perf
    filas = [[g, f"{pf.loc[g, 'poblacion_millones']:.1f}", f"{pf.loc[g, 'mujeres_pct']:.0f}", f"{pf.loc[g, 'anios_esc']:.1f}", f"{pf.loc[g, 'edad']:.0f}", f"{pf.loc[g, 'informal_pct']:.0f}",
              f"{pf.loc[g, 'cuenta_propia_pct']:.0f}", f"{pf.loc[g, 'sin_pago_pct']:.0f}", f"{pf.loc[g, 'horas_semana']:.0f}"] for g in "ABCD"]
    inf.tabla(filas, ["Grupo", "Millones", "% mujeres", "Años esc.", "Edad", "% informal", "% cuenta propia", "% sin pago", "Horas/sem."], [1.4, 1.8, 1.9, 1.8, 1.4, 1.9, 2.4, 2.0, 1.9],
              pie="Perfil promedio de cada grupo (ponderado).", alinear=["centro"] + ["der"] * 8, fuente=9)
    inf.p("El grupo C es distinto de los demás: casi todas sus personas son informales (99 %), 77 % son trabajadores sin pago y tienen menos escolaridad. Los grupos B y D tienen más escolaridad que el A, lo que anticipa que la no respuesta del monto no es aleatoria.", alinear="justificado")
    inf.h3("¿La no respuesta es aleatoria? Pruebas χ² y regresión logística")
    ch = D.calidad_ingreso_chi2
    filas = [[r.variable.capitalize(), f"{r.chi2:,.0f}", str(int(r.gl)), pval(r.p), f"{r.v_cramer:.3f}"] for r in ch.itertuples()]
    inf.tabla(filas, ["Variable que se cruza con el grupo", "χ²", "g.l.", "Valor p", "V de Cramér"], [6.4, 2.6, 1.4, 2.6, 3.0], pie="Asociación entre el grupo de ingreso y características de la persona (χ² con n = 180,766).",
              alinear=["izq", "der", "der", "der", "der"], fuente=9.5)
    inf.p("Todas las asociaciones son estadísticamente significativas, pero la **V de Cramér** (0 = sin asociación, 1 = asociación perfecta) revela su tamaño real: mínima con el sexo (0.04), pequeña con el nivel de instrucción (0.10), "
          "moderada con la informalidad (0.22) y fuerte con la posición en la ocupación (0.52), lo que es lógico porque el grupo C está formado por trabajadores sin pago.", alinear="justificado")
    lg = D.no_respuesta_logit.set_index(["modelo", "variable"])
    def rm(m, v):
        r = lg.loc[(m, v)]
        return f"{r.razon_momios:.2f} ({r.rm_inf:.2f}–{r.rm_sup:.2f})"
    nombres = {"mujer": "Mujer", "anios_esc": "Un año más de escolaridad", "informal": "Empleo informal", "pos_empleador": "Empleador (vs. subordinado)",
               "pos_cuenta_propia": "Cuenta propia (vs. subordinado)", "eda_c": "Un año más de edad"}
    filas = [[nombres[v], rm("A_vs_resto", v), rm("D_vs_resto", v)] for v in nombres]
    inf.tabla(filas, ["Característica", "Declarar monto exacto (A) · razón de momios", "No especificar el ingreso (D) · razón de momios"], [5.7, 5.4, 5.4],
              pie="Regresión logística de la no respuesta (errores estándar agrupados por UPM). Una razón de momios mayor que 1 aumenta la probabilidad.", alinear=["izq", "centro", "centro"], fuente=9.5)
    inf.p("**Lectura.** Cada año adicional de escolaridad *reduce* 6.6 % los momios de declarar el monto exacto (razón de momios 0.93) y *aumenta* 7.5 % los de no especificar el ingreso (1.08). "
          "Las mujeres tienen mayor probabilidad de declarar el monto exacto (1.26) y los empleadores y trabajadores por cuenta propia, menor. La conclusión es importante: **quienes aparecen en la muestra salarial no son un subconjunto aleatorio**; "
          "tienden a tener menos escolaridad que quienes no declaran. Si esa selección distorsionara los resultados, se vería en los análisis de sensibilidad (imputación de rangos y ponderación por probabilidad inversa), que se presentan en las secciones 6 y 7.", alinear="justificado")

    # ------------------------------------------------------------------ 4.4
    inf.h2("4.4 Imputación del ingreso a partir del rango (grupo B)")
    inf.p("A las personas del grupo B se les conoce el rango (por ejemplo «más de 2 a 3 salarios mínimos»), pero no el monto. Para aprovechar esa información en el análisis de sensibilidad se les asigna un valor plausible con una imputación "
          "*hot-deck por rango*: se calcula la **mediana ponderada de (ingreso ÷ salario mínimo)** entre quienes sí declararon un monto exacto dentro del mismo rango y se multiplica por el salario mínimo de la persona. "
          "Se usa la mediana observada y no el punto medio del rango porque la distribución dentro del rango es asimétrica: hay más personas cerca del límite inferior que del superior.", alinear="justificado")
    im = D.etl_imputacion_rangos
    filas = [[int(r.p6c), r.rango, n_es(r.n_referencia_A), f"{r.razon_mediana_sm:.2f}", n_es(r.n_B_imputados)] for r in im.itertuples()]
    inf.tabla(filas, ["Código p6c", "Rango declarado", "Referencia (grupo A en el rango)", "Mediana imputada (× SM)", "Personas del grupo B"], [2.0, 4.3, 4.2, 3.4, 2.6],
              pie="Tabla de imputación por rango. SM = salario mínimo mensual de la persona.", alinear=["centro", "izq", "der", "der", "der"], fuente=9.5)
    r4 = im[im.p6c == 4].iloc[0]
    inf.p(f"*Ejemplo:* una persona de la zona general que declaró «más de 2 a 3 salarios mínimos» recibe {r4.razon_mediana_sm:.2f} × $8,364 = **${r4.razon_mediana_sm * 8364:,.0f} mensuales** (la mediana de quienes declararon un monto en ese rango). "
          "Para el rango «exactamente 1 SM» se asigna 1.00 por definición.", alinear="justificado")
    inf.recuadro("Advertencia metodológica", ["La imputación asigna **el mismo valor a todos los hombres y mujeres de un mismo rango**, por lo que comprime artificialmente las diferencias entre ellos. En consecuencia, "
                                              "*sesga la brecha de género hacia cero por construcción*. Por eso la imputación se usa solo como análisis de sensibilidad (muestra salarial ampliada: 145,529 personas) y nunca en el resultado principal."],
                fondo="FFF7E6", borde="EDA100")

    # ------------------------------------------------------------------ 4.5
    inf.h2("4.5 Valores atípicos")
    ub = D.etl_umbrales_atipicos
    inf.p(f"Un ingreso por hora de $5 o de $900 puede ser un error de captura o una persona verdaderamente extrema. Para que unas pocas observaciones no dominen los resultados se excluye el **0.5 % más bajo y el 0.5 % más alto de ln(ingreso por hora) dentro de cada entidad** "
          f"(percentiles P0.5 y P99.5). El corte se hace por entidad, y no a nivel nacional, para no eliminar sistemáticamente a los habitantes de las entidades más ricas o más pobres. En total se marcan {n_es(bit.loc['O1', 'afectados'])} observaciones "
          f"(1.0 % de las 113,338 con ingreso por hora calculable). Los umbrales varían de ${ub.hora_min.min():.0f} a ${ub.hora_min.max():.0f} por hora en el extremo inferior y de ${ub.hora_max.min():.0f} a ${ub.hora_max.max():.0f} en el superior, según la entidad.", alinear="justificado")
    inf.figura(FIG / "03_distribucion_ingreso.png", 15.8, "Distribución del ingreso por hora: en pesos (cola larga a la derecha) y en logaritmo natural (casi simétrica).")
    inf.p(f"El logaritmo corrige la asimetría: de {D.dg['asimetria_ingreso_nivel']:.2f} en pesos a {D.dg['asimetria_ln_ingreso']:.2f} en logaritmo, y la curtosis en exceso baja de {D.dg['curtosis_exceso_ingreso_nivel']:.1f} a {D.dg['curtosis_exceso_ln_ingreso']:.1f}. "
          "El recorte se evalúa además como análisis de sensibilidad (especificación sin recortar, sección 7.7).", alinear="justificado")

    # ------------------------------------------------------------------ 4.6
    inf.h2("4.6 Muestras de análisis")
    inf.p("Del universo de 190,187 ocupados se derivan las muestras de análisis mediante exclusiones sucesivas, todas registradas:", alinear="justificado", despues=3)
    em = D.etl_embudo_salarial
    filas = [[r.id, r.descripcion, n_es(r.n), n_es(r.excluidos)] for r in em.itertuples()]
    inf.tabla(filas, ["Paso", "Descripción", "Personas", "Excluidas"], [1.5, 9.5, 2.8, 2.7], pie="Embudo de la muestra salarial.", alinear=["centro", "izq", "der", "der"], resaltar_fila={4})
    inf.vinetas([f"**Universo ({n_es(D.n_u)}):** todas las personas ocupadas de 15 años o más. Se usa para informalidad (TIL1), escolaridad y la validación externa.",
                 f"**Ventana 15 a 65 años ({n_es(D.n_v)}):** edades en las que la relación ingreso-educación es más estable (excluye a quienes ya se retiran).",
                 f"**Muestra salarial ({n_es(D.n_s)}, equivale a {R['muestras']['salarial_poblacion_millones']:.1f} millones de personas):** ventana 15-65 con monto exacto de ingreso, horas válidas, escolaridad y nivel especificados y sin ingreso atípico. Es la base de todos los resultados salariales.",
                 f"**Muestra salarial ampliada ({n_es(D.n_ext)}):** agrega a las personas del grupo B con ingreso imputado; solo para sensibilidad."])
    inf.p("La mayor pérdida del embudo (65,413 personas) es la del paso W1: quienes no declararon un monto exacto de ingreso. Por eso el análisis de sensibilidad de la selección es una parte central de este trabajo.", alinear="justificado")

    # ------------------------------------------------------------------ 4.7
    inf.h2("4.7 Pruebas automáticas de calidad de los datos (15 «expectativas»)")
    inf.p("Después de limpiar y transformar, el ETL verifica **15 expectativas** sobre la base resultante. Son afirmaciones que deben ser verdaderas si los datos están bien; si alguna crítica falla, el proceso se detiene con un error en lugar de continuar con datos dudosos "
          "(es el equivalente a las pruebas unitarias, pero aplicadas a los datos).", alinear="justificado")
    ex = D.etl_expectativas
    def limpio(d) -> str:
        t = re.sub(r"np\.int64\((\d+)\)", r"\1", str(d)).replace("100.0000%", "100 %")
        if t.startswith("{"):                       # {'A': 120948, ...} -> A 120,948 · B 36,438 · ...
            try:
                t = " · ".join(f"{k} {int(v):,}" for k, v in sorted(ast.literal_eval(t).items()))
            except (ValueError, SyntaxError):
                pass
        return t

    filas = [[str(k + 1), r.expectativa, "Sí" if r.cumple else "No", "Crítica" if r.critica else "Informativa", limpio(r.detalle)] for k, r in enumerate(ex.itertuples())]
    inf.tabla(filas, ["#", "Expectativa", "¿Cumple?", "Tipo", "Detalle"], [0.9, 6.0, 1.7, 2.0, 5.9], pie="Expectativas de calidad de datos evaluadas en cada corrida (15 de 15 cumplidas).",
              alinear=["centro", "izq", "centro", "centro", "izq"], fuente=8.5)
    inf.p("Dos de ellas validan el ingreso contra una segunda fuente: la expectativa 9 comprueba que el ingreso por hora recalculado (`ingocup / (hrsocup × 4.3)`) coincide con la variable `ing_x_hrs` del INEGI, y la 14 que el rango `p6c` de la tabla COE2T reproduce al 100 % el rango `ing7c` de SDEMT; "
          "esto confirma que la unión de tablas y la interpretación de los códigos son correctas.", alinear="justificado")


def seccion5(inf: Informe, D) -> None:
    meta = D.meta
    inf.h1("5. Transformación e ingeniería de datos (KDD fase 3)")
    inf.p("Con los datos limpios, esta fase crea las variables que usarán los modelos y los guarda en una arquitectura pensada para analizar y para servir los resultados. Es la parte de «ingeniería de datos» del proyecto: "
          "no solo importa el resultado, sino que el proceso sea **repetible, auditable y verificable**.", alinear="justificado")

    # ------------------------------------------------------------------ 5.1
    inf.h2("5.1 Variables derivadas")
    inf.tabla([["`mujer`", "1 si `sex = 2`, 0 si hombre", "Variable binaria para regresiones y la brecha de género."],
               ["`edad2`", "`eda² / 100`", "Término cuadrático de la edad (el ingreso sube con la experiencia y luego se aplana). Se divide entre 100 para que el coeficiente sea legible."],
               ["`grupo_edad`", "15-24, 25-34, 35-44, 45-54, 55-64, 65+", "Heterogeneidad por edad (sección 7.8)."],
               ["`informal`", "1 si `emp_ppal = 1`, 0 si formal", "Variable de informalidad (TIL1)."],
               ["`niv_det`", "Nivel 4 dividido: medio superior (4) vs. superior (5, con 16+ años)", "Detalle del nivel de instrucción para el premio por nivel."],
               ["`entidad`, `region`", "Nombre y región (Norte, Centro-Norte, Centro, Sur)", "Etiquetas y análisis regional."],
               ["`log_horas`", "ln(`hrsocup`)", "Control de horas trabajadas."],
               ["`grupo_ingreso`", "A, B, C o D según `ingocup` e `ing7c`", "Calidad del ingreso (sección 4.3)."],
               ["`ing_mensual`", "`ingocup` solo en el grupo A", "Ingreso mensual conocido."],
               ["`ing_hora`", "`ingocup / (hrsocup × 4.3)` (grupo A, horas válidas)", "Ingreso por hora; se verifica contra el del INEGI."],
               ["`ln_ing_hora`", "ln(`ing_hora`)", "Variable dependiente de los modelos."],
               ["`ing_mensual_imp`, `ing_hora_imp`", "Imputación por rango para el grupo B", "Solo en análisis de sensibilidad."],
               ["`persona_id`", "Concatenación de la llave de 11 campos", "Llave primaria legible."]],
              ["Variable", "Definición", "Para qué sirve"], [3.6, 6.3, 6.6], pie="Principales variables derivadas en la fase de transformación.", alinear=["izq", "izq", "izq"], fuente=9)
    inf.p("Siete banderas (`en_ventana_15_65`, `anios_esc_valido`, `horas_validas`, `nivel_especificado`, `outlier_ing_hora`, `en_muestra_salarial` y `en_muestra_salarial_ext`) definen, combinadas, las muestras de análisis. "
          f"La tabla de hechos guarda {D.n_cols_fact} columnas para las {n_es(D.n_u)} personas ocupadas; las transformaciones puramente algebraicas (`mujer`, `edad2`, `log_horas`) se calculan en el momento del análisis.", alinear="justificado")

    # ------------------------------------------------------------------ 5.2
    inf.h2("5.2 Arquitectura del proyecto")
    inf.p("El proyecto es una tubería de datos de cinco etapas con dos almacenes. Cada etapa es una función de Python independiente, probada por separado y encadenada por un orquestador (`pipeline.py`):", alinear="justificado")
    inf.figura(FIG / "D02_arquitectura.png", 16.2, "Arquitectura del proyecto: de los microdatos del INEGI a los resultados, el tablero y la base documental.")
    inf.vinetas(["**Microdatos** (CSV del INEGI) → **ETL** (extraer, limpiar, transformar, validar) → **SQLite** (almacén relacional, fuente de verdad).",
                 "**Análisis** estadístico lee de SQLite/ETL y escribe 30 tablas de **resultados** (CSV y tablas `res_*` en la propia base).",
                 "**MongoDB** recibe una copia derivada (documentos por entidad y por persona) para servir el tablero.",
                 f"Garantías transversales: semilla única (20251231), idempotencia, {D.n_pruebas} pruebas automáticas, bitácora de ejecución y huellas SHA-256 de los datos de origen."])

    # ------------------------------------------------------------------ 5.3
    inf.h2("5.3 Almacén relacional: SQLite con esquema en estrella")
    inf.p("**¿Por qué una base de datos relacional?** Los datos de la ENOE son una tabla rectangular de esquema fijo y el análisis consiste en agregaciones (`GROUP BY`) y uniones (`JOIN`): justo para lo que fue diseñado SQL. "
          "**¿Por qué SQLite?** Es una base completa (transacciones ACID, SQL estándar, restricciones de integridad) contenida en **un solo archivo**, sin servidor que instalar, lo que hace el proyecto reproducible en cualquier computadora.", alinear="justificado")
    inf.figura(FIG / "D03_esquema_estrella.png", 16.0, "Esquema en estrella: la tabla de hechos fact_ocupado (190,187 filas) rodeada de diez tablas de dimensiones.")
    inf.p("En un **esquema en estrella** la tabla de hechos contiene las mediciones (una fila por persona ocupada) y cada dimensión describe un atributo (entidad, sexo, nivel de instrucción...) con una clave. "
          "Ventajas: se evita repetir textos largos en 190 mil filas, los cambios de una descripción se hacen en un solo lugar y las consultas son rápidas y legibles.", alinear="justificado")
    ts = D.sqlite_tablas
    desc = {"fact_ocupado": f"Hechos: una fila por persona ocupada, con {D.n_cols_fact} columnas.", "dim_entidad": "32 entidades federativas con nombre, abreviatura, región y posición en el mosaico.",
            "dim_upm": "Unidades primarias de muestreo con su estrato (original y colapsado).", "dim_sexo": "Hombre/Mujer.", "dim_nivel_instruccion": "Cuatro niveles de instrucción más «no especificado».",
            "dim_nivel_detalle": "Niveles con el medio superior y el superior separados.", "dim_posicion_ocupacion": "Subordinado, empleador, cuenta propia, sin pago.", "dim_rama": "Gran rama de actividad económica.",
            "dim_tamano_localidad": "Tamaño de la localidad.", "dim_ing7c": "Rangos de ingreso en salarios mínimos.", "dim_grupo_ingreso": "Los grupos A, B, C y D.",
            "v_til_entidad": "Vista: TIL1 ponderado por entidad.", "v_escolaridad_entidad": "Vista: años de escolaridad promedio por entidad.", "v_calidad_ingreso_entidad": "Vista: composición A/B/C/D por entidad.",
            "v_muestra_salarial": "Vista: la muestra salarial lista para el análisis.", "etl_bitacora": "Auditoría: reglas de limpieza y registros afectados.", "etl_embudo_salarial": "Auditoría: embudo de la muestra salarial.",
            "etl_expectativas": "Auditoría: resultado de las 15 expectativas.", "etl_validacion_externa": "Auditoría: comparación con cifras del INEGI.", "etl_imputacion_rangos": "Auditoría: tabla de imputación.",
            "etl_umbrales_atipicos": "Auditoría: umbrales de ingreso atípico por entidad.", "etl_run": "Linaje: versiones, semilla, huellas SHA-256, parámetros."}
    filas = [[r.name, "Vista" if r.type == "view" else "Tabla", n_es(r.filas), desc.get(r.name, "")] for r in ts.itertuples()]
    inf.tabla(filas, ["Objeto", "Tipo", "Filas", "Descripción"], [4.5, 1.6, 2.0, 8.4], pie=f"Objetos de la base de datos relacional ({D.sqlite_mb:.0f} MB; además contiene {D.sqlite_n_res} tablas de resultados `res_*`).",
              alinear=["izq", "centro", "der", "izq"], fuente=8.5)
    inf.h3("Integridad: el motor rechaza los datos inconsistentes")
    inf.vinetas(["**Llaves primarias** (`persona_id`, `upm`, `cve_ent`...): sin duplicados.",
                 "**Llaves foráneas** (`PRAGMA foreign_keys = ON`): cada código de la tabla de hechos debe existir en su dimensión.",
                 "**Restricciones CHECK**: `fac_tri > 0`, `eda` entre 15 y 98, `emp_ppal` en {1, 2}, `hrsocup_raw` entre 0 y 168, `grupo` en {A, B, C, D}.",
                 f"**Verificación al cargar:** `integrity_check = {meta['verificacion_sqlite']['integrity_check']}`, {meta['verificacion_sqlite']['foreign_key_violations']} violaciones de llave foránea, "
                 f"{n_es(meta['verificacion_sqlite']['filas_fact_ocupado'])} filas, suma de ponderadores {meta['verificacion_sqlite']['suma_ponderadores'] / 1e6:.2f} millones y TIL1 nacional calculado con SQL de {meta['verificacion_sqlite']['til1_nacional_sql']:.2f} %."])
    inf.h3("Un ejemplo de consulta")
    inf.p("La vista `v_til_entidad` calcula la tasa de informalidad ponderada de cada entidad. Obsérvese que la ponderación se expresa directamente en SQL:", despues=3)
    inf.codigo("""SELECT e.entidad,
       ROUND(100.0 * SUM(f.fac_tri * f.informal) / SUM(f.fac_tri), 2) AS til1_pct
FROM fact_ocupado f
JOIN dim_entidad e USING (cve_ent)
GROUP BY e.entidad
ORDER BY til1_pct DESC;""")
    inf.p("Se crearon además cinco índices (por entidad, UPM, entidad-sexo, muestra salarial y grupo de ingreso) para acelerar estas agregaciones.", alinear="justificado")

    # ------------------------------------------------------------------ 5.4
    inf.h2("5.4 Almacén documental: MongoDB")
    inf.p("Una base **documental** guarda cada elemento como un documento JSON anidado, sin un esquema rígido. Es la herramienta adecuada cuando se necesita leer «toda la información de un elemento» en una sola operación. "
          "En este proyecto sirve para el tablero: al elegir un estado se muestra su ficha completa (informalidad, escolaridad, ingreso, rendimiento, correlación, brecha, calidad del ingreso).", alinear="justificado")
    inf.h3("Persistencia políglota: cada base donde funciona mejor")
    inf.tabla([["Análisis estadístico", "Agregaciones ponderadas y uniones sobre 190 mil filas; regresiones", "Relacional · SQLite", "Datos tabulares de esquema fijo; SQL expresa `GROUP BY` y `JOIN`; restricciones de integridad; archivo único y ACID."],
               ["Servicio de lectura (tablero, API)", "«Dame la ficha de la entidad 20»", "Documental · MongoDB", "Un documento por clave con todo anidado (*embedding*), sin `JOIN`; el esquema puede crecer sin migraciones; escala por entidad."]],
              ["Uso", "Patrón de acceso", "Modelo elegido", "Por qué"], [3.2, 4.0, 3.2, 6.1], pie="Justificación de la elección de modelo de datos.", alinear=["izq", "izq", "izq", "izq"], fuente=9, negrita_col0=True)
    inf.p("La elección responde al **patrón de acceso**, no al volumen: 190 mil filas caben en memoria y no son un caso de «big data». SQLite es la fuente de verdad; los documentos de MongoDB son una vista materializada que se regenera con `scripts/run_mongo.py`.", alinear="justificado")
    inf.h3("Modelo de documentos")
    inf.p("Base `enoe_2025t4` con tres colecciones:", despues=2, keep=True)
    inf.vinetas(["**`entidades`** (32 documentos): una ficha por entidad con indicadores, intervalos de confianza y lugares en el ranking, todos **embebidos** porque siempre se leen juntos.",
                 "**`personas`** (190,187 documentos): una persona por documento con subdocumentos temáticos (`persona`, `trabajo`, `ingreso`, `diseno`, `muestras`). No se embeben dentro de la entidad porque 190 mil subdocumentos superarían el límite de 16 MB de BSON; se relacionan por `cve_ent`.",
                 "**`metadatos`** (1 documento): linaje del pipeline (versiones, semilla, parámetros, huellas SHA-256)."])
    inf.codigo("""{
  "_id": 20, "cve_ent": 20, "entidad": "Oaxaca", "region": "Sur", "periodo": "2025-T4",
  "informalidad": {"til1_pct": 80.06, "ic95": [78.11, 81.88], "lugar": 1},
  "escolaridad":  {"anios_medios_ocupados": 9.07, "ic95": [8.82, 9.33]},
  "rendimiento_escolaridad": {"pct_por_anio": 6.18, "ic95": [5.21, 7.17]},
  "correlacion_spearman": {"rho": 0.28, "ic95": [0.23, 0.33], "lugar": 20},
  "brecha_genero": {"hora_pct": 16.5, "hora_ic95": [7.3, 25.0], "mensual_pct": 40.7},
  "calidad_ingreso_pct": {"A": 58.0, "B": 14.0, "C": 18.0, "D": 10.0}
}""", size=8.5)
    inf.p("Los índices creados (`entidades.cve_ent` único; `region`; `informalidad.til1_pct`; en `personas`: `cve_ent`, `cve_ent + ingreso.grupo`, `cve_ent + persona.sexo` y un índice **parcial** solo para la muestra salarial) corresponden a las consultas que hace el tablero.", alinear="justificado")
    inf.h3("La misma pregunta en SQL y en MongoDB")
    inf.tabla([["Ficha de Oaxaca", "`SELECT * FROM … WHERE cve_ent = 20`", "`db.entidades.findOne({cve_ent: 20})`"],
               ["Entidades con TIL1 > 70 %", "`… HAVING til1_pct > 70`", "`db.entidades.find({\"informalidad.til1_pct\": {$gt: 70}})`"],
               ["TIL1 ponderado por entidad", "`SUM(fac_tri*informal)/SUM(fac_tri) … GROUP BY cve_ent`", "`db.personas.aggregate([{$group: {_id: \"$cve_ent\", ocupados: {$sum: \"$fac_tri\"}, informales: {$sum: {$cond: [\"$trabajo.informal\", \"$fac_tri\", 0]}}}}, …])`"]],
              ["Pregunta", "SQL", "MongoDB"], [3.6, 5.6, 7.3], pie="Consultas equivalentes.", alinear=["izq", "izq", "izq"], fuente=8.5, negrita_col0=True)
    inf.h3("Qué se verificó y qué no (alcance honesto)")
    inf.vinetas(["**Verificado:** los documentos se construyen y se exportan (`entidades.json`, `entidades.ndjson`, `personas.ndjson.gz`, `metadatos.ndjson`) y la **carga completa se probó contra mongomock**, un simulador de MongoDB en memoria: los 190,187 documentos de persona, los 32 de entidad y el de metadatos, siete índices, documentos BSON válidos y una recarga que no duplica nada. "
                 "El pipeline de agregación «TIL1 por entidad», ejecutado en el motor, reproduce la vista SQL `v_til_entidad` con una diferencia máxima de 0.005 puntos porcentuales (el redondeo del SQL); el tablero se alimenta de la colección `entidades`. Siete pruebas automáticas cubren esta capa.",
                 "**No ejecutado:** la carga a un servidor MongoDB real, porque en el equipo de desarrollo no hay un servidor. mongomock imita la API y la agregación, pero **no es MongoDB**: no reproduce todo el comportamiento del servidor (por ejemplo, algunas reglas sobre los índices). "
                 "El código de carga usa solo `insert_many`, `create_index` y `drop_collection`, y los archivos están listos para `mongoimport`."])
    inf.recuadro("Cómo cargar en un servidor real", ["Con Python: `pip install -r requirements.txt` (incluye `pymongo`) y luego `python scripts/run_mongo.py --uri mongodb://localhost:27017` (o una URI de MongoDB Atlas).",
                                                     "Sin Python: `mongoimport --db enoe_2025t4 --collection entidades --file data/processed/mongo/entidades.ndjson`.",
                                                     "Sin servidor: `python scripts/run_mongo.py --simulado --limite 20000` carga y verifica contra mongomock (sin `--limite`, la carga completa tarda unos 6 minutos)."], fondo="FFF7E6", borde="EDA100")

    # ------------------------------------------------------------------ 5.5
    inf.h2("5.5 Reproducibilidad y pruebas")
    inf.p("Un resultado científico solo vale si otra persona puede obtenerlo. El proyecto incorpora varios mecanismos:", despues=2, keep=True)
    inf.vinetas([f"**Una sola orden:** `python scripts/run_all.py` ejecuta el ETL, el análisis, las figuras, la base documental, el tablero, el cuaderno, las dos presentaciones, el informe en Word y las {D.n_pruebas} pruebas (de 6 a 10 minutos según el equipo; la opción `--rapido` usa 100 réplicas bootstrap y omite el cuaderno, las presentaciones y el informe).",
                 f"**Semilla fija:** toda operación aleatoria usa la semilla {meta['semilla']}. Dos ejecuciones producen exactamente los mismos números: se comprobó que los 30 archivos de resultados son idénticos.",
                 "**Idempotencia:** la base se recrea desde cero y las colecciones documentales se eliminan y recargan, de modo que correr el proceso dos veces no duplica datos.",
                 "**Linaje:** la tabla `etl_run` guarda las versiones de Python y las bibliotecas, la semilla, los parámetros y la huella SHA-256 de cada archivo de origen.",
                 f"**Pruebas automáticas ({D.n_pruebas}):** limpieza, estadística de encuestas (comparadas con `statsmodels` y con soluciones analíticas), modelos, la capa documental contra mongomock y una prueba de integración con los datos reales (se omite si los datos no están).",
                 "**Parámetros centralizados:** todos los umbrales y catálogos viven en `config.py`; ninguna cifra queda «escondida» dentro del código."])
    n_p = D.pruebas
    filas = [["`test_clean.py`", str(n_p["test_clean.py"]), "Cada regla de cobertura excluye lo que debe; ventana 15-65; recodificación de faltantes; grupos de ingreso excluyentes (y error si un ingreso queda sin clasificar); ingreso por hora; atípicos por entidad; imputación por mediana del rango"],
             ["`test_survey.py`", str(n_p["test_survey.py"]), "Cuantiles y medias ponderadas; Spearman ponderado (igual a SciPy y a los datos «expandidos»); WLS; Holm; colapso de estratos; factores Rao-Wu con esperanza 1 y reproducibles; bootstrap = Taylor; el diseño complejo agranda la varianza; dominios; IC percentil"],
             ["`test_modelos.py`", str(n_p["test_modelos.py"]), "WLS y logit con diseño iguales a `statsmodels`; el efecto de conglomerado agranda el error; dominios con ponderadores cero; identidad exacta de Oaxaca-Blinder; brecha en %"],
             ["`test_etl_datos_reales.py`", str(n_p["test_etl_datos_reales.py"]), "Integridad de SQLite; cifras oficiales del INEGI; TIL1 estatal; conteos de la cascada; la muestra salarial cumple su definición; 32 entidades y ponderador positivo; la vista de calidad suma 100 %"],
             ["`test_mongo_simulado.py`", str(n_p["test_mongo_simulado.py"]), "Capa documental contra mongomock: carga por lotes e idempotente, siete índices, documentos BSON válidos, el pipeline de agregación reproduce la vista SQL y la comparación detecta una diferencia"]]
    inf.tabla(filas, ["Archivo", "Pruebas", "Qué verifica"], [4.4, 1.6, 10.5], pie=f"Conjunto de pruebas automáticas ({D.n_pruebas} en total).", alinear=["izq", "centro", "izq"], fuente=9)

    # ------------------------------------------------------------------ 5.6
    inf.h2("5.6 Mapa del código")
    inf.p("El código está organizado como un paquete de Python (`src/enoe/`) con una responsabilidad por módulo, y un conjunto de scripts que lo ejecutan:", alinear="justificado")
    mapa = [["`config.py`", "Rutas, parámetros (edad, horas, semilla, réplicas), catálogos de entidades y cifras de referencia del INEGI."],
            ["`extract.py`", "Lectura de los CSV (latin-1), selección de columnas, huella SHA-256."],
            ["`clean.py`", "Filtros de cobertura, faltantes, grupos de ingreso, atípicos, muestras y las 15 expectativas."],
            ["`transform.py`", "Llave de persona, unión SDEMT-COE2T, variables derivadas e imputación por rangos."],
            ["`validacion.py`", "Comparación con las cifras publicadas por el INEGI."],
            ["`load_sqlite.py`, `load_mongo.py`", "Carga al modelo relacional y al modelo documental."],
            ["`pipeline.py`", "Orquesta el ETL completo y escribe los metadatos."],
            ["`survey.py`", "Estadística de encuestas: diseño, Rao-Wu, Taylor, Spearman ponderado, WLS/logit, Holm."],
            ["`datos.py`, `estimadores.py`, `modelos.py`", "Bloques de réplicas, fábricas de estimadores, modelos de regresión, Oaxaca-Blinder y IPW."],
            ["`analisis.py`", "Ejecuta todo el análisis y escribe las 30 tablas de resultados."],
            ["`viz.py`, `viz_diagramas.py`, `figuras.py`", "Las 17 figuras de datos y los 8 diagramas explicativos."],
            ["`scripts/`", "`run_etl`, `run_analysis`, `make_figures`, `run_mongo`, `build_dashboard`, `build_notebook`, `build_deck` (corta), `build_deck_completa`, `build_informe` y `run_all`; las bibliotecas de diseño `deck_lib`, `deck_slides_base`, `deck_slides_extra`, `informe_lib`, `informe_datos` e `informe_s1` a `informe_s4`."]]
    inf.tabla(mapa, ["Módulo", "Qué contiene"], [5.8, 10.7], pie="Mapa del código fuente.", alinear=["izq", "izq"], fuente=9, negrita_col0=True)
