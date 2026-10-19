"""Reproduce TODO el proyecto de principio a fin y se detiene si algún paso falla.

    python scripts/run_all.py            # ~10 minutos (el bootstrap de 1,000 réplicas toma ~5)
    python scripts/run_all.py --rapido   # B=100 réplicas, sin cuaderno, presentaciones, informe ni sitio (verificación rápida)

Pasos: ETL -> análisis -> figuras -> documentos NoSQL -> tablero -> cuaderno -> presentaciones (corta y completa) -> informe (Word) -> sitio web (guía de estudio y versión para presentar) -> pruebas.
El índice y el PDF del informe se actualizan aparte con scripts/exportar_informe.ps1 y el PDF de la presentación con scripts/exportar_presentacion.ps1
(necesitan Microsoft Word y PowerPoint en Windows); el sitio copia esos PDF si existen.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
S = RAIZ / "scripts"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    py = sys.executable
    pasos = [
        ("ETL (limpieza, validación, SQLite)", [py, str(S / "run_etl.py")]),
        ("Análisis estadístico", [py, str(S / "run_analysis.py")] + (["--B", "100"] if args.rapido else [])),
        ("Figuras", [py, str(S / "make_figures.py")]),
        ("Documentos NoSQL + verificación SQL", [py, str(S / "run_mongo.py"), "--exportar"]),
        ("Tablero interactivo", [py, str(S / "build_dashboard.py")]),
    ]
    if not args.rapido:
        pasos += [("Cuaderno (ejecuta y exporta HTML)", [py, str(S / "build_notebook.py")]),
                  ("Presentación corta", [py, str(S / "build_deck.py")]),
                  ("Presentación completa", [py, str(S / "build_deck_completa.py")]),
                  ("Informe técnico (Word)", [py, str(S / "build_informe.py")]),
                  ("Sitio web: guía de estudio (estudio.html)", [py, str(S / "build_sitio.py")]),
                  ("Sitio web: versión para presentar (index.html)", [py, str(S / "build_sitio_lite.py")])]
    pasos.append(("Pruebas automáticas", [py, "-m", "unittest", "discover", "-s", str(RAIZ / "tests")]))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    t0 = time.time()
    for nombre, cmd in pasos:
        t = time.time()
        print(f"\n=== {nombre} ===", flush=True)
        r = subprocess.run(cmd, cwd=RAIZ, env=env)
        print(f"--- {nombre}: {'OK' if r.returncode == 0 else 'FALLÓ'} ({time.time() - t:.0f} s)", flush=True)
        if r.returncode != 0:
            sys.exit(r.returncode)
    print(f"\nTodo terminó correctamente en {(time.time() - t0) / 60:.1f} minutos.")


if __name__ == "__main__":
    main()
