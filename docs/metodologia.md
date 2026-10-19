# Metodología

Proyecto Integrador de Ciencia de Datos · ENOE 2025 T4 (INEGI) · Equipo 1

Este documento explica **qué se hizo, por qué y con qué supuestos**. Las cifras están en `results/` y en el cuaderno
`notebooks/Proyecto_Integrador_ENOE.ipynb` (versión HTML incluida).

## 1. Diseño general (ciclo KDD)

| Fase KDD | Semana | Qué se hizo | Dónde |
|---|---|---|---|
| Selección | 1 | Elegir SDEMT + COE2T, verificar llave, diseño y cifras oficiales | `extract.py`, `validacion.py` |
| Preprocesamiento | 4 | Cobertura, faltantes codificados, calidad del ingreso, atípicos, 15 expectativas | `clean.py` |
| Transformación | 4 · 6 | Unión 1:1, variables derivadas, imputación por rango, carga a SQLite y documentos | `transform.py`, `load_sqlite.py`, `load_mongo.py` |
| Minería | 2 · 3 · 5 | Estadística ponderada, bootstrap de Rao-Wu, regresión, Oaxaca-Blinder, logit | `survey.py`, `estimadores.py`, `modelos.py`, `analisis.py` |
| Interpretación | 5 | Hallazgos, métricas de éxito, límites | cuaderno, `docs/`, presentación |

## 2. Poblaciones y muestras

| Nombre | Definición | n |
|---|---|---:|
| **Universo** | Ocupados (`clase2 = 1`) de 15+ años, entrevista completa (`r_def = 0`), residentes habituales (`c_res ∈ {1,3}`) | 190,187 |
| **Ventana 15-65** | Universo con `eda ≤ 65` (ventana del protocolo) | 181,198 |
| **Muestra salarial** (análisis principal) | Ventana + monto exacto de ingreso (grupo A) + 1 ≤ horas ≤ 112 + escolaridad y nivel especificados + sin atípicos | 111,958 |
| **Muestra salarial ampliada** (sensibilidad) | Igual, pero grupos A o B (B con ingreso imputado por rango) | 145,529 |

*Por qué 15+:* es la base con la que INEGI publica sus indicadores. Se comprobó que con esa base y `fac_tri` se reproducen 7 cifras oficiales (PEA, participación, ocupación informal, TIL1 nacional y de tres estados); incluir a los 1,078 menores de 15 años ocupados desvía el TIL1 de 55.00 % a 55.27 %.

## 3. Definiciones de las variables de interés

* **Ingreso por hora** = `ingocup / (hrsocup × 4.3)` (4.3 semanas por mes, convención del INEGI; coincide con `ing_x_hrs` con error relativo < 10⁻⁴). Se trabaja con su **logaritmo natural** porque la variable está muy sesgada (asimetría 3.1) y `ln` la vuelve simétrica (0.06); además, diferencias de `ln` son diferencias porcentuales aproximadas.
* **Rendimiento de la escolaridad (Mincer):** coeficiente `β` de `anios_esc` en `ln(ingreso/hora) = α + β·escolaridad + γ₁·edad + γ₂·edad² + δ·mujer + efectos fijos`. Se reporta `100·(exp(β) − 1)` = % de aumento por año.
* **Brecha de género (%)** = `100·(1 − exp(−Δ))`, con `Δ = media_ponderada(ln w | hombres) − media_ponderada(ln w | mujeres)`. Equivale a «las mujeres ganan X % menos que los hombres» comparando ingresos medios geométricos.
* **TIL1** = ocupados con `emp_ppal = 1` ÷ ocupados de 15+, ponderado (definición oficial).

## 4. Calidad del ingreso: cuatro grupos

El archivo reporta `ingocup = 0` en 36 % de los registros. Cruzando `ingocup` con `ing7c` (SDEMT) y `p6c` (COE2T):

| Grupo | Regla | % ponderado (15-65) |
|---|---|---:|
| A | `ingocup > 0` | 61 |
| B | `ingocup = 0` y `ing7c ∈ 1..5` (solo rango de salarios mínimos) | 22 |
| C | `ing7c = 6` (no recibe ingresos; 77 % trabajadores sin pago) | 4 |
| D | `ing7c = 7` (no especificó) | 13 |

La proporción de A **baja con la escolaridad** (69 % → 55 %), así que «solo casos completos» sobrerrepresenta a quienes menos estudiaron. Decisión: el análisis principal usa A y **todo resultado clave se contrasta** con (i) imputación del grupo B, (ii) ponderación inversa a la probabilidad de declarar (IPW) y (iii) solo asalariados.

**Imputación por rangos.** A cada persona del grupo B se le asigna `salario_mínimo_de_su_zona × mediana_ponderada(ingocup/salario)` de quienes dieron monto exacto dentro de ese mismo rango. No se usa el punto medio porque dentro de cada rango la distribución es asimétrica. *Limitación conocida:* asigna el mismo ingreso a hombres y mujeres del mismo rango, por lo que **atenúa por construcción las diferencias entre sexos**; es una cota inferior de la brecha.

**IPW.** Logit ponderado de `P(grupo A | A, B o D)` con sexo, escolaridad, edad, informalidad, posición, rama, entidad y localidad. Se multiplica el ponderador de cada observación A por `1/p̂` (con `p̂` acotada a [0.05, 0.95]).

## 5. Inferencia con el diseño muestral complejo

La ENOE es estratificada y por conglomerados (estrato `est_d_tri` → UPM `upm`). Tratar los datos como muestra aleatoria simple subestima los errores estándar (efecto de diseño ≈ 3–5 en este trimestre).

1. **Estratos con una sola UPM** (11 de 724) se fusionan con el estrato vecino de la misma entidad (*collapsed strata*): 713 estratos finales con ≥ 2 UPM.
2. **Bootstrap de Rao y Wu (1988)** (*rescaled bootstrap*): en cada estrato con `n_h` UPM se remuestrean `n_h − 1` UPM con reemplazo y el ponderador se multiplica por `n_h/(n_h − 1) × (veces que salió la UPM)`. Con `B = 1,000` réplicas y una **única semilla** (`20251231`) para todo el proyecto, de modo que la réplica *b* es el mismo remuestreo en todos los análisis.
3. **Dominios.** Las réplicas se construyen sobre **todas las UPM de la muestra completa**; cada fila de un subconjunto toma el factor de su UPM. Así no se pierde variabilidad cuando una UPM no aporta casos al dominio (error común al filtrar antes de estimar).
4. **Intervalos:** percentil (2.5 %, 97.5 %) de las réplicas. **Pruebas de hipótesis:** Wald bilateral con el error estándar bootstrap (los grados de libertad del diseño, ≈ 20 mil, justifican la aproximación normal).
5. **Modelos de regresión y logit:** estimador de sándwich con **linealización de Taylor** que respeta estratos y UPM (`survey.regresion_diseno`, `survey.logit_diseno`), equivalente a `svy:` de Stata o `survey` de R. Se verificó contra statsmodels (mismos coeficientes; errores equivalentes a HC1 en el caso de m.a.s.).

**Pruebas del método (`tests/test_survey.py`, `tests/test_modelos.py`):** E[factor] = 1; varianza bootstrap = varianza de Taylor (± 8 %); Spearman ponderado = `scipy.stats.spearmanr` con pesos iguales y = datos expandidos con pesos enteros; WLS = statsmodels; identidad exacta de Oaxaca-Blinder; con efecto de conglomerado el error de diseño supera al de m.a.s.

## 6. Estimadores y pruebas

| Objetivo | Estimador | Incertidumbre |
|---|---|---|
| Correlación escolaridad-ingreso por entidad | **Spearman ponderado** = Pearson entre rangos medios ponderados (rango medio de un empate = (W_<  + W_≤)/2) | Bootstrap de Rao-Wu; rango de cada entidad con su intervalo (rango en cada réplica) |
| Rendimiento por entidad | WLS por entidad con edad, edad² y sexo | Bootstrap de Rao-Wu |
| Estados de mayor vs. menor ingreso | Cuartiles de ingreso mediano por hora (**recalculados en cada réplica**); diferencia de rendimiento medio Q4 − Q1 | Bootstrap + Wald |
| Brecha por hora, mensual y de horas por nivel | Diferencia de medias ponderadas de logaritmos | Bootstrap + Wald; **Holm** sobre las 4 pruebas por nivel |
| Pruebas «clásicas» del protocolo | Welch (t) y Mann-Whitney (sin ponderar) por nivel; *d* de Cohen; correlación biserial por rangos | Valores p ajustados por Holm |
| Brecha ajustada | WLS de `ln w` sobre `mujer` con escalera de controles G0–G6 | Sándwich de diseño |
| Descomposición | **Oaxaca-Blinder** con referencia agrupada de Neumark (1988); también con coeficientes de hombres o mujeres | Bootstrap |
| Brecha por percentil | Cuantiles ponderados por sexo; diferencia en P10…P90 | Bootstrap |
| Informalidad | TIL1 ponderado (nacional, sexo, región, nivel, entidad); asociación entre estados (Pearson, Spearman, pendiente); logit individual ponderado y efecto marginal promedio | Bootstrap / sándwich |
| No respuesta | Logit ponderado `A vs resto` y `D vs resto` | Sándwich de diseño |

**Tamaño de efecto.** Con 112 mil observaciones casi toda diferencia es «significativa»; por eso se reportan *d* de Cohen y la brecha en %.
**Corrección por multiplicidad.** Holm (1979) controla la tasa de error por familia (los 4 niveles; las categorías de cada dimensión de heterogeneidad). Los 32 intervalos por entidad no se prueban uno a uno: se reporta el ranking con su incertidumbre.

## 7. Sesgo de división y por qué no se interpreta el modelo G6

El ingreso por hora es ingreso mensual ÷ horas. Cualquier error de medición en las horas crea una relación negativa **mecánica** entre `ln(ingreso/hora)` y `ln(horas)`: controlar por horas infla la brecha (de ≈ 8 % a 16 %) y la «parte explicada» por horas (−11 puntos). Por eso **G6 y la descomposición «con horas» se muestran solo por transparencia**, y la estimación de referencia de «personas parecidas» es G5 (8.2 %), sin horas.
La brecha **mensual** sí se interpreta, con la identidad exacta en logaritmos: *brecha mensual = brecha por hora + brecha de horas*.

## 8. Decisiones del analista y su sensibilidad

| Decisión | Valor | Sensibilidad |
|---|---|---|
| Ventana de edad | 15-65 (protocolo); 15+ para informalidad (base oficial) | — |
| Horas válidas | 1 ≤ h ≤ 112 | 41 casos > 112 |
| Atípicos | Fuera de P0.5-P99.5 del ingreso por hora de su entidad | S1 «sin recorte»: brecha 3.6 % vs 3.7 %; rendimiento 5.4 % vs 5.1 % |
| Tratamiento del ingreso faltante | Grupo A | S3 (imputación), S4 (IPW), S2 (asalariados) |
| Estratos con 1 UPM | Se fusionan con el vecino | — |
| Réplicas bootstrap | 1,000 | La semilla es única y fija |
| Nivel detallado | Se parte el nivel 4 con `anios_esc` (12-15 / 16+) | Resultados por subnivel en `brecha_subgrupos.csv` |

## 9. Validación y control de calidad

* **15 expectativas** de datos verificadas por el pipeline (llave única, rangos, `ing7c` vs `ingocup/salario`, `ing_x_hrs`, `p6c` vs `ing7c`, `ingocup` vs `p6b2`...).
* **Validación externa:** 7 de 7 cifras del INEGI.
* **Pruebas automáticas:** `python -m unittest discover -s tests` (unitarias, de método y de integración sobre la base real).
* **Reproducibilidad:** una semilla, versiones registradas en `results/etl_meta.json`, huellas SHA-256 de los archivos de origen, ETL idempotente.

## 10. Limitaciones

Correlación y no causalidad (sesgo de habilidad); selección en el empleo y en la declaración del ingreso; ingreso autorreportado con redondeo; ingreso por hora basado en las horas de *una* semana; un solo trimestre; relaciones entre estados (falacia ecológica); precisión limitada por entidad (1,900–5,900 observaciones salariales); significado literal de los códigos de `p6c` inferido de su correspondencia exacta con `ing7c`.

## 11. Referencias

* Rao, J. N. K., y Wu, C. F. J. (1988). Resampling inference with complex survey data. *Journal of the American Statistical Association*, 83(401), 231-241.
* Lumley, T. (2010). *Complex Surveys: A Guide to Analysis Using R*. Wiley.
* Kish, L. (1965). *Survey Sampling*. Wiley.
* Mincer, J. (1974). *Schooling, Experience, and Earnings*. NBER.
* Oaxaca, R. (1973). Male-female wage differentials in urban labor markets. *International Economic Review*, 14(3), 693-709. · Blinder, A. S. (1973). Wage discrimination: reduced form and structural estimates. *Journal of Human Resources*, 8(4), 436-455.
* Neumark, D. (1988). Employers' discriminatory behavior and the estimation of wage discrimination. *Journal of Human Resources*, 23(3), 279-295. · Jann, B. (2008). The Blinder-Oaxaca decomposition for linear regression models. *The Stata Journal*, 8(4), 453-479.
* Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65-70.
* INEGI. Encuesta Nacional de Ocupación y Empleo (ENOE), población de 15 años y más: metodología, descriptor de archivos y tabulados. <https://www.inegi.org.mx/programas/enoe/15ymas/>
