"""Construye el informe técnico final en Word (documento/Informe_Final_Proyecto_ENOE.docx).

Todas las cifras, tablas y figuras salen de results/, figures/ y de la base SQLite: el documento se regenera
cada vez que cambian los resultados. El índice es un campo de Word; para llenarlo y exportar a PDF use
scripts/exportar_informe.ps1 (requiere Microsoft Word en Windows) o, en Word, clic derecho > Actualizar campo.

    python scripts/build_informe.py
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import informe_s1 as s1  # noqa: E402
import informe_s2 as s2  # noqa: E402
import informe_s3 as s3  # noqa: E402
import informe_s4 as s4  # noqa: E402
from informe_datos import cargar  # noqa: E402
from informe_lib import Informe  # noqa: E402

SALIDA = RAIZ / "documento" / "Informe_Final_Proyecto_ENOE.docx"


def main() -> Path:
    D = cargar()
    inf = Informe()
    s1.portada(inf, D)
    s1.resumen(inf, D)
    inf.indice()
    s1.seccion1(inf, D)
    s1.seccion2(inf, D)
    s1.seccion3(inf, D)
    s2.seccion4(inf, D)
    s2.seccion5(inf, D)
    s3.seccion6(inf, D)
    s3.seccion7(inf, D)
    s4.seccion8(inf, D)
    s4.seccion9(inf, D)
    s4.anexos(inf, D)
    inf.guardar(SALIDA)
    print(f"Informe escrito en {SALIDA} ({SALIDA.stat().st_size / 1e6:.1f} MB; {inf.n_fig} figuras, {inf.n_tab} tablas)")
    return SALIDA


if __name__ == "__main__":
    main()
