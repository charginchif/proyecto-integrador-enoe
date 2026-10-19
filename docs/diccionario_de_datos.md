# Diccionario de datos

Proyecto Integrador de Ciencia de Datos · ENOE 2025 T4 (INEGI) · Equipo 1

> Los códigos que INEGI documenta en el «descriptor de archivos» **se verificaron contra los propios
> microdatos** (sección 6). Donde la verificación fue solo empírica (no contra el cuestionario oficial) se indica.

## 1. Fuente

| Elemento | Valor |
|---|---|
| Encuesta | Encuesta Nacional de Ocupación y Empleo (ENOE), población de 15 años y más |
| Periodo | 4.º trimestre de 2025 (sufijo de archivo `425`) |
| Publica | INEGI · <https://www.inegi.org.mx/programas/enoe/15ymas/> (Microdatos / Datos abiertos) |
| Formato | CSV, codificación `latin-1`, una fila por unidad de observación |
| Diseño | Probabilístico, bietápico, estratificado y por conglomerados (estrato `est_d_tri` → UPM `upm` → vivienda → persona) |
| Ponderador | `fac_tri` (factor de expansión trimestral; suma ≈ 131 millones de personas) |

### Archivos del paquete

| Tabla | Filas | Cols. | Uso en el proyecto |
|---|---:|---:|---|
| `SDEMT` (sociodemográfica y laboral) | 419,038 | 115 | **Principal.** Una fila por residente del hogar, todas las edades. Se leen 35 columnas |
| `COE2T` (cuestionario de ocupación, parte 2) | 344,166 | 84 | **Complementaria.** Detalle de captación del ingreso (`p6b1`, `p6b2`, `p6c`). Se une 1 a 1 con SDEMT |
| `COE1T`, `HOGT`, `VIVT` | — | — | No se usan (no aportan variables al problema de investigación) |

### Llave de persona (verificada)

`cd_a, cve_ent, con, upm, d_sem, n_pro_viv, v_sel, n_hog, h_mud, n_ent, n_ren`

Es **única en SDEMT y en COE2T (0 duplicados)** y los 190,187 ocupados de SDEMT encuentran su pareja en COE2T (100 %).
La llave de 7 campos que se cita habitualmente (`cd_a, ent, con, v_sel, n_hog, h_mud, n_ren`) **no** es única en este trimestre
(8,371 duplicados): hay que agregar `n_pro_viv`, y por seguridad `upm`, `d_sem` y `n_ent`.
En la base se concatena como `persona_id`.

## 2. Variables de origen utilizadas

| Variable | Tabla | Descripción | Valores / unidades |
|---|---|---|---|
| `r_def` | SDEMT | Resultado definitivo de la entrevista | 0 = completa (418,146); 15 = incompleta (892, sin clasificar) |
| `c_res` | SDEMT | Condición de residencia | 1 = residente habitual; 3 = residente definitivo; **2 = nuevo residente** (10,065 filas con sexo y edad en blanco, sin clasificar) |
| `cve_ent` | SDEMT | Entidad federativa | 1–32 (catálogo INEGI) |
| `upm`, `est_d_tri` | SDEMT | Unidad primaria de muestreo y estrato de diseño trimestral | 21,194 UPM en 724 estratos; las UPM no cruzan estratos ni entidades |
| `fac_tri` | SDEMT | Ponderador trimestral | > 0 en todos los ocupados |
| `t_loc_tri`, `ur` | SDEMT | Tamaño de localidad / urbano-rural | 1 = ≥100 mil hab., 2 = 15 mil–99,999, 3 = 2,500–14,999, 4 = <2,500 |
| `zona`, `salario` | SDEMT | Zona salarial y salario mínimo **mensual** (pesos) | 8,364 (zona general, 278.80 × 30) / 12,596 (frontera norte, 419.88 × 30) |
| `sex` | SDEMT | Sexo | 1 = hombre, 2 = mujer (en blanco solo cuando `c_res` = 2) |
| `eda` | SDEMT | Edad en años | 0–98; 99 = no especificado (56 filas, ninguna ocupada) |
| `niv_ins` | SDEMT | Nivel de instrucción | 1 primaria incompleta · 2 primaria completa · 3 secundaria completa · 4 medio superior y superior · 5 no especificado |
| `anios_esc` | SDEMT | Años de escolaridad aprobados | 0–24; **99 = no especificado** |
| `clase1`, `clase2` | SDEMT | Condición de actividad | `clase1` = 1 → PEA; `clase2` = 1 → ocupada, 2 desocupada, 3 disponible, 4 no disponible |
| `pos_ocu` | SDEMT | Posición en la ocupación | 1 subordinado remunerado · 2 empleador · 3 cuenta propia · 4 sin pago |
| `emp_ppal` | SDEMT | Empleo informal en la ocupación principal | 1 = informal, 2 = formal (0 = no aplica) |
| `rama_est2` | SDEMT | Gran rama de actividad (11 + no especificado) | ver `config.RAMA_EST2` |
| `hrsocup` | SDEMT | Horas trabajadas la semana pasada | 0–168; 0 en 5,278 ocupados (ausentes del trabajo) |
| `ingocup` | SDEMT | Ingreso mensual de la ocupación principal (pesos) | 0 si no hay monto exacto; máx. 250,000 |
| `ing_x_hrs` | SDEMT | Ingreso por hora (pesos) | `ingocup / (hrsocup × 4.3)`; 0 si no se puede calcular |
| `ing7c` | SDEMT | Ingreso en salarios mínimos | 1 ≤1 SM · 2 (1,2] · 3 (2,3] · 4 (3,5] · 5 >5 · 6 no recibe · 7 no especificó |
| `p6b1` | COE2T | Forma de captación del monto | no se usa en el análisis |
| `p6b2` | COE2T | Monto mensual declarado | idéntico a `ingocup` cuando `ingocup > 0` |
| `p6c` | COE2T | Rango de salarios mínimos cuando no hubo monto exacto | 1–7 rangos, 8 no sabe, 9 no respondió |

## 3. Variables derivadas

| Variable | Definición |
|---|---|
| `persona_id` | `ent-upm-d_sem-n_pro_viv-v_sel-n_hog-h_mud-n_ent-n_ren-cd_a-con` |
| `mujer` | 1 si `sex = 2` |
| `eda_c`, `eda_c2` | `eda − 40` y `(eda − 40)² / 100` (centrado para reducir la colinealidad entre edad y edad²) |
| `grupo_edad` | 15-24, 25-34, 35-44, 45-54, 55-64, 65+ |
| `informal` | 1 si `emp_ppal = 1` |
| `niv_det` | `niv_ins` 1-3 igual; el nivel 4 se parte en **4 = media superior / superior trunca (12–15 años)** y **5 = licenciatura o posgrado (≥16 años)** |
| `anios_esc` (limpia) | `anios_esc` con 99 → NaN (610 ocupados) |
| `hrsocup` (limpia) | NaN si `hrsocup = 0` (5,278) o `> 112` (41); se conserva `hrsocup_raw` |
| `grupo_ingreso` | **A** monto exacto (`ingocup > 0`) · **B** solo rango (`ingocup = 0`, `ing7c` 1–5) · **C** no recibe (`ing7c` = 6) · **D** no especificó (`ing7c` = 7) |
| `ing_mensual`, `ing_hora`, `ln_ing_hora` | solo grupo A; `ing_hora = ingocup / (hrsocup × 4.3)` |
| `ing_mensual_imp`, `ing_hora_imp` | A = observado; B = `salario × mediana(ingocup/salario)` de quienes ganan en ese mismo rango; C y D = vacío (análisis de sensibilidad) |
| `outlier_ing_hora` | `ln(ing_hora)` fuera de [P0.5, P99.5] de su entidad |
| `en_ventana_15_65` | 15 ≤ edad ≤ 65 |
| `en_muestra_salarial` | grupo A, horas válidas, escolaridad y nivel especificados, 15–65 años y sin atípicos |
| `en_muestra_salarial_ext` | igual, pero grupos A **o** B (con ingreso imputado) |

## 4. Esquema relacional (SQLite)

Archivo `data/processed/enoe_2025t4.sqlite`. Modelo en estrella:

* **Hechos:** `fact_ocupado` (190,187 filas: ocupados de 15+).
* **Dimensiones:** `dim_entidad`, `dim_sexo`, `dim_nivel_instruccion`, `dim_nivel_detalle`, `dim_posicion_ocupacion`, `dim_rama`,
  `dim_tamano_localidad`, `dim_ing7c`, `dim_grupo_ingreso`, `dim_upm` (21,194 UPM con su estrato original y colapsado).
* **Vistas:** `v_til_entidad`, `v_escolaridad_entidad`, `v_calidad_ingreso_entidad`, `v_muestra_salarial`.
* **Auditoría:** `etl_bitacora`, `etl_embudo_salarial`, `etl_expectativas`, `etl_validacion_externa`, `etl_umbrales_atipicos`, `etl_imputacion_rangos`, `etl_run`.
* **Resultados del análisis:** tablas `res_*` (una por cada CSV de `results/`).

Restricciones: llaves primarias y foráneas (se activan con `PRAGMA foreign_keys = ON`), `CHECK` de rangos válidos
(`fac_tri > 0`, `eda BETWEEN 15 AND 98`, `emp_ppal IN (1,2)`, ...). Verificación al cargar: `integrity_check = ok`, 0 violaciones de llave foránea.

## 5. Valores especiales y decisiones de limpieza

| Situación | Tratamiento |
|---|---|
| La ENOE no tiene celdas vacías (0 % de nulos) | Los faltantes vienen como códigos válidos (`99`, `0`, `9`); se recodifican a nulo |
| `r_def = 15` o `c_res = 2` | Se excluyen (no tienen datos analizables); coincide con el filtro oficial |
| Menores de 15 años ocupados (1,078 en la muestra) | Se excluyen: INEGI publica sus indicadores para 15+. Incluirlos sube el TIL1 de 55.00 % a 55.27 % |
| `hrsocup = 0` en ocupados | No hay ingreso por hora; se excluyen del análisis salarial (siguen en el universo) |
| `hrsocup > 112` | Jornada imposible (16 h × 7 días): se marca como no válida |
| Ingreso 0 | Se separa en A/B/C/D; el análisis principal usa A (ver `docs/metodologia.md`) |
| Ingreso por hora atípico | Se recorta P0.5–P99.5 dentro de cada entidad (≈ 1 % de la muestra con monto exacto) |
| Heaping | Los montos se concentran en cifras redondas (p. ej. 5,000 o 10,000); no se corrige |

## 6. Verificación empírica de códigos

| Comprobación | Resultado |
|---|---|
| `ing_x_hrs = ingocup / (hrsocup × 4.3)` | Máxima diferencia relativa 7.3 × 10⁻⁵ |
| Intervalos de `ing7c` en múltiplos de `salario` (grupo A) | 100 % de los registros dentro de su intervalo (≤1, (1,2], (2,3], (3,5], >5) |
| `p6c` de COE2T reproduce `ing7c` de SDEMT (grupo B) | 100 % de 36,438 registros (p6c 1 y 2 → 1; 3 → 2; 4 → 3; 5 → 4; 6 y 7 → 5) |
| `ingocup = p6b2` (grupo A) | 100 % de 120,948 registros |
| `niv_ins` vs `anios_esc` | `niv_ins = 1` ⇒ ≤ 5 años; `niv_ins = 4` ⇒ ≥ 12 años (100 %) |
| `rama_est2` vs. 21 sectores SCIAN | p. ej. comercio (5) = SCIAN 6 + 7 = 5,382 + 32,172 = 37,554; servicios profesionales, financieros y corporativos (8) = 14,751 |
| `salario` por zona | 8,364 = 278.80 × 30 y 12,596 = 419.88 × 30 (frontera norte) |
| Ponderadores y filtros vs. cifras oficiales del INEGI (4T-2025) | PEA 61.3 M · participación 59.3 % · informales 32.9 M · TIL1 55.0 % · TIL1 de Chiapas 74.9 %, Chihuahua 36.2 %, CDMX 45.7 % (**7 de 7 coinciden**) |

> **Pendiente de contrastar con el cuestionario oficial:** la redacción literal de cada código de `p6c`
> («menos de 1 SM», «1 SM», …). La correspondencia con `ing7c` es exacta, por lo que no afecta los resultados.
