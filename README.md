# Radiografía socioeconómica de México: escolaridad, ingreso y brecha de género

**Proyecto Integrador de Ciencia de Datos** · Optativa III: Ciencia de Datos · Ingeniería en Computación, 9.º semestre · UNE Plantel Centro
**Equipo 1:** Juan Evelio Culin Grajeda · Angel Yireh Garcia Jara · Luis Andre Gutierrez Zuñiga
**Datos:** INEGI, Encuesta Nacional de Ocupación y Empleo (ENOE), 4.º trimestre de 2025 (SDEMT y COE2T)
**Sitio en línea:** <https://charginchif.github.io/proyecto-integrador-enoe/> · **Repositorio:** <https://github.com/charginchif/proyecto-integrador-enoe>

Ciclo KDD completo sobre 419,038 registros reales: selección y validación contra cifras oficiales, limpieza documentada, pipeline de ingeniería de datos
(SQLite + MongoDB), estadística con **diseño muestral complejo** (bootstrap de Rao-Wu), 17 visualizaciones y 8 diagramas explicativos, cuaderno narrado,
tablero interactivo, **informe técnico en Word** (67 páginas, explica todo en palabras sencillas), **dos presentaciones** (completa de 48 diapositivas y corta de 24)
y un **sitio web** con la **tesina en formato web** (el documento completo, con figuras interactivas y una **presentación breve** de 18 diapositivas con guion y reloj), una presentación de 11 láminas para exponer y una guía de estudio.

## Entregables

| Qué | Dónde |
|---|---|
| **Tesina web** (el documento principal): portada, resumen en español e inglés, hallazgos clave, ficha técnica, índice con figuras y tablas, 9 capítulos, bibliografía y 4 anexos; 14 figuras interactivas, tablas ordenables, búsqueda, tema claro y oscuro y ficha de la entidad elegida | `sitio/index.html` (doble clic; la carpeta `sitio/` es autocontenida) |
| **Presentación breve** (la ruta corta ★ de la presentación completa: 18 diapositivas, unos 18 minutos, con quién presenta cada bloque, guion y reloj); está dentro de la tesina: botón «Presentar», tecla `P` o `index.html#presentacion-breve` | `sitio/index.html` |
| **Presentación web** (11 láminas, casi sin texto): responde las 3 preguntas de investigación con gráficas interactivas, las 3 métricas de éxito, las competencias y la reflexión; `N` abre el guion | `sitio/presentacion.html` |
| **Guía de estudio** (versión larga con modo presentación): storytelling, ciclo KDD, semanas 1-7, protocolo, glosario, preguntas de defensa y autoevaluación | `sitio/estudio.html` |
| **Informe técnico** (Word y PDF): marco conceptual, datos, limpieza, ingeniería, metodología, resultados, discusión, glosario, guía de ejecución, preguntas de defensa y guion | `documento/Informe_Final_Proyecto_ENOE.docx` · `.pdf` |
| **Presentación completa** (48 diapositivas con guion en las notas; ★ = ruta corta de 18 diapositivas) | `presentacion/Presentacion_Completa_Proyecto_ENOE.pptx` · `.pdf` |
| Presentación corta (18 principales + 5 de respaldo) | `presentacion/Proyecto_Integrador_ENOE.pptx` |
| Cuaderno ejecutado y narrado | `notebooks/Proyecto_Integrador_ENOE.ipynb` · `.html` |
| Tablero interactivo (un solo archivo, sin internet) | `tablero/tablero_enoe.html` |

## Resultados clave

| | Resultado |
|---|---|
| Validación | Con la base oficial se reproducen **7 de 7** cifras del INEGI (PEA 61.3 M, TIL1 55.0 %, ...) |
| Calidad del ingreso | El «ingreso 0» (36 % de los registros) es sobre todo información incompleta: 22 % da solo un rango, 13 % no especifica, 4 % no recibe ingresos |
| Rendimiento de estudiar | **+5.1 % por hora por cada año de escolaridad** (IC 95 %: 5.0-5.3); licenciatura o posgrado paga +92 % frente a no terminar primaria; igual en estados ricos y pobres (p = 0.91) |
| Spearman por entidad | De 0.21 (Baja California Sur) a 0.49 (Ciudad de México); ranking con intervalo de lugar |
| Brecha de género | **3.7 % por hora** (IC 2.3-5.0) y **26.9 % por mes**: la diferencia mensual es de horas (−24 %); ≈ 8 % entre personas comparables; se concentra en el P10-P25 |
| Informalidad | 55.0 % nacional; 33 % (Coahuila) a 80 % (Oaxaca); 87 % sin primaria vs. 38 % con media superior o más; Spearman entre estados −0.86 |

## Estructura

```
Proyecto_ENOE/
├── README.md · requirements.txt
├── src/enoe/              paquete del pipeline (ver docstring de cada módulo)
│   ├── config.py          parámetros metodológicos y catálogos (única fuente de decisiones)
│   ├── extract.py         lectura tipada + SHA-256         · validacion.py   cifras oficiales del INEGI
│   ├── clean.py           reglas de limpieza + expectativas · transform.py    variables, unión 1:1, imputación
│   ├── load_sqlite.py     esquema en estrella (PK/FK/CHECK) · load_mongo.py   documentos y carga NoSQL
│   ├── survey.py          diseño complejo, Rao-Wu, Spearman ponderado, regresión/logit con Taylor
│   ├── estimadores.py · modelos.py · analisis.py   análisis estadístico
│   └── viz.py · viz_diagramas.py · figuras.py   gráficas con paleta validada para daltonismo y diagramas explicativos
├── scripts/               run_all · run_etl · run_analysis · make_figures · run_mongo · build_dashboard · build_notebook
│                          build_deck (corta) · build_deck_completa · build_informe · build_sitio (estudio.html) · build_sitio_lite (presentacion.html) · build_tesina (index.html)
│                          exportar_informe.ps1 · exportar_presentacion.ps1
│                          bibliotecas: deck_lib · deck_slides_base · deck_slides_extra · informe_lib · informe_datos · informe_s1…s4
│                                       sitio_lib · sitio_textos · sitio_contenido_a/b · sitio_estudio · sitio_assets/ (estilo.css, app.js)
│                                       informe_html (el informe en HTML) · web_datos (cifras de las páginas interactivas) · web_ruta_corta (presentación breve)
│                                       web_assets/ (charts.css/js compartidos · tesina.css/js · lite.css/js)
├── notebooks/             Proyecto_Integrador_ENOE.ipynb  (ejecutado)  y .html
├── tablero/               tablero_enoe.html  (un solo archivo, funciona sin internet)
├── sitio/                 index.html (tesina) · presentacion.html · estudio.html · img/ · cuaderno.html · tablero.html · descargas/*.pdf  (autocontenido)
├── documento/             Informe_Final_Proyecto_ENOE.docx y .pdf  (informe técnico, 67 páginas)
├── presentacion/          Presentacion_Completa_Proyecto_ENOE.pptx (48 diapositivas) · Proyecto_Integrador_ENOE.pptx (24), con notas del orador
├── docs/                  diccionario_de_datos · metodologia · modelo_de_datos_nosql · guia_de_defensa
├── results/               tablas CSV, resumen.json (cifras clave), bitácoras del ETL
├── figures/               17 figuras de datos (01…17) y 8 diagramas (D01…D08), PNG
├── data/processed/        enoe_2025t4.sqlite · mongo/*.ndjson
└── tests/                 pruebas unitarias, de método y de integración
```

## Cómo reproducir

Requisitos: Python 3.12 y los paquetes de `requirements.txt` (`pip install -r requirements.txt`).
Los microdatos de INEGI **no se incluyen** (pesan 300 MB): descárguelos de <https://www.inegi.org.mx/programas/enoe/15ymas/> (Microdatos, CSV, 4.º trimestre 2025) y apunte a la carpeta con `ENOE_SDEMT425.csv` y `ENOE_COE2T425.csv`:

```powershell
$env:ENOE_RAW_DIR = "C:\ruta\a\enoe_2025_trim4_csv"        # o copie los CSV a data\raw
python scripts/run_etl.py                    # 10 s   · limpia, valida y crea data/processed/enoe_2025t4.sqlite
python scripts/run_analysis.py               # ~5 min · 1,000 réplicas Rao-Wu; escribe results/ y tablas res_*
python scripts/make_figures.py               # 17 figuras de datos y 8 diagramas en figures/
python scripts/run_mongo.py --exportar       # documentos NoSQL + verificación contra SQL
python scripts/run_mongo.py --simulado --limite 20000   # (opcional) carga y pipeline contra mongomock, sin servidor (sin --limite: carga completa, ~6 min)
python scripts/build_dashboard.py            # tablero/tablero_enoe.html
python scripts/build_notebook.py             # ejecuta y exporta el cuaderno (.ipynb y .html)
python scripts/build_deck.py                 # presentación corta (.pptx, 24 diapositivas con notas del orador)
python scripts/build_deck_completa.py        # presentación completa (.pptx, 48 diapositivas, secciones y guion)
python scripts/build_informe.py              # informe técnico (.docx)
powershell -File scripts\exportar_informe.ps1   # (Windows con Word) actualiza el índice y exporta el PDF del informe
powershell -File scripts\exportar_presentacion.ps1   # (Windows con PowerPoint) exporta el PDF de la presentación completa
python scripts/build_sitio.py                # guía de estudio: sitio/estudio.html (usa results/, figures/, el guion de la presentación completa y los PDF)
python scripts/build_sitio_lite.py           # presentación de 11 láminas: sitio/presentacion.html (usa results/, SQLite y los documentos NoSQL)
python scripts/build_tesina.py               # tesina web: sitio/index.html (mismo texto que el informe en Word; usa results/, SQLite y las figuras de sitio/img)
python -m unittest discover -s tests         # pruebas
```
**Todo de una vez:** `python scripts/run_all.py` (≈ 10 min; `--rapido` usa 100 réplicas y omite cuaderno, presentaciones, informe y sitio).
Para una prueba rápida del análisis: `python scripts/run_analysis.py --B 100`.
Para cargar en un servidor MongoDB: `python scripts/run_mongo.py --uri mongodb://localhost:27017` (necesita `pymongo`; carga las colecciones y repite la verificación con el motor del servidor; ver `docs/modelo_de_datos_nosql.md`).

**Tesina web.** Abra `sitio/index.html` con doble clic (necesita internet solo para las tipografías; sin ellas se ve igual con las del sistema). Es HTML, CSS y JavaScript sin dependencias.
El texto, las tablas y las figuras salen de las mismas funciones que arman el informe en Word (`informe_s1.py` a `informe_s4.py`) mediante `informe_html.py`, así que una frase o una cifra se corrige en un solo lugar. Las figuras de datos se dibujan en el navegador a partir de los resultados; cada una conserva su imagen (botón «Imagen») y su tabla («Ver tabla»).
Funciones: índice lateral con la sección actual, búsqueda (tecla `/` o `Ctrl+K`), selector de entidad que resalta una entidad en todas las figuras y abre su ficha, definiciones al pasar el cursor por los términos del glosario, tablas ordenables y con filtro, tema claro u oscuro, calculadora del rendimiento de estudiar y un ejemplo de la misma consulta en SQL y en MongoDB. Al imprimir desde el navegador (guardar como PDF) se usa una hoja de estilo propia.
**Presentación breve.** Es la ruta corta de la presentación completa (las 18 diapositivas con ★) dentro de la tesina, con las mismas gráficas del documento. Se abre con el botón «Presentar» de la barra superior, la tecla `P` o la dirección `index.html#presentacion-breve`. `→` `Espacio` `↓` avanzan; `←` `↑` retroceden; `N` muestra u oculta el guion de quien expone (propuesta de quién presenta cada bloque); `T` inicia o pausa el reloj de 18 minutos (doble clic en el reloj lo reinicia y se pone ámbar si se pasa del tiempo sugerido); `F` pantalla completa; `Esc` sale; en el teléfono se desliza con el dedo. Los títulos y el guion se leen de las notas de `presentacion/Presentacion_Completa_Proyecto_ENOE.pptx` (`scripts/web_ruta_corta.py`); si se cambian las diapositivas con ★ hay que regenerar con `python scripts/build_tesina.py`.
**Presentación y guía de estudio.** `sitio/presentacion.html` son 11 láminas del Proyecto 1 para exponer (`↑ ↓ ← →` o `Espacio` cambian de lámina, `N` abre el guion, `F` pantalla completa); `sitio/estudio.html` es la versión larga con modo presentación (`#presentar`), guion y reloj. Las cifras salen de `results/`, de la base SQLite y de los documentos NoSQL: si se vuelve a correr el análisis basta con `python scripts/build_sitio.py`, `python scripts/build_sitio_lite.py` y `python scripts/build_tesina.py`.

**Publicación en GitHub Pages.** Se sirve la rama `main` desde la raíz (Settings → Pages → Deploy from a branch → `main` / `(root)`): el `index.html` de la raíz redirige a `sitio/` y `.nojekyll` evita que Jekyll procese los archivos.
Para actualizar la página: regenerar con `python scripts/build_sitio.py`, `python scripts/build_sitio_lite.py` y `python scripts/build_tesina.py` y luego `git add -A`, `git commit` y `git push`; GitHub tarda uno o dos minutos en reflejarlo.

## Qué se verificó y qué no

* ✔ 15 expectativas de datos, 7 cifras oficiales del INEGI, ETL idempotente, pruebas automáticas, equivalencia SQL ↔ agregación de MongoDB sobre los documentos exportados.
* ✔ Cuaderno ejecutado de principio a fin; sus conclusiones tienen aserciones que impiden construirlo si dejaran de ser ciertas.
* ✔ Capa documental probada **sin servidor, con mongomock** (simulador de MongoDB en memoria): carga completa por lotes de los 190,187 documentos de persona, los 32 de entidad y el de metadatos, recarga idempotente, siete índices, documentos BSON válidos y el pipeline de agregación «TIL1 por entidad» ejecutado en el motor, que reproduce la vista SQL (diferencia máxima 0.0049 pp). 41 pruebas automáticas en total, 7 de ellas de esta capa.
* ⚠ **No se ejecutó la carga a un servidor MongoDB real** (no hay servidor instalado en la máquina de desarrollo): mongomock imita la API y la agregación, pero no es MongoDB. `python scripts/run_mongo.py --uri ...` hace la carga y las mismas verificaciones contra un servidor; los documentos también están listos para `mongoimport`.
* ⚠ La redacción literal de los códigos de `p6c` (rangos de salarios mínimos) se infirió de su correspondencia exacta con `ing7c`; conviene contrastarla con el cuestionario oficial.
* ⚠ Las cifras oficiales del INEGI usadas para validar se consultaron mediante búsqueda web de los boletines del 4T-2025; contrástelas con el PDF oficial antes de exponer.

## Datos y licencia
Microdatos públicos del INEGI (anonimizados). Material académico; cite la fuente: INEGI, ENOE 2025-T4.
