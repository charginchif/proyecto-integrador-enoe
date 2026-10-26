"""Construye y ejecuta el cuaderno del proyecto (notebooks/Proyecto_Integrador_ENOE.ipynb) y exporta HTML.

    python scripts/build_notebook.py

El texto interpretativo se genera a partir de results/ (resumen.json y CSV): si cambian los datos o el análisis,
el cuaderno se reconstruye con las cifras nuevas y las aserciones al inicio avisan si alguna conclusión dejó de ser cierta.
"""
import json
import sys
from pathlib import Path

import nbformat as nbf
import numpy as np
import pandas as pd
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from enoe import config as C  # noqa: E402

RES = C.RESULTS
R = json.loads((RES / "resumen.json").read_text(encoding="utf-8"))


def leer(n):
    return pd.read_csv(RES / f"{n}.csv", encoding="utf-8-sig")


bn = leer("brecha_nivel").set_index("nivel")
esc = leer("escalera_brecha").set_index("modelo")
rob = leer("robustez_brecha")
robr = leer("robustez_retorno").set_index("especificacion")
cu = leer("brecha_cuantiles").set_index("percentil")
ob = leer("oaxaca")
til = leer("til1_entidad")
ret = leer("retorno_entidad")
cal = leer("calidad_ingreso")
perf = leer("perfil_grupos_ingreso").set_index("grupo")
nrl = leer("no_respuesta_logit")
rm = leer("retorno_modelos").set_index("modelo")
prem = leer("premio_por_nivel").set_index("nivel")
tg = leer("til1_grupos").set_index("grupo")
sub = leer("brecha_subgrupos")
rr = leer("retorno_resumen").set_index("indicador")
asoc = leer("til1_vs_escolaridad_estatal").set_index("indicador")
deff = leer("efecto_diseno").set_index("estimador")
bit = leer("etl_bitacora").set_index("id")
meta = json.loads((RES / "etl_meta.json").read_text(encoding="utf-8"))

# ----------------------------- cifras formateadas para el texto ----------------------------- #
def f1(x):
    return f"{x:.1f}"


def pc(x):
    return f"{x:.1f} %"


def ci(lo, hi, d=1):
    return f"{lo:.{d}f} a {hi:.{d}f}"


n_u, n_v, n_s = R["muestras"]["universo"], R["muestras"]["ventana_15_65"], R["muestras"]["salarial"]
A_t, B_t, C_t, D_t = (float(cal[(cal.grupo == g) & (cal.poblacion == "Total")]["pct"].iloc[0]) for g in "ABCD")
A_n1 = float(cal[(cal.grupo == "A") & (cal.poblacion == "Nivel 1. Primaria incompleta")]["pct"].iloc[0])
A_n4 = float(cal[(cal.grupo == "A") & (cal.poblacion == "Nivel 4. Medio superior y superior")]["pct"].iloc[0])
nac = R["til1"]["nacional"]
bh = R["brecha"]["total_hora"]
bm = R["brecha"]["total_mens"]
bhr = R["brecha"]["total_horas"]
tot = bn.loc["Total"]
rt = R["retorno"]
mx_til, mn_til = til.loc[til.til1_est.idxmax()], til.loc[til.til1_est.idxmin()]
g5 = esc.loc["G5 + rama de actividad"]
g0 = esc.loc["G0 Sin controles"]
o_total = ob[(ob.especificacion.str.startswith("Principal")) & (ob.componente.str.startswith("Brecha total"))].iloc[0]
o_exp = ob[(ob.especificacion.str.startswith("Principal")) & (ob.componente.str.startswith("Explicada por"))].iloc[0]
o_noexp = ob[(ob.especificacion.str.startswith("Principal")) & (ob.componente.str.startswith("No explicada (referencia agrupada)"))].iloc[0]
o_esc = ob[(ob.especificacion.str.startswith("Principal")) & (ob.componente.str.contains("escolaridad"))].iloc[0]
rob_tot = rob[rob.grupo == "Total"].set_index("especificacion")
hora_specs = rob_tot[~rob_tot.index.str.startswith(("S6", "S8", "S9"))]
ind = R["individual_informalidad"]
dg = R["diagnosticos"]
nr_a = nrl[(nrl.modelo == "A_vs_resto") & (nrl.variable == "anios_esc")].iloc[0]
nr_m = nrl[(nrl.modelo == "A_vs_resto") & (nrl.variable == "mujer")].iloc[0]
rho_max, rho_min = R["retorno"]["rho_max"], R["retorno"]["rho_min"]
ret_max, ret_min = R["retorno"]["ret_max"], R["retorno"]["ret_min"]
dq = R["retorno"]["dif_q4_q1_log"]
q1, q4 = R["retorno"]["q1_pct"], R["retorno"]["q4_pct"]
rho_nac = R["retorno"]["spearman_nacional"]
rho_est_esc = R["retorno"]["rho_estatal_esc_ingreso"]
rho_est_ret = R["retorno"]["rho_estatal_ret_ingreso"]
cero_reg = 100 * (1 - float(bit.loc["QA", "n_despues"]) / n_u)     # % de registros con ingocup = 0
cero_pct = 100 - A_t                                               # % ponderado (ventana 15-65) sin monto exacto

# ---- Aserciones: si alguna conclusión del texto deja de ser cierta con los datos, el cuaderno no se construye ---- #
assert bh["brecha_hora_inf"] > 0 and bh["p_hora"] < 0.001, "La brecha por hora ya no es significativa"
assert bm["brecha_mens_pct"] > 5 * bh["brecha_hora_pct"], "La brecha mensual ya no es >5 veces la horaria"
assert all(R["brecha"]["por_nivel"][str(k)]["p_hora_holm"] < 0.01 for k in (1, 2, 3, 4))
assert dq["p"] > 0.05, "Ahora sí hay diferencia de rendimiento entre cuartiles"
assert R["til1_vs_escolaridad_estatal"]["rho_spearman_til_esc"]["est"] < -0.7
assert hora_specs["brecha_pct"].min() > 0
assert cu.loc[10, "inf"] > 0 and cu.loc[25, "inf"] > 0 and cu.loc[90, "inf"] <= 0 <= cu.loc[90, "sup"]
assert abs(nac["est"] - 55.0) < 0.1

nb = nbf.v4.new_notebook()
cells = []


def md(t):
    cells.append(nbf.v4.new_markdown_cell(t.strip("\n")))


def code(t):
    cells.append(nbf.v4.new_code_cell(t.strip("\n")))


# =========================================================================================== #
md(f"""
# Radiografía socioeconómica de México: escolaridad, ingreso y brecha de género

**Proyecto Integrador de Ciencia de Datos · Examen final**
Optativa III: Ciencia de Datos · Ingeniería en Computación, 9.º semestre · Universidad de Especialidades UNE, Plantel Centro

**Equipo 1:** Juan Evelio Culin Grajeda · Angel Yireh Garcia Jara · Luis Andre Gutierrez Zuñiga
**Datos:** INEGI, Encuesta Nacional de Ocupación y Empleo (ENOE), 4.º trimestre de 2025 · **Fecha:** 18 de octubre de 2026

---
""")

md(f"""
## Resumen ejecutivo

**Pregunta.** ¿Cuánto aumenta el ingreso laboral por cada año adicional de escolaridad en México, cómo cambia esa relación entre entidades
federativas y existe una brecha salarial significativa entre hombres y mujeres con la misma escolaridad?

| # | Hallazgo | Evidencia |
|---|---|---|
| 1 | **Los datos son confiables.** Con la base oficial (ocupados de 15+, `fac_tri`) se reproducen **7 de 7** cifras publicadas por el INEGI (PEA 61.3 M, participación 59.3 %, informalidad 55.0 %, ...). | Sección 2.4 |
| 2 | **El «ingreso cero» esconde tres fenómenos.** El {cero_pct:.0f} % de los ocupados no tiene monto exacto de ingreso (aparece con ingreso 0), pero solo {C_t:.0f} % no recibe ingresos: {B_t:.0f} % da un rango de salarios mínimos y {D_t:.0f} % no especifica. Quien más estudió declara menos el monto exacto ({A_n4:.0f} % vs. {A_n1:.0f} %), lo que sesga el análisis de «solo casos completos». | Sección 3.3 |
| 3 | **Un año más de escolaridad eleva el ingreso por hora {f1(rt['nacional_pct']['est'])} %** (IC 95 %: {ci(rt['nacional_pct']['ic_inf'], rt['nacional_pct']['ic_sup'])}), controlando edad, sexo y entidad. Terminar licenciatura o posgrado paga **{prem.loc['Licenciatura o posgrado (16+ años)', 'premio_pct']:.0f} % más** que no terminar primaria. | Sección 5.1 |
| 4 | **Estudiar rinde casi igual en estados ricos y pobres** (cuartil 4 − cuartil 1 = {dq['est']:.3f} log-puntos, p = {dq['p']:.2f}), pero entre estados va de {f1(ret_min['ret_est'])} % ({ret_min['entidad']}) a {f1(ret_max['ret_est'])} % ({ret_max['entidad']}). El **vínculo (Spearman)** escolaridad-ingreso va de {rho_min['rho_est']:.2f} ({rho_min['entidad']}) a {rho_max['rho_est']:.2f} ({rho_max['entidad']}); solo los extremos del ranking son estadísticamente distinguibles. | Sección 5.1 |
| 5 | **La brecha de género por hora es de {f1(bh['brecha_hora_pct'])} %** (IC 95 %: {ci(bh['brecha_hora_inf'], bh['brecha_hora_sup'])}; p < 0.001) y **por mes de {f1(bm['brecha_mens_pct'])} %**: la diferencia mensual es sobre todo de **horas** (las mujeres trabajan {f1(bhr['menos_horas_mujeres_pct'])} % menos). Entre personas parecidas la brecha por hora sube a **{f1(g5['brecha_pct'])} %**, se concentra en la parte baja de la distribución (P10-P25: {f1(cu.loc[10, 'brecha_pct'])}-{f1(cu.loc[25, 'brecha_pct'])} %) y desaparece arriba. | Sección 5.2 |
| 6 | **La informalidad cae con la escolaridad:** {f1(nac['est'])} % nacional; de {f1(mn_til['til1_est'])} % ({mn_til['entidad']}) a {f1(mx_til['til1_est'])} % ({mx_til['entidad']}); {f1(tg.loc['Nivel 1. Primaria incompleta', 'est'])} % entre quienes no terminaron primaria vs. {f1(tg.loc['Nivel 4. Medio superior y superior', 'est'])} % con medio superior o superior. Entre estados, ρ = {R['til1_vs_escolaridad_estatal']['rho_spearman_til_esc']['est']:.2f}; individualmente, cada año de estudio baja {abs(ind['ame_anios_esc_pp']):.1f} puntos la probabilidad de informalidad. | Sección 5.3 |

**Cómo leer este cuaderno.** Sigue el ciclo KDD; cada sección dice *qué se hace*, *por qué*, y *qué se encontró*. Todas las cifras de este texto se
generan desde `results/`; las celdas de código se pueden ejecutar de nuevo. Las incertidumbres usan el **diseño muestral complejo** de la ENOE (bootstrap de Rao-Wu, {R['B']:,} réplicas).
""")

md("""
## Contenido

| Sección | Fase KDD | Semana del curso | Qué se evidencia |
|---|---|---|---|
| 1. Marco del proyecto | — | — | Problema, objetivos, métricas de éxito |
| 2. Selección | 1 | 1 | Fuente, tablas, diseño muestral, validación contra cifras del INEGI |
| 3. Preprocesamiento | 2 | 4 | Reglas de limpieza, faltantes codificados, calidad del ingreso, atípicos, pruebas de calidad |
| 4. Transformación e ingeniería de datos | 3 | 4 · 6 · 7 | Variables derivadas, pipeline ETL, almacén relacional (SQLite) y modelo documental (MongoDB) |
| 5. Minería y análisis | 4 | 2 · 3 · 5 | Estadística descriptiva e inferencial, pruebas de hipótesis, regresión, descomposición, visualización |
| 6. Interpretación | 5 | 5 | Hallazgos, métricas de éxito, recomendaciones, limitaciones |
| 7. Reproducibilidad | — | 6 | Versiones, semilla, huellas de los archivos, cómo correr todo |
""")

md(f"""
## 1. Marco del proyecto

**Pregunta de investigación.** ¿Cuánto aumenta el ingreso laboral por cada año adicional de escolaridad en México, cómo cambia esa relación entre
entidades federativas y existe una brecha salarial significativa entre hombres y mujeres con la misma escolaridad?

**Objetivo general.** Cuantificar la relación entre escolaridad e ingreso laboral y la brecha salarial de género en la población ocupada de México,
por entidad federativa, a partir de los microdatos de la ENOE.

**Objetivos específicos.**
1. Estimar la correlación y el retorno de un año adicional de escolaridad sobre el ingreso por hora en cada una de las 32 entidades, comparando estados de mayor y menor ingreso.
2. Determinar si existe una diferencia estadísticamente significativa de ingreso por hora entre hombres y mujeres con el mismo nivel de instrucción.
3. Identificar las entidades con mayor tasa de informalidad laboral y medir su relación con la escolaridad promedio.

**Métricas de éxito (del protocolo).**
- *M1.* Brecha salarial de género (%) en el ingreso por hora para cada nivel de instrucción, con IC 95 % y prueba de hipótesis (significativa si p < 0.05).
- *M2.* Coeficiente de correlación escolaridad-ingreso (Spearman) para las 32 entidades, con IC por bootstrap, y un ranking de estados defendible.
- *M3.* Tablero con al menos 4 visualizaciones interpretables por un no especialista, alimentado por un pipeline que carga datos limpios a una base NoSQL (MongoDB) consultable por entidad.

La sección 6.2 contrasta el resultado con cada métrica.
""")

code("""
import sys, json, sqlite3, warnings
from pathlib import Path
RAIZ = Path.cwd().resolve().parent if Path.cwd().name == "notebooks" else Path.cwd().resolve()
sys.path.insert(0, str(RAIZ / "src"))
warnings.filterwarnings("ignore")

import numpy as np, pandas as pd, matplotlib.pyplot as plt
from IPython.display import display, Markdown
from enoe import (config as C, extract, clean, transform, validacion, survey, estimadores as E, modelos as M,
                  viz, figuras, load_mongo as LM, datos as DT, pipeline)

pd.set_option("display.max_columns", 40); pd.set_option("display.width", 200)
def ver(df, dec=2):
    \"\"\"Tabla con formato de miles y decimales, sin índice.\"\"\"
    return df.style.format(precision=dec, thousands=",").hide(axis="index")
def leer(nombre):
    return pd.read_csv(C.RESULTS / f"{nombre}.csv", encoding="utf-8-sig")

print(f"Python {sys.version.split()[0]} · pandas {pd.__version__} · numpy {np.__version__}")
print("Semilla única del proyecto:", C.SEMILLA, "| réplicas bootstrap:", C.N_BOOTSTRAP)
RAW_OK = (C.RAW_DIR / f"ENOE_SDEMT{C.PERIODO}.csv").exists()
print("Microdatos originales disponibles:", RAW_OK, "->", C.RAW_DIR.name)
""")

# =========================================================================================== #
md("""
## 2. Selección (KDD fase 1 · Semana 1)

### 2.1 Fuente y archivos
La ENOE es la principal fuente de información del mercado laboral mexicano. INEGI publica sus microdatos en varias tablas; este proyecto usa dos:

- **SDEMT** (sociodemográfica y laboral): una fila por residente del hogar, de todas las edades; contiene el ponderador, el diseño muestral, escolaridad, ingreso y horas.
- **COE2T** (cuestionario de ocupación, parte 2): el detalle de cómo se captó el ingreso (monto, o rango de salarios mínimos si no hubo monto).

Las tablas COE1T, HOGT y VIVT no aportan variables al problema y no se usan. Se guarda la huella SHA-256 de cada archivo para poder demostrar con qué datos se corrió todo.
""")

code("""
meta = json.loads((C.RESULTS / "etl_meta.json").read_text(encoding="utf-8"))
display(ver(pd.DataFrame(meta["archivos_origen"])[["tabla", "archivo", "filas", "columnas_leidas", "bytes", "sha256"]], 0))
""")

code("""
if RAW_OK:
    sdemt = extract.leer_sdemt()
    coe2 = extract.leer_coe2t()
    print(f"SDEMT: {sdemt.shape[0]:,} filas x {sdemt.shape[1]} columnas leídas (de 115) | COE2T: {coe2.shape[0]:,} filas")
    display(sdemt.head(5))
else:
    print("Sin microdatos locales: las celdas siguientes usan los resultados guardados en results/.")
""")

md("""
### 2.2 Diseño muestral: por qué no basta con «promediar las filas»
La ENOE es una encuesta **probabilística, bietápica, estratificada y por conglomerados**: se sortean *Unidades Primarias de Muestreo* (UPM, `upm`)
dentro de *estratos* (`est_d_tri`), y dentro de ellas viviendas y personas. Cada persona representa a `fac_tri` personas de la población.

Consecuencias para el análisis (todas se aplican en este proyecto):
1. **Estimar con ponderadores**: sin `fac_tri`, los promedios representan a la muestra, no al país.
2. **Medir la incertidumbre con el diseño**: las personas de una misma UPM se parecen entre sí (efecto de diseño), así que los errores estándar de una muestra aleatoria simple son demasiado pequeños.
3. **Estratos con una sola UPM** no permiten estimar varianza; se fusionan con un estrato vecino de la misma entidad.
""")

code("""
if RAW_OK:
    tabla_upm = pipeline.construir_tabla_upm(sdemt)
    por_estrato = sdemt.groupby("est_d_tri")["upm"].nunique()
    resumen_diseno = pd.DataFrame({
        "indicador": ["UPM en la muestra", "Estratos originales", "Estratos con una sola UPM", "Estratos tras colapsar", "UPM por estrato (mediana)", "Suma de fac_tri (millones de personas)"],
        "valor": [len(tabla_upm), sdemt["est_d_tri"].nunique(), int((por_estrato == 1).sum()), tabla_upm["estrato_col"].nunique(), por_estrato.median(), sdemt["fac_tri"].sum() / 1e6]})
else:
    resumen_diseno = pd.DataFrame({"indicador": ["UPM", "Estratos originales", "Estratos colapsados"], "valor": [meta["n_upm"], meta["n_estratos_originales"], meta["n_estratos_colapsados"]]})
display(ver(resumen_diseno, 1))
""")

md("""
### 2.3 Llave de persona y unión de tablas
La llave que se cita habitualmente (`cd_a, ent, con, v_sel, n_hog, h_mud, n_ren`) **no es única** en este trimestre (8,371 duplicados en SDEMT). Se verificó empíricamente que
`cd_a, cve_ent, con, upm, d_sem, n_pro_viv, v_sel, n_hog, h_mud, n_ent, n_ren` sí lo es (0 duplicados), y la unión SDEMT–COE2T se hace con `validate="one_to_one"`: si alguna fila no encontrara pareja, el pipeline falla.
""")

md("""
### 2.4 Validación externa: ¿nuestros filtros y ponderadores reproducen las cifras oficiales?
Antes de analizar nada, se comprueba que la **base** (ocupados de 15 años y más, entrevista completa, residentes habituales, ponderador `fac_tri`) reproduce lo que publica el INEGI para este trimestre.
Si lo hace, entonces estamos interpretando bien los códigos y los ponderadores, y los resultados son comparables con la estadística oficial.
""")

code("""
if RAW_OK:
    ext = validacion.comparar_con_inegi(sdemt)
    efecto = validacion.efecto_base_menores_15(sdemt)
else:
    ext = leer("etl_validacion_externa"); efecto = meta["efecto_base_menores_15"]
display(ver(ext, 3))
print(f"\\nSi se incluyeran los {efecto['menores_de_15_ocupados_en_muestra']:,} menores de 15 años ocupados, el TIL1 subiría de "
      f"{efecto['til1_base_15_y_mas']:.2f} % a {efecto['til1_con_menores_de_15']:.2f} % y ya no coincidiría con el oficial: por eso se restringe a 15+.")
""")

md(f"""
**Resultado:** las 7 comparaciones coinciden al redondear a la precisión publicada (PEA, participación, ocupación informal, TIL1 nacional y TIL1 de tres estados). Esto valida la lectura de `clase1`, `clase2`, `emp_ppal`, `r_def`, `c_res` y `fac_tri`.
*(Cifras oficiales tomadas de los boletines del INEGI para el 4T-2025; se citan en `docs/diccionario_de_datos.md`.)*
""")

# =========================================================================================== #
md("""
## 3. Preprocesamiento (KDD fase 2 · Semana 4)

Cada regla de limpieza es una función con nombre, probada con datos sintéticos (`tests/test_clean.py`) y registrada en una **bitácora**. Las reglas que *eliminan filas* son solo las de cobertura
(¿esta persona pertenece al universo de estudio?); todo lo demás —faltantes codificados, calidad del ingreso, atípicos— **crea banderas**, de modo que el análisis de sensibilidad puede cambiar una decisión sin volver a limpiar.

### 3.1 Cobertura: del registro crudo al universo de estudio
""")

code("""
if RAW_OK:
    bit_demo = clean.Bitacora()
    universo = clean.aplicar_cobertura(sdemt, bit_demo)
    display(ver(bit_demo.a_dataframe()[["id", "descripcion", "regla", "n_antes", "n_despues", "afectados"]], 0))
else:
    display(ver(leer("etl_bitacora").query("tipo == 'filtro'")[["id", "descripcion", "regla", "n_antes", "n_despues", "afectados"]], 0))
""")

md("""
**Por qué estas reglas.** `r_def = 0` deja solo entrevistas completas; `c_res ∈ {1, 3}` excluye a los «nuevos residentes» (que vienen con sexo y edad en blanco); `eda ≥ 15` es la base oficial de la ENOE;
`clase2 = 1` define a los ocupados. Ninguna otra fila se elimina en esta etapa.
""")


code("""
if RAW_OK:
    tabla_upm = pipeline.construir_tabla_upm(sdemt)
    base, bitacora, embudo, umbrales, imputacion, expectativas = pipeline.construir_base_analitica(sdemt, coe2, tabla_upm)
else:
    base = None
    bitacora, embudo, umbrales, imputacion, expectativas = (leer(n) for n in ["etl_bitacora", "etl_embudo_salarial", "etl_umbrales_atipicos", "etl_imputacion_rangos", "etl_expectativas"])
x = figuras.cargar_insumos()
fig = viz.fig_embudo(bitacora, embudo); plt.show()
""")

md(f"""
**Cómo leer la figura.** Cada barra es el número de registros que quedan tras cada regla. El universo de estudio son los **{n_u:,} ocupados de 15+**; de ellos, {n_v:,} tienen 15–65 años (ventana del protocolo)
y **{n_s:,}** cumplen todas las condiciones para el análisis salarial (monto exacto de ingreso, horas válidas, escolaridad especificada, sin atípicos).

### 3.2 Faltantes codificados y valores imposibles
La ENOE **no tiene celdas vacías** (0 % de nulos): los faltantes vienen como códigos válidos. Un `describe()` ingenuo diría que los datos están completos; la limpieza consiste en detectarlos.
""")

code("""
marcas = bitacora[bitacora["id"].isin(["M1", "M2", "M3", "M4", "L6"])][["id", "descripcion", "regla", "n_despues"]].rename(columns={"n_despues": "casos"})
display(ver(marcas, 0))
""")

md(f"""
- **Años de escolaridad = 99** (no especificado): {int(bit.loc['M1', 'n_despues']):,} ocupados → se recodifica a nulo.
- **Horas trabajadas = 0** en {int(bit.loc['M2', 'n_despues']):,} ocupados (ausentes del trabajo la semana de referencia): no se puede calcular ingreso por hora → quedan fuera de la muestra salarial, aunque siguen en el universo.
- **Más de 112 horas semanales** (16 h × 7 días): {int(bit.loc['M3', 'n_despues']):,} casos con jornadas materialmente imposibles (hasta 168 h) → se marcan como no válidas.
- **Nivel de instrucción = 5** (no especificado): {int(bit.loc['M4', 'n_despues']):,} casos.

### 3.3 Hallazgo de calidad: el «ingreso cero» no es un solo fenómeno
El archivo reporta `ingocup = 0` para el **{cero_reg:.0f} %** de los registros ({cero_pct:.0f} % ponderado). La primera lectura —«no reciben ingresos»— es incorrecta. Cruzando `ingocup` con `ing7c` (ingreso en salarios mínimos) y con `p6c` de COE2T se distinguen **cuatro grupos**:

| Grupo | Definición | Qué sabemos del ingreso |
|---|---|---|
| **A** | Declaró monto exacto (`ingocup > 0`) | El monto |
| **B** | Solo declaró un **rango de salarios mínimos** (`ingocup = 0`, `ing7c` 1-5) | Un intervalo |
| **C** | No recibe ingresos (`ing7c` = 6) | Es cero de verdad ({perf.loc['C', 'sin_pago_pct']:.0f} % son trabajadores sin pago) |
| **D** | No especificó (`ing7c` = 7) | Nada |
""")

code("""
fig = viz.fig_calidad_ingreso(x["calidad_ingreso"]); plt.show()
""")

md(f"""
**Lectura.** Solo **{A_t:.0f} %** de los ocupados (ponderado) declara un monto exacto; **{B_t:.0f} %** da únicamente un rango; **{D_t:.0f} %** no especifica y **{C_t:.0f} %** realmente no recibe ingresos.
Lo importante es el **patrón**: la proporción que declara monto exacto **baja con la escolaridad** ({A_n1:.0f} % en primaria incompleta → {A_n4:.0f} % en medio superior y superior).
Es decir, los datos faltan de forma **no aleatoria**: un análisis de «solo casos completos» sobrerrepresenta a quienes menos estudiaron.
""")

code("""
perfil = leer("perfil_grupos_ingreso")
display(ver(perfil[["grupo", "n", "poblacion_millones", "mujeres_pct", "anios_esc", "edad", "informal_pct", "empleadores_pct", "cuenta_propia_pct", "sin_pago_pct", "horas_semana"]], 1))
display(Markdown("**Pruebas de asociación** (χ² indicativa —no corrige por diseño— y V de Cramér como tamaño de efecto):"))
display(ver(leer("calidad_ingreso_chi2"), 3))
display(Markdown("**¿Quién declara el monto exacto?** Logit ponderado con errores robustos de diseño (razones de momios; >1 = más probable declarar):"))
display(ver(leer("no_respuesta_logit").query("modelo == 'A_vs_resto'")[["variable", "coef", "razon_momios", "rm_inf", "rm_sup", "p"]], 3))
""")

md(f"""
**Interpretación.** Quienes dan solo rango (B) o no especifican (D) tienen **más escolaridad** ({perf.loc['B', 'anios_esc']:.1f} y {perf.loc['D', 'anios_esc']:.1f} años vs. {perf.loc['A', 'anios_esc']:.1f} del grupo A), son más a menudo empleadores y menos informales ({perf.loc['B', 'informal_pct']:.0f} % vs. {perf.loc['A', 'informal_pct']:.0f} %).
En el logit, cada año de escolaridad **reduce {100 * (1 - nr_a['razon_momios']):.1f} %** los momios de declarar el monto exacto (RM = {nr_a['razon_momios']:.3f}); las mujeres tienen RM = {nr_m['razon_momios']:.2f} (declaran un poco más).
**Decisión metodológica:** el análisis principal usa el grupo A (es lo estándar y lo que INEGI usa para el ingreso por hora), y **cada resultado importante se somete a tres correcciones de sensibilidad**:
(i) incluir el grupo B con ingreso imputado por rango, (ii) ponderar por el inverso de la probabilidad de declarar (IPW), (iii) usar solo asalariados. Los resultados están en las secciones 5.1 y 5.2.

### 3.4 Imputación por rangos (solo para el análisis de sensibilidad)
A quien solo declaró «entre 2 y 3 salarios mínimos» se le asigna la **mediana ponderada observada** de quienes ganan entre 2 y 3 salarios mínimos y dieron monto exacto (no el punto medio del rango, porque dentro de cada rango la distribución es asimétrica).
Se usa el salario mínimo de la zona de cada persona (`salario`: $8,364 o $12,596 mensuales en la frontera norte). Los 7 códigos de `p6c` reproducen **exactamente** las 5 clases de `ing7c` (verificado en el 100 % de los 36,438 casos del grupo B).
""")

code("""
display(ver(imputacion[["p6c", "rango", "n_referencia_A", "razon_mediana_sm", "n_B_imputados"]], 3))
""")

md("""
### 3.5 Atípicos del ingreso por hora
El ingreso por hora es `ingocup / (hrsocup × 4.3)` (se verificó contra la variable `ing_x_hrs` de INEGI: diferencia relativa máxima 7 × 10⁻⁵). Los extremos son implausibles: desde $0.03 hasta $11,628 por hora.
Se marcan como atípicos los valores fuera de los **percentiles 0.5 y 99.5 de su propia entidad** (≈ 1 % de la muestra con monto exacto). Se recortan las dos colas: la inferior (p. ej. $0.5 por hora) casi siempre es error de captura.
""")

code("""
print(f"Atípicos marcados: {int(bitacora.set_index('id').loc['O1', 'n_despues']):,} de {int(bitacora.set_index('id').loc['O1', 'n_antes']):,} observaciones con monto exacto y horas válidas")
display(ver(umbrales.rename(columns={"cve_ent": "entidad (clave)"}).head(6)[["entidad (clave)", "hora_min", "hora_max"]], 2))
W = x["W"].df
fig = viz.fig_distribucion_ingreso(W); plt.show()
""")

md(f"""
**Por qué se trabaja en logaritmos.** El ingreso por hora tiene una asimetría de **{dg['asimetria_ingreso_nivel']:.1f}** (cola derecha larga); su logaritmo natural, de **{dg['asimetria_ln_ingreso']:.2f}**. Con el logaritmo, una diferencia de medias es una diferencia porcentual aproximada y los supuestos de los modelos se cumplen mucho mejor.
Los picos en cifras redondas ($50, $100...) son «heaping» —los entrevistados redondean—; no se corrige, pero se reconoce como limitación.

### 3.6 Expectativas de calidad (contratos de datos)
Tras limpiar, el pipeline **verifica 15 condiciones** y se detiene si una crítica falla. Incluyen cruces entre tablas que prueban que las variables significan lo que creemos:
""")

code("""
display(ver(expectativas[["expectativa", "cumple", "critica", "detalle"]], 0))
print(f"\\n{int(expectativas['cumple'].sum())} de {len(expectativas)} expectativas cumplidas")
""")

# =========================================================================================== #
md("""
## 4. Transformación e ingeniería de datos (KDD fase 3 · Semanas 4, 6 y 7)

### 4.1 Variables derivadas
`mujer`, `informal`, `eda_c` y `eda_c2` (edad centrada en 40 años y su cuadrado/100, para reducir la colinealidad), `grupo_edad`, `niv_det` (se parte el nivel 4 «medio superior y superior» con los años de escolaridad en **12–15** y **16+**),
`grupo_ingreso` (A/B/C/D), `ing_hora`, `ln_ing_hora`, `ing_mensual_imp`, banderas de muestra y la llave `persona_id`. El detalle está en `docs/diccionario_de_datos.md`.
""")

code("""
con = sqlite3.connect(C.DB_PATH); con.execute("PRAGMA foreign_keys = ON")
cols = ["persona_id", "cve_ent", "sex", "eda", "anios_esc", "niv_ins", "niv_det", "informal", "hrsocup", "grupo_ingreso", "ing_mensual", "ing_hora", "ln_ing_hora", "en_muestra_salarial", "fac_tri"]
display(ver(pd.read_sql(f"SELECT {', '.join(cols)} FROM fact_ocupado WHERE en_muestra_salarial = 1 LIMIT 6", con), 2))
""")

md("""
### 4.2 Pipeline de ingeniería de datos (Semana 6)

```
CSV de INEGI (SDEMT, COE2T)                      scripts/run_etl.py
        │  extract.py   lectura tipada (usecols), SHA-256 de cada archivo
        ▼
   validacion.py ──► contraste con cifras oficiales del INEGI (7/7)
        │  clean.py     cobertura · faltantes · calidad del ingreso · atípicos · expectativas
        │  transform.py unión 1:1 SDEMT-COE2T · variables derivadas · imputación por rango
        ▼
  load_sqlite.py ──► SQLite (esquema en estrella, PK/FK/CHECK, índices, vistas, auditoría)
        │                     │
        │                     └─► analisis.py: estimadores + bootstrap de Rao-Wu  ──► results/*.csv, resumen.json
        ▼
  load_mongo.py ──► MongoDB / NDJSON (fichas por entidad + personas)  ──► tablero/tablero_enoe.html
```
El pipeline es **idempotente** (recrea la base desde cero), **determinista** (una sola semilla) y está **probado** (`tests/`: más de 30 pruebas unitarias y de integración).

### 4.3 Almacén relacional: SQLite con esquema en estrella
Se eligió SQLite porque los datos son **tabulares**, las consultas son **agregaciones con JOIN** (promedios ponderados por entidad, nivel, sexo), el volumen (190 mil filas) cabe en un archivo transaccional (ACID) sin servidor
y las restricciones (`PRIMARY KEY`, `FOREIGN KEY`, `CHECK`) hacen que el propio motor rechace datos inconsistentes.
""")

code("""
tablas = pd.read_sql("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY type DESC, name", con)
tablas["filas"] = [pd.read_sql(f"SELECT COUNT(*) AS n FROM {n}", con)["n"][0] for n in tablas["name"]]
display(ver(tablas[~tablas["name"].str.startswith("res_")], 0))
print("integrity_check:", con.execute("PRAGMA integrity_check").fetchone()[0], "| violaciones de llave foránea:", len(con.execute("PRAGMA foreign_key_check").fetchall()))
""")

md("""
**Consulta de ejemplo (SQL).** Tasa de informalidad (TIL1) ponderada por entidad, con un `JOIN` a la dimensión; es la vista `v_til_entidad`:
""")

code("""
sql = '''
SELECT e.entidad, COUNT(*) AS n_muestra, ROUND(SUM(f.fac_tri)) AS ocupados_estimados,
       ROUND(100.0 * SUM(f.fac_tri * f.informal) / SUM(f.fac_tri), 2) AS til1_pct
FROM fact_ocupado f JOIN dim_entidad e USING (cve_ent)
GROUP BY e.entidad ORDER BY til1_pct DESC LIMIT 5
'''
print(sql)
display(ver(pd.read_sql(sql, con), 1))
""")

md("""
### 4.4 Modelo documental: MongoDB (Semana 7) y por qué *además* del relacional
**Justificación del modelo de datos.** El almacenamiento «más adecuado» depende del patrón de acceso:

| Necesidad | Modelo adecuado | Razón |
|---|---|---|
| Análisis: agregaciones ponderadas sobre 190 mil filas, JOIN, regresiones | **Relacional (SQLite)** | Datos tabulares de esquema fijo; el motor valida restricciones; SQL expresa bien `GROUP BY` y `JOIN` |
| Servir la «ficha de una entidad» a un tablero o API | **Documental (MongoDB)** | Se lee *un documento por clave* con todos los indicadores anidados (embedding); el esquema puede crecer con otros trimestres sin migraciones; no requiere JOIN |

Por eso el proyecto usa **persistencia políglota**: SQLite como almacén analítico y MongoDB como capa de lectura. Colecciones: `entidades` (32 documentos con indicadores, intervalos y rankings anidados), `personas` (un documento por ocupado con subdocumentos `persona`, `trabajo`, `ingreso`, `diseno`) y `metadatos` (linaje).
Índices: único por `cve_ent`, compuestos `(cve_ent, ingreso.grupo)` y `(cve_ent, persona.sexo)`, y uno **parcial** sobre la muestra salarial.
""")

code("""
ficha = LM.ficha_entidad("Oaxaca")
print(json.dumps(ficha, ensure_ascii=False, indent=1)[:1500], "...")
""")

md("""
**Consulta equivalente en MongoDB** (pipeline de agregación) y verificación de que da lo mismo que SQL, sin necesidad de un servidor:
""")

code("""
print(json.dumps(LM.PIPELINE_TIL1_POR_ENTIDAD, ensure_ascii=False, indent=1))
doc = LM.til1_por_entidad_desde_ndjson().set_index("cve_ent")["til1_pct"]
sql_v = pd.read_sql("SELECT cve_ent, til1_pct FROM v_til_entidad", con).set_index("cve_ent")["til1_pct"]
print(f"\\nDiferencia máxima entre la consulta sobre documentos y la vista SQL: {(doc - sql_v).abs().max():.4f} puntos porcentuales (el SQL redondea a 2 decimales)")
""")

# =========================================================================================== #
md("""
## 5. Minería y análisis (KDD fase 4 · Semanas 2, 3 y 5)

### 5.0 Estadística descriptiva y supuestos
""")

code("""
desc = leer("descriptivos_salario")
display(ver(desc.query("variable in ['Ingreso por hora ($)', 'Ingreso mensual ($)', 'Horas por semana', 'Años de escolaridad']")[["grupo", "variable", "n", "media_pond", "mediana_pond", "p10", "p90", "asimetria"]], 2))
D = DT.cargar_datos(); W = D.salarial; U = D.universo
print(f"Muestra salarial: {len(W):,} observaciones que representan a {W.w.sum() / 1e6:.1f} millones de trabajadores con monto exacto de ingreso")
""")

md(f"""
**Lectura.** Los hombres de la muestra trabajan en promedio **{R['brecha']['total_horas']['horas_h']:.1f} horas** por semana y las mujeres **{R['brecha']['total_horas']['horas_m']:.1f}**; las mujeres tienen **más escolaridad** (10.97 vs. 10.22 años).
Las medias y medianas ponderadas casi coinciden entre sexos *por hora*, pero no *por mes*: esa es la clave de la sección 5.2.

### 5.0.1 Incertidumbre con diseño complejo: el bootstrap de Rao-Wu
En cada estrato con *n* UPM se remuestrean *n − 1* UPM con reemplazo y se reescalan los ponderadores por *n/(n−1)* × (veces que salió la UPM). Es el método de réplicas que usan los institutos de estadística. Se probó que:
(a) los totales ponderados son insesgados bajo el remuestreo, (b) su varianza reproduce la de linealización de Taylor, (c) el Spearman ponderado coincide con `scipy` cuando los pesos son iguales y con los datos «expandidos» cuando son enteros (`tests/test_survey.py`).
Las estimaciones en **dominios** (subpoblaciones) conservan *todas* las UPM del diseño, para no perder variabilidad.
""")

code("""
est, nom = E.fab_universo(U)
r = E.correr(est, nom, U, D.diseno, B=200, semilla=C.SEMILLA)            # demostración con 200 réplicas
se_boot = r.tabla().set_index("nombre").loc["til1_nac", "ee"] * 100
se_taylor = survey.regresion_diseno(np.ones((len(U), 1)), U.col("informal"), U.w, U.psu, D.diseno, ["c"]).ee[0] * 100
se_mas = np.sqrt(0.55 * 0.45 / len(U)) * 100
print(f"TIL1 nacional = {r.theta[0] * 100:.2f} %")
print(f"Error estándar: bootstrap Rao-Wu (B=200) = {se_boot:.3f} pp | linealización de Taylor = {se_taylor:.3f} pp | si fuera muestra aleatoria simple = {se_mas:.3f} pp")
display(ver(leer("efecto_diseno"), 2))
""")

md(f"""
**Lectura.** Bootstrap y Taylor coinciden; un análisis que ignorara el diseño subestimaría el error estándar a **menos de la mitad** (efecto de diseño ≈ {deff.loc['TIL1 nacional', 'deff']:.1f}: los {n_u:,} ocupados «valen» como {deff.loc['TIL1 nacional', 'n_efectivo']:,.0f} observaciones independientes).
Con n efectivo ≈ 36–40 mil, las conclusiones siguen siendo muy precisas a nivel nacional, pero hay que ser prudentes con estados individuales (1,900 a 5,900 observaciones salariales cada uno).

### 5.1 Objetivo 1 · Escolaridad e ingreso
#### El panorama nacional
""")

code("""
fig = viz.fig_ingreso_por_escolaridad(W.df); plt.show()
fig = viz.fig_cajas_nivel_sexo(W.df); plt.show()
""")

md(f"""
**Lectura.** El ingreso por hora sube con la escolaridad de forma suave hasta secundaria y media superior, y **se dispara al llegar a la licenciatura** (16–17 años). Las distribuciones se traslapan mucho: la escolaridad *desplaza* la distribución, pero no determina el ingreso de nadie en particular.
En todos los niveles las medianas de las mujeres (naranja) quedan un poco por debajo de las de los hombres (azul), salvo en media superior y superior, donde casi se igualan.
""")

code("""
rm = leer("retorno_modelos")
display(ver(rm[["modelo", "retorno_pct", "retorno_pct_inf", "retorno_pct_sup", "r2", "n"]], 2))
display(Markdown("**Premio salarial de cada nivel respecto a «primaria incompleta»** (controlando edad, sexo y entidad):"))
display(ver(leer("premio_por_nivel"), 1))
""")

md(f"""
**Resultados (ecuación de Mincer, WLS con errores robustos de diseño).**
- Un año adicional de escolaridad eleva el ingreso por hora **{f1(rm.loc['M3 + entidad y localidad', 'retorno_pct'])} %** (M3: controlando edad, edad², sexo, entidad y tamaño de localidad; IC 95 %: {ci(rm.loc['M3 + entidad y localidad', 'retorno_pct_inf'], rm.loc['M3 + entidad y localidad', 'retorno_pct_sup'])}).
  Sin controles es {f1(rm.loc['M1 Mincer simple', 'retorno_pct'])} %; al agregar posición, informalidad y rama baja a {f1(rm.loc['M4 + posición, informalidad y rama', 'retorno_pct'])} %, porque parte del beneficio de estudiar *pasa por* conseguir un mejor empleo.
- **No es lineal:** el premio por nivel es de {prem.loc['Primaria completa', 'premio_pct']:.0f} % (primaria), {prem.loc['Secundaria completa', 'premio_pct']:.0f} % (secundaria), {prem.loc['Media superior / superior trunca (12-15 años)', 'premio_pct']:.0f} % (media superior) y **{prem.loc['Licenciatura o posgrado (16+ años)', 'premio_pct']:.0f} %** (licenciatura o posgrado) frente a no terminar primaria.
- **Las mujeres obtienen un mayor rendimiento por año de estudio:** {f1(rt['mujeres_pct']['est'])} % vs. {f1(rt['hombres_pct']['est'])} % de los hombres (diferencia = {rt['dif_mujeres_hombres_log']['est']:.3f} log-puntos; IC 95 %: {rt['dif_mujeres_hombres_log']['ic_inf']:.3f} a {rt['dif_mujeres_hombres_log']['ic_sup']:.3f}).
- **Correlación nacional (Spearman ponderado):** ρ = {rho_nac['est']:.3f} (IC 95 %: {ci(rho_nac['ic_inf'], rho_nac['ic_sup'], 3)}): asociación positiva y moderada.

#### Robustez: ¿depende el rendimiento de a quién se incluye?
""")

code("""
display(ver(leer("robustez_retorno")[["especificacion", "descripcion", "n", "retorno_pct", "inf", "sup"]], 2))
""")

md(f"""
**El rendimiento es robusto:** entre {robr['retorno_pct'].min():.1f} % y {robr['retorno_pct'].max():.1f} % en las siete especificaciones (incluida la que añade el grupo B imputado y la ponderada por no respuesta). La conclusión «≈ 5 % por año» no depende de cómo se trate el ingreso faltante.

#### Por entidad: correlación (Métrica 2) y rendimiento
""")

code("""
ret = x["retorno_entidad"]
fig = viz.fig_spearman_estados(ret, x["retorno_resumen"].set_index("indicador").loc["Spearman nacional (escolaridad - ingreso/hora)", "est"]); plt.show()
""")

md(f"""
**Lectura.** Cada punto es el Spearman ponderado de una entidad con su intervalo de confianza por bootstrap; a la derecha, su **lugar en el ranking con un intervalo** (el lugar también es incierto, y se estimó en cada réplica).
La Ciudad de México ({rho_max['rho_est']:.2f}) encabeza el ranking con certeza (lugar 1–2); {rho_min['entidad']} ({rho_min['rho_est']:.2f}) es la de menor vínculo. **Las diferencias entre estados vecinos del centro del ranking no son estadísticamente distinguibles** (sus intervalos de lugar abarcan 15 o más posiciones):
un ranking «defendible» es el que reporta esa incertidumbre, y por eso solo los extremos se pueden afirmar.
""")

code("""
t = ret.sort_values("rho_est", ascending=False)[["entidad", "n_salarial", "rho_est", "rho_ic_inf", "rho_ic_sup", "rho_rango", "rho_rango_inf", "rho_rango_sup"]]
display(Markdown("**Cinco mayores y cinco menores correlaciones:**"))
display(ver(pd.concat([t.head(5), t.tail(5)]), 3))
fig = viz.fig_retorno_estados(ret, x["retorno_resumen"].set_index("indicador").loc["Rendimiento nacional por año de escolaridad (%)", "est"]); plt.show()
""")

md(f"""
#### Estados de mayor vs. menor ingreso (Objetivo 1)
Se agrupan las 32 entidades en **cuartiles de ingreso mediano por hora** (el agrupamiento se recalcula en cada réplica del bootstrap, para no ignorar la incertidumbre de la propia clasificación) y se compara el rendimiento medio del cuarto cuartil (más rico) con el del primero (más pobre).
""")

code("""
rr = leer("retorno_resumen")
display(ver(rr[rr["indicador"].str.contains("cuartil|Q4|estados")], 3))
fig = viz.fig_dispersion_estatal(ret, x["retorno_resumen"].set_index("indicador").loc["Spearman entre estados: escolaridad media vs. ingreso mediano", "est"]); plt.show()
""")

md(f"""
**Resultado.** El rendimiento medio es {f1(q1['est'])} % en los estados más pobres (Q1) y {f1(q4['est'])} % en los más ricos (Q4): la diferencia es **{dq['est']:.3f} log-puntos** (IC 95 %: {dq['ic_inf']:.3f} a {dq['ic_sup']:.3f}; **p = {dq['p']:.2f}**). **No hay evidencia de que estudiar rinda más o menos según la riqueza del estado.**
Lo que sí difiere entre estados es el *nivel*: los estados con trabajadores más escolarizados pagan más por hora (Spearman entre estados = {rho_est_esc['est']:.2f}; IC 95 %: {ci(rho_est_esc['ic_inf'], rho_est_esc['ic_sup'], 2)}), y el rendimiento por año tiene una relación ligeramente **negativa** con el ingreso mediano del estado (ρ = {rho_est_ret['est']:.2f}; IC 95 %: {ci(rho_est_ret['ic_inf'], rho_est_ret['ic_sup'], 2)}): donde el ingreso es bajo, un año extra de estudio rinde un poco más porque los trabajadores parten de menos escolaridad.
*Advertencia:* estas son relaciones **entre estados**; no se deben leer como efectos causales para una persona.

### 5.2 Objetivo 2 · Brecha salarial de género (Métrica 1)
**Definición.** Brecha = 1 − (ingreso medio geométrico de las mujeres ÷ el de los hombres), es decir, «cuánto menos ganan las mujeres». Se calcula con la diferencia de medias ponderadas del *logaritmo* del ingreso por hora y se transforma a porcentaje.
La prueba de hipótesis (H₀: brecha = 0, α = 0.05) usa el error estándar bootstrap de diseño; se reportan los p-valores **ajustados por Holm** para las cuatro pruebas por nivel, y —como en el protocolo— también las pruebas **clásicas** de Welch y Mann-Whitney (sin ponderar) con su tamaño de efecto.
""")

code("""
bn = leer("brecha_nivel")
display(ver(bn[["nivel", "n_hombres", "n_mujeres", "ing_hora_h", "ing_hora_m", "brecha_hora_pct", "brecha_hora_inf", "brecha_hora_sup", "p_hora", "p_hora_holm"]], 3))
display(Markdown("**Pruebas clásicas (sin ponderar) y tamaños de efecto:**"))
display(ver(leer("tests_clasicos")[["nivel", "t_welch", "p_welch_holm", "p_mwu_holm", "d_cohen", "r_biserial"]], 4))
fig = viz.fig_brecha_nivel(bn); plt.show()
""")

md(f"""
**Resultados (Métrica 1).**
- **Por hora**, las mujeres ganan **{f1(tot['brecha_hora_pct'])} % menos** (IC 95 %: {ci(tot['brecha_hora_inf'], tot['brecha_hora_sup'])}; p < 0.001). Por nivel de instrucción: **{f1(bn.iloc[0]['brecha_hora_pct'])} %** (primaria incompleta), **{f1(bn.iloc[1]['brecha_hora_pct'])} %** (primaria), **{f1(bn.iloc[2]['brecha_hora_pct'])} %** (secundaria) y **{f1(bn.iloc[3]['brecha_hora_pct'])} %** (medio superior y superior).
  **Las cuatro son estadísticamente significativas** aun tras el ajuste de Holm (p ajustado < 0.001 en todos los niveles), y las pruebas clásicas coinciden.
- **Tamaño de efecto:** la *d* de Cohen es **pequeña** ({bn.iloc[3]['d_cohen']:.2f} a {bn.iloc[0]['d_cohen']:.2f}). Con 112 mil observaciones casi cualquier diferencia es «significativa»; lo relevante es el tamaño: una brecha **real pero modesta por hora**, mayor entre quienes menos estudiaron.
- **Por mes**, la brecha es de **{f1(tot['brecha_mens_pct'])} %** (hasta {f1(bn.iloc[0]['brecha_mens_pct'])} % en primaria incompleta). ¿De dónde sale la diferencia? **De las horas:** las mujeres de la muestra trabajan {tot['horas_m']:.1f} h por semana y los hombres {tot['horas_h']:.1f} h, es decir **{f1(tot['menos_horas_mujeres_pct'])} % menos**.
  En logaritmos la identidad es exacta: *brecha mensual = brecha por hora + brecha de horas*. La desigualdad mensual **no es principalmente de salario por hora, sino de horas pagadas**, que reflejan la división del trabajo de cuidados.

#### ¿Cuánto cambia la brecha al comparar personas parecidas?
""")

code("""
esc = leer("escalera_brecha")
display(ver(esc[["modelo", "brecha_pct", "brecha_pct_inf", "brecha_pct_sup", "p", "r2", "n_parametros"]], 3))
fig = viz.fig_escalera(esc); plt.show()
""")

md(f"""
**Lectura.** Sin controles la brecha es {f1(g0['brecha_pct'])} %; al comparar personas con **la misma escolaridad** sube a {f1(esc.loc['G1 + escolaridad', 'brecha_pct'])} % (las mujeres de la muestra tienen *más* escolaridad, lo que oculta parte de la brecha) y se estabiliza en **{f1(g5['brecha_pct'])} %** (IC 95 %: {ci(g5['brecha_pct_inf'], g5['brecha_pct_sup'])}) con edad, entidad, localidad, posición, informalidad y rama.
El modelo **G6** agrega las horas trabajadas y la brecha se dispara a {f1(esc.loc['G6 + horas trabajadas', 'brecha_pct'])} %, pero ese número **no se debe interpretar**: el ingreso por hora es ingreso mensual ÷ horas, de modo que cualquier error en las horas crea una relación negativa mecánica
entre ingreso por hora y horas (el «sesgo de división»). Se muestra para transparencia, no como resultado.

#### Descomposición de Oaxaca-Blinder: ¿cuánto se explica por características?
Se separa la brecha en una parte **explicada** (porque hombres y mujeres difieren en escolaridad, edad, lugar, empleo, rama) y una **no explicada** (distinto pago por las mismas características), con la referencia agrupada de Neumark (1988) y bootstrap de diseño.
""")

code("""
display(ver(leer("oaxaca").query("especificacion.str.startswith('Principal')")[["componente", "log_puntos", "ee", "ic_inf", "ic_sup", "p"]], 4))
fig = viz.fig_oaxaca(leer("oaxaca")); plt.show()
""")

md(f"""
**Resultado.** La brecha total ({o_total['log_puntos'] * 100:.1f} puntos logarítmicos) es la **suma** de una parte explicada **negativa** ({o_exp['log_puntos'] * 100:.1f}: las características medibles de las mujeres —sobre todo su **mayor escolaridad** ({o_esc['log_puntos'] * 100:.1f})— *favorecerían* un ingreso por hora más alto)
y una parte **no explicada positiva de {o_noexp['log_puntos'] * 100:.1f} puntos** (IC 95 %: {o_noexp['ic_inf'] * 100:.1f} a {o_noexp['ic_sup'] * 100:.1f}). Dicho de otra forma: si las mujeres fueran pagadas como los hombres con las mismas características, **ganarían ≈ {o_noexp['log_puntos'] * 100:.0f} % más por hora**.
El residuo no explicado agrupa discriminación, características no observadas (ocupación específica, experiencia real, negociación) y diferencias de selección; por eso es una **cota** de desigualdad no atribuible a lo medido, no una prueba de discriminación.
Los resultados con los coeficientes de los hombres o de las mujeres como referencia llevan a la misma conclusión (tabla completa en `results/oaxaca.csv`).

#### ¿En qué parte de la distribución está la brecha?
""")

code("""
cu = leer("brecha_cuantiles")
display(ver(cu, 3))
fig = viz.fig_cuantiles(cu); plt.show()
""")

md(f"""
**Resultado.** La brecha por hora **se concentra abajo**: {f1(cu.loc[10, 'brecha_pct'])} % en el percentil 10 y {f1(cu.loc[25, 'brecha_pct'])} % en el 25 (ambas significativas), pero en el percentil 50 es {f1(cu.loc[50, 'brecha_pct'])} % (IC 95 %: {ci(cu.loc[50, 'inf'], cu.loc[50, 'sup'])}), y arriba (P75 y P90) es nula o incluso ligeramente favorable a las mujeres.
Es un patrón de **«piso pegajoso»**: la desventaja pesa más donde el salario es bajo (informalidad, servicio doméstico, comercio). Esto sugiere que políticas como el salario mínimo o la formalización inciden más en la brecha que las que apuntan a puestos directivos.
*(Nota: las medianas de ingreso tienen «heaping» —cifras redondas—, por lo que sus intervalos son discretos.)*

#### ¿Es homogénea la brecha?
""")

code("""
sub = leer("brecha_subgrupos")
display(ver(sub[["dimension", "categoria", "n_hombres", "n_mujeres", "brecha_pct", "inf", "sup", "p_holm_dimension"]], 2))
""")

md("""
**Lectura.** La brecha por hora es **significativa entre informales** (4.3 %) y **no entre formales** (1.2 %, IC que incluye 0); es mayor entre **empleadores** (7.8 %) que entre asalariados (1.6 %); y es mayor en localidades pequeñas y medianas (6–8 %) que en la región Sur (1.1 %, no significativa).
Dentro del nivel «medio superior y superior» la brecha es de 7.8 % (12–15 años) y 5.9 % (licenciatura o posgrado), **mayores que el 3.9 % del agregado**: es un efecto de composición (en el subnivel universitario hay más mujeres que hombres, y ese subnivel paga más); por eso es valioso mirar por subnivel.

#### Robustez: ¿cuánto dependen estos resultados de las decisiones metodológicas?
""")

code("""
rob = leer("robustez_brecha")
display(ver(rob[rob["grupo"] == "Total"][["especificacion", "descripcion", "brecha_pct", "inf", "sup", "p", "n"]], 3))
fig = viz.fig_robustez(rob); plt.show()
""")

md(f"""
**Lectura honesta de la robustez.**
- El **signo** de la brecha por hora es positivo en todas las muestras, pero su **tamaño depende de a quién se incluya**: de {hora_specs['brecha_pct'].min():.1f} % (S3, con rangos imputados) a {hora_specs['brecha_pct'].max():.1f} % (S7, sin ponderar).
- **S2 (solo asalariados):** {rob_tot.loc['S2 Solo asalariados', 'brecha_pct']:.1f} % (IC 95 %: {ci(rob_tot.loc['S2 Solo asalariados', 'inf'], rob_tot.loc['S2 Solo asalariados', 'sup'])}): la brecha es menor donde el ingreso es un salario (no una ganancia de negocio propio).
- **S3 (imputar el grupo B):** {rob_tot.loc['S3 Con rangos imputados', 'brecha_pct']:.1f} % (IC 95 %: {ci(rob_tot.loc['S3 Con rangos imputados', 'inf'], rob_tot.loc['S3 Con rangos imputados', 'sup'])}), **no significativa**. Pero esta especificación **sesga hacia cero por construcción**: la imputación asigna *el mismo* ingreso a un hombre y a una mujer del mismo rango, borrando cualquier diferencia dentro del rango. Es una cota inferior, no una estimación puntual.
- **S4 (corregir por no respuesta, IPW):** {rob_tot.loc['S4 Ajuste por no respuesta', 'brecha_pct']:.1f} %: al dar más peso a quienes se parecen a los que no declararon, la brecha *aumenta*.
- **S8 (ajustada, sin horas):** **{rob_tot.loc['S8 Ajustada (sin horas)', 'brecha_pct']:.1f} %** (IC 95 %: {ci(rob_tot.loc['S8 Ajustada (sin horas)', 'inf'], rob_tot.loc['S8 Ajustada (sin horas)', 'sup'])}), la estimación más robusta de «personas parecidas».
**Conclusión sobre M1:** hay evidencia **consistente y significativa** de una brecha por hora de entre {hora_specs['brecha_pct'].min():.1f} y {hora_specs['brecha_pct'].max():.1f} % antes de controles y de ≈ {g5['brecha_pct']:.0f} % entre personas comparables, concentrada en la parte baja de la distribución; la **brecha mensual de ≈ {tot['brecha_mens_pct']:.0f} %** es indiscutible y se debe sobre todo a menos horas pagadas.

### 5.3 Objetivo 3 · Informalidad laboral
**Definición.** TIL1 = ocupados en empleo informal (`emp_ppal = 1`) ÷ ocupados de 15+, ponderado; es la tasa que publica el INEGI (55.0 % nacional, verificada en la sección 2.4).
""")

code("""
til = x["til1_entidad"]
fig = viz.fig_mapa_informalidad(til); plt.show()
""")

code("""
g = leer("til1_grupos")
display(ver(g, 2))
t = til.sort_values("til1_est", ascending=False)[["entidad", "region", "til1_est", "til1_ic_inf", "til1_ic_sup", "til1_rango", "til1_rango_inf", "til1_rango_sup", "esc15_est"]]
display(Markdown("**Cinco entidades con mayor y cinco con menor informalidad:**"))
display(ver(pd.concat([t.head(5), t.tail(5)]), 2))
""")

md(f"""
**Resultados.** La informalidad nacional es **{f1(nac['est'])} %** (IC 95 %: {ci(nac['ic_inf'], nac['ic_sup'])}). Las entidades con más informalidad son **{R['til1']['top3'][0]['entidad']} ({f1(R['til1']['top3'][0]['pct'])} %), {R['til1']['top3'][1]['entidad']} ({f1(R['til1']['top3'][1]['pct'])} %) y {R['til1']['top3'][2]['entidad']} ({f1(R['til1']['top3'][2]['pct'])} %)**; las de menos, **{R['til1']['bottom3'][0]['entidad']} ({f1(R['til1']['bottom3'][0]['pct'])} %), {R['til1']['bottom3'][1]['entidad']} ({f1(R['til1']['bottom3'][1]['pct'])} %) y {R['til1']['bottom3'][2]['entidad']} ({f1(R['til1']['bottom3'][2]['pct'])} %)**.
Por región: Norte {f1(R['til1']['regiones']['Norte'])} %, Centro-Norte {f1(R['til1']['regiones']['Centro-Norte'])} %, Centro {f1(R['til1']['regiones']['Centro'])} %, Sur {f1(R['til1']['regiones']['Sur'])} %.
Por escolaridad: {f1(R['til1']['por_nivel']['1'])} % (primaria incompleta), {f1(R['til1']['por_nivel']['2'])} %, {f1(R['til1']['por_nivel']['3'])} % y {f1(R['til1']['por_nivel']['4'])} % (medio superior y superior): **la escolaridad es la gran frontera de la informalidad**.
Las mujeres tienen una tasa ligeramente mayor ({f1(R['til1']['mujeres']['est'])} % vs. {f1(R['til1']['hombres']['est'])} %).

#### Relación entre la escolaridad y la informalidad
""")

code("""
asoc = leer("til1_vs_escolaridad_estatal")
display(ver(asoc, 3))
fig = viz.fig_informalidad_vs_escolaridad(til, asoc.set_index("indicador").loc["rho_spearman_til_esc", "est"]); plt.show()
display(Markdown("**Modelo individual** (logit ponderado de P(empleo informal), con errores robustos de diseño; controla sexo, edad, entidad y tamaño de localidad):"))
display(ver(leer("logit_informalidad"), 3))
""")

md(f"""
**Resultados.** Entre estados, la escolaridad promedio y la informalidad tienen una relación **muy fuerte y negativa**: Spearman = {R['til1_vs_escolaridad_estatal']['rho_spearman_til_esc']['est']:.2f} (IC 95 %: {ci(R['til1_vs_escolaridad_estatal']['rho_spearman_til_esc']['ic_inf'], R['til1_vs_escolaridad_estatal']['rho_spearman_til_esc']['ic_sup'], 2)}) y una pendiente de **{R['til1_vs_escolaridad_estatal']['pendiente_til_esc']['est']:.1f} puntos porcentuales por cada año de escolaridad promedio**.
A nivel **individual** (que es el que importa para la causalidad plausible, no la falacia ecológica), cada año de escolaridad reduce los momios de informalidad a {np.exp(leer('logit_informalidad').set_index('variable').loc['anios_esc', 'coef']):.2f} veces (RM; IC 95 %: {leer('logit_informalidad').set_index('variable').loc['anios_esc', 'rm_inf']:.2f}–{leer('logit_informalidad').set_index('variable').loc['anios_esc', 'rm_sup']:.2f}),
es decir **{abs(ind['ame_anios_esc_pp']):.1f} puntos porcentuales menos de probabilidad** por año (efecto marginal promedio); y, a igual escolaridad, edad y lugar, **ser mujer suma {ind['ame_mujer_pp']:.1f} puntos** a la probabilidad de estar en un empleo informal.

### 5.4 Diagnóstico de supuestos del modelo
""")

code("""
diag = M.diagnosticos(W, D.diseno)
res = pd.DataFrame({"prueba": ["Breusch-Pagan (heterocedasticidad)", "VIF máximo (variables clave)", "Distancia de Cook máxima", "Asimetría de los residuos", "Curtosis exceso de los residuos", "Coef. de «mujer» con todo / sin el 0.1 % más influyente"],
                    "resultado": [f"LM = {diag['breusch_pagan_LM']:,.0f}, p = {diag['breusch_pagan_p']:.1e}", f"{diag['vif_max_variables_clave']:.2f}", f"{diag['cook_max']:.5f}", f"{diag['asimetria_residuos']:.2f}", f"{diag['curtosis_exceso_residuos']:.2f}", f"{diag['coef_mujer_con_todo']:.4f} / {diag['coef_mujer_sin_influyentes']:.4f}"]})
display(ver(res, 2))
fig = viz.fig_diagnosticos(diag["residuos_ols"], diag["ajustados_ols"]); plt.show()
""")

md(f"""
**Lectura.** (i) Hay **heterocedasticidad** (Breusch-Pagan rechaza homocedasticidad) y colas algo pesadas (curtosis en exceso ≈ {dg['curtosis_exceso_residuos']:.1f}); por eso toda la inferencia usa **errores estándar robustos de diseño** y no supuestos de normalidad.
(ii) **No hay multicolinealidad** problemática (VIF máximo {dg['vif_max_variables_clave']:.1f}; centrar la edad ayudó). (iii) **No hay observaciones influyentes** (Cook máxima {dg['cook_max']:.4f}) y el coeficiente de «mujer» casi no cambia al quitar el 0.1 % más influyente.
(iv) Los contrastes de normalidad (D'Agostino, Shapiro) rechazan, como ocurre con cualquier muestra de 112 mil observaciones; no importa porque la inferencia no los usa.
""")

# =========================================================================================== #
md(f"""
## 6. Interpretación (KDD fase 5 · Semana 5)

### 6.1 Hallazgos
1. **La escolaridad paga, y más al final del camino.** Cada año adicional eleva el ingreso por hora ≈ {f1(rt['nacional_pct']['est'])} %; terminar licenciatura o posgrado paga {prem.loc['Licenciatura o posgrado (16+ años)', 'premio_pct']:.0f} % más que no terminar primaria. El rendimiento por año **no depende de la riqueza del estado** (diferencia Q4−Q1 ≈ 0, p = {dq['p']:.2f}) y es **mayor para las mujeres** (+{rt['dif_mujeres_hombres_log']['est'] * 100:.1f} puntos).
2. **La brecha de género es pequeña por hora, grande por mes, y se concentra abajo.** {f1(bh['brecha_hora_pct'])} % por hora (de {f1(bn.iloc[3]['brecha_hora_pct'])} % a {f1(bn.iloc[1]['brecha_hora_pct'])} % según el nivel), {f1(bm['brecha_mens_pct'])} % por mes por menos horas pagadas; ≈ {g5['brecha_pct']:.0f} % entre personas comparables; {f1(cu.loc[10, 'brecha_pct'])}–{f1(cu.loc[25, 'brecha_pct'])} % en el 10–25 % más bajo de la distribución y nula arriba.
3. **La informalidad se reduce con la escolaridad** y refleja una geografía muy marcada (Sur {f1(R['til1']['regiones']['Sur'])} % vs. Norte {f1(R['til1']['regiones']['Norte'])} %).
4. **El «ingreso cero» es mayoritariamente información incompleta, no ausencia de ingreso** ({B_t:.0f} % da solo un rango, {D_t:.0f} % no especifica); y falta más entre quienes más estudiaron, lo que sesga análisis de «casos completos».

### 6.2 Cumplimiento de las métricas de éxito del protocolo
""")

code("""
resumen = json.loads((C.RESULTS / "resumen.json").read_text(encoding="utf-8"))
bn = leer("brecha_nivel"); ret = leer("retorno_entidad")
p_max = bn[bn["nivel"] != "Total"]["p_hora_holm"].max()
cumple = pd.DataFrame([
    ("M1", "Brecha por hora (%) para cada nivel de instrucción, con IC 95 % y prueba (p < 0.05)",
     f"4 niveles + total con IC; p ajustado (Holm) máximo = {p_max:.4f}", "Sí"),
    ("M2", "Spearman escolaridad-ingreso para las 32 entidades con IC bootstrap y ranking",
     f"{ret['rho_est'].notna().sum()} entidades con IC 95 % de {resumen['B']:,} réplicas de Rao-Wu; ranking con intervalo de lugar", "Sí"),
    ("M3", "Tablero con ≥ 4 visualizaciones alimentado por un pipeline que carga a una base NoSQL consultable por entidad",
     "tablero/tablero_enoe.html: mapa, ranking, 2 dispersiones, brechas, calidad del ingreso + tabla; lee la colección «entidades» exportada para MongoDB", "Sí"),
    ("Dataset", "≥ decenas de miles de registros, fuente oficial, con suciedad real, documentado",
     f"{resumen['muestras']['universo']:,} ocupados (419,038 registros); INEGI; 36 % de ingreso 0 y faltantes codificados; diccionario de datos", "Sí"),
    ("Visualización (Sem. 5)", "≥ 4 gráficos justificados y honestos", "16 figuras con paleta validada para daltonismo, IC y sin ejes duales", "Sí"),
    ("Ingeniería (Sem. 6)", "Pipeline de carga a una base", "ETL idempotente → SQLite (PK/FK/CHECK, vistas, auditoría)", "Sí"),
    ("NoSQL (Sem. 7)", "Justificación del modelo de datos elegido", "Persistencia políglota SQLite + MongoDB (sección 4.4); documentos NDJSON listos para mongoimport", "Sí"),
], columns=["Criterio", "Qué pedía", "Cómo se cumple", "¿Cumple?"])
display(cumple.style.hide(axis="index"))
""")

md(f"""
### 6.3 Recomendaciones
- **Política educativa:** como el rendimiento por año de estudio es ≈ {f1(rt['nacional_pct']['est'])} % *en todos los estados* y el premio se concentra en terminar licenciatura y posgrado, **ampliar el acceso y la permanencia** rinde en todas las regiones; el Sur, con la mayor informalidad ({f1(R['til1']['regiones']['Sur'])} %) y menos escolaridad, es donde el margen de mejora es mayor.
- **Formalización:** la informalidad cae de {f1(R['til1']['por_nivel']['1'])} % a {f1(R['til1']['por_nivel']['4'])} % con la escolaridad; los programas de formalización deben acompañarse de capacitación y certificación en estados con baja escolaridad (Oaxaca, Guerrero, Chiapas).
- **Igualdad de género:** el problema principal no es el pago *por hora* sino las **horas pagadas** (−{f1(tot['menos_horas_mujeres_pct'])} %) → políticas de cuidados (guarderías, horarios flexibles de tiempo completo) y atención al «piso pegajoso» (los percentiles bajos), donde actúan el salario mínimo y la formalización.
- **Medición:** el INEGI podría publicar ingresos imputados por rango para el {B_t:.0f} % que solo declara un rango, y se recomienda reportar siempre el ingreso con su corrección por no respuesta.

### 6.4 Limitaciones y amenazas a la validez
- **Correlación, no causalidad.** El rendimiento estimado mezcla el efecto de estudiar con habilidad no observada y redes sociales (sesgo de variable omitida). Las comparaciones entre estados no son causales (falacia ecológica).
- **Sesgo de selección.** Solo se observa ingreso de quien trabaja y lo declara; la participación laboral femenina es selectiva (la brecha entre las trabajadoras comparables podría subestimar la desventaja total). Se mitigó con IPW y análisis con rangos imputados.
- **Medición del ingreso.** Autorreportado, con redondeo («heaping») y subdeclaración; el ingreso por hora usa las horas *de la semana pasada*, lo que introduce ruido y el sesgo de división (por eso no se interpreta el modelo con horas).
- **La imputación por rangos** atenúa la brecha por construcción (cota inferior). El significado literal de cada código de `p6c` se infirió de su correspondencia exacta con `ing7c`; conviene contrastarlo con el cuestionario oficial.
- **Un solo trimestre** (4T-2025): sin dinámica temporal ni estacionalidad. El diseño de panel rotativo de la ENOE no se explota.
- **Precisión por estado.** 1,900–5,900 observaciones salariales por entidad y un efecto de diseño ≈ 3–5: los rankings estatales se reportan con intervalos y solo se afirman los extremos.
- **Decisiones del analista** (ventana 15–65, recorte P0.5–P99.5, tope de 112 h) se documentan en `config.py` y se someten a sensibilidad.

## 7. Reproducibilidad
""")

code("""
meta = json.loads((C.RESULTS / "etl_meta.json").read_text(encoding="utf-8"))
display(ver(pd.DataFrame({"elemento": ["Python", "pandas", "numpy", "SQLite", "Semilla", "Réplicas bootstrap", "Periodo"],
                          "valor": [meta["python"], meta["pandas"], meta["numpy"], meta["sqlite"], meta["semilla"], resumen["B"], meta["periodo"]]}), 0))
print("Para reproducir todo desde los CSV de INEGI:")
print("  python scripts/run_etl.py && python scripts/run_analysis.py && python scripts/make_figures.py")
print("  python scripts/run_mongo.py --exportar && python scripts/build_dashboard.py && python scripts/build_notebook.py")
print("  python -m unittest discover -s tests")
""")

md("""
**Código y documentación.** Todo el código vive en `src/enoe/` (módulos documentados), los scripts en `scripts/`, las pruebas en `tests/` y la documentación en `docs/`
(diccionario de datos, metodología, modelo de datos NoSQL, guía de defensa). La presentación está en `presentacion/` y el tablero en `tablero/`.
""")

nb["cells"] = cells
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}

SALIDA = ROOT / "notebooks" / "Proyecto_Integrador_ENOE.ipynb"
print("Ejecutando cuaderno (celdas:", len(cells), ")...")
ep = ExecutePreprocessor(timeout=1800, kernel_name="python3")
ep.preprocess(nb, {"metadata": {"path": str(ROOT / "notebooks")}})
nbf.write(nb, SALIDA)
cuerpo, _ = HTMLExporter().from_notebook_node(nb)
(ROOT / "notebooks" / "Proyecto_Integrador_ENOE.html").write_text(cuerpo, encoding="utf-8")
print("Cuaderno escrito:", SALIDA, f"({SALIDA.stat().st_size / 1e6:.1f} MB) y HTML ({len(cuerpo) / 1e6:.1f} MB)")
