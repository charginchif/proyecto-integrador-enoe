"""Ejecuta el ETL completo y crea data/processed/enoe_2025t4.sqlite.

    python scripts/run_etl.py [--raw-dir RUTA] [--db RUTA]

La carpeta con los CSV de INEGI también puede indicarse con la variable de entorno ENOE_RAW_DIR.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enoe import config as C  # noqa: E402
from enoe import pipeline  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", type=Path, default=None, help="carpeta con ENOE_SDEMT425.csv y ENOE_COE2T425.csv")
    ap.add_argument("--db", type=Path, default=None, help="ruta del archivo SQLite de salida")
    args = ap.parse_args()
    C.RESULTS.mkdir(parents=True, exist_ok=True)
    pipeline.configurar_logging()
    pipeline.ejecutar_etl(args.raw_dir, args.db)
