"""Contenido del sitio, parte B: minería y análisis (fundamentos, objetivos 1 a 3) e interpretación (capítulos 4 y 5)."""
from __future__ import annotations

import pandas as pd

from informe_datos import f1, n_es, pval
from sitio_contenido_a import F, ir, mosaico
from sitio_lib import Ctx, Raw, barras, cifras, dos, e, lista, md, nota, p, pasos, tabla, tarjeta


def ic(a: float, b: float, d: int = 1) -> str:
    return f"{a:.{d}f} a {b:.{d}f}"


def construir(ctx: Ctx) -> list[str]:
    D = ctx.D
    R, tot, rt, bn = D.R, D.tot, D.rt, D.bn
    esc = ctx.escena
    out: list[str] = []
    deff = D.deff
    prem = D.premio_por_nivel
    prem92 = float(prem.iloc[3]["premio_pct"])
    ret = f1(rt["nacional_pct"]["est"])
    ic_ret = ic(rt["nacional_pct"]["ic_inf"], rt["nacional_pct"]["ic_sup"])
    sg = D.brecha_subgrupos
    re = D.retorno_entidad

    # ================================================================= 4 · MINERÍA Y ANÁLISIS · fundamentos
    fund = "Fundamentos estadísticos"
    items = [("Tasa de informalidad · si fuera muestra aleatoria simple", 100 * deff.loc["TIL1 nacional", "ee_mas"], f"{100 * deff.loc['TIL1 nacional', 'ee_mas']:.2f} pp", "gris"),
             ("Tasa de informalidad · con el diseño complejo", 100 * deff.loc["TIL1 nacional", "ee_diseno"], f"{100 * deff.loc['TIL1 nacional', 'ee_diseno']:.2f} pp"),
             ("Brecha por hora · si fuera muestra aleatoria simple", 100 * deff.loc["Brecha por hora total (log-puntos)", "ee_mas"], f"{100 * deff.loc['Brecha por hora total (log-puntos)', 'ee_mas']:.2f}", "gris"),
             ("Brecha por hora · con el diseño complejo", 100 * deff.loc["Brecha por hora total (log-puntos)", "ee_diseno"], f"{100 * deff.loc['Brecha por hora total (log-puntos)', 'ee_diseno']:.2f}")]
    out.append(esc("diseno", 4, "Ignorar el diseño muestral subestimaría el error a la mitad",
                   '<p class="tit-c">Error estándar de dos estimaciones clave (pp = puntos porcentuales; la brecha, en puntos logarítmicos × 100)</p>' + barras(items, escala=0.8)
                   + cifras([(f"×{deff.loc['TIL1 nacional', 'deff']:.1f}", "efecto de diseño en la informalidad"), (f"{deff.loc['TIL1 nacional', 'n_efectivo'] / 1000:.0f} mil", f"observaciones efectivas de {D.n_u / 1000:.0f} mil"),
                             (f"{R['B']:,}", "réplicas de Rao-Wu sobre 713 estratos y 21,194 UPM")])
                   + nota("En palabras sencillas", "Las personas de una misma zona se parecen, así que aportan menos información que personas elegidas al azar en todo el país. Con el diseño real el error es casi el doble; sin él, todo parecería «significativo».", "sencillo"),
                   g=("Ignorar el diseño muestral",), sub=fund))

    out.append(esc("raowu", 4, "El bootstrap de Rao–Wu, paso a paso",
                   F("D05_rao_wu.png", "El bootstrap de Rao-Wu en cuatro pasos (ejemplo con un estrato de cuatro UPM).")
                   + dos(pasos(["En cada estrato con *n* UPM se sortean *n − 1* con reemplazo.", "Los pesos se reescalan: × *n/(n − 1)* × las veces que salió la UPM.", "Se repite 1,000 veces con la misma semilla.", "Error estándar = desviación estándar de las réplicas; IC = percentiles 2.5 y 97.5."]),
                         nota("Verificado con pruebas", "La varianza del bootstrap coincide con la de la linealización de Taylor (dentro de 8 %), y los dominios conservan todas las UPM del diseño."), "dos--igual"),
                   g=("El bootstrap de Rao",), sub=fund))

    p50 = D.cu.loc[50]
    sur = sg[(sg.dimension == "Región") & (sg.categoria == "Sur")].iloc[0]
    casos = (tarjeta("1 · Excluye el 0", p(f"Brecha por hora total: **{f1(tot['brecha_hora_pct'])} %** (IC {ic(tot['brecha_hora_inf'], tot['brecha_hora_sup'])}). Hay brecha demostrable."))
             + tarjeta("2 · Toca el 0", p(f"Brecha en la mediana: **{f1(p50['brecha_pct'])} %** (p = {p50['p']:.2f}). Evidencia débil."))
             + tarjeta("3 · Incluye el 0", p(f"Brecha en la región Sur: **{f1(sur['brecha_pct'])} %** (p = {sur['p']:.2f}). No se puede afirmar.")))
    out.append(esc("icp", 4, "Cómo leer un intervalo de confianza y un valor p",
                   F("D06_como_leer_ic.png", "Tres casos reales: un intervalo que excluye el 0, uno que lo toca y uno que lo incluye.")
                   + dos(nota("IC 95 %", "Rango de valores plausibles: si el estudio se repitiera muchas veces, el 95 % de los intervalos construidos así contendría el valor verdadero. Si **no incluye el 0**, la diferencia es significativa.", "sencillo"),
                         nota("Valor p", "Probabilidad de ver una diferencia así si en realidad no hubiera brecha. Si p < 0.05 se dice que es estadísticamente significativa.", "sencillo"), "dos--igual")
                   + '<div class="rejilla">' + casos + "</div>", g=("Cómo leer un intervalo",), sub=fund))

    out.append(esc("spearman", 4, "Spearman: la correlación entre rangos",
                   F("D08_spearman_ejemplo.png", "Ejemplo con seis personas: al convertir los valores en rangos, Spearman = 0.93.")
                   + pasos(["Ordenar cada variable.", "Cambiar los valores por su lugar (rango); los empates reciben el rango medio.", "Calcular la correlación de Pearson entre los rangos, ponderada por `fac_tri`."])
                   + cifras([("≈ 0.1", "débil"), ("≈ 0.3", "moderada"), ("≈ 0.5", "fuerte"), (f"{rt['spearman_nacional']['est']:.2f}", "escolaridad e ingreso por hora, nacional (IC "
                                                                                                                                  f"{ic(rt['spearman_nacional']['ic_inf'], rt['spearman_nacional']['ic_sup'], 2)})")]), g=("Spearman: la correlación",), sub=fund))

    rm = D.retorno_modelos
    m3 = rm[rm.modelo.str.startswith("M3")].iloc[0]
    filas = [[r.modelo, f"{r.coef:.4f}", f"{r.retorno_pct:.2f} % ({r.retorno_pct_inf:.2f} a {r.retorno_pct_sup:.2f})", f"{r.r2:.3f}"] for r in rm.iloc[:4].itertuples()]
    dos_anios = 100 * ((1 + m3.retorno_pct / 100) ** 2 - 1)
    out.append(esc("mincer", 4, f"La ecuación de Mincer: cómo se lee el {ret} %",
                   '<div class="formula">ln(ingreso por hora) = α + β · escolaridad + γ₁ · edad + γ₂ · edad² + δ · mujer + efectos de entidad y de localidad + error<small>β es el aumento del logaritmo del ingreso por año de estudio; rendimiento (%) = 100 × (e^β − 1)</small></div>'
                   + tabla(["Modelo (controles acumulados)", "β", "Rendimiento por año (IC 95 %)", "R²"], filas, num=(1, 2, 3), destacar=(2,))
                   + cifras([(f"+{m3.retorno_pct:.1f} %", "por cada año de estudio (modelo M3)"), (f"+{dos_anios:.1f} %", "por dos años: (1.051)² − 1")])
                   + nota("Cómo leerla", "M3 (con entidad y localidad) es el resultado de referencia. Al agregar la posición en la ocupación y la informalidad (M4) baja a 3.8 %, porque una parte del beneficio de estudiar actúa **a través de** conseguir un mejor empleo; por eso M4 no es el resultado principal.", "sencillo"),
                   g=("La ecuación de Mincer",), sub=fund))

    tc = D.tests_clasicos.set_index("nivel")
    filas = []
    for k in ["1. Primaria incompleta", "2. Primaria completa", "3. Secundaria completa", "4. Medio superior y superior"]:
        filas.append([k.split(". ", 1)[1], f"{bn.loc[k, 'brecha_hora_pct']:.1f} %", ic(bn.loc[k, "brecha_hora_inf"], bn.loc[k, "brecha_hora_sup"]), f"{tc.loc[k, 'd_cohen']:.2f}", "< 0.001" if bn.loc[k, "p_hora_holm"] < 0.001 else f"{bn.loc[k, 'p_hora_holm']:.3f}"])
    filas.append(["Total", f"{f1(tot['brecha_hora_pct'])} %", ic(tot["brecha_hora_inf"], tot["brecha_hora_sup"]), f"{tc.loc['Total', 'd_cohen']:.2f}", "< 0.001"])
    out.append(esc("herramientas", 4, "Tres herramientas para leer la brecha: porcentaje, tamaño del efecto y Holm",
                   '<div class="rejilla">' + tarjeta("Brecha (%)", p(f"1 − ({tot['ing_hora_m']:.2f} ÷ {tot['ing_hora_h']:.2f}) = **{f1(tot['brecha_hora_pct'])} %**. Las mujeres ganan {f1(tot['brecha_hora_pct'])} % menos por hora (medias geométricas)."))
                   + tarjeta("d de Cohen", p("Diferencia de medias entre la desviación estándar. 0.2 es pequeño, 0.5 mediano y 0.8 grande. Aquí va de 0.06 a 0.24: un efecto pequeño."))
                   + tarjeta("Corrección de Holm", p("Como se hacen cuatro pruebas (una por nivel), los valores p se ordenan y se comparan con umbrales crecientes para controlar el error de todo el conjunto. Las cuatro siguen siendo significativas.")) + "</div>"
                   + tabla(["Nivel de instrucción", "Brecha por hora", "IC 95 %", "d de Cohen", "p (Holm)"], filas, num=(1, 2, 3, 4), destacar=(4,)), g=("Tres herramientas para leer la brecha",), sub=fund))

    # ================================================================= objetivo 1
    o1 = "Objetivo 1 · Escolaridad e ingreso"
    nombres = ["Primaria completa", "Secundaria completa", "Media superior (12 a 15 años)", "Licenciatura o posgrado (16+ años)"]
    barras_prem = barras([(n, float(prem.iloc[i]["premio_pct"]), f"+{prem.iloc[i]['premio_pct']:.0f} %") for i, n in enumerate(nombres)], escala=100.0)
    out.append(esc("rendimiento", 4, f"Cada año de estudio eleva el ingreso por hora {ret} %, y la licenciatura casi lo duplica",
                   F("04_ingreso_por_escolaridad.png", "Mediana ponderada del ingreso por hora según los años de escolaridad, por sexo (escala logarítmica).")
                   + dos('<p class="tit-c">Premio salarial frente a no terminar la primaria (controlando edad, sexo y entidad)</p>' + barras_prem,
                         cifras([(f"+{ret} %", f"por año de escolaridad (IC 95 %: {ic_ret})"), (f"{f1(rt['mujeres_pct']['est'])} % vs {f1(rt['hombres_pct']['est'])} %", "rendimiento por año de mujeres frente a hombres"),
                                 (f"{D.robustez_retorno.retorno_pct.min():.1f} a {D.robustez_retorno.retorno_pct.max():.1f} %", "en siete especificaciones alternativas")]), "dos--igual"),
                   g=("Cada año de estudio eleva",), sub=o1))

    q = D.rr
    filas = []
    for k in (1, 2, 3, 4):
        a, b = f"Rendimiento medio, cuartil {k} de ingreso estatal (%)", f"Spearman medio, cuartil {k} de ingreso estatal"
        filas.append([f"Cuartil {k}" + (" (ingreso más bajo)" if k == 1 else " (ingreso más alto)" if k == 4 else ""), f"{q.loc[a, 'est']:.2f} ({q.loc[a, 'ic_inf']:.2f} a {q.loc[a, 'ic_sup']:.2f})", f"{q.loc[b, 'est']:.2f} ({q.loc[b, 'ic_inf']:.2f} a {q.loc[b, 'ic_sup']:.2f})"])
    dq = D.dq
    mx, mn = re.loc[re.ret_est.idxmax()], re.loc[re.ret_est.idxmin()]
    out.append(esc("estados", 4, "Estudiar rinde parecido en estados ricos y pobres",
                   F("05_retorno_estados.png", "Rendimiento por año de escolaridad en cada entidad (con IC 95 %); el color indica el cuartil de ingreso mediano por hora del estado.")
                   + cifras([("≈ 0", f"diferencia entre estados ricos (Q4) y pobres (Q1): {dq['est']:+.3f} log-puntos, p = {dq['p']:.2f}"), (f"{mn.ret_est:.1f} a {mx.ret_est:.1f} %", f"rango entre estados: de {mn.entidad} a {mx.entidad}")])
                   + tabla(["Estados por ingreso mediano", "Rendimiento medio (IC 95 %)", "Spearman medio (IC 95 %)"], filas, num=(1, 2))
                   + nota("Cuidado", "Son relaciones **entre estados**, no efectos individuales. Los estados ricos pagan más en todos los niveles; lo que no cambia es el aumento porcentual por año de estudio.", "cuidado"), g=("Estudiar rinde parecido",), sub=o1))

    srt = re.sort_values("rho_est", ascending=False)
    sel = pd.concat([srt.head(5), srt.tail(5)])
    filas = [[f"{int(r.rho_rango)}", r.entidad, f"{r.rho_est:.2f} ({r.rho_ic_inf:.2f} a {r.rho_ic_sup:.2f})", f"{int(r.rho_rango_inf)} a {int(r.rho_rango_sup)}"] for r in sel.itertuples()]
    out.append(esc("ranking", 4, "Un ranking defendible distingue solo los extremos",
                   F("06_spearman_estados.png", "Correlación de Spearman entre escolaridad e ingreso por hora en cada entidad, con IC 95 % y lugar en el ranking.")
                   + cifras([(f"{rt['spearman_nacional']['est']:.2f}", "Spearman nacional: asociación positiva y moderada"), (f"{D.rt['rho_max']['rho_est']:.2f} → {D.rt['rho_min']['rho_est']:.2f}", f"de {D.rt['rho_max']['entidad']} a {D.rt['rho_min']['entidad']}")])
                   + nota("Cómo leerlo", "Los lugares centrales tienen intervalos de 15 o más posiciones: no son estadísticamente distinguibles. Un ranking defendible reporta esa incertidumbre.", "sencillo")
                   + tabla(["Lugar", "Entidad", "ρ (IC 95 %)", "Intervalo del lugar"], filas, num=(0, 3), pie="Las cinco entidades con mayor y menor correlación; el ranking completo está en la tabla del informe.")
                   + F("07_escolaridad_vs_ingreso_estatal.png", "Los estados más escolarizados pagan más por hora (Spearman entre estados = 0.74; relación entre estados, no causal).")
                   + nota("Cuidado con la falacia ecológica", f"Entre estados, la escolaridad promedio y el ingreso mediano van juntos (Spearman = {rt['rho_estatal_esc_ingreso']['est']:.2f}), pero cada punto es una entidad: eso no dice qué le pasaría a una persona que estudiara más.", "cuidado"),
                   g=("Un ranking defendible",), sub=o1))

    # ================================================================= objetivo 2
    o2 = "Objetivo 2 · Brecha de género"
    filas = []
    for k in bn.index:
        r = bn.loc[k]
        filas.append([k.split(". ", 1)[-1], f"{r.brecha_hora_pct:.1f} %", ic(r.brecha_hora_inf, r.brecha_hora_sup), f"{r.brecha_mens_pct:.1f} %", f"{r.menos_horas_mujeres_pct:.1f} %"])
    out.append(esc("brechahm", 4, f"Por hora la brecha es de {f1(tot['brecha_hora_pct'])} %; por mes, de {f1(tot['brecha_mens_pct'])} %",
                   F("09_brecha_por_nivel.png", "Brecha salarial de género por hora y por mes, por nivel de instrucción (IC 95 %).")
                   + cifras([(f"{f1(tot['brecha_hora_pct'])} %", f"por hora (IC {ic(tot['brecha_hora_inf'], tot['brecha_hora_sup'])}; p < 0.001)"), (f"{f1(tot['brecha_mens_pct'])} %", "por mes"),
                             (f"−{tot['menos_horas_mujeres_pct']:.0f} %", f"horas pagadas: {tot['horas_m']:.1f} frente a {tot['horas_h']:.1f} por semana")])
                   + tabla(["Nivel", "Brecha por hora", "IC 95 %", "Brecha mensual", "Mujeres trabajan menos horas"], filas, num=(1, 2, 3, 4), destacar=(4,))
                   + nota("En palabras sencillas", "En logaritmos la identidad es exacta: **brecha mensual = brecha por hora + brecha de horas**. Casi toda la diferencia mensual viene de que las mujeres trabajan menos horas pagadas, y las cuatro brechas por hora son significativas incluso con la corrección de Holm; el tamaño del efecto es pequeño (d de Cohen de 0.06 a 0.24).", "sencillo")
                   + '<details class="guion"><summary>Distribución por nivel y sexo (cajas)</summary>' + F("08_cajas_nivel_sexo.png", "Distribución de ln(ingreso por hora) por nivel de instrucción y sexo.") + "</details>",
                   g=("Por hora la brecha es de",), sub=o2))

    ec = D.escalera_brecha
    filas = [[r.modelo, f"{r.brecha_pct:.1f} %", ic(r.brecha_pct_inf, r.brecha_pct_sup), f"{r.r2:.3f}"] for r in ec.itertuples()]
    out.append(esc("comparables", 4, "Entre personas comparables, la brecha por hora ronda 8 %",
                   F("10_escalera_controles.png", "Cómo cambia la brecha por hora al agregar controles; el último modelo (horas) no se interpreta.")
                   + cifras([(f"{ec.iloc[0]['brecha_pct']:.1f} %", "sin controles"), (f"{D.g5['brecha_pct']:.1f} %", "con escolaridad, edad, lugar, empleo y rama"), ("≈ 7 pts", "parte no explicada (Oaxaca-Blinder)")])
                   + tabla(["Modelo (controles acumulados)", "Brecha", "IC 95 %", "R²"], filas, num=(1, 2, 3), destacar=(5,))
                   + nota("Por qué no se interpreta el último modelo", "Controlar por horas da 16 %, pero es un artefacto: el ingreso por hora es ingreso entre horas, y un error en las horas crea una relación negativa mecánica (**sesgo de división**).", "cuidado"), g=("Entre personas comparables",), sub=o2))

    ob = D.ob
    comp = [("Brecha total", "Brecha total (log-puntos)"), ("Explicada por diferencias en características", "Explicada por características (referencia agrupada)"), ("   · escolaridad", "escolaridad"), ("   · edad y experiencia", "edad / experiencia"),
            ("   · entidad y tamaño de localidad", "entidad y tamaño de localidad"), ("   · posición e informalidad", "posición e informalidad"), ("   · rama de actividad", "rama de actividad"), ("No explicada (mismas características, distinto pago)", "No explicada (referencia agrupada)")]
    filas = [[n.replace("   · ", "· "), f"{ob.loc[k, 'log_puntos'] * 100:.2f}", ic(ob.loc[k, "ic_inf"] * 100, ob.loc[k, "ic_sup"] * 100, 2)] for n, k in comp]
    out.append(esc("oaxaca", 4, "Oaxaca–Blinder: las mujeres tienen mejores características, pero un residuo desfavorable",
                   F("D07_oaxaca_idea.png", "Idea de la descomposición: brecha total = parte explicada + parte no explicada.")
                   + dos(nota("Cómo leerla", ["**Explicada:** hombres y mujeres difieren en sus características medidas (escolaridad, edad, lugar, empleo, rama).", "**No explicada:** a iguales características, se les paga distinto."], "sencillo"),
                         nota("Cuidado", "La parte no explicada **no prueba discriminación**: incluye todo lo que no se mide (ocupación específica, experiencia real, negociación, selección).", "cuidado"), "dos--igual")
                   + F("11_oaxaca_blinder.png", "Descomposición de la brecha total en parte explicada y no explicada, y contribución de cada grupo de características (puntos logarítmicos).")
                   + tabla(["Componente", "Centésimas de log-punto", "IC 95 %"], filas, num=(1, 2), destacar=(0, 1, 7), pie="1 centésima de log-punto ≈ 1 %."), g=("Oaxaca–Blinder: separar", "Oaxaca-Blinder: las mujeres"), sub=o2))

    cu = D.cu
    filas = [[f"P{int(i)}", f"{r.ing_hora_h:.2f}", f"{r.ing_hora_m:.2f}", f"{r.brecha_pct:.1f} %", ic(r.inf, r.sup), pval(r.p)] for i, r in cu.iterrows()]
    out.append(esc("cuantiles", 4, "La brecha se concentra en la parte baja de la distribución",
                   F("12_brecha_cuantiles.png", "Brecha por hora en distintos percentiles del ingreso por hora (IC 95 %).")
                   + cifras([(f"{cu.loc[10, 'brecha_pct']:.0f} a {cu.loc[25, 'brecha_pct']:.0f} %", "en el 10 a 25 % que menos gana"), (f"{cu.loc[50, 'brecha_pct']:.1f} %", "en la mediana (no significativa)"), ("≈ 0", "en el 25 % que más gana")])
                   + tabla(["Percentil", "$/h hombres", "$/h mujeres", "Brecha", "IC 95 %", "Valor p"], filas, num=(1, 2, 3, 4, 5))
                   + nota("Cómo leerlo", "Es un «piso pegajoso»: la desventaja pesa más donde el salario es bajo. Como los ingresos por hora son muy «redondos» ($50, $100), los percentiles saltan de un valor a otro y sus intervalos son irregulares; conviene leerlos como tendencia.", "sencillo"), g=("La brecha se concentra",), sub=o2))

    g_ = lambda dim, cat: sg[(sg.dimension == dim) & (sg.categoria == cat)].iloc[0]  # noqa: E731
    edad = sg[(sg.dimension == "Grupo de edad") & (sg.categoria != "65+")]
    out.append(esc("heterog", 4, "La brecha por hora varía por grupo: es mayor en el empleo informal",
                   F("17_brecha_subgrupos.png", "Brecha por hora por subgrupo (IC 95 %). Punto relleno: significativa con Holm; hueco: no significativa.")
                   + (lista([f"**Informalidad:** {g_('Informalidad', 'Informal').brecha_pct:.1f} % entre informales (significativa) y {g_('Informalidad', 'Formal').brecha_pct:.1f} % entre formales (no significativa).",
                              f"**Región:** de {g_('Región', 'Sur').brecha_pct:.1f} % en el Sur (no significativa) a {g_('Región', 'Centro-Norte').brecha_pct:.1f} % en el Centro-Norte.",
                              f"**Edad:** significativa de los 15 a los 64 años ({edad.brecha_pct.min():.1f} a {edad.brecha_pct.max():.1f} %); a partir de los 65 las muestras son pequeñas.",
                              f"**Posición:** {g_('Posición en la ocupación', 'Subordinado y remunerado').brecha_pct:.1f} % entre subordinados (significativa); empleadores y cuenta propia tienen intervalos amplios y no son significativos con Holm.",
                              f"**Tamaño de localidad:** significativa en todos los tamaños ({sg[sg.dimension == 'Tamaño de localidad'].brecha_pct.min():.1f} a {sg[sg.dimension == 'Tamaño de localidad'].brecha_pct.max():.1f} %)."]))
                   + nota("Cuidado", "Con intervalos tan amplios en algunos subgrupos, hay que evitar conclusiones fuertes sobre diferencias pequeñas entre ellos.", "cuidado"), g=("La brecha por hora varía por grupo",), sub=o2))

    rt_tot = D.rob_tot
    filas = [[i, rt_tot.loc[i, "descripcion"], f"{rt_tot.loc[i, 'brecha_pct']:.1f} %", ic(rt_tot.loc[i, "inf"], rt_tot.loc[i, "sup"]), pval(rt_tot.loc[i, "p"])] for i in rt_tot.index]
    rr = D.robustez_retorno
    out.append(esc("robustez", 4, f"La brecha por hora es positiva en todas las muestras, pero su tamaño va de {D.hora_specs['brecha_pct'].min():.1f} % a {D.hora_specs['brecha_pct'].max():.1f} %",
                   F("13_robustez_brecha.png", "Brecha total bajo diez especificaciones (S3 sesga hacia cero por construcción; S6 es otro estimando).")
                   + tabla(["Especificación", "Qué cambia", "Brecha", "IC 95 %", "p"], filas, num=(2, 3, 4), destacar=(0,))
                   + nota("Lectura honesta", [f"La brecha por hora es positiva en las diez especificaciones; su tamaño depende de ellas. **S3** (imputar el rango) sesga hacia cero porque asigna el mismo ingreso a hombres y mujeres del mismo rango; **S4** (ponderar por no respuesta) la sube a {rt_tot.loc['S4 Ajuste por no respuesta', 'brecha_pct']:.1f} %.",
                                               f"En cambio el rendimiento de la escolaridad es muy estable: de {rr.retorno_pct.min():.1f} a {rr.retorno_pct.max():.1f} % en siete especificaciones."], "sencillo"), g=("La brecha por hora es positiva",), sub=o2))

    # ================================================================= objetivo 3
    o3 = "Objetivo 3 · Informalidad"
    til = D.til1_entidad.sort_values("til1_est", ascending=False)
    sel = pd.concat([til.head(5), til.tail(5)])
    filas = [[f"{int(r.til1_rango)}", r.entidad, r.region, f"{r.til1_est:.1f} %", ic(r.til1_ic_inf, r.til1_ic_sup), f"{int(r.til1_rango_inf)} a {int(r.til1_rango_sup)}"] for r in sel.itertuples()]
    out.append(esc("informalidad", 4, f"La informalidad cae con la escolaridad: de {R['til1']['por_nivel']['1']:.0f} % a {R['til1']['por_nivel']['4']:.0f} %",
                   dos(mosaico(D) + nota("Por qué este mosaico", "Cada estado ocupa la misma área para que los estados grandes no dominen la vista; la escala es de un solo tono y el número está escrito en cada mosaico.", ""),
                       cifras([(f"{f1(D.nac['est'])} %", "informalidad nacional (TIL1)"), (f"{D.mn_til['til1_est']:.0f} → {D.mx_til['til1_est']:.0f} %", f"de {D.mn_til['entidad']} a {D.mx_til['entidad']}"),
                               (f"{R['til1']['por_nivel']['1']:.0f} → {R['til1']['por_nivel']['4']:.0f} %", "de primaria incompleta a media superior o más"), (f"{R['til1']['regiones']['Norte']:.0f} % vs {R['til1']['regiones']['Sur']:.0f} %", "Norte frente a Sur")]))
                   + tabla(["Lugar", "Entidad", "Región", "TIL1", "IC 95 %", "Intervalo del lugar"], filas, num=(0, 3, 4, 5), pie="Las cinco entidades con mayor y menor informalidad. TIL1 = ocupados en empleo informal ÷ ocupados de 15+ (definición del INEGI)."),
                   g=("La informalidad cae con la escolaridad",), sub=o3))

    asoc = D.asoc
    li = D.logit_informalidad.set_index("variable")
    out.append(esc("infvsesc", 4, "Donde se estudia más hay menos informalidad (relación entre estados)",
                   F("15_informalidad_vs_escolaridad.png", "Informalidad laboral y escolaridad promedio de los ocupados de cada entidad.")
                   + cifras([(f"{asoc.loc['rho_spearman_til_esc', 'est']:.2f}", "Spearman entre estados"), (f"{asoc.loc['pendiente_til_esc', 'est']:.1f}", "puntos porcentuales por año de escolaridad promedio"),
                             (f"{li.loc['anios_esc', 'razon_momios']:.2f}", "razón de momios individual por año de escolaridad"), (f"{D.ind['ame_anios_esc_pp']:.1f} pp", "efecto marginal promedio por año (individual)")])
                   + nota("Cuidado", f"La relación entre estados no es un efecto individual. A nivel individual, cada año de escolaridad reduce {100 * (1 - li.loc['anios_esc', 'razon_momios']):.0f} % los momios de tener un empleo informal, y ser mujer los aumenta {100 * (li.loc['mujer', 'razon_momios'] - 1):.0f} % a igual escolaridad y edad.", "cuidado"),
                   g=("Donde se estudia más hay menos informalidad",), sub=o3))

    out.append(esc("tablero", 4, "Tablero interactivo: la ficha de cada entidad",
                   dos(Raw('<figure class="fig"><img src="img/tablero.jpg" alt="Captura del tablero interactivo con indicadores, mapa de mosaicos y ranking de las entidades" loading="lazy" decoding="async">'
                           '<figcaption>Captura del tablero (tablero_enoe.html).</figcaption></figure>'),
                       Raw('<p><a class="btn" href="tablero.html" target="_blank" rel="noopener">Abrir el tablero interactivo</a></p>') + lista(["Selector de entidad y de indicador (informalidad, rendimiento, ingreso mediano, Spearman y brecha).", "Mapa de mosaicos y ranking con intervalos de confianza.",
                                                                                                                                                        "Dos dispersiones, las brechas por nivel y la calidad del ingreso por entidad.", "Tabla accesible con las 32 entidades y el documento JSON que se guardaría en MongoDB."])
                       + nota("Métrica M3", "Seis visualizaciones y una ficha por entidad, alimentadas por la colección `entidades` exportada para MongoDB.", "ok")), g=("Tablero interactivo",), sub="Visualización (métrica M3)"))

    dg = D.dg
    filas = [["R² del modelo OLS", f"{dg['r2_ols']:.3f}", f"Con {dg['p']} parámetros explica 40 % de la variación de ln(ingreso por hora)"], ["Prueba de Breusch-Pagan", f"LM = {dg['breusch_pagan_LM']:,.0f}, p < 0.001", "Varianza no constante: por eso los errores estándar son robustos de diseño"],
             ["VIF máximo", f"{dg['vif_max_variables_clave']:.2f}", "Muy por debajo de 5: sin multicolinealidad problemática"], ["Distancia de Cook máxima", f"{dg['cook_max']:.4f}", "Ninguna observación tiene influencia relevante"],
             ["Cook > 4/n", f"{100 * dg['cook_prop_mayor_4_sobre_n']:.1f} %", f"Sin ellas, el coeficiente de «mujer» pasa de {dg['coef_mujer_con_todo']:.4f} a {dg['coef_mujer_sin_influyentes']:.4f}"],
             ["Residuos", f"asimetría {dg['asimetria_residuos']:.2f}; curtosis en exceso {dg['curtosis_exceso_residuos']:.2f}", "Casi simétricos con colas algo pesadas"]]
    out.append(esc("diagnostico", 4, "Diagnóstico del modelo: varianza no constante y colas pesadas, por eso errores robustos",
                   F("16_diagnosticos_modelo.png", "Residuos contra valores ajustados (izquierda) y gráfico Q-Q de normalidad (derecha) del modelo con todos los controles.")
                   + tabla(["Diagnóstico", "Resultado", "Interpretación"], filas),
                   g=("Diagnóstico del modelo",), sub="Calidad del análisis"))

    # ================================================================= 5 · INTERPRETACIÓN
    hall = [f"**Estudiar paga, y más al final del camino.** {ret} % por año (IC 95 %: {ic_ret}); licenciatura o posgrado, {prem92:.0f} % más que no terminar la primaria.",
            f"**Rinde parecido en estados ricos y pobres** (p = {D.dq['p']:.2f}); los estados más escolarizados pagan más, pero el aumento por año es similar.",
            f"**El ranking de entidades solo es defendible en los extremos:** ρ de {D.rt['rho_min']['rho_est']:.2f} ({D.rt['rho_min']['entidad']}) a {D.rt['rho_max']['rho_est']:.2f} ({D.rt['rho_max']['entidad']}).",
            f"**La brecha de género depende de qué se mida:** {f1(tot['brecha_hora_pct'])} % por hora, {f1(tot['brecha_mens_pct'])} % por mes (mujeres con {f1(tot['menos_horas_mujeres_pct'])} % menos horas) y {D.g5['brecha_pct']:.1f} % entre personas comparables.",
            "**Se concentra abajo y en el empleo informal:** 8.2 % en el P10 y 10.4 % en el P25; 4.3 % entre informales frente a 1.2 % (no significativa) entre formales.",
            "**Las mujeres tienen mejores características, pero a iguales características reciben menos** (6.9 puntos logarítmicos de parte no explicada, que no prueba discriminación).",
            f"**La informalidad es alta, desigual y baja con la escolaridad:** {f1(D.nac['est'])} % nacional; de {D.mn_til['til1_est']:.0f} % a {D.mx_til['til1_est']:.0f} % según la entidad.",
            f"**El «ingreso cero» es un problema de medición:** {D.cero_pond:.0f} % sin monto exacto, pero solo {D.C_t:.0f} % sin ingresos; quien más estudió declara menos."]
    reco = ["**Educación:** reducir el abandono entre la secundaria y la licenciatura (becas, cobertura, transporte) apunta al tramo con mayor rendimiento asociado; el beneficio no es exclusivo de los estados ricos.",
            "**Informalidad:** formalizar el empleo exige considerar la oferta de personas con estudios y la generación de empleos formales en el Sur y el Centro.",
            "**Igualdad de género:** la brecha mensual depende sobre todo de las horas; medidas de cuidado y de trabajo remunerado de jornada completa, y atención a los pisos salariales y la formalización.",
            f"**Medición:** el {D.cero_pond:.0f} % de los ocupados no da un monto exacto de ingreso; mejorar su captación o publicar ajustes por no respuesta aumentaría la precisión."]
    out.append(esc("conclusiones", 5, "Estudiar paga en todas partes; la brecha de género es de horas",
                   dos('<p class="tit-c">Qué encontramos</p>' + lista(hall), '<p class="tit-c">Qué recomendamos (como líneas de reflexión)</p>' + lista(reco)
                       + nota("Cuidado", "Son asociaciones de un trimestre; las implicaciones se formulan con esa cautela y no como evaluación de políticas.", "cuidado")), g=("Estudiar paga en todas partes",)))

    filas = [["M1", "Brecha salarial por nivel de instrucción con IC 95 % y prueba de hipótesis", "Brecha por hora y por mes en los 4 niveles; IC de Rao-Wu; p con Holm; Welch, Mann-Whitney y d de Cohen", si_no_s(True)],
             ["M2", "Spearman en las 32 entidades con IC por bootstrap y ranking defendible", "ρ de 32 entidades con IC y con el intervalo del lugar; el ranking solo distingue los extremos", si_no_s(True)],
             ["M3", "Tablero con 4 o más visualizaciones alimentado por un pipeline a una base NoSQL", "Tablero HTML con 6 visualizaciones y ficha por entidad; documentos MongoDB y agregación verificada contra SQL", Raw('<span class="si">Sí*</span>')]]
    out.append(esc("metricas", 5, "Métricas de éxito del protocolo: las tres se cumplen", tabla(["", "Qué pedía el protocolo", "Evidencia", "Estado"], filas, centro=(3,))
                   + nota("* Salvedad", "La carga a un servidor MongoDB real no se ejecutó (no hay servidor instalado); los documentos están listos para `mongoimport` y la agregación equivalente está verificada.", "cuidado"), g=("Métricas de éxito del protocolo",)))

    lim = [["Correlación, no causalidad", "No se puede afirmar que estudiar un año más *cause* un aumento de 5 %: puede haber habilidad no observada y contexto familiar."], ["Selección en el empleo", "Solo se observa el ingreso de quienes trabajan; no se modeló la participación laboral (corrección de Heckman)."],
           ["Selección en la declaración del ingreso", "Solo se usa a quienes dan monto exacto; se evaluó con imputación, IPW y asalariados, pero puede quedar un sesgo residual."], ["Medición del ingreso", "Autorreportado, redondeado y con las horas de una sola semana (sesgo de división)."],
           ["Un solo trimestre", "Sin tendencias ni estacionalidad."], ["Falacia ecológica", "Las relaciones entre estados no se leen a nivel individual."], ["Precisión por entidad", "Entre 1,900 y 5,900 observaciones salariales por estado; las brechas estatales son solo descriptivas."],
           ["Elementos por verificar", "Los códigos de `p6c` se infirieron de su correspondencia con `ing7c`; las cifras del INEGI se consultaron en una búsqueda web; no se cargó a un MongoDB real."]]
    fut = ["Varios trimestres (panel rotativo) para tendencias y características fijas no observadas.", "Corrección de Heckman para la participación laboral y horas de trabajo no remunerado (Encuesta sobre Uso del Tiempo).", "Ocupación detallada (SINCO) y regresiones cuantílicas.",
           "Mapa geográfico real con el Marco Geoestadístico y estimación en áreas pequeñas.", "Carga a un servidor MongoDB real con una API de consulta."]
    out.append(esc("limites", 5, "Qué no podemos afirmar, y qué haríamos después", dos(tabla(["Límite", "Qué implica"], lim), '<p class="tit-c">Con más tiempo</p>' + lista(fut), "dos--inv"), g=("Qué no podemos afirmar",)))

    tres = ["Cada año de escolaridad se asocia con " + ret + " % más ingreso por hora, con un beneficio mucho mayor en la licenciatura, y el rendimiento es parecido en estados ricos y pobres.",
            f"La brecha de género es de {f1(tot['brecha_hora_pct'])} % por hora y de {f1(tot['brecha_mens_pct'])} % por mes: la diferencia mensual es sobre todo de horas trabajadas.",
            "Los resultados son asociaciones, descritas con intervalos de confianza que respetan el diseño de la encuesta; el trabajo documenta qué se hizo, qué se verificó y qué no."]
    out.append(esc("cierre", 5, "Gracias", '<p class="tit-c">Tres mensajes que todo el equipo debe poder repetir</p>' + pasos(tres)
                   + '<div class="rejilla">' + tarjeta("Para estudiar", p("Glosario, números clave, preguntas de defensa y autoevaluación.") + f'<p>{ir("estudiar", "Ir a Estudiar")}</p>')
                   + tarjeta("Para exponer", p("Reparto, tiempos, lista de verificación y modo presentación.") + f'<p>{ir("exponer", "Ir a Exponer")}</p>')
                   + tarjeta("Para revisar", p("Informe técnico, presentación, cuaderno y tablero.") + f'<p>{ir("descargas", "Ir a Descargas")}</p>') + "</div>", g=("Gracias",)))
    return out


def si_no_s(v: bool) -> Raw:
    return Raw('<span class="si">Sí</span>' if v else '<span class="no">No</span>')
