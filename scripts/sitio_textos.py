"""Textos compartidos del sitio: justificación de cada gráfico, texto alternativo y recortes de las figuras."""

# Recorte (pulgadas a 200 dpi) del encabezado y del pie de cada figura: el sitio ya dice el titular y la fuente en texto.
RECORTES = {
    "01_embudo_datos.png": (0.62, 0.2), "02_calidad_ingreso.png": (0.62, 0.2), "03_distribucion_ingreso.png": (0.62, 0.2),
    "04_ingreso_por_escolaridad.png": (0.62, 0.2), "05_retorno_estados.png": (0.74, 0.2), "06_spearman_estados.png": (0.74, 0.2),
    "07_escolaridad_vs_ingreso_estatal.png": (0.62, 0.2), "08_cajas_nivel_sexo.png": (0.62, 0.2), "09_brecha_por_nivel.png": (0.62, 0.2),
    "10_escalera_controles.png": (0.62, 0.2), "11_oaxaca_blinder.png": (0.62, 0.2), "12_brecha_cuantiles.png": (0.55, 0.2),
    "13_robustez_brecha.png": (0.62, 0.2), "14_mapa_informalidad.png": (0.62, 0.2), "15_informalidad_vs_escolaridad.png": (0.62, 0.2),
    "16_diagnosticos_modelo.png": (0.62, 0.2), "17_brecha_subgrupos.png": (0.62, 0.24),
}
DIAGRAMAS = ["D01_kdd.png", "D02_arquitectura.png", "D03_esquema_estrella.png", "D04_diseno_muestral.png", "D05_rao_wu.png", "D06_como_leer_ic.png",
             "D07_oaxaca_idea.png", "D08_spearman_ejemplo.png"]

# «Por qué este gráfico»: la guía de la maestra pide gráficos justificados y honestos. Cada texto dice por qué se eligió el tipo de gráfico
# y qué decisiones lo vuelven honesto (eje desde cero, intervalos visibles, escala explícita, sin ejes duales, paleta apta para daltonismo).
PORQUE = {
    "01_embudo_datos.png": "Barras horizontales porque comparan cantidades del mismo tipo (registros) y los nombres largos caben mejor. El eje parte de cero, así que la longitud de cada barra es proporcional a la cantidad.",
    "02_calidad_ingreso.png": "Los cuatro grupos suman 100 %, así que se muestran como partes de un todo en barras apiladas. Cada barra es una población (total, sexo, nivel) y se comparan sus composiciones; todas llevan el porcentaje escrito y los colores se distinguen también en escala de grises.",
    "03_distribucion_ingreso.png": "El histograma muestra la forma de la distribución. Dos paneles lado a lado (pesos y logaritmo) enseñan por qué el ingreso se transforma: la cola larga de la izquierda casi desaparece en la derecha. Las alturas están ponderadas con el factor de expansión.",
    "04_ingreso_por_escolaridad.png": "La escolaridad es una variable ordenada, así que se usa una línea. El eje del ingreso es logarítmico (y está rotulado así) porque el ingreso cambia en proporciones. Solo se grafican celdas con al menos 60 observaciones para no dibujar ruido, y hombres y mujeres usan colores validados para daltonismo.",
    "05_retorno_estados.png": "Un punto con su intervalo de confianza por entidad, ordenadas de mayor a menor: la incertidumbre es parte del mensaje, y las barras (que sugieren una precisión que no existe) se evitaron. El color indica el cuartil de ingreso del estado para comparar ricos y pobres.",
    "06_spearman_estados.png": "Mismo diseño de puntos con intervalos. A la derecha se escribe el lugar de cada entidad en el ranking con su propio intervalo, para que se vea que solo los extremos se distinguen.",
    "07_escolaridad_vs_ingreso_estatal.png": "Una dispersión relaciona dos variables continuas; cada punto es una entidad, y la línea resume la tendencia. Solo se rotulan los puntos notables para no saturar. Es una relación entre estados, no un efecto individual.",
    "08_cajas_nivel_sexo.png": "Las cajas comparan distribuciones completas y no solo promedios: la caja cubre del percentil 25 al 75, la raya blanca es la mediana y los bigotes van del 10 al 90. El eje es logarítmico.",
    "09_brecha_por_nivel.png": "Las barras parten de cero porque la brecha es una magnitud. Llevan su intervalo de confianza y los dos paneles (por hora y por mes) comparten la misma escala, así que la diferencia de altura es real y no un efecto del eje.",
    "10_escalera_controles.png": "Muestra cómo cambia la estimación al agregar controles uno por uno: un punto con intervalo por modelo, todos en la misma escala. El último modelo (con horas) está marcado porque no se interpreta.",
    "11_oaxaca_blinder.png": "Barras divergentes que parten de cero: las rojas aumentan la brecha y las azules la reducen. Cada una trae su intervalo de confianza y la leyenda dice qué significa cada color.",
    "12_brecha_cuantiles.png": "Los percentiles son una secuencia ordenada, así que se usa una línea, con una banda para el intervalo de confianza y una referencia en cero. Así se ve de inmediato dónde la banda cruza el cero y la brecha deja de ser demostrable.",
    "13_robustez_brecha.png": "Un punto con intervalo por cada decisión metodológica, todos en la misma escala. La estimación de ingreso mensual va en gris porque mide otra cosa, y la que imputa rangos está anotada porque sesga hacia cero por construcción.",
    "14_mapa_informalidad.png": "Un cartograma de mosaicos: cada estado ocupa la misma área, para que los estados grandes no dominen la vista. La escala es de un solo tono (azules), con el número escrito en cada mosaico, y se lee bien con daltonismo.",
    "15_informalidad_vs_escolaridad.png": "Dispersión con recta de ajuste: cada punto es una entidad. Sirve para ver la relación entre estados y se acompaña de la advertencia de que no es un efecto individual.",
    "16_diagnosticos_modelo.png": "Residuos contra valores ajustados en hexágonos (hexbin) porque miles de puntos se encimarían y taparían la forma; el gráfico Q-Q compara los residuos con la normal. Son diagnósticos, no resultados.",
    "17_brecha_subgrupos.png": "Un punto con intervalo por subgrupo. El punto relleno indica significativo tras la corrección de Holm y el hueco, no significativo, así que la significancia se lee sin una tabla aparte.",
}

ALT = {
    "01_embudo_datos.png": "Barras horizontales del embudo de registros: de 419,038 registros crudos a 111,958 observaciones salariales.",
    "02_calidad_ingreso.png": "Barras apiladas por población (total, sexo y nivel de instrucción) con el porcentaje que declara monto exacto, solo rango, no recibe ingresos o no especificó.",
    "03_distribucion_ingreso.png": "Dos histogramas del ingreso por hora: en pesos con cola larga a la derecha y en logaritmo natural, casi simétrico.",
    "04_ingreso_por_escolaridad.png": "Líneas de la mediana ponderada del ingreso por hora según los años de escolaridad, para hombres y mujeres, en escala logarítmica.",
    "05_retorno_estados.png": "Puntos con intervalos de confianza del rendimiento por año de escolaridad en cada entidad, coloreados por cuartil de ingreso estatal.",
    "06_spearman_estados.png": "Puntos con intervalos de confianza del Spearman por entidad y su lugar en el ranking con intervalo.",
    "07_escolaridad_vs_ingreso_estatal.png": "Dispersión de la escolaridad promedio contra el ingreso mediano por hora de las 32 entidades, con recta de ajuste.",
    "08_cajas_nivel_sexo.png": "Cajas de ln(ingreso por hora) por nivel de instrucción y sexo.",
    "09_brecha_por_nivel.png": "Dos paneles de barras con intervalos: brecha de género por hora y por mes, por nivel de instrucción y total.",
    "10_escalera_controles.png": "Puntos con intervalos de la brecha por hora al agregar controles sucesivos.",
    "11_oaxaca_blinder.png": "Barras con intervalos de la descomposición de Oaxaca-Blinder: brecha total, parte explicada por componentes y parte no explicada.",
    "12_brecha_cuantiles.png": "Línea con banda de intervalo de la brecha de género en los percentiles 10 a 90 del ingreso por hora.",
    "13_robustez_brecha.png": "Puntos con intervalos de la brecha total bajo diez especificaciones.",
    "14_mapa_informalidad.png": "Cartograma de mosaicos con la tasa de informalidad laboral de cada entidad.",
    "15_informalidad_vs_escolaridad.png": "Dispersión de la escolaridad promedio contra la tasa de informalidad de las 32 entidades con su recta de ajuste.",
    "16_diagnosticos_modelo.png": "Residuos contra ajustados (hexbin) y gráfico Q-Q de normalidad del modelo con todos los controles.",
    "17_brecha_subgrupos.png": "Puntos con intervalos de la brecha por hora en subgrupos de informalidad, posición, región, tamaño de localidad y edad.",
    "D01_kdd.png": "Las cinco fases del ciclo KDD y qué se hizo en cada una.",
    "D02_arquitectura.png": "Arquitectura del proyecto: de los microdatos del INEGI al ETL, SQLite, el análisis, los resultados, MongoDB y el tablero.",
    "D03_esquema_estrella.png": "Esquema en estrella: la tabla de hechos fact_ocupado rodeada de diez tablas de dimensiones.",
    "D04_diseno_muestral.png": "Niveles del diseño muestral (estrato, UPM, vivienda, persona) y significado del factor de expansión.",
    "D05_rao_wu.png": "El bootstrap de Rao-Wu en cuatro pasos con un estrato de cuatro unidades primarias de muestreo.",
    "D06_como_leer_ic.png": "Tres intervalos de confianza reales del proyecto: uno que excluye el cero, uno que lo toca y uno que lo incluye.",
    "D07_oaxaca_idea.png": "Idea de la descomposición de Oaxaca-Blinder: brecha total igual a parte explicada más parte no explicada.",
    "D08_spearman_ejemplo.png": "Ejemplo con seis personas: valores originales a la izquierda y rangos a la derecha, con Spearman igual a 0.93.",
}
