"""Capa documental (NoSQL): exporta las colecciones y, si se indica, las carga en MongoDB.

    python scripts/run_mongo.py --exportar                       # genera data/processed/mongo/*.ndjson (sin servidor)
    python scripts/run_mongo.py --uri mongodb://localhost:27017  # además carga en MongoDB (requiere pymongo)

Después de exportar se comprueba que la consulta «TIL1 por entidad» calculada sobre los DOCUMENTOS
(misma lógica que el pipeline de agregación de MongoDB) coincide con la vista SQL ``v_til_entidad``.
Para cargar manualmente: mongoimport --db enoe_2025t4 --collection entidades --file entidades.ndjson
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enoe import config as C, load_mongo as L  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exportar", action="store_true", help="solo genera los archivos NDJSON")
    ap.add_argument("--uri", default=None, help="URI de MongoDB; si se indica, carga las colecciones")
    ap.add_argument("--base", default="enoe_2025t4")
    args = ap.parse_args()

    cuentas = L.exportar_todo()
    print("Documentos exportados:", cuentas, "->", L.DIR_MONGO)

    doc = L.til1_por_entidad_desde_ndjson()
    con = sqlite3.connect(C.DB_PATH)
    sql = pd.read_sql("SELECT cve_ent, til1_pct FROM v_til_entidad", con).set_index("cve_ent")["til1_pct"]
    con.close()
    dif = (doc.set_index("cve_ent")["til1_pct"] - sql).abs().max()
    print(f"Equivalencia SQL <-> documentos: diferencia máxima del TIL1 por entidad = {dif:.4f} puntos porcentuales")
    assert dif < 0.01, "Los documentos no reproducen la vista SQL"
    print(json.dumps(L.ficha_entidad("Oaxaca")["informalidad"], ensure_ascii=False))

    if args.uri:
        print("Cargando en MongoDB...", L.cargar_mongo(args.uri, args.base))
