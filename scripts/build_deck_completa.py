"""Construye la presentación completa explicada (presentacion/Presentacion_Completa_Proyecto_ENOE.pptx, 48 diapositivas).

    python scripts/build_deck_completa.py

Reúne las 18 diapositivas principales de la presentación corta (marcadas con ★ = «ruta corta»), las 5 de respaldo integradas en el flujo y 25 nuevas
que explican qué es la ENOE, cómo se limpió, cómo se guardó, cómo se calcula cada estadístico y cómo se lee. Cada diapositiva trae el guion en las notas del
orador (con el nombre de quien presenta) y el archivo tiene secciones por bloque. Las cifras salen de results/ y las figuras de figures/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deck_slides_base as B  # noqa: E402
import deck_slides_extra as X  # noqa: E402
from deck_lib import ROOT, Deck  # noqa: E402

SALIDA = ROOT / "presentacion" / "Presentacion_Completa_Proyecto_ENOE.pptx"
TOTAL, RUTA_CORTA = 48, 18


def construir() -> Path:
    d = Deck(SALIDA, completa=True)
    n_ruta = 0

    def bloque(k):
        d.bloque(X.BLOQUES[k], X.PRESENTA.get(k))

    def add(fn, ruta=False, respaldo=False):
        nonlocal n_ruta
        fn(d)
        if ruta:
            d.ruta_corta()
            n_ruta += 1
        if respaldo:      # las diapositivas de respaldo de la versión corta pasan a ser parte del flujo principal
            tf = d.prs.slides[-1].notes_slide.notes_text_frame
            tf.text = tf.text.replace("Respaldo para la métrica tres. ", "Métrica tres. ").replace("Respaldo. ", "")

    bloque("A")
    add(B.s_portada, True)
    add(B.s_pregunta, True)
    add(X.s_agenda)
    add(X.s_por_que_importa)
    add(B.s_kdd, True)
    bloque("B")
    add(X.s_enoe)
    add(X.s_diseno_muestral)
    add(B.s_validacion, True)
    bloque("C")
    add(X.s_cobertura)
    add(X.s_faltantes)
    add(B.s_ingreso_cero, True)
    add(X.s_no_respuesta)
    add(X.s_imputacion)
    add(X.s_atipicos)
    add(B.s_embudo, True)
    add(X.s_quince_pruebas)
    bloque("D")
    add(B.s_arquitectura, True)
    add(X.s_estrella)
    add(X.s_sql_mongo)
    add(X.s_reproducibilidad)
    add(X.s_mapa_codigo)
    bloque("E")
    add(B.s_diseno_complejo, True)
    add(X.s_rao_wu)
    add(X.s_ic_p)
    add(X.s_spearman)
    add(X.s_mincer)
    add(X.s_brecha_d_holm)
    bloque("F1")
    add(B.s_rendimiento, True)
    add(B.s_estados, True)
    add(B.s_ranking, True)
    bloque("F2")
    add(B.s_brecha_hora_mes, True)
    add(B.s_comparables, True)
    add(X.s_oaxaca_idea)
    add(B.s_oaxaca, respaldo=True)
    add(B.s_cuantiles, True)
    add(X.s_heterogeneidad)
    add(B.s_robustez, respaldo=True)
    bloque("F3")
    add(B.s_informalidad, True)
    add(B.s_inf_vs_escolaridad, respaldo=True)
    add(B.s_tablero, respaldo=True)
    add(B.s_diagnosticos, respaldo=True)
    bloque("G")
    add(B.s_conclusiones, True)
    add(X.s_metricas)
    add(B.s_limitaciones, True)
    add(B.s_gracias, True)
    bloque("H")
    add(X.s_glosario_1)
    add(X.s_glosario_2)
    add(X.s_preguntas)
    assert d.n == TOTAL, f"se esperaban {TOTAL} diapositivas y hay {d.n}"
    assert n_ruta == RUTA_CORTA, f"se esperaban {RUTA_CORTA} diapositivas de ruta corta y hay {n_ruta}"
    return d.guardar()


if __name__ == "__main__":
    construir()
