"""Configuración central: rutas, parámetros metodológicos y catálogos.

Todo lo que es "decisión del analista" vive aquí (y solo aquí) para que cada
umbral esté documentado y sea fácil de cambiar en un análisis de sensibilidad.

Los catálogos de códigos se verificaron contra los propios microdatos (ver
docs/diccionario_de_datos.md, sección "Verificación empírica de códigos").
"""
from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# Rutas
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[2]


def contar_pruebas() -> dict[str, int]:
    """Pruebas automáticas por archivo de tests/ (se cuentan las funciones ``test_``): los documentos citan esta cifra sin escribirla a mano."""
    import re
    return {p.name: len(re.findall(r"^\s+def test_", p.read_text(encoding="utf-8"), re.M)) for p in sorted((ROOT / "tests").glob("test_*.py"))}
DATA_PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
DOCS = ROOT / "docs"
LOGS = ROOT / "logs"

PERIODO = "425"          # ENOE 4.º trimestre de 2025 (sufijo de archivo de INEGI)
PERIODO_ETIQUETA = "2025-T4"
DB_PATH = DATA_PROCESSED / "enoe_2025t4.sqlite"


def _resolver_raw() -> Path:
    """Carpeta con los CSV de INEGI. Prioridad: variable ENOE_RAW_DIR > data/raw > ruta del equipo."""
    candidatos = []
    if os.environ.get("ENOE_RAW_DIR"):
        candidatos.append(Path(os.environ["ENOE_RAW_DIR"]))
    candidatos += [
        ROOT / "data" / "raw",
        Path.home() / "OneDrive" / "Escritorio" / "ProyectoINEGI" / "enoe_2025_trim4_csv",
    ]
    for c in candidatos:
        if (c / f"ENOE_SDEMT{PERIODO}.csv").exists():
            return c
    return candidatos[0]


RAW_DIR = _resolver_raw()

# --------------------------------------------------------------------------- #
# Parámetros metodológicos (decisiones documentadas en docs/metodologia.md)
# --------------------------------------------------------------------------- #
EDAD_MIN = 15                 # base oficial de la ENOE (población de 15 años y más)
EDAD_MAX_ANALISIS = 65        # ventana del protocolo: 15 a 65 años
HORAS_MAX = 112               # 16 h x 7 días: por arriba se considera jornada imposible
SEMANAS_POR_MES = 4.3         # factor con el que INEGI construye ing_x_hrs = ingocup / (hrsocup * 4.3)
RECORTE_PCT = (0.5, 99.5)     # atípicos: percentiles del ingreso por hora DENTRO de cada entidad
ANIOS_ESC_NO_ESPECIFICADO = 99
NIV_INS_NO_ESPECIFICADO = 5
SEMILLA = 20251231            # semilla única para bootstrap y cualquier aleatoriedad
N_BOOTSTRAP = 1000            # réplicas del bootstrap de Rao-Wu
ALPHA = 0.05

# --------------------------------------------------------------------------- #
# Catálogos
# --------------------------------------------------------------------------- #
# cve_ent -> (nombre corto, nombre oficial, abreviatura, región, columna_mosaico, fila_mosaico)
# Región: agrupación en 4 regiones (Norte, Centro-Norte, Centro, Sur) inspirada en la
# regionalización del Banco de México; solo se usa para exposición, no para inferencia.
# Mosaico: posición en un cartograma de cuadrícula (cada estado ocupa el mismo área).
ENTIDADES = {
    1: ("Aguascalientes", "Aguascalientes", "AGS", "Centro-Norte", 3, 2),
    2: ("Baja California", "Baja California", "BC", "Norte", 0, 0),
    3: ("Baja California Sur", "Baja California Sur", "BCS", "Centro-Norte", 0, 1),
    4: ("Campeche", "Campeche", "CAM", "Sur", 9, 4),
    5: ("Coahuila", "Coahuila de Zaragoza", "COA", "Norte", 3, 0),
    6: ("Colima", "Colima", "COL", "Centro-Norte", 2, 3),
    7: ("Chiapas", "Chiapas", "CHIS", "Sur", 8, 5),
    8: ("Chihuahua", "Chihuahua", "CHIH", "Norte", 2, 0),
    9: ("Ciudad de México", "Ciudad de México", "CDMX", "Centro", 5, 3),
    10: ("Durango", "Durango", "DGO", "Centro-Norte", 2, 1),
    11: ("Guanajuato", "Guanajuato", "GTO", "Centro-Norte", 4, 2),
    12: ("Guerrero", "Guerrero", "GRO", "Sur", 4, 4),
    13: ("Hidalgo", "Hidalgo", "HGO", "Centro", 6, 2),
    14: ("Jalisco", "Jalisco", "JAL", "Centro-Norte", 2, 2),
    15: ("Estado de México", "México", "MEX", "Centro", 4, 3),
    16: ("Michoacán", "Michoacán de Ocampo", "MICH", "Centro-Norte", 3, 3),
    17: ("Morelos", "Morelos", "MOR", "Centro", 5, 4),
    18: ("Nayarit", "Nayarit", "NAY", "Centro-Norte", 1, 2),
    19: ("Nuevo León", "Nuevo León", "NL", "Norte", 4, 0),
    20: ("Oaxaca", "Oaxaca", "OAX", "Sur", 7, 4),
    21: ("Puebla", "Puebla", "PUE", "Centro", 7, 3),
    22: ("Querétaro", "Querétaro", "QRO", "Centro-Norte", 5, 2),
    23: ("Quintana Roo", "Quintana Roo", "QROO", "Sur", 10, 4),
    24: ("San Luis Potosí", "San Luis Potosí", "SLP", "Centro-Norte", 4, 1),
    25: ("Sinaloa", "Sinaloa", "SIN", "Centro-Norte", 1, 1),
    26: ("Sonora", "Sonora", "SON", "Norte", 1, 0),
    27: ("Tabasco", "Tabasco", "TAB", "Sur", 8, 4),
    28: ("Tamaulipas", "Tamaulipas", "TAMPS", "Norte", 5, 0),
    29: ("Tlaxcala", "Tlaxcala", "TLAX", "Centro", 6, 3),
    30: ("Veracruz", "Veracruz de Ignacio de la Llave", "VER", "Sur", 7, 2),
    31: ("Yucatán", "Yucatán", "YUC", "Sur", 10, 3),
    32: ("Zacatecas", "Zacatecas", "ZAC", "Centro-Norte", 3, 1),
}

SEXO = {1: "Hombre", 2: "Mujer"}

# niv_ins (ENOE): el nivel 4 agrupa media superior y superior; el 2 incluye secundaria incompleta
NIV_INS = {
    1: "Primaria incompleta",
    2: "Primaria completa",
    3: "Secundaria completa",
    4: "Medio superior y superior",
    5: "No especificado",
}
# Desagregación propia del nivel 4 usando años de escolaridad (ver metodologia.md)
NIV_DET = {
    1: "Primaria incompleta",
    2: "Primaria completa",
    3: "Secundaria completa",
    4: "Media superior / superior trunca (12-15 años)",
    5: "Licenciatura o posgrado (16+ años)",
}

POS_OCU = {
    1: "Subordinado y remunerado",
    2: "Empleador",
    3: "Cuenta propia",
    4: "Trabajador sin pago",
}

EMP_PPAL = {1: "Informal", 2: "Formal"}

# rama_est2: 11 grandes ramas. Verificada sumando los 21 sectores SCIAN de la tabla (ver diccionario).
RAMA_EST2 = {
    1: "Agropecuario",
    2: "Industria extractiva y electricidad",
    3: "Industria manufacturera",
    4: "Construcción",
    5: "Comercio",
    6: "Restaurantes y alojamiento",
    7: "Transportes y comunicaciones",
    8: "Servicios profesionales, financieros y corporativos",
    9: "Servicios sociales (educación y salud)",
    10: "Servicios diversos",
    11: "Gobierno y organismos internacionales",
    0: "No especificado",
}

T_LOC_TRI = {
    1: "100 mil o más habitantes",
    2: "15 mil a 99,999",
    3: "2,500 a 14,999",
    4: "Menos de 2,500",
}

# ing7c: ingreso en salarios mínimos (SM). Verificado: ingocup/salario cae en cada intervalo.
ING7C = {
    1: "Hasta 1 SM",
    2: "Más de 1 hasta 2 SM",
    3: "Más de 2 hasta 3 SM",
    4: "Más de 3 hasta 5 SM",
    5: "Más de 5 SM",
    6: "No recibe ingresos",
    7: "No especificado",
}

# Grupos de reporte del ingreso (clasificación propia, ver docs/metodologia.md)
GRUPO_INGRESO = {
    "A": "Monto exacto declarado (ingocup > 0)",
    "B": "Solo rango de salarios mínimos (ingocup = 0, ing7c 1-5)",
    "C": "No recibe ingresos (ing7c = 6)",
    "D": "No especificó (ing7c = 7)",
}

# COE2T p6c -> (límite inferior, límite superior) en múltiplos del salario mínimo mensual.
# Los códigos 1-7 reproducen exactamente ing7c (1,2->1; 3->2; 4->3; 5->4; 6,7->5) en los datos;
# la redacción literal de cada código ("menos de 1 SM", "1 SM", ...) debe contrastarse con el
# cuestionario oficial. Los códigos 8 y 9 (no sabe / no responde) caen siempre en ing7c = 7.
P6C_RANGOS_SM = {
    1: (0.0, 1.0),
    2: (1.0, 1.0),
    3: (1.0, 2.0),
    4: (2.0, 3.0),
    5: (3.0, 5.0),
    6: (5.0, 10.0),
    7: (10.0, float("inf")),
}

REGIONES = ["Norte", "Centro-Norte", "Centro", "Sur"]

# Llave única de persona dentro del trimestre (verificada: 0 duplicados en SDEMT y COE2T)
LLAVE_PERSONA = [
    "cd_a", "cve_ent", "con", "upm", "d_sem", "n_pro_viv", "v_sel", "n_hog", "h_mud", "n_ent", "n_ren",
]

# --------------------------------------------------------------------------- #
# Cifras oficiales de referencia (validación externa de ponderadores y filtros)
# Fuente: INEGI, ENOE 4T-2025, boletín de prensa nacional y boletines estatales
# (consultadas el 18-oct-2026 mediante búsqueda web; contrastar con el PDF oficial antes de exponer).
# --------------------------------------------------------------------------- #
REFERENCIA_INEGI = {
    "pea_millones": 61.3,
    "tasa_participacion_pct": 59.3,
    "til1_nacional_pct": 55.0,
    "ocupacion_informal_millones": 32.9,
    "til1_estatal_pct": {7: 74.9, 8: 36.2, 9: 45.7},  # Chiapas, Chihuahua, Ciudad de México
}
