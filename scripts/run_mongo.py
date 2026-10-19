"""Capa documental (NoSQL): exporta las colecciones y, si se indica, las carga en MongoDB.

    python scripts/run_mongo.py --exportar                       # genera data/processed/mongo/*.ndjson (sin servidor)
    python scripts/run_mongo.py --simulado                       # además prueba la carga completa contra mongomock (sin servidor; ~5 min)
    python scripts/run_mongo.py --simulado --limite 20000        # igual, pero con solo 20 mil personas (~1 min)
    python scripts/run_mongo.py --uri mongodb://localhost:27017  # además carga en un MongoDB real (requiere pymongo)

Después de exportar se comprueba que la consulta «TIL1 por entidad» calculada sobre los DOCUMENTOS
(misma lógica que el pipeline de agregación de MongoDB) coincide con la vista SQL ``v_til_entidad``.
Con --simulado o --uri se carga la base, se revisa que los documentos sean BSON válidos y se ejecuta el pipeline de agregación EN EL MOTOR
(mongomock o el servidor): con la carga completa se compara con la vista SQL; con --limite, con la lógica en Python sobre los mismos documentos.
mongomock es un simulador en memoria: sirve para probar el código y el pipeline, pero NO sustituye una prueba contra un servidor real.
Para cargar manualmente: mongoimport --db enoe_2025t4 --collection entidades --file entidades.ndjson
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enoe import load_mongo as L  # noqa: E402


def verificar(cli, base: str, limite: int | None, etiqueta: str) -> None:
    """Ejecuta el pipeline de agregación en el motor de ``cli`` y lo compara con SQL (carga completa) o con Python (carga parcial)."""
    col = cli[base].personas
    t = time.time()
    motor = L.til1_por_entidad_en_motor(col)
    seg = time.time() - t
    if limite is None:
        dif = L.diferencia_con_sql(motor)
        print(f"{etiqueta}: pipeline de agregación en el motor ({seg:.0f} s) frente a la vista SQL: diferencia máxima del TIL1 = {dif:.4f} pp")
        assert dif < 0.01, "El pipeline de agregación no reproduce la vista SQL"
    else:
        dif = L.diferencia_maxima(motor, L.til1_por_entidad_desde_documentos(col.find({})))
        print(f"{etiqueta}: pipeline de agregación en el motor ({seg:.0f} s) frente a la lógica en Python sobre los mismos {limite:,} documentos: diferencia máxima = {dif:.2e} pp")
        assert dif < 1e-6, "El motor y la lógica en Python no coinciden"
    print("  find_one({cve_ent: 20}):", json.dumps(cli[base].entidades.find_one({"cve_ent": 20}, {"_id": 0, "entidad": 1, "informalidad.til1_pct": 1}), ensure_ascii=False))
    print("  índices de personas:", ", ".join(sorted(cli[base].personas.index_information())))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exportar", action="store_true", help="solo genera los archivos NDJSON")
    ap.add_argument("--simulado", action="store_true", help="prueba la carga contra mongomock (simulador en memoria, sin servidor)")
    ap.add_argument("--uri", default=None, help="URI de MongoDB; si se indica, carga las colecciones")
    ap.add_argument("--base", default="enoe_2025t4")
    ap.add_argument("--limite", type=int, default=None, help="con --simulado o --uri: carga solo N personas (prueba rápida)")
    args = ap.parse_args()

    cuentas = L.exportar_todo()
    print("Documentos exportados:", cuentas, "->", L.DIR_MONGO)

    dif = L.diferencia_con_sql(L.til1_por_entidad_desde_ndjson())
    print(f"Equivalencia SQL <-> documentos: diferencia máxima del TIL1 por entidad = {dif:.4f} puntos porcentuales")
    assert dif < 0.01, "Los documentos no reproducen la vista SQL"
    print(json.dumps(L.ficha_entidad("Oaxaca")["informalidad"], ensure_ascii=False))

    if args.simulado:
        try:
            import mongomock
        except ImportError:
            sys.exit("Falta mongomock: ejecute 'pip install mongomock' (y 'pip install pymongo' para revisar el BSON).")
        t0 = time.time()
        cli = mongomock.MongoClient()
        cuentas = L.cargar_mongo(cliente=cli, base=args.base, limite_personas=args.limite, validar=True)
        print(f"Carga SIMULADA con mongomock (no es un servidor real; {time.time() - t0:.0f} s, BSON válido):", cuentas)
        verificar(cli, args.base, args.limite, "mongomock")

    if args.uri:
        from pymongo import MongoClient
        print("Cargando en MongoDB...", L.cargar_mongo(args.uri, args.base, limite_personas=args.limite))
        verificar(MongoClient(args.uri, serverSelectionTimeoutMS=4000), args.base, args.limite, "servidor MongoDB")
