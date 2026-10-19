"""Proyecto Integrador de Ciencia de Datos - ENOE 2025 T4 (INEGI).

Paquete con el pipeline completo del ciclo KDD:

    extract    -> lectura tipada de los microdatos (SDEMT + COE2T) y auditoría de archivos
    clean      -> filtros de cobertura, faltantes codificados, calidad del ingreso, atípicos
    transform  -> variables derivadas e imputación por rangos (análisis de sensibilidad)
    survey     -> diseño muestral complejo: ponderadores, bootstrap de Rao-Wu, estadísticos ponderados
    analysis   -> pruebas de hipótesis, regresiones, Oaxaca-Blinder, no respuesta, robustez
    load_sqlite / load_mongo -> almacenes relacional y documental
    viz        -> gráficos con una paleta validada para daltonismo
"""

__version__ = "1.0.0"
