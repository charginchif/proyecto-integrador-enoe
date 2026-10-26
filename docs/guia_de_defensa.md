# Guía de defensa: preguntas probables y respuestas

Para la exposición del proyecto integrador. Las cifras vienen de `results/resumen.json` y del cuaderno. **Entiendan la lógica de cada respuesta; no las memoricen.**

## A. Datos y limpieza

**1. ¿Por qué ese dataset y cómo saben que está bien leído?**
ENOE 4T-2025 del INEGI: 419,038 registros, fuente oficial, con «suciedad» real y diccionario. Se validó contra el INEGI: con la base oficial (ocupados de 15+, `fac_tri`) se reproducen **7 de 7 cifras publicadas** (PEA 61.3 M, participación 59.3 %, informales 32.9 M, TIL1 55.0 % y los TIL1 de Chiapas, Chihuahua y CDMX). Si hubiéramos incluido a los menores de 15 años, el TIL1 sería 55.27 % y *no* coincidiría.

**2. ¿Qué limpieza hicieron y por qué esas reglas?**
Cobertura (entrevista completa, residente habitual, 15+, ocupado) elimina filas; todo lo demás (faltantes codificados, calidad del ingreso, atípicos) **crea banderas**, para poder hacer análisis de sensibilidad sin volver a limpiar. Cada regla es una función probada y queda en una bitácora (embudo de 419 mil a 112 mil).

**3. «No hay nulos» en la ENOE, ¿entonces qué limpiaron?**
Los faltantes vienen **codificados como valores reales**: escolaridad 99 (610 casos), horas 0 (5,278 ocupados ausentes) o > 112 horas (41 casos imposibles). Un `isna()` diría que todo está completo.

**4. ¿Qué es el «ingreso cero» y por qué importa?**
El 36 % de los registros tiene `ingocup = 0`, pero no es «sin ingreso»: 22 % (ponderado) solo da un **rango de salarios mínimos**, 13 % no especifica y solo 4 % realmente no recibe ingresos. Además, **quien más estudió declara menos el monto exacto** (55 % vs. 69 %): los datos faltan de forma no aleatoria. Por eso contrastamos con imputación por rango, IPW y solo asalariados.

**5. ¿Por qué recortan atípicos en P0.5–P99.5 por entidad?**
El ingreso por hora va de $0.03 a $11,628. Recortar dentro de cada entidad respeta que el costo de vida y los salarios difieren por estado. Es 1 % de la muestra y el resultado casi no cambia sin recorte (brecha 3.6 % vs. 3.7 %; rendimiento 5.4 % vs. 5.1 %).

## B. Estadística

**6. ¿Por qué ponderan con `fac_tri` y por qué bootstrap de Rao-Wu?**
Cada persona representa a `fac_tri` personas; sin ponderar describiríamos la muestra, no el país. Y como la ENOE es por conglomerados, los errores estándar «normales» son demasiado pequeños: el **efecto de diseño es ≈ 3–5** (190 mil ocupados valen como ≈ 40 mil independientes). Rao-Wu remuestrea UPM dentro de estratos y reescala ponderadores; verificamos que reproduce la varianza de Taylor.

**7. ¿Por qué logaritmo del ingreso?**
Porque el ingreso por hora tiene asimetría 3.1 y el logaritmo la vuelve simétrica (0.06); además una diferencia de logaritmos es una diferencia porcentual aproximada.

**8. ¿Spearman o Pearson?**
Spearman: mide asociación monótona, robusta a atípicos y a la forma de la relación; la escolaridad tiene muchos empates (se usan rangos medios ponderados). Con pesos iguales coincide con `scipy`.

**9. ¿Qué significa «ranking defendible»?**
Que se reporta con incertidumbre: cada estado tiene un intervalo del lugar que ocupa (por bootstrap). La CDMX es 1.º con seguridad (1-2), Baja California Sur está entre los últimos (23-32), pero estados del centro del ranking tienen intervalos de 15+ lugares y **no se pueden distinguir**.

**10. ¿Por qué Holm y no Bonferroni?**
Holm controla la misma tasa de error por familia pero es uniformemente más potente. Se aplica a las 4 pruebas por nivel de instrucción.

**11. Con 112 mil observaciones todo sale significativo; ¿entonces?**
Por eso se reporta el **tamaño**: la *d* de Cohen es pequeña (0.06–0.24) y la brecha es 3.7 % por hora. «Significativo» ≠ «grande».

**12. ¿Por qué hay Welch y Mann-Whitney *y* el método de diseño?**
El protocolo pedía las pruebas clásicas (sin ponderar) y coinciden en las conclusiones; pero la inferencia **correcta** para la población es la que usa el diseño. Se muestran las dos.

## C. Resultados

**13. ¿Cuánto rinde un año de escolaridad?**
≈ **5.1 %** más ingreso por hora (IC 95 %: 5.0–5.3) controlando edad, sexo y entidad; ≈ 3.8 % si además se controla el tipo de empleo (parte del beneficio pasa por conseguir un mejor empleo). Es **robusto**: 4.9–5.7 % en siete especificaciones. No es lineal: licenciatura o posgrado paga **+92 %** frente a no terminar primaria.

**14. ¿Estudiar rinde más en estados ricos?**
No: la diferencia entre el cuarto cuartil y el primero es ≈ 0 (p = 0.91). El *nivel* de ingreso sí difiere (estados más escolarizados pagan más: ρ = 0.74 entre estados), pero el *rendimiento por año* es parecido.

**15. ¿Hay brecha de género?**
Sí, **pero depende de qué mides**: por hora 3.7 % (IC 2.3–5.0, p < 0.001); por nivel 8.4 / 10.1 / 7.6 / 3.9 %, las cuatro significativas tras Holm; por **mes 26.9 %**. La diferencia mensual es de **horas** (las mujeres trabajan 24 % menos), no de pago por hora. Entre personas comparables, 8.2 %.

**16. ¿Qué es la parte «no explicada» de Oaxaca-Blinder?**
Parte de la brecha que **no** se explica por las características medidas (escolaridad, edad, lugar, empleo, rama). Aquí las mujeres tienen *mejores* características (más escolaridad) pero la misma paga o menos, así que el residuo es mayor (6.9 puntos) que la brecha total (3.8). **No prueba discriminación**: incluye lo no observado.

**17. ¿Por qué no interpretan el modelo con horas (G6)?**
Por el **sesgo de división**: el ingreso por hora es ingreso ÷ horas, así que un error en las horas crea una relación negativa mecánica y la brecha «sube» a 16 % artificialmente. Se muestra por transparencia.

**18. ¿Por qué S3 da 0.7 % si las demás dan más?**
Imputar el grupo B con la mediana del rango le asigna **el mismo ingreso a un hombre y a una mujer**, borrando diferencias dentro del rango: sesga hacia cero por construcción; es una cota inferior. La conclusión honesta es: la brecha por hora es positiva pero su tamaño depende de la muestra (0.7–4.6 %); la ajustada (≈ 8 %) y la mensual (≈ 27 %) son sólidas.

**19. ¿Dónde está la brecha?**
Abajo: 8.2 % en el P10 y 10.4 % en el P25; en la mediana es 2.1 % (no significativa) y arriba es nula o favorece a las mujeres («piso pegajoso»).

**20. ¿Qué hallazgo sobre informalidad?**
TIL1 nacional 55.0 %; de 33 % (Coahuila) a 80 % (Oaxaca); 87 % entre quienes no terminaron primaria vs. 38 % con medio superior/superior. Entre estados ρ = −0.86; a nivel individual cada año de escolaridad baja ≈ 3.9 puntos la probabilidad; ser mujer suma ≈ 6 puntos.

**21. ¿Es causal?**
No. Es asociación: hay sesgo de habilidad no observada y selección. Y las relaciones entre estados no deben leerse a nivel individual (falacia ecológica).

## D. Ingeniería de datos y NoSQL

**22. ¿Por qué SQLite *y* MongoDB?**
Persistencia políglota por **patrón de acceso**: análisis (agregaciones ponderadas, JOIN, integridad) → relacional; servir la ficha de una entidad (un documento por clave, esquema flexible) → documental. SQLite es la fuente de verdad; Mongo es una vista de lectura que se regenera.

**23. ¿Por qué embeben los indicadores en `entidades` pero no las personas?**
Los indicadores se leen siempre junto con la entidad (una lectura, sin JOIN). Las 190 mil personas no caben en un documento (límite de 16 MB) ni se leen con la entidad: colección aparte relacionada por `cve_ent`.

**24. ¿Cargaron a un servidor MongoDB real?**
No: en la máquina de desarrollo no hay un servidor MongoDB. Se exportaron los documentos (NDJSON listos para `mongoimport`), la carga completa se probó contra **mongomock** (un simulador en memoria; imita la API pero no es MongoDB) y se **verificó que la agregación ejecutada en el motor reproduce la vista SQL** (diferencia 0.005 pp). Con un servidor, `python scripts/run_mongo.py --uri …` hace la carga y las mismas verificaciones (ver `docs/modelo_de_datos_nosql.md`).

**25. ¿Cómo garantizan la reproducibilidad?**
Una sola semilla (20251231), versiones y huellas SHA-256 en `etl_meta.json`, ETL idempotente, pruebas automáticas (`python -m unittest discover -s tests`) y el cuaderno se reconstruye desde `results/` con aserciones que avisan si una conclusión deja de ser cierta.

## E. Preguntas incómodas

**26. ¿Qué limitaciones tiene su trabajo?**
Un trimestre; ingreso autorreportado con redondeo; ingreso por hora a partir de las horas de *una* semana; selección en el empleo; no causalidad; 1,900–5,900 observaciones por estado; y la redacción literal de los códigos de `p6c` se infirió de su correspondencia exacta con `ing7c` (conviene confirmarla con el cuestionario).

**27. ¿Qué harían con más tiempo?**
Usar varios trimestres (panel rotativo), modelar la participación laboral (corrección de Heckman), un mapa geográfico real con el Marco Geoestadístico, y estimaciones para áreas pequeñas.

**28. ¿Qué parte es tuya?** *(prepárenla ustedes)* Roles propuestos: ingeniería de datos y pipeline · análisis estadístico · visualización y comunicación. Cada integrante debe poder explicar al menos una sección del cuaderno de principio a fin.
