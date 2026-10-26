"""Construye la guía de estudio completa del sitio (sitio/estudio.html): informe visual largo con storytelling, glosario, preguntas de defensa y modo presentación.

    python scripts/build_sitio.py                  # sitio/estudio.html + img/ + cuaderno.html + tablero.html + descargas/
    python scripts/build_sitio.py --sin-copias     # solo estudio.html e img/ (sin copiar cuaderno, tablero ni PDF)
    python scripts/build_sitio.py --fragmento RUTA # además escribe una versión sin la envoltura del documento (para publicarla como artefacto)

El documento principal es la tesina web, sitio/index.html (scripts/build_tesina.py); para exponer hay una versión de pocas láminas, sitio/presentacion.html (scripts/build_sitio_lite.py).
Esta versión larga sigue la guía de la maestra: ciclo KDD (5 fases), evidencia de las siete semanas, protocolo, dataset validado, gráficos justificados y
honestos, y el informe visual con hallazgos. Todas las cifras salen de results/ (las mismas del cuaderno, el informe y las presentaciones) y el guion de
cada escena es el de las notas del orador de la presentación completa. Abre sitio/estudio.html con doble clic o súbela a cualquier hosting estático.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image  # noqa: E402

import sitio_contenido_a as A  # noqa: E402
import sitio_contenido_b as B  # noqa: E402
import sitio_estudio as S  # noqa: E402
from deck_slides_extra import MIN_CORTA, MINUTOS  # noqa: E402
from enoe import config as C  # noqa: E402
from informe_datos import cargar  # noqa: E402
from sitio_lib import Ctx, Guiones, e, preparar_figura  # noqa: E402
from sitio_textos import DIAGRAMAS, RECORTES  # noqa: E402

ASSETS = Path(__file__).resolve().parent / "sitio_assets"
TITULO = "Radiografía socioeconómica de México"
FUENTES = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap">')
RESET = "html{padding:0}body{margin:0}"

ETIQUETA = {
    "portada": "Portada", "historia": "La historia en cinco frases", "pregunta": "La pregunta", "protocolo": "Protocolo", "mapa": "Qué pide la maestra", "kdd": "Ciclo KDD",
    "enoe": "La ENOE y el diseño muestral", "validacion": "Validación con cifras del INEGI", "cobertura": "Cobertura", "faltantes": "Faltantes codificados", "ingreso0": "El «ingreso cero»",
    "norespuesta": "No respuesta del ingreso", "imputacion": "Imputación por rango", "atipicos": "Atípicos y logaritmo", "embudo": "Del registro crudo a la muestra", "pruebas": "15 pruebas de calidad",
    "variables": "Variables derivadas", "arquitectura": "Arquitectura", "estrella": "Esquema en estrella", "sqlmongo": "SQL y MongoDB", "reprod": "Reproducibilidad",
    "diseno": "Diseño muestral y error", "raowu": "Bootstrap de Rao-Wu", "icp": "Intervalos y valor p", "spearman": "Spearman", "mincer": "Ecuación de Mincer", "herramientas": "Brecha, d de Cohen y Holm",
    "rendimiento": "Rendimiento de estudiar", "estados": "Estados ricos y pobres", "ranking": "Ranking de entidades", "brechahm": "Brecha por hora y por mes", "comparables": "Personas comparables",
    "oaxaca": "Oaxaca-Blinder", "cuantiles": "Brecha en la distribución", "heterog": "Brecha por grupo", "robustez": "Robustez", "informalidad": "Informalidad", "infvsesc": "Informalidad y escolaridad",
    "tablero": "Tablero interactivo", "diagnostico": "Diagnóstico del modelo", "conclusiones": "Conclusiones", "metricas": "Métricas de éxito", "limites": "Límites y trabajo futuro", "cierre": "Cierre",
}


def indice(reg: list[dict]) -> str:
    por_cap: dict[int, list[dict]] = {}
    for r in reg:
        por_cap.setdefault(r["cap"], []).append(r)
    h = '<nav class="rail" aria-label="Índice del sitio"><p class="rail__t">Contenido</p>'
    for i, (nombre, fase, _sem) in enumerate(Ctx.CAPS):
        et = nombre + (f" · {fase}" if fase else "")
        h += f'<details{" open" if i == 0 else ""}><summary>{e(et)}</summary><ol>' + "".join(f'<li><a href="#{r["id"]}">{e(ETIQUETA[r["id"]])}</a></li>' for r in por_cap.get(i, [])) + "</ol></details>"
    return h + '<details open><summary>Para el equipo</summary><ol><li><a href="#estudiar">Estudiar</a></li><li><a href="#exponer">Exponer</a></li><li><a href="#descargas">Descargas</a></li></ol></details></nav>'


def pagina(cuerpo: str, rail: str, css: str, js: str, fragmento: bool) -> str:
    barra = (f'<header class="topbar"><div class="topbar__in"><button type="button" class="btn btn--chico btn--ghost" id="btn-indice" aria-label="Abrir el índice">Índice</button>'
             f'<a class="marca" href="#portada">{e(TITULO)}<small>Equipo 1 · ENOE 2025-T4</small></a>'
             f'<a class="btn btn--chico btn--ghost" href="index.html">Tesina</a><a class="btn btn--chico btn--ghost" href="presentacion.html">Versión para presentar</a>'
             f'<button type="button" class="btn btn--chico" data-presentar>Presentar</button>'
             f'<button type="button" class="btn btn--chico btn--ghost" id="btn-tema" aria-label="Cambiar entre tema claro y oscuro">Tema</button></div></header>')
    pres = ('<div class="pres" id="pres" role="toolbar" aria-label="Controles del modo presentación"><button type="button" id="pres-ant" aria-label="Escena anterior">←</button><button type="button" id="pres-sig" aria-label="Escena siguiente">→</button>'
            '<span class="pos" id="pres-pos">1 / 1</span><span class="tit" id="pres-tit"></span><span class="reloj" id="pres-reloj">00:00</span>'
            '<button type="button" id="pres-ruta" aria-pressed="false" title="Cambiar entre la ruta completa y la ruta corta (solo las escenas con ★)">Ruta: completa (R)</button><button type="button" id="pres-notas-btn" aria-pressed="false">Guion (N)</button><button type="button" id="pres-salir">Salir (Esc)</button></div>'
            '<aside id="pres-notas" hidden aria-label="Guion de la escena"></aside>')
    visor = '<dialog class="visor" id="visor" aria-label="Figura ampliada"><button type="button" class="btn btn--chico" id="visor-cerrar">Cerrar</button><img id="visor-img" alt=""><p id="visor-pie"></p></dialog>'
    pie = (f'<footer class="pie"><div class="cont"><p>Proyecto Integrador de Ciencia de Datos · Equipo 1 (Juan Evelio Culin Grajeda, Angel Yireh Garcia Jara, Luis Andre Gutierrez Zuñiga) · Universidad de Especialidades UNE, Plantel Centro · '
           f'Datos: INEGI, Encuesta Nacional de Ocupación y Empleo, 4.º trimestre de 2025 (microdatos públicos). Material académico.</p></div></footer>')
    app = (f'<div id="app" data-min-corta="{sum(MIN_CORTA.values())}" data-min-completa="{sum(MINUTOS.values())}">{barra}<div class="shell">{rail}<main class="principal" id="contenido">{cuerpo}{pie}</main></div>{pres}{visor}</div>')
    if fragmento:
        return (f'<title>{e(TITULO)}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n{FUENTES}\n<style>\n{css}\n</style>\n{app}\n<script>\n{js}\n</script>\n')
    return (f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>{e(TITULO)}</title>\n{FUENTES}\n'
            f'<style>\n{RESET}\n{css}\n</style>\n</head>\n<body>\n{app}\n<script>\n{js}\n</script>\n</body>\n</html>\n')


def preparar_imagenes(salida: Path) -> int:
    img = salida / "img"
    img.mkdir(parents=True, exist_ok=True)
    n = 0
    for nombre, (arriba, abajo) in RECORTES.items():
        preparar_figura(C.FIGURES / nombre, img / nombre, arriba, abajo)
        n += 1
    for nombre in DIAGRAMAS:
        shutil.copy2(C.FIGURES / nombre, img / nombre)
        n += 1
    captura = RAIZ / "presentacion" / "img" / "tablero.jpg"
    if captura.exists():
        with Image.open(captura) as im:
            im.crop((0, 0, 800, 692)).convert("RGB").save(img / "tablero.jpg", quality=88, optimize=True)
        n += 1
    else:
        print("Aviso: no está presentacion/img/tablero.jpg; la escena del tablero quedará sin captura.")
    return n


RUTA_LOCAL = re.compile(r"[A-Za-z]:\\{1,2}Users\\{1,2}[^\\\s<\"']+(?:\\{1,2}[^\\\s<\"']+)*")


def limpiar_rutas(texto: str) -> str:
    """Cambia las rutas absolutas de esta computadora por «…\\carpeta»: el cuaderno imprime dónde estaban los microdatos y eso no debe viajar con el sitio."""
    return RUTA_LOCAL.sub(lambda m: "…\\" + re.split(r"\\+", m.group(0))[-1], texto)


def copiar_documentos(salida: Path) -> list[str]:
    copiados = []
    (salida / "descargas").mkdir(parents=True, exist_ok=True)
    for origen, destino in [(RAIZ / "notebooks" / "Proyecto_Integrador_ENOE.html", "cuaderno.html"), (RAIZ / "tablero" / "tablero_enoe.html", "tablero.html"),
                            (RAIZ / "documento" / "Informe_Final_Proyecto_ENOE.pdf", "descargas/Informe_Final_Proyecto_ENOE.pdf"),
                            (RAIZ / "presentacion" / "Presentacion_Completa_Proyecto_ENOE.pdf", "descargas/Presentacion_Completa_Proyecto_ENOE.pdf"),
                            (RAIZ / "presentacion" / "Proyecto_Integrador_ENOE.pdf", "descargas/Proyecto_Integrador_ENOE.pdf")]:
        if origen.exists():
            if destino == "cuaderno.html":
                (salida / destino).write_text(limpiar_rutas(origen.read_text(encoding="utf-8")), encoding="utf-8")
            elif destino == "tablero.html":
                # la biblioteca de mapas incluida en el tablero trae un carácter de reemplazo (U+FFFD) literal dentro de una expresión regular;
                # escrito como � significa lo mismo y evita que los publicadores lo tomen por un archivo mal codificado
                (salida / destino).write_text(origen.read_text(encoding="utf-8").replace("�", "\\uFFFD"), encoding="utf-8")
            else:
                shutil.copy2(origen, salida / destino)
            copiados.append(destino)
        else:
            print(f"Aviso: falta {origen.relative_to(RAIZ)}; el enlace de {destino} no funcionará.")
    return copiados


def main() -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(RAIZ / "sitio"))
    ap.add_argument("--sin-copias", action="store_true")
    ap.add_argument("--fragmento", default=None, help="ruta donde escribir la versión sin envoltura de documento")
    a = ap.parse_args()
    salida = Path(a.salida)
    D = cargar()
    G = Guiones(RAIZ / "presentacion" / "Presentacion_Completa_Proyecto_ENOE.pptx")
    if not G.items:
        print("Aviso: no se encontró la presentación completa; las escenas saldrán sin guion (ejecuta antes build_deck_completa.py).")
    ctx = Ctx(D, G)
    escenas = A.construir(ctx) + B.construir(ctx)
    cuerpo = "\n".join(escenas) + "\n" + S.estudiar(D) + "\n" + S.exponer(D) + "\n" + S.descargas()
    rail = indice(ctx.reg)
    css = (ASSETS / "estilo.css").read_text(encoding="utf-8")
    js = (ASSETS / "app.js").read_text(encoding="utf-8")
    salida.mkdir(parents=True, exist_ok=True)
    n_img = preparar_imagenes(salida)
    copias = [] if a.sin_copias else copiar_documentos(salida)
    destino = salida / "estudio.html"
    destino.write_text(pagina(cuerpo, rail, css, js, fragmento=False), encoding="utf-8")
    if a.fragmento:
        Path(a.fragmento).write_text(pagina(cuerpo, rail, css, js, fragmento=True), encoding="utf-8")
    corta = sum(1 for r in ctx.reg if r["corta"])
    print(f"Sitio escrito en {destino} ({destino.stat().st_size / 1e3:.0f} KB; {len(ctx.reg)} escenas, {corta} en la ruta corta; {n_img} imágenes; {len(copias)} documentos copiados)")
    return destino


if __name__ == "__main__":
    main()
