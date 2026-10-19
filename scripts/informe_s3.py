"""Informe técnico · secciones 6 (metodología detallada) y 7 (resultados)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from informe_datos import f1, n_es, pval
from informe_lib import Informe
from enoe import config as C

FIG = C.FIGURES


def ic(a: float, b: float, d: int = 1) -> str:
    return f"{a:.{d}f} a {b:.{d}f}"


def seccion6(inf: Informe, D) -> None:
    R, tot = D.R, D.tot
    inf.h1("6. Metodología estadística (KDD fase 4: análisis)")
    inf.p("Esta sección detalla **qué se calculó, cómo y con qué supuestos**. Es el puente entre los conceptos de la sección 2 y los resultados de la sección 7: aquí se fija, para cada objetivo, el estimador, la medida de incertidumbre y las decisiones que tomó el equipo.", alinear="justificado")

    inf.h2("6.1 Poblaciones y muestras")
    inf.tabla([["Universo", "Ocupados de 15+ años, entrevista completa (`r_def = 0`), residentes habituales (`c_res` ∈ {1, 3})", n_es(D.n_u), "Informalidad (objetivo 3), escolaridad, validación externa"],
               ["Ventana 15-65", "Universo con `eda ≤ 65`", n_es(D.n_v), "Ventana definida en el protocolo"],
               ["Muestra salarial", "Ventana + monto exacto (grupo A) + 1 ≤ horas ≤ 112 + escolaridad y nivel especificados + sin atípicos", n_es(D.n_s), "Resultado principal de ingreso (objetivos 1 y 2)"],
               ["Muestra salarial ampliada", "Igual, pero grupos A o B (B con ingreso imputado por rango)", n_es(D.n_ext), "Solo análisis de sensibilidad"]],
              ["Nombre", "Definición", "n", "Se usa para"], [3.0, 7.6, 1.9, 4.0], pie="Poblaciones y muestras de análisis.", alinear=["izq", "izq", "der", "izq"], fuente=9, negrita_col0=True)
    inf.p(f"*¿Por qué 15 años o más para la informalidad?* Porque es la base con la que el INEGI publica sus indicadores: con ella se reproducen siete cifras oficiales (sección 3.4). *¿Por qué 15 a 65 años para el ingreso?* "
          f"Es la ventana del protocolo y evita mezclar a personas en retiro, cuyo ingreso responde a otras dinámicas.", alinear="justificado")

    inf.h2("6.2 Definiciones operativas")
    inf.tabla([["Ingreso por hora", "`ingocup / (hrsocup × 4.3)`", "Pesos por hora trabajada. Se trabaja con su logaritmo natural."],
               ["Rendimiento de la escolaridad", "`100 × (exp(β) − 1)`", "β es el coeficiente de `anios_esc` en la regresión de Mincer. Es el % de aumento del ingreso por hora por cada año de estudio."],
               ["Brecha de género (%)", "`100 × (1 − exp(−Δ))`, con `Δ = media(ln w | hombres) − media(ln w | mujeres)`", "«Las mujeres ganan X % menos que los hombres», comparando ingresos medios geométricos. Un valor negativo significa que ganan más."],
               ["Brecha mensual y de horas", "Igual, con `ln(ingocup)` y `ln(hrsocup)`", "Por identidad en logaritmos: *brecha mensual = brecha por hora + brecha de horas*."],
               ["TIL1", "`ocupados informales / ocupados de 15+` (ponderado)", "Tasa de informalidad laboral, definición oficial del INEGI."]],
              ["Concepto", "Fórmula", "Cómo se lee"], [3.8, 5.6, 7.1], pie="Definiciones operativas de los indicadores.", alinear=["izq", "izq", "izq"], fuente=9, negrita_col0=True)
    dh, dm, dhs = -np.log(1 - tot["brecha_hora_pct"] / 100), -np.log(1 - tot["brecha_mens_pct"] / 100), -np.log(1 - tot["menos_horas_mujeres_pct"] / 100)
    inf.p(f"*Verificación de la identidad con los datos:* en log-puntos, la brecha mensual ({dm:.4f}) es igual a la brecha por hora ({dh:.4f}) más la brecha de horas ({dhs:.4f}), porque {dh:.4f} + {dhs:.4f} = {dh + dhs:.4f}.", alinear="justificado")

    inf.h2("6.3 Inferencia con el diseño muestral complejo")
    inf.p("Tratar la ENOE como una muestra aleatoria simple subestima los errores estándar (sección 2.2). Los pasos para evitarlo son:", despues=2, keep=True)
    inf.numerada(["**Estratos con una sola UPM.** Para estimar la varianza hacen falta al menos dos UPM por estrato. Hay 11 estratos con una sola UPM (de 724); se fusionan con el estrato vecino de la misma entidad (*collapsed strata*), lo que deja 713 estratos con dos UPM o más.",
                  f"**Bootstrap de Rao y Wu (1988).** En cada estrato con *n* UPM se remuestrean *n − 1* UPM con reemplazo y el ponderador de cada persona se multiplica por *n/(n − 1) × (veces que salió su UPM)*. Se generan B = {R['B']:,} réplicas con una **única semilla** ({D.meta['semilla']}) para todo el proyecto, de modo que la réplica *b* es el mismo remuestreo en todos los análisis (esto permite, por ejemplo, calcular el ranking de las entidades en cada réplica).",
                  "**Dominios.** Las réplicas se construyen sobre **todas las UPM** de la muestra completa y cada fila de un subconjunto (la muestra salarial, una entidad, un nivel...) toma el factor de su UPM. Así no se pierde variabilidad cuando una UPM no aporta casos al dominio, un error común al filtrar antes de estimar.",
                  "**Intervalos y pruebas.** El intervalo de confianza es el percentil 2.5 y 97.5 de las réplicas. Las pruebas de hipótesis son de Wald bilaterales con el error estándar bootstrap (los grados de libertad del diseño, cerca de 20 mil, justifican la aproximación normal).",
                  "**Modelos de regresión y logit.** Se usa el estimador de sándwich con **linealización de Taylor** que respeta estratos y UPM (`survey.regresion_diseno` y `survey.logit_diseno`), equivalente a `svy:` de Stata o al paquete `survey` de R. Se verificó contra `statsmodels`: mismos coeficientes y errores equivalentes en el caso de muestreo aleatorio simple."])
    de = D.efecto_diseno[D.efecto_diseno["ee_diseno"].notna()]
    filas = [[r.estimador, n_es(r.n), f"{r.ee_diseno:.4f}", f"{r.ee_mas:.4f}", f"{r.deff:.2f}", n_es(r.n_efectivo)] for r in de.itertuples()]
    inf.tabla(filas, ["Estimador", "n", "EE con diseño", "EE como m.a.s.", "Efecto de diseño", "n efectivo"], [6.1, 1.9, 2.2, 2.3, 2.0, 2.0],
              pie="Efecto de diseño: cuánto cambia el error estándar al respetar estratos y UPM (el EE como muestreo aleatorio simple, m.a.s., es siempre menor).", alinear=["izq", "der", "der", "der", "der", "der"], fuente=9)
    inf.p("El efecto de diseño de 4.8 en la tasa de informalidad significa que la varianza real es casi cinco veces mayor que la de una muestra aleatoria simple, o que los 190 mil ocupados equivalen a unos 40 mil independientes; "
          "para la brecha por hora es de 3.1. Ignorar el diseño haría que los errores estándar fueran entre 1.8 y 2.2 veces demasiado pequeños (la raíz cuadrada del efecto de diseño).", alinear="justificado")

    inf.h2("6.4 Estimadores y pruebas por objetivo")
    inf.tabla([["Correlación escolaridad-ingreso por entidad (M2)", "Spearman ponderado: Pearson entre rangos medios ponderados", "Bootstrap de Rao-Wu; lugar de cada entidad en el ranking con su intervalo (el ranking se recalcula en cada réplica)"],
               ["Rendimiento por entidad", "WLS por entidad con edad, edad² y sexo", "Bootstrap de Rao-Wu"],
               ["Estados de mayor vs. menor ingreso", "Cuartiles de ingreso mediano por hora (recalculados en cada réplica); diferencia del rendimiento medio Q4 − Q1", "Bootstrap + Wald"],
               ["Brecha por hora, mensual y de horas por nivel (M1)", "Diferencia de medias ponderadas de logaritmos", "Bootstrap + Wald; **Holm** sobre las cuatro pruebas por nivel"],
               ["Pruebas «clásicas» del protocolo", "Welch (t) y Mann-Whitney por nivel, sin ponderar; *d* de Cohen; correlación biserial por rangos", "Valores p ajustados con Holm"],
               ["Brecha ajustada", "WLS de ln(w) sobre `mujer` con escalera de controles G0 a G6", "Sándwich de diseño"],
               ["Descomposición de la brecha", "Oaxaca-Blinder con referencia agrupada de Neumark (1988); también con coeficientes de hombres o de mujeres", "Bootstrap"],
               ["Brecha por percentil", "Cuantiles ponderados por sexo; diferencia en P10, P25, P50, P75 y P90", "Bootstrap"],
               ["Informalidad (objetivo 3)", "TIL1 ponderado (nacional, sexo, región, nivel, entidad); asociación entre estados (Pearson, Spearman, pendiente); logit individual y efecto marginal promedio", "Bootstrap / sándwich"],
               ["No respuesta del ingreso", "Logit ponderado «A vs. resto» y «D vs. resto»; IPW", "Sándwich de diseño"]],
              ["Objetivo", "Estimador", "Incertidumbre"], [4.7, 6.5, 5.3], pie="Estimadores y medidas de incertidumbre para cada objetivo.", alinear=["izq", "izq", "izq"], fuente=9, negrita_col0=True)
    inf.p("**Tamaño del efecto.** Con 112 mil observaciones casi cualquier diferencia es «significativa»; por eso se reportan siempre la brecha en % y la *d* de Cohen. **Multiplicidad.** Holm controla el error por familia de pruebas: los cuatro niveles de instrucción y las categorías de cada dimensión de heterogeneidad. "
          "Los 32 intervalos por entidad no se prueban uno a uno: se reporta el ranking con su incertidumbre.", alinear="justificado")

    inf.h2("6.5 El sesgo de división: por qué no se interpreta el modelo con horas")
    inf.p("El ingreso por hora es el ingreso mensual dividido entre las horas semanales. Si las horas tienen algún error de medición (la encuesta pregunta las horas de *una sola semana*), ese error aparece en el denominador de la variable dependiente y crea una relación negativa **mecánica** entre ln(ingreso por hora) y ln(horas), aunque no exista una relación económica. "
          f"Controlar por horas infla entonces la brecha ajustada (de {D.g5['brecha_pct']:.1f} % a {D.g6['brecha_pct']:.1f} %) y la «parte explicada» por horas ({D.ob_h.assign(clave=D.ob_h['componente'].str.strip(' ·')).set_index('clave').loc['horas trabajadas', 'log_puntos'] * 100:.0f} puntos logarítmicos).", alinear="justificado")
    inf.recuadro("Decisión", [f"El modelo con horas (G6) y la descomposición «con horas» se muestran **solo por transparencia y no se interpretan**. La estimación de referencia para «personas comparables» es G5 ({D.g5['brecha_pct']:.1f} %), que no controla por horas. "
                              "La brecha **mensual** sí se interpreta, porque la identidad en logaritmos es exacta: la diferencia mensual se descompone sin sesgo en diferencia por hora más diferencia de horas."])

    inf.h2("6.6 Decisiones del analista y su sensibilidad")
    inf.tabla([["Ventana de edad", "15-65 (protocolo); 15+ para informalidad", "La base oficial es 15+"],
               ["Horas válidas", "1 ≤ horas ≤ 112", "Solo 41 casos con más de 112 horas"],
               ["Atípicos", "Fuera de P0.5-P99.5 del ingreso por hora de su entidad", f"S1 «sin recorte»: brecha {D.rob_tot.loc['S1 Sin recorte', 'brecha_pct']:.1f} % vs. {tot['brecha_hora_pct']:.1f} %; rendimiento {D.robr.loc['R1 Sin recorte', 'retorno_pct']:.1f} % vs. {D.robr.loc['R0 Base', 'retorno_pct']:.1f} %"],
               ["Ingreso faltante", "Muestra del grupo A (monto exacto)", "S2 (asalariados), S3 (imputación) y S4 (IPW)"],
               ["Estratos con una UPM", "Se fusionan con el estrato vecino", "—"],
               ["Réplicas bootstrap", f"{R['B']:,} con una semilla única", "—"],
               ["Nivel detallado", "El nivel 4 se divide con `anios_esc` (12 a 15 años / 16+)", "Resultados por subnivel (sección 7.8)"]],
              ["Decisión", "Valor elegido", "Sensibilidad"], [3.6, 6.4, 6.5], pie="Decisiones metodológicas y cómo se evaluó su efecto.", alinear=["izq", "izq", "izq"], fuente=9, negrita_col0=True)
    inf.h2("6.7 Verificación del método")
    inf.p("Las piezas estadísticas se programaron desde cero (no hay una biblioteca estándar de Python para el bootstrap de Rao-Wu), por lo que se verificaron con pruebas automáticas: el factor de remuestreo tiene esperanza 1; la varianza bootstrap coincide con la de Taylor (dentro de ±8 %); "
          "el Spearman ponderado coincide con `scipy.stats.spearmanr` cuando los pesos son iguales y con los datos «expandidos» cuando son enteros; la regresión ponderada coincide con `statsmodels`; la descomposición de Oaxaca-Blinder cumple su identidad exacta; "
          "y con efecto de conglomerado el error con diseño supera al de muestreo aleatorio simple.", alinear="justificado")


def seccion7(inf: Informe, D) -> None:
    R, tot, bn = D.R, D.tot, D.bn
    rt = D.rt
    inf.h1("7. Resultados")
    inf.p("Todos los resultados se calculan con los ponderadores de la encuesta, con intervalos de confianza del 95 % del bootstrap de Rao-Wu (salvo que se indique lo contrario) y con 1,000 réplicas. Cada subsección explica **qué se calculó**, muestra el resultado y termina con una **lectura** en palabras sencillas.", alinear="justificado")

    # ------------------------------------------------------------------ 7.1
    inf.h2("7.1 Panorama: la muestra salarial")
    ds = D.descriptivos_salario
    def v(g, var, col):
        return float(ds[(ds.grupo == g) & (ds.variable == var)][col].iloc[0])
    filas = []
    for var, fm in [("Ingreso por hora ($)", "{:.1f}"), ("Ingreso mensual ($)", "{:,.0f}"), ("Horas por semana", "{:.1f}"), ("Años de escolaridad", "{:.1f}"), ("Edad", "{:.1f}")]:
        filas.append([var, fm.format(v("Total", var, "media_pond")), fm.format(v("Total", var, "mediana_pond")), fm.format(v("Hombres", var, "media_pond")), fm.format(v("Mujeres", var, "media_pond"))])
    inf.tabla(filas, ["Variable", "Media (total)", "Mediana (total)", "Media hombres", "Media mujeres"], [4.9, 2.9, 2.9, 2.9, 2.9], pie=f"Descriptivos ponderados de la muestra salarial (n = {n_es(D.n_s)}, {R['muestras']['salarial_poblacion_millones']:.1f} millones de personas).", alinear=["izq", "der", "der", "der", "der"])
    inf.p(f"La persona ocupada típica de la muestra salarial tiene {v('Total', 'Edad', 'media_pond'):.0f} años, {v('Total', 'Años de escolaridad', 'media_pond'):.1f} años de estudio (secundaria terminada y un poco más), trabaja {v('Total', 'Horas por semana', 'media_pond'):.0f} horas a la semana y gana "
          f"${v('Total', 'Ingreso por hora ($)', 'mediana_pond'):.0f} por hora (${v('Total', 'Ingreso mensual ($)', 'mediana_pond'):,.0f} al mes). Las mujeres trabajan menos horas (37.5 frente a 45.7) y tienen algo más de escolaridad (11.0 frente a 10.2 años).", alinear="justificado")
    inf.figura(FIG / "04_ingreso_por_escolaridad.png", 15.8, "Mediana ponderada del ingreso por hora según los años de escolaridad, por sexo (escala logarítmica).")
    inf.p("**Lectura.** El ingreso por hora casi no cambia durante los primeros años de escolaridad (la curva es casi plana de 0 a 10 años), empieza a subir con la preparatoria y da su salto más grande al llegar a la licenciatura. "
          "La curva de las mujeres queda por debajo de la de los hombres en casi todos los niveles; las diferencias más visibles aparecen con 0 a 10 años de estudio y con posgrado (19 y 20 años), mientras que con 11 años y entre 16 y 18 las medianas casi coinciden.", alinear="justificado")

    # ------------------------------------------------------------------ 7.2
    inf.h2("7.2 Rendimiento de la escolaridad (objetivo 1)")
    inf.p("**Qué se calculó.** El coeficiente de Mincer: en una regresión del logaritmo del ingreso por hora sobre los años de escolaridad, controlando por edad, edad², sexo, entidad y tamaño de localidad (modelo M3), "
          "se obtiene el aumento porcentual del ingreso por cada año adicional de estudio. Se compararon cinco especificaciones para ver cómo cambia al agregar controles:", alinear="justificado")
    rm = D.retorno_modelos
    filas = [[r.modelo, f"{r.coef:.4f}", f"{r.retorno_pct:.2f} ({r.retorno_pct_inf:.2f} a {r.retorno_pct_sup:.2f})", f"{r.r2:.3f}"] for r in rm.itertuples()]
    inf.tabla(filas, ["Modelo", "β (log-puntos)", "Rendimiento por año, % (IC 95 %)", "R²"], [7.0, 2.6, 5.0, 1.9], pie="Rendimiento por año de escolaridad según el modelo (n = 111,958). El modelo M3 es el de referencia.", alinear=["izq", "der", "der", "der"], resaltar_fila={2})
    inf.vinetas([f"**Resultado principal (M3): {f1(rt['nacional_pct']['est'])} % por año** (IC 95 %: {ic(rt['nacional_pct']['ic_inf'], rt['nacional_pct']['ic_sup'])}). Es la comparación entre personas de la misma edad, sexo, entidad y tamaño de localidad.",
                 "Al agregar solo edad y sexo (M2) sube a 6.1 %; al incluir la entidad y el tamaño de localidad (M3) baja a 5.1 % porque parte de la ventaja de estudiar se debe a vivir en lugares de mayor ingreso.",
                 "Al agregar la posición en la ocupación, la informalidad y la rama (M4) baja a 3.8 %: una parte del beneficio de estudiar **actúa a través** de conseguir mejores empleos (formales, asalariados). Por eso M4 no es el resultado principal: controlar por un canal subestimaría el beneficio total.",
                 f"**Por sexo (M5):** {f1(rt['hombres_pct']['est'])} % para los hombres y {f1(rt['mujeres_pct']['est'])} % para las mujeres; la diferencia es de 0.012 log-puntos (p < 0.001). Cada año de estudio rinde algo más a las mujeres."])
    inf.h3("El rendimiento no es lineal: el premio por nivel")
    pr = D.premio_por_nivel
    filas = [[r.nivel, f"+{r.premio_pct:.1f} %", f"{r.inf:.1f} a {r.sup:.1f}", n_es(r.n)] for r in pr.itertuples()]
    inf.tabla(filas, ["Nivel de instrucción", "Premio frente a primaria incompleta", "IC 95 %", "n"], [7.2, 4.0, 3.3, 2.0], pie="Premio salarial por nivel respecto a primaria incompleta (controlando edad, sexo y entidad).", alinear=["izq", "der", "der", "der"])
    inf.p("**Lectura.** Terminar la primaria agrega 7 % al ingreso por hora; la secundaria, 16 %; la preparatoria, 28 %; y una licenciatura o posgrado, **92 %** (casi lo duplica). El beneficio de estudiar se concentra en los niveles altos, no se reparte parejo entre los años.", alinear="justificado")
    inf.h3("Diferencias entre entidades")
    inf.figura(FIG / "05_retorno_estados.png", 14.8, "Rendimiento por año de escolaridad en cada entidad (con IC 95 %). El color indica el cuartil de ingreso mediano por hora del estado.")
    re = D.retorno_entidad
    mx, mn = re.loc[re.ret_est.idxmax()], re.loc[re.ret_est.idxmin()]
    inf.p(f"**Lectura.** El rendimiento va de {mn.ret_est:.1f} % ({mn.entidad}) a {mx.ret_est:.1f} % ({mx.entidad}). Sin embargo, la mayoría de los intervalos se traslapan (la precisión por entidad es limitada: entre 1,900 y 5,900 observaciones salariales por estado), "
          f"de modo que solo las diferencias grandes son confiables.", alinear="justificado")
    inf.h3("¿Es distinto el rendimiento en los estados de mayor y menor ingreso?")
    q = D.rr
    filas = [[f"Cuartil {k}" + (" (ingreso más bajo)" if k == 1 else (" (ingreso más alto)" if k == 4 else "")), f"{q.loc[f'Rendimiento medio, cuartil {k} de ingreso estatal (%)', 'est']:.2f} ({q.loc[f'Rendimiento medio, cuartil {k} de ingreso estatal (%)', 'ic_inf']:.2f} a {q.loc[f'Rendimiento medio, cuartil {k} de ingreso estatal (%)', 'ic_sup']:.2f})",
              f"{q.loc[f'Spearman medio, cuartil {k} de ingreso estatal', 'est']:.2f} ({q.loc[f'Spearman medio, cuartil {k} de ingreso estatal', 'ic_inf']:.2f} a {q.loc[f'Spearman medio, cuartil {k} de ingreso estatal', 'ic_sup']:.2f})"] for k in (1, 2, 3, 4)]
    inf.tabla(filas, ["Estados agrupados por ingreso mediano por hora", "Rendimiento medio por año, % (IC 95 %)", "Spearman medio (IC 95 %)"], [6.2, 5.4, 4.9], pie="Rendimiento y correlación promedio por cuartil de ingreso estatal.", alinear=["izq", "centro", "centro"])
    inf.p(f"La diferencia de rendimiento entre los cuartiles de mayor y menor ingreso es de {rt['dif_q4_q1_log']['est']:.4f} log-puntos (IC {ic(rt['dif_q4_q1_log']['ic_inf'], rt['dif_q4_q1_log']['ic_sup'], 3)}; p = {rt['dif_q4_q1_log']['p']:.2f}); la de las correlaciones es de {rt['dif_rho_q4_q1']['est']:.2f} (p = {rt['dif_rho_q4_q1']['p']:.2f}). "
          "**Lectura:** no hay evidencia de que estudiar rinda más en los estados ricos que en los pobres. Los estados ricos pagan más *en todos los niveles*, pero el aumento porcentual por año de estudio es similar.", alinear="justificado")
    inf.recuadro("Cuidado con la lectura", [f"Entre los estados, la escolaridad promedio y el ingreso mediano sí están fuertemente asociados (Spearman = {rt['rho_estatal_esc_ingreso']['est']:.2f}, sección 7.3), pero esta es una relación **entre estados** (cada punto es una entidad) y no dice nada sobre lo que le pasaría a una persona que estudiara más (falacia ecológica). "
                                           f"El rendimiento por año no se asocia positivamente con el ingreso del estado (Spearman = {rt['rho_estatal_ret_ingreso']['est']:.2f}, IC {ic(rt['rho_estatal_ret_ingreso']['ic_inf'], rt['rho_estatal_ret_ingreso']['ic_sup'], 2)})."])

    # ------------------------------------------------------------------ 7.3
    inf.h2("7.3 Correlación escolaridad-ingreso por entidad (métrica M2)")
    inf.p(f"**Qué se calculó.** El coeficiente de Spearman ponderado entre los años de escolaridad y el ingreso por hora en cada una de las 32 entidades, con su intervalo de confianza por bootstrap y el lugar que ocupa cada entidad en el ranking (con el intervalo de ese lugar, recalculado en cada réplica). "
          f"A nivel nacional, ρ = {rt['spearman_nacional']['est']:.2f} (IC {ic(rt['spearman_nacional']['ic_inf'], rt['spearman_nacional']['ic_sup'], 2)}): una relación moderada.", alinear="justificado")
    inf.figura(FIG / "06_spearman_estados.png", 14.8, "Correlación de Spearman entre escolaridad e ingreso por hora en cada entidad, con IC 95 % y lugar en el ranking.")
    srt = re.sort_values("rho_est", ascending=False)
    top = srt.head(5)
    bot = srt.tail(5)
    filas = [[f"{r.rho_rango:.0f}", r.entidad, f"{r.rho_est:.2f} ({r.rho_ic_inf:.2f} a {r.rho_ic_sup:.2f})", f"{int(r.rho_rango_inf)} a {int(r.rho_rango_sup)}", f"{r.ret_est:.1f}"] for r in pd.concat([top, bot]).itertuples()]
    inf.tabla(filas, ["Lugar", "Entidad", "ρ de Spearman (IC 95 %)", "Intervalo del lugar", "Rendimiento % por año"], [1.6, 4.6, 4.6, 3.0, 2.7],
              pie="Las cinco entidades con mayor y menor correlación (el ranking completo está en el Anexo C).", alinear=["centro", "izq", "centro", "centro", "der"], resaltar_fila=set())
    inf.p(f"**Lectura.** La correlación va de {rt['rho_min']['rho_est']:.2f} ({rt['rho_min']['entidad']}) a {rt['rho_max']['rho_est']:.2f} ({rt['rho_max']['entidad']}). En todas las entidades es positiva y significativa: dentro de cada entidad, quienes tienen más escolaridad tienden a ganar más por hora. "
          "El **ranking es defendible solo en los extremos**: los lugares de las entidades intermedias tienen intervalos muy amplios (varios lugares hacia arriba y hacia abajo), por lo que no conviene interpretar diferencias de uno o dos lugares.", alinear="justificado")
    inf.figura(FIG / "07_escolaridad_vs_ingreso_estatal.png", 14.0, "Relación entre la escolaridad promedio y el ingreso mediano por hora entre estados (Spearman entre estados = 0.74; relación entre estados, no causal).")

    # ------------------------------------------------------------------ 7.4
    inf.h2("7.4 Brecha salarial de género por nivel de instrucción (métrica M1)")
    inf.p("**Qué se calculó.** Para cada nivel de instrucción, la brecha de género en el ingreso por hora (y, para completar el panorama, en el ingreso mensual y en las horas trabajadas), con su intervalo de confianza y su valor p ajustado por Holm.", alinear="justificado")
    inf.figura(FIG / "08_cajas_nivel_sexo.png", 15.0, "Distribución de ln(ingreso por hora) por nivel de instrucción y sexo.")
    filas = []
    for k in bn.index:
        r = bn.loc[k]
        filas.append([k.split(". ", 1)[-1] if k != "Total" else "Total", n_es(r.n_hombres), n_es(r.n_mujeres), f"{r.ing_hora_h:.2f}", f"{r.ing_hora_m:.2f}", f"{r.brecha_hora_pct:.1f}", f"{r.brecha_hora_inf:.1f} a {r.brecha_hora_sup:.1f}",
                      pval(r.p_hora_holm) if pd.notna(r.p_hora_holm) else pval(r.p_hora)])
    inf.tabla(filas, ["Nivel", "Hombres", "Mujeres", "$/h hombres", "$/h mujeres", "Brecha %", "IC 95 %", "p (Holm)"], [4.0, 1.7, 1.7, 1.7, 1.7, 1.5, 2.4, 1.8],
              pie="Brecha salarial de género por hora, por nivel de instrucción ($/h = media geométrica del ingreso por hora).", alinear=["izq", "der", "der", "der", "der", "der", "centro", "der"], fuente=9, resaltar_fila={4})
    inf.figura(FIG / "09_brecha_por_nivel.png", 15.0, "Brecha salarial de género por hora, por nivel de instrucción (IC 95 %).")
    inf.p(f"**Lectura.** Las mujeres ganan menos por hora que los hombres en **los cuatro niveles**, y las cuatro diferencias son estadísticamente significativas aun después de la corrección de Holm (p < 0.001 en todos). "
          f"La brecha va de {bn.loc['4. Medio superior y superior', 'brecha_hora_pct']:.1f} % (preparatoria y superior) a {bn.loc['2. Primaria completa', 'brecha_hora_pct']:.1f} % (primaria completa); es **mayor en los niveles bajos** y menor entre quienes tienen más estudios. "
          f"En el total es de {f1(tot['brecha_hora_pct'])} % (IC {ic(tot['brecha_hora_inf'], tot['brecha_hora_sup'])}).", alinear="justificado")
    inf.h3("Las pruebas «clásicas» del protocolo")
    tc = D.tests_clasicos
    filas = [[r.nivel.split(". ", 1)[-1], f"{r.t_welch:.1f}", pval(r.p_welch_holm) if pd.notna(r.p_welch_holm) else pval(r.p_welch), pval(r.p_mwu_holm) if pd.notna(r.p_mwu_holm) else pval(r.p_mwu), f"{r.d_cohen:.2f}", f"{r.r_biserial:.2f}"] for r in tc.itertuples()]
    inf.tabla(filas, ["Nivel", "t de Welch", "p Welch (Holm)", "p Mann-Whitney (Holm)", "d de Cohen", "r biserial"], [4.9, 2.0, 2.7, 3.2, 1.9, 1.8],
              pie="Pruebas sin ponderar de diferencia de ln(ingreso por hora) entre hombres y mujeres, como pide el protocolo.", alinear=["izq", "der", "der", "der", "der", "der"], fuente=9)
    inf.p("Las pruebas t de Welch (diferencia de medias) y U de Mann-Whitney (diferencia de distribuciones, sin supuesto de normalidad) confirman la significancia en todos los niveles. Pero la **d de Cohen** muestra que el tamaño del efecto es **pequeño** (entre 0.06 y 0.24, por debajo del 0.5 que se considera mediano): "
          "hay diferencia, pero hombres y mujeres se traslapan mucho. Estas pruebas no ponderan por el diseño y se incluyen porque el protocolo las pide; los intervalos de la tabla anterior son los válidos para inferir sobre la población.", alinear="justificado")
    inf.h3("La brecha mensual es mucho mayor que la brecha por hora")
    filas = [[k.split(". ", 1)[-1], f"{bn.loc[k, 'brecha_hora_pct']:.1f}", f"{bn.loc[k, 'brecha_mens_pct']:.1f}", f"{bn.loc[k, 'menos_horas_mujeres_pct']:.1f}", f"{bn.loc[k, 'horas_h']:.1f}", f"{bn.loc[k, 'horas_m']:.1f}"] for k in bn.index]
    inf.tabla(filas, ["Nivel", "Brecha por hora %", "Brecha mensual %", "Mujeres trabajan menos horas, %", "Horas/sem. hombres", "Horas/sem. mujeres"], [4.0, 2.2, 2.4, 3.4, 2.3, 2.2],
              pie="Brecha por hora, brecha mensual y diferencia de horas trabajadas.", alinear=["izq", "der", "der", "der", "der", "der"], fuente=9, resaltar_fila={4})
    inf.p(f"**Lectura.** En el ingreso **mensual** la brecha es de {f1(tot['brecha_mens_pct'])} %, siete veces mayor que la brecha por hora. La razón es que las mujeres trabajan en promedio {tot['horas_m']:.1f} horas a la semana y los hombres {tot['horas_h']:.1f}: **{f1(tot['menos_horas_mujeres_pct'])} % menos horas pagadas**. "
          "Por la identidad en logaritmos, casi toda la diferencia mensual se debe a la diferencia de horas y solo una pequeña parte a la diferencia de pago por hora. Que las mujeres trabajen menos horas remuneradas no es necesariamente una elección libre: "
          "refleja, en parte, la distribución del trabajo doméstico y de cuidados, que esta encuesta no mide en el ingreso.", alinear="justificado")

    # ------------------------------------------------------------------ 7.5
    inf.h2("7.5 Brecha entre personas comparables: la escalera de controles")
    inf.p("**Qué se calculó.** La brecha por hora entre mujeres y hombres «de iguales características». Se agregan controles uno por uno (regresión ponderada de ln(ingreso por hora) sobre `mujer`) para ver cómo cambia la brecha:", alinear="justificado")
    ec = D.escalera_brecha
    filas = [[r.modelo, f"{r.brecha_pct:.1f}", f"{r.brecha_pct_inf:.1f} a {r.brecha_pct_sup:.1f}", f"{r.r2:.3f}", str(int(r.n_parametros))] for r in ec.itertuples()]
    inf.tabla(filas, ["Modelo (controles acumulados)", "Brecha %", "IC 95 %", "R²", "Parámetros"], [6.8, 2.0, 3.3, 1.8, 2.2],
              pie="Brecha por hora ajustada: G0 es la brecha sin ajustar; G5 es la estimación de referencia; G6 sufre del sesgo de división y no se interpreta.", alinear=["izq", "der", "centro", "der", "der"], resaltar_fila={5})
    inf.figura(FIG / "10_escalera_controles.png", 15.0, "Escalera de controles: cómo cambia la brecha por hora al agregar controles (G6 no se interpreta).")
    inf.vinetas([f"**G0 → G1:** al comparar personas con la misma escolaridad, la brecha **sube** de 3.7 % a 7.7 %. Eso ocurre porque las mujeres de la muestra tienen *más* escolaridad que los hombres: la escolaridad «compensa» parcialmente la desventaja y, al igualarla, la brecha aparece completa.",
                 "**G2 → G3:** al comparar dentro de la misma entidad y tamaño de localidad llega a su máximo (9.9 %).",
                 "**G3 → G5:** al agregar la posición en la ocupación y la informalidad (G4: 8.4 %) y luego la rama de actividad (G5: 8.2 %) la brecha baja un poco: una parte menor se asocia con que mujeres y hombres se concentran en puestos y ramas distintos.",
                 f"**G5 es la estimación de referencia: {D.g5['brecha_pct']:.1f} % (IC {ic(D.g5['brecha_pct_inf'], D.g5['brecha_pct_sup'])}).** Entre personas comparables en escolaridad, edad, lugar, tipo de empleo y rama, las mujeres ganan alrededor de 8 % menos por hora.",
                 f"**G6** agrega las horas y salta a {D.g6['brecha_pct']:.1f} %, pero ese valor es un artefacto del sesgo de división (sección 6.5) y no se interpreta."])
    inf.h3("Descomposición de Oaxaca-Blinder: ¿qué la explica?")
    inf.figura(FIG / "11_oaxaca_blinder.png", 15.0, "Descomposición de la brecha total (en puntos logarítmicos) en parte explicada y no explicada, y contribución de cada grupo de características.")
    ob = D.ob
    filas = [["Brecha total", f"{ob.loc['Brecha total (log-puntos)', 'log_puntos'] * 100:.2f}", ic(ob.loc['Brecha total (log-puntos)', 'ic_inf'] * 100, ob.loc['Brecha total (log-puntos)', 'ic_sup'] * 100, 2)],
             ["Explicada por diferencias en características", f"{ob.loc['Explicada por características (referencia agrupada)', 'log_puntos'] * 100:.2f}", ic(ob.loc['Explicada por características (referencia agrupada)', 'ic_inf'] * 100, ob.loc['Explicada por características (referencia agrupada)', 'ic_sup'] * 100, 2)],
             ["    · escolaridad", f"{ob.loc['escolaridad', 'log_puntos'] * 100:.2f}", ic(ob.loc['escolaridad', 'ic_inf'] * 100, ob.loc['escolaridad', 'ic_sup'] * 100, 2)],
             ["    · edad / experiencia", f"{ob.loc['edad / experiencia', 'log_puntos'] * 100:.2f}", ic(ob.loc['edad / experiencia', 'ic_inf'] * 100, ob.loc['edad / experiencia', 'ic_sup'] * 100, 2)],
             ["    · entidad y tamaño de localidad", f"{ob.loc['entidad y tamaño de localidad', 'log_puntos'] * 100:.2f}", ic(ob.loc['entidad y tamaño de localidad', 'ic_inf'] * 100, ob.loc['entidad y tamaño de localidad', 'ic_sup'] * 100, 2)],
             ["    · posición e informalidad", f"{ob.loc['posición e informalidad', 'log_puntos'] * 100:.2f}", ic(ob.loc['posición e informalidad', 'ic_inf'] * 100, ob.loc['posición e informalidad', 'ic_sup'] * 100, 2)],
             ["    · rama de actividad", f"{ob.loc['rama de actividad', 'log_puntos'] * 100:.2f}", ic(ob.loc['rama de actividad', 'ic_inf'] * 100, ob.loc['rama de actividad', 'ic_sup'] * 100, 2)],
             ["No explicada (mismas características, distinto pago)", f"{ob.loc['No explicada (referencia agrupada)', 'log_puntos'] * 100:.2f}", ic(ob.loc['No explicada (referencia agrupada)', 'ic_inf'] * 100, ob.loc['No explicada (referencia agrupada)', 'ic_sup'] * 100, 2)]]
    inf.tabla(filas, ["Componente", "Centésimas de log-punto", "IC 95 %"], [8.7, 3.8, 4.0], pie="Descomposición de Oaxaca-Blinder (referencia agrupada de Neumark); 1 centésima de log-punto ≈ 1 %.", alinear=["izq", "der", "centro"], resaltar_fila={0, 1, 7}, fuente=9.5)
    inf.p("**Lectura.** Con los mismos niveles de escolaridad, edad y ubicación que los hombres, las mujeres *deberían* ganar más (la parte explicada es negativa: −3.2): su **ventaja en escolaridad** (−2.8) y en ubicación (−1.7) pesa más que la ventaja de los hombres en tipo de empleo y rama de actividad (+1.0 y +0.9). "
          "Lo que ocurre, en cambio, es que **a iguales características las mujeres reciben 6.9 puntos logarítmicos (6.7 %) menos**: esa es la parte *no explicada*, que es mayor que la brecha total precisamente porque las características de las mujeres las favorecen. "
          "Importante: la parte no explicada **no prueba discriminación**; incluye todo lo que el estudio no mide (la ocupación específica, la experiencia real, la negociación, las interrupciones de carrera, la selección hacia el empleo).", alinear="justificado")

    # ------------------------------------------------------------------ 7.6
    inf.h2("7.6 La brecha a lo largo de la distribución")
    inf.p("**Qué se calculó.** La brecha en distintos puntos de la distribución del ingreso por hora (percentiles 10, 25, 50, 75 y 90). El promedio puede ocultar que la desigualdad sea distinta entre quienes ganan poco y quienes ganan mucho.", alinear="justificado")
    cu = D.brecha_cuantiles
    filas = [[f"P{int(r.percentil)}", f"{r.ing_hora_h:.2f}", f"{r.ing_hora_m:.2f}", f"{r.brecha_pct:.1f}", f"{r.inf:.1f} a {r.sup:.1f}", pval(r.p)] for r in cu.itertuples()]
    inf.tabla(filas, ["Percentil", "$/h hombres", "$/h mujeres", "Brecha %", "IC 95 %", "Valor p"], [2.2, 2.7, 2.7, 2.4, 3.6, 2.4], pie="Brecha por hora en cinco puntos de la distribución.", alinear=["centro", "der", "der", "der", "centro", "der"])
    inf.figura(FIG / "12_brecha_cuantiles.png", 14.5, "Brecha por hora en distintos percentiles del ingreso por hora (IC 95 %).")
    inf.p("**Lectura.** La brecha se concentra en la parte baja de la distribución: **8.2 % en el decil inferior (P10) y 10.4 % en el cuartil inferior (P25)**, ambas significativas. En la mediana (2.1 %) ya no es significativa, en el cuartil superior se invierte levemente (−2.3 %, p = 0.04) y en el decil superior es nula. "
          "Es decir, el pago por hora es más desigual entre quienes ganan poco: el «piso» de las mujeres está por debajo del de los hombres. Como los ingresos por hora son muy «redondos» (muchas personas declaran $50 o $100 por hora), los percentiles saltan de un valor a otro y sus intervalos son irregulares; "
          "conviene leerlos como una tendencia y no como cifras exactas.", alinear="justificado")

    # ------------------------------------------------------------------ 7.7
    inf.h2("7.7 Robustez: ¿cambian las conclusiones si cambian las decisiones?")
    inf.p("**Qué se calculó.** La brecha total y el rendimiento de la escolaridad bajo diez especificaciones alternativas (S0 a S9) y siete (R0 a R6): sin recortar atípicos, solo asalariados, imputando los rangos de ingreso, corrigiendo por no respuesta (IPW), usando medianas, usando el ingreso mensual, sin ponderar y con controles.", alinear="justificado")
    rb = D.rob_tot
    filas = [[i, rb.loc[i, "descripcion"], f"{rb.loc[i, 'brecha_pct']:.1f}", f"{rb.loc[i, 'inf']:.1f} a {rb.loc[i, 'sup']:.1f}", pval(rb.loc[i, "p"]), n_es(rb.loc[i, "n"])] for i in rb.index]
    inf.tabla(filas, ["Especificación", "Qué cambia", "Brecha %", "IC 95 %", "p", "n"], [3.1, 6.1, 1.5, 2.4, 1.6, 1.8], pie="Robustez de la brecha total ante las decisiones metodológicas.", alinear=["izq", "izq", "der", "centro", "der", "der"], fuente=8.5, resaltar_fila={0})
    inf.figura(FIG / "13_robustez_brecha.png", 15.0, "Robustez de la brecha por hora ante distintas decisiones metodológicas (S3 sesga hacia cero por construcción; S6 es otro estimando).")
    inf.vinetas(["**La brecha por hora es positiva en las diez especificaciones**, pero su tamaño depende de ellas: de 0.7 % a 4.6 % sin controles, y 8.2 % con controles de personas comparables.",
                 f"**En {int((D.hora_specs.p < 0.05).sum())} de las {len(D.hora_specs)} especificaciones sin controles la brecha es significativa;** las excepciones son {' y '.join(i.split(' ')[0] for i in D.hora_specs.index[D.hora_specs.p >= 0.05])} "
                 "(la imputación S3, que se sabe sesgada hacia cero, y la diferencia de medianas S5, cuyo intervalo llega al cero). Con controles (S8 y S9) es significativa en todos los casos. La existencia de una brecha por hora no depende de una decisión particular.",
                 f"**S2 (solo asalariados) muestra una brecha menor** ({D.rob_tot.loc['S2 Solo asalariados', 'brecha_pct']:.1f} %): en el empleo subordinado y remunerado la diferencia es menor; se amplía en el empleo informal (sección 7.8).",
                 "**S4 (corrección por no respuesta) sube la brecha a 4.5 %:** al dar más peso a quienes se parecen a los que no declararon su ingreso, la brecha crece, lo que sugiere que la muestra de quienes declaran subestima ligeramente la desigualdad.",
                 "**S6 (mensual) es otro estimando**: incluye la diferencia de horas (sección 7.4)."])
    rr = D.robustez_retorno
    filas = [[r.especificacion, r.descripcion, f"{r.retorno_pct:.2f}", f"{r.inf:.2f} a {r.sup:.2f}", n_es(r.n)] for r in rr.itertuples()]
    inf.tabla(filas, ["Especificación", "Qué cambia", "Rendimiento %", "IC 95 %", "n"], [3.2, 6.5, 2.2, 2.9, 1.7], pie="Robustez del rendimiento de la escolaridad.", alinear=["izq", "izq", "der", "centro", "der"], fuente=9, resaltar_fila={0})
    inf.p(f"**Lectura.** El rendimiento por año de escolaridad es muy estable: entre {rr.retorno_pct.min():.1f} % y {rr.retorno_pct.max():.1f} % en las siete especificaciones. Esta conclusión **no depende** de cómo se traten los atípicos, los rangos de ingreso o la no respuesta.", alinear="justificado")

    # ------------------------------------------------------------------ 7.8
    inf.h2("7.8 Heterogeneidad: ¿en qué grupos es mayor la brecha?")
    inf.p("**Qué se calculó.** La brecha por hora dentro de subgrupos definidos por cinco dimensiones: informalidad, posición en la ocupación, región, tamaño de localidad y edad (más el nivel de instrucción detallado). La figura marca con un punto relleno las categorías significativas tras la corrección de Holm dentro de cada dimensión.", alinear="justificado")
    inf.figura(FIG / "17_brecha_subgrupos.png", 15.0, "Brecha por hora por subgrupo (IC 95 %). Punto relleno: significativa con Holm (p < 0.05); hueco: no significativa.")
    sg = D.brecha_subgrupos
    def g(dim, cat):
        r = sg[(sg.dimension == dim) & (sg.categoria == cat)].iloc[0]
        return r
    inf.vinetas([f"**Informalidad:** la brecha es de {g('Informalidad', 'Informal').brecha_pct:.1f} % entre trabajadores informales (significativa) y de {g('Informalidad', 'Formal').brecha_pct:.1f} % entre formales (no significativa). La desigualdad se concentra en el empleo informal.",
                 f"**Región:** de {g('Región', 'Sur').brecha_pct:.1f} % en el Sur (no significativa) a {g('Región', 'Centro-Norte').brecha_pct:.1f} % en el Centro-Norte; en el Norte es de {g('Región', 'Norte').brecha_pct:.1f} %.",
                 f"**Edad:** es significativa entre los 15 y los 64 años ({sg[(sg.dimension == 'Grupo de edad') & (sg.categoria != '65+')].brecha_pct.min():.1f} % a {sg[(sg.dimension == 'Grupo de edad') & (sg.categoria != '65+')].brecha_pct.max():.1f} %), con un máximo de {g('Grupo de edad', '45-54').brecha_pct:.1f} % a los 45-54 años; a partir de los 65 las muestras son pequeñas y el intervalo, muy amplio.",
                 f"**Posición:** {g('Posición en la ocupación', 'Subordinado y remunerado').brecha_pct:.1f} % entre subordinados (significativa), {g('Posición en la ocupación', 'Empleador').brecha_pct:.1f} % entre empleadores y {g('Posición en la ocupación', 'Cuenta propia').brecha_pct:.1f} % entre trabajadores por cuenta propia; estas dos últimas tienen intervalos amplios y no son significativas con Holm.",
                 f"**Tamaño de localidad:** significativa en todos los tamaños, de {sg[sg.dimension == 'Tamaño de localidad'].brecha_pct.min():.1f} % a {sg[sg.dimension == 'Tamaño de localidad'].brecha_pct.max():.1f} %.",
                 f"**Nivel de instrucción detallado:** entre {sg[sg.dimension == 'Nivel de instrucción detallado'].brecha_pct.min():.1f} % y {sg[sg.dimension == 'Nivel de instrucción detallado'].brecha_pct.max():.1f} %; incluso entre quienes tienen licenciatura o posgrado la brecha es de {g('Nivel de instrucción detallado', 'Licenciatura o posgrado (16+ años)').brecha_pct:.1f} %."])
    inf.p("**Lectura.** La brecha no es uniforme: es más visible en el empleo informal, en el centro-norte del país y en la mitad de la vida laboral. Sin embargo, con intervalos tan amplios en algunos subgrupos, conviene evitar conclusiones fuertes sobre diferencias pequeñas entre ellos.", alinear="justificado")

    # ------------------------------------------------------------------ 7.9
    inf.h2("7.9 La brecha de género por entidad federativa")
    be = D.brecha_estados
    be_sig = int((be.brecha_hora_p < 0.05).sum())
    bmx, bmn = be.loc[be.brecha_hora_est.idxmax()], be.loc[be.brecha_hora_est.idxmin()]
    inf.p(f"Con 1,900 a 5,900 observaciones por entidad la brecha por hora se estima con poca precisión: es positiva en {int((be.brecha_hora_est > 0).sum())} de las 32 entidades y significativa (p < 0.05, sin ajuste por multiplicidad) en {be_sig}. "
          f"Va de {bmn.brecha_hora_est:.1f} % ({bmn.entidad}) a {bmx.brecha_hora_est:.1f} % ({bmx.entidad}). Estas cifras se incluyen en el Anexo C y en las fichas del tablero como **descriptivas**, con sus intervalos; no se comparan entidades entre sí. "
          f"En cambio, la brecha *mensual* es significativa en {int((be.brecha_mens_p < 0.05).sum())} de las 32 entidades (de {be.brecha_mens_est.min():.1f} % a {be.brecha_mens_est.max():.1f} %).", alinear="justificado")

    # ------------------------------------------------------------------ 7.10
    inf.h2("7.10 Informalidad laboral y escolaridad (objetivo 3)")
    inf.p(f"**Qué se calculó.** La tasa de informalidad laboral (TIL1) ponderada para todo el país, por sexo, región, nivel de instrucción y entidad, con intervalos por bootstrap, y su asociación con la escolaridad promedio de cada entidad.", alinear="justificado")
    nac = D.til1_grupos.set_index("grupo")
    filas = [[g_, f"{nac.loc[g_, 'est']:.1f}", f"{nac.loc[g_, 'ic_inf']:.1f} a {nac.loc[g_, 'ic_sup']:.1f}"] for g_ in nac.index]
    inf.tabla(filas, ["Grupo", "TIL1 %", "IC 95 %"], [8.0, 3.0, 4.0], pie="Tasa de informalidad laboral (TIL1) por grupo.", alinear=["izq", "der", "centro"], resaltar_fila={0})
    inf.p(f"**Lectura.** El **{f1(D.nac['est'])} %** de las personas ocupadas está en un empleo informal. Es algo mayor entre las mujeres ({f1(R['til1']['mujeres']['est'])} %) que entre los hombres ({f1(R['til1']['hombres']['est'])} %), pero la diferencia por regiones es enorme: de {R['til1']['regiones']['Norte']:.0f} % en el Norte a {R['til1']['regiones']['Sur']:.0f} % en el Sur. "
          f"Y la escolaridad es decisiva: la informalidad baja de {R['til1']['por_nivel']['1']:.0f} % entre quienes no terminaron la primaria a {R['til1']['por_nivel']['4']:.0f} % entre quienes tienen preparatoria o más.", alinear="justificado")
    inf.figura(FIG / "14_mapa_informalidad.png", 14.5, "Informalidad laboral por entidad (TIL1, %) en un cartograma de mosaicos: cada estado ocupa la misma área.")
    tl = D.til1_entidad.sort_values("til1_est", ascending=False)
    sel = pd.concat([tl.head(5), tl.tail(5)])
    filas = [[f"{int(r.til1_rango)}", r.entidad, r.region, f"{r.til1_est:.1f}", f"{r.til1_ic_inf:.1f} a {r.til1_ic_sup:.1f}", f"{int(r.til1_rango_inf)} a {int(r.til1_rango_sup)}", f"{r.esc15_est:.1f}"] for r in sel.itertuples()]
    inf.tabla(filas, ["Lugar", "Entidad", "Región", "TIL1 %", "IC 95 %", "Intervalo del lugar", "Esc. media"], [1.4, 3.7, 2.6, 1.7, 2.8, 2.6, 1.7], pie="Las cinco entidades con mayor y menor informalidad (ranking completo en el Anexo C).",
              alinear=["centro", "izq", "izq", "der", "centro", "centro", "der"], fuente=9)
    inf.p("Las entidades con más informalidad son Oaxaca, Guerrero y Chiapas (más de 74 %), y las de menos, Coahuila, Nuevo León y Chihuahua (alrededor de 33 a 36 %). El ranking es confiable en los extremos: Oaxaca ocupa siempre el primer lugar en las réplicas (intervalo de 1 a 1).", alinear="justificado")
    inf.figura(FIG / "15_informalidad_vs_escolaridad.png", 14.5, "Informalidad laboral y escolaridad promedio de los ocupados de cada entidad.")
    asoc = D.asoc
    inf.p(f"**Asociación entre estados.** La correlación de Pearson entre la informalidad y la escolaridad promedio de las entidades es {asoc.loc['r_pearson_til_esc', 'est']:.2f} (IC {ic(asoc.loc['r_pearson_til_esc', 'ic_inf'], asoc.loc['r_pearson_til_esc', 'ic_sup'], 2)}) y la de Spearman {asoc.loc['rho_spearman_til_esc', 'est']:.2f}: una relación negativa muy fuerte. "
          f"La pendiente es de {asoc.loc['pendiente_til_esc', 'est']:.1f} puntos porcentuales por cada año adicional de escolaridad promedio (IC {ic(asoc.loc['pendiente_til_esc', 'ic_inf'], asoc.loc['pendiente_til_esc', 'ic_sup'])}). Es una relación entre estados y no causal.", alinear="justificado")
    li = D.logit_informalidad.set_index("variable")
    inf.p(f"**Asociación individual (regresión logística con diseño).** Controlando por edad y sexo, cada año de escolaridad reduce los momios de tener un empleo informal en {100 * (1 - li.loc['anios_esc', 'razon_momios']):.0f} % (razón de momios {li.loc['anios_esc', 'razon_momios']:.2f}; IC {ic(li.loc['anios_esc', 'rm_inf'], li.loc['anios_esc', 'rm_sup'], 2)}), "
          f"lo que equivale a un **efecto marginal promedio de {D.ind['ame_anios_esc_pp']:.1f} puntos porcentuales por año** (con un modelo lineal de probabilidad se obtiene {D.ind['lpm_anios_esc_pp']:.1f}). Las mujeres tienen {100 * (li.loc['mujer', 'razon_momios'] - 1):.0f} % más momios de ser informales ({D.ind['ame_mujer_pp']:.1f} puntos porcentuales) a igualdad de edad y escolaridad. "
          f"El pseudo-R² de McFadden es {D.ind['mcfadden']:.2f}.", alinear="justificado")

    # ------------------------------------------------------------------ 7.11
    inf.h2("7.11 Diagnósticos del modelo")
    dg = D.dg
    inf.p("Los modelos de regresión se revisaron con los diagnósticos habituales. El análisis se hace sobre el modelo con todos los controles (G6) para no ocultar problemas:", alinear="justificado", despues=3)
    inf.figura(FIG / "16_diagnosticos_modelo.png", 15.0, "Diagnósticos del modelo con todos los controles: residuos contra valores ajustados (izquierda) y gráfico Q-Q de normalidad (derecha).")
    inf.tabla([["R² del modelo OLS", f"{dg['r2_ols']:.3f}", "Con los 53 parámetros explica 40 % de la variación de ln(ingreso por hora)."],
               ["Prueba de Breusch-Pagan", f"LM = {dg['breusch_pagan_LM']:,.0f}, p < 0.001", "Hay **varianza no constante** (heterocedasticidad): por eso los errores estándar son robustos de diseño y no los clásicos."],
               ["VIF máximo (variables clave)", f"{dg['vif_max_variables_clave']:.2f}", "Muy por debajo de 5: no hay multicolinealidad problemática."],
               ["Distancia de Cook máxima", f"{dg['cook_max']:.4f}", "Ninguna observación individual tiene influencia relevante."],
               ["Observaciones con Cook > 4/n", f"{100 * dg['cook_prop_mayor_4_sobre_n']:.1f} %", f"Al eliminarlas, el coeficiente de «mujer» cambia de {dg['coef_mujer_con_todo']:.4f} a {dg['coef_mujer_sin_influyentes']:.4f}: el resultado no depende de ellas."],
               ["Forma de los residuos", f"asimetría {dg['asimetria_residuos']:.2f}; curtosis en exceso {dg['curtosis_exceso_residuos']:.2f}", "Los residuos son casi simétricos con colas algo pesadas, sobre todo en el extremo inferior (panel derecho de la figura)."],
               ["Normalidad de ln(ingreso por hora)", "Se rechaza (p < 0.001)", "Con 112 mil observaciones cualquier desviación pequeña se rechaza. La inferencia no la necesita: se basa en el bootstrap y en errores robustos."]],
              ["Diagnóstico", "Resultado", "Interpretación"], [4.2, 4.3, 8.0], pie="Diagnósticos del modelo con todos los controles.", alinear=["izq", "izq", "izq"], fuente=9, negrita_col0=True)
