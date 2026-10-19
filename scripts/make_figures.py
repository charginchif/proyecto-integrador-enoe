"""Genera todas las figuras (PNG, 200 dpi) en figures/ a partir de results/ y la base SQLite.

    python scripts/make_figures.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enoe import figuras  # noqa: E402

if __name__ == "__main__":
    figs = figuras.generar_todas(guardar=True)
    print(f"{len(figs)} figuras de datos guardadas en figures/")
    diag = figuras.generar_diagramas(guardar=True)
    print(f"{len(diag)} diagramas explicativos guardados en figures/")
