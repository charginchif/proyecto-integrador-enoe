"""Corre todo el análisis estadístico sobre la base SQLite y guarda tablas en results/ (y res_* en SQLite).

    python scripts/run_analysis.py [--B 1000]

Requiere haber corrido antes scripts/run_etl.py. Con B=1000 réplicas tarda unos 6-8 minutos.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enoe import analisis, config as C, pipeline  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--B", type=int, default=C.N_BOOTSTRAP, help="réplicas del bootstrap de Rao-Wu")
    ap.add_argument("--sin-guardar", action="store_true", help="no escribir resultados (prueba rápida)")
    args = ap.parse_args()
    pipeline.configurar_logging(C.LOGS / f"analisis_{time.strftime('%Y%m%d_%H%M%S')}.log")
    T, resumen = analisis.ejecutar_analisis(B=args.B)
    if not args.sin_guardar:
        analisis.guardar_resultados(T, resumen)
        print(f"Resultados guardados en {C.RESULTS}")
