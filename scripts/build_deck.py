"""Construye la presentación corta (presentacion/Proyecto_Integrador_ENOE.pptx: 18 diapositivas principales + anexos) a partir de results/ y figures/.

    python scripts/build_deck.py

Todas las cifras de las diapositivas se leen de results/ (resumen.json y CSV); las figuras son las de figures/.
Tema propio (colores y fuentes en el tema del archivo), gráficas nativas editables, texto alternativo en imágenes y notas del orador.
Las diapositivas están definidas en deck_slides_base.py y el diseño común en deck_lib.py (la versión completa es build_deck_completa.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deck_slides_base as base  # noqa: E402
from deck_lib import ROOT, Deck  # noqa: E402

SALIDA = ROOT / "presentacion" / "Proyecto_Integrador_ENOE.pptx"


def main() -> Path:
    d = Deck(SALIDA)
    for diapositiva in base.ORDEN_CORTA:
        diapositiva(d)
    return d.guardar()


if __name__ == "__main__":
    main()
