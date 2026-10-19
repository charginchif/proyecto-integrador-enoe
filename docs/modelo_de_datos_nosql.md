# Modelo de datos: relacional + documental (Semanas 6 y 7)

Proyecto Integrador de Ciencia de Datos · ENOE 2025 T4 · Equipo 1

## 1. Decisión de arquitectura: persistencia políglota

El protocolo pide una «justificación del modelo de datos elegido» y, de ser pertinente, su implementación. La conclusión del equipo es que **ningún modelo único es óptimo** para los dos usos del proyecto:

| Uso | Patrón de acceso | Modelo elegido | Por qué |
|---|---|---|---|
| **Análisis** estadístico | Agregaciones ponderadas (`SUM(fac_tri × x) / SUM(fac_tri)`) sobre 190 mil filas, `JOIN` con dimensiones, regresiones sobre 112 mil filas | **Relacional · SQLite** (esquema en estrella) | Datos **tabulares de esquema fijo**; SQL expresa bien `GROUP BY`/`JOIN`; las restricciones `PRIMARY KEY`, `FOREIGN KEY` y `CHECK` hacen que el motor rechace datos inconsistentes; un solo archivo transaccional (ACID), sin servidor, reproducible |
| **Servicio de lectura** (tablero, API) | «Dame la ficha de la entidad 20» | **Documental · MongoDB** | Se lee **un documento por clave** con todos sus indicadores anidados (patrón *embedding*), sin `JOIN`; el esquema puede crecer (otros trimestres, otros indicadores) sin migraciones; escala horizontalmente por entidad |

SQLite es la **fuente de verdad** (con linaje y auditoría); los documentos de MongoDB son una **vista materializada** de lectura que se regenera con `scripts/run_mongo.py`.

### ¿Por qué no solo MongoDB, o solo SQLite?
* *Solo MongoDB:* las agregaciones ponderadas y los `JOIN` con dimensiones son menos naturales y menos eficientes; se pierden las restricciones de integridad referencial. Los datos de la ENOE **no son semiestructurados**: son una tabla rectangular.
* *Solo SQLite:* servir la ficha completa de una entidad exige varios `JOIN`/consultas y el esquema relacional es rígido ante nuevos indicadores. Para un tablero multiusuario conviene un almacén de documentos.
* *No es un caso de uso para «big data»:* 190 mil filas caben en memoria; la elección responde al **patrón de acceso**, no al volumen.

## 2. Modelo relacional (SQLite)

Archivo `data/processed/enoe_2025t4.sqlite`. Esquema en estrella:

```
                     dim_entidad ─┐
 dim_sexo ─┐                      │
 dim_nivel_instruccion ─┐         │
 dim_nivel_detalle ──┐  │         │
 dim_posicion_ocupacion ┼─ fact_ocupado (190,187 filas) ── dim_upm (21,194)
 dim_rama ───────────┘  │         │
 dim_tamano_localidad ──┘         │
 dim_ing7c ─ dim_grupo_ingreso ───┘
```

* **Integridad:** `PRAGMA foreign_keys = ON`; `CHECK (fac_tri > 0)`, `eda BETWEEN 15 AND 98`, `emp_ppal IN (1,2)`, `hrsocup_raw BETWEEN 0 AND 168`, etc. Verificación al cargar: `integrity_check = ok`, 0 violaciones de llave foránea.
* **Índices:** `(cve_ent)`, `(upm)`, `(cve_ent, sex)`, `(en_muestra_salarial, cve_ent)`, `(grupo_ingreso)`.
* **Vistas:** `v_til_entidad`, `v_escolaridad_entidad`, `v_calidad_ingreso_entidad`, `v_muestra_salarial`.
* **Auditoría/linaje:** `etl_run` (versiones, semilla, SHA-256 de los archivos de origen), `etl_bitacora`, `etl_embudo_salarial`, `etl_expectativas`, `etl_validacion_externa`.
* **Resultados del análisis:** tablas `res_*`.

```sql
-- TIL1 ponderado por entidad (vista v_til_entidad)
SELECT e.entidad, ROUND(100.0 * SUM(f.fac_tri * f.informal) / SUM(f.fac_tri), 2) AS til1_pct
FROM fact_ocupado f JOIN dim_entidad e USING (cve_ent)
GROUP BY e.entidad ORDER BY til1_pct DESC;
```

## 3. Modelo documental (MongoDB)

Base `enoe_2025t4`, tres colecciones (archivos en `data/processed/mongo/`):

### 3.1 `entidades` (32 documentos, `entidades.ndjson` / `entidades.json`)
Un documento por entidad; todo lo que el tablero muestra al elegir un estado vive en un solo documento (*embedding*):

```json
{
  "_id": 20, "cve_ent": 20, "entidad": "Oaxaca", "abreviatura": "OAX", "region": "Sur", "periodo": "2025-T4",
  "muestra": {"universo": 6282, "ventana_15_65": 5899, "salarial": 3216, "ocupados_estimados": 1806311},
  "informalidad": {"til1_pct": 80.06, "ic95": [78.11, 81.88], "lugar": 1, "lugar_ic95": [1, 1]},
  "escolaridad": {"anios_medios_ocupados": 9.07, "ic95": [8.82, 9.33], "anios_medios_muestra_salarial": 9.65},
  "ingreso_hora": {"mediana_pesos": 41.34, "ic95": [39.99, 41.98], "lugar": 27, "cuartil": 1},
  "rendimiento_escolaridad": {"pct_por_anio": 6.18, "ic95": [5.21, 7.17]},
  "correlacion_spearman": {"rho": 0.28, "ic95": [0.23, 0.33], "lugar": 20, "lugar_ic95": [10, 29]},
  "brecha_genero": {"hora_pct": 16.5, "hora_ic95": [7.3, 25.0], "mensual_pct": 40.7, "mensual_ic95": [33.4, 47.8]},
  "calidad_ingreso_pct": {"A": 58.0, "B": 14.0, "C": 18.0, "D": 10.0}
}
```
**Decisión de diseño — embeber vs. referenciar:** los intervalos, rankings y desgloses **se leen siempre junto con la entidad** y no se actualizan por separado → se **embeben** (una lectura, sin `JOIN`). Los datos de persona, en cambio, **no** se embeben dentro de la entidad (190 mil documentos en un solo documento superarían el límite de 16 MB de BSON y harían la entidad ilegible); viven en su propia colección y se relacionan por `cve_ent`.

### 3.2 `personas` (190,187 documentos, `personas.ndjson.gz`) — ejemplo ilustrativo (los valores no son de una persona real)
```json
{"_id": "20-…", "cve_ent": 20, "entidad": "Oaxaca", "fac_tri": 187,
 "persona": {"sexo": "Mujer", "edad": 34, "escolaridad": {"anios": 9, "nivel": "Secundaria completa"}},
 "trabajo": {"posicion": "Subordinado y remunerado", "informal": true, "rama": "Comercio", "horas_semana": 40, "tamano_localidad": "2,500 a 14,999"},
 "ingreso": {"grupo": "A", "rango_sm": "Hasta 1 SM", "mensual": 6450, "por_hora": 37.5, "ln_por_hora": 3.62, "mensual_imputado": 6450},
 "diseno": {"upm": 2012345},
 "muestras": {"ventana_15_65": true, "salarial": true}}
```
Subdocumentos (`persona`, `trabajo`, `ingreso`, `diseno`, `muestras`) agrupan atributos por tema, lo que permite proyecciones como `{"trabajo.informal": 1, "fac_tri": 1}`.

### 3.3 `metadatos` (1 documento): linaje del pipeline (versiones, semilla, parámetros, huellas SHA-256).

### 3.4 Índices (`load_mongo.INDICES`)
| Colección | Índice | Para qué |
|---|---|---|
| `entidades` | `{cve_ent: 1}` único | Ficha por clave (`find_one`) |
| `entidades` | `{region: 1}`, `{"informalidad.til1_pct": -1}` | Filtrar por región; ranking de informalidad |
| `personas` | `{cve_ent: 1}` | Consultas por entidad |
| `personas` | `{cve_ent: 1, "ingreso.grupo": 1}` | Calidad del ingreso por entidad |
| `personas` | `{cve_ent: 1, "persona.sexo": 1}` | Comparaciones por sexo |
| `personas` | `{cve_ent: 1, "ingreso.por_hora": 1}` **parcial** (`muestras.salarial: true`) | Solo la muestra salarial: índice más pequeño. Su clave difiere de `{cve_ent: 1}` a propósito: antes de MongoDB 7.3 dos índices con la misma clave que solo se distinguen por sus opciones dan `IndexOptionsConflict` |

### 3.5 Consultas equivalentes

| Pregunta | SQL | MongoDB |
|---|---|---|
| Ficha de Oaxaca | `SELECT * FROM v_… WHERE cve_ent = 20` | `db.entidades.findOne({cve_ent: 20})` |
| TIL1 por entidad (ponderado) | `SUM(fac_tri*informal)/SUM(fac_tri) … GROUP BY cve_ent` | `db.personas.aggregate([{$group: {_id: "$cve_ent", ocupados: {$sum: "$fac_tri"}, informales: {$sum: {$cond: ["$trabajo.informal", "$fac_tri", 0]}}}}, {$project: {til1_pct: {$multiply: [100, {$divide: ["$informales", "$ocupados"]}]}}}])` |
| Estados con TIL1 > 70 % | `… HAVING til1_pct > 70` | `db.entidades.find({"informalidad.til1_pct": {$gt: 70}}, {entidad: 1, "informalidad.til1_pct": 1})` |

## 4. Verificación

* `scripts/run_mongo.py --exportar` genera los documentos y **comprueba que el pipeline de agregación «TIL1 por entidad» calculado sobre los documentos reproduce la vista SQL** `v_til_entidad` (diferencia máxima 0.005 puntos porcentuales, el redondeo a 2 decimales del SQL).
* `scripts/run_mongo.py --simulado` (requiere `pip install pymongo mongomock`) hace además la **carga completa contra mongomock**, un simulador de MongoDB en memoria: inserta por lotes los 190,187 documentos de persona, los 32 de entidad y el de metadatos con la misma API de `pymongo` que se usaría con un servidor, vuelve a cargar reemplazando las colecciones, crea los siete índices, comprueba que **todos los documentos son BSON válido** y ejecuta `PIPELINE_TIL1_POR_ENTIDAD` en el motor de agregación. Resultado de la corrida completa: 32 entidades y una diferencia máxima de 0.0049 puntos porcentuales frente a la vista SQL (el redondeo a 2 decimales del SQL), en unos 6 minutos porque mongomock evalúa el pipeline en Python.
* `tests/test_mongo_simulado.py` repite una versión rápida dentro de las pruebas automáticas (3,000 personas; conteos, idempotencia, índices, índice único, ficha por clave, BSON válido y pipeline con las 32 entidades). Se omite si faltan `pymongo`, `mongomock` o la base SQLite.
* El tablero (`tablero/tablero_enoe.html`) se alimenta de `entidades.json`, es decir, de la colección «entidades» exportada.

> **Alcance de la verificación (honestidad técnica).** En el equipo de desarrollo no hay un servidor MongoDB, así que la **carga a un servidor real no se ejecutó**. Lo que sí se verificó es (a) la construcción de los documentos y su exportación, (b) la equivalencia de la consulta de agregación con la lógica en Python y ejecutando el pipeline en mongomock, (c) la carga por lotes, el reemplazo idempotente y la creación de índices con la API de `pymongo` contra mongomock y (d) que los documentos son BSON válido. mongomock imita la API y el motor de agregación, pero **no es MongoDB**: no comprueba, por ejemplo, el plan de consultas ni todas las reglas de índices de cada versión del servidor. Por eso el índice parcial usa una clave distinta de la del índice simple (ver 3.4): es una precaución basada en la documentación de MongoDB, no algo confirmado en un servidor.
> Para cargar en un servidor real, `run_mongo.py` carga y repite la verificación con el motor del propio servidor:
> ```bash
> pip install pymongo
> python scripts/run_mongo.py --uri mongodb://localhost:27017        # o una URI de MongoDB Atlas
> python scripts/run_mongo.py --uri mongodb://localhost:27017 --limite 20000   # prueba rápida con 20 mil personas
> # o, sin Python:
> mongoimport --db enoe_2025t4 --collection entidades --file data/processed/mongo/entidades.ndjson
> mongoimport --db enoe_2025t4 --collection personas  --gzip --file data/processed/mongo/personas.ndjson.gz
> ```

## 5. Consideraciones de ingeniería

* **Consistencia:** SQLite es ACID y sirve como fuente de verdad; MongoDB es una copia derivada (consistencia eventual aceptable: se regenera por lote tras cada corrida del ETL).
* **Idempotencia:** `crear_esquema` borra y recrea el archivo; `cargar_mongo` elimina y recarga las colecciones.
* **Escalamiento:** si el proyecto creciera a todos los trimestres disponibles (decenas de trimestres × 400 mil filas), la colección `personas` se podría particionar (*shard*) por `cve_ent` y los documentos de `entidades` incorporarían un arreglo `historico` por trimestre.
* **Privacidad:** los microdatos de la ENOE son públicos y anonimizados; no se incluyen nombres ni domicilios.
