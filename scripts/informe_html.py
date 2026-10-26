"""Versión HTML del informe técnico: ``InformeHTML`` acepta las mismas llamadas que ``informe_lib.Informe`` (h1, h2, p, tabla, figura...) y produce
el cuerpo de la tesina web (capítulos, secciones, figuras y tablas numeradas, recuadros, código y referencias).

Así el texto del Word y el de la web salen de las mismas funciones (informe_s1 a informe_s4): una cifra o una frase se corrige en un solo lugar.
La clase solo construye estructura; el diseño (tipografía, colores, interactividad) está en web_assets/tesina.css y tesina.js.
"""
from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path

from PIL import Image


def e(t) -> str:
    return html.escape(str(t), quote=True)


def slug(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:64] or "x"


_INL = re.compile(r"(\*\*.+?\*\*|`.+?`|\*.+?\*)")
_URL = re.compile(r"(https?://[^\s<>\"']+?)(?=[).,;:]*(?:\s|$))")


def texto(t: str) -> str:
    """Escapa el texto y convierte las direcciones web en enlaces."""
    return _URL.sub(lambda m: f'<a href="{m.group(1)}" rel="noopener">{m.group(1)}</a>', e(t))


def md(t) -> str:
    """Mini-marcado del informe: **negrita**, *cursiva* y `código` (igual que en el Word); todo lo demás se escapa."""
    out = []
    for p in _INL.split(str(t)):
        if not p:
            continue
        if p.startswith("**") and p.endswith("**") and len(p) > 4:
            out.append(f"<strong>{md(p[2:-2])}</strong>")
        elif p.startswith("`") and p.endswith("`") and len(p) > 2:
            out.append(f"<code>{e(p[1:-1])}</code>")
        elif p.startswith("*") and p.endswith("*") and len(p) > 2:
            out.append(f"<em>{texto(p[1:-1])}</em>")
        else:
            out.append(texto(p))
    return "".join(out)


def sin_marcas(t: str) -> str:
    """Texto plano de un fragmento con mini-marcado (para índices y atributos)."""
    return re.sub(r"\*\*|`|(?<!\w)\*|\*(?!\w)", "", str(t))


def palabras(fragmento: str) -> int:
    return len(re.sub(r"<[^>]+>", " ", fragmento).split())


# --------------------------------------------------------------------------- #
# resaltado de código (SQL, JSON/documentos de MongoDB y órdenes de consola)
# --------------------------------------------------------------------------- #
_SQL = re.compile(r"(?P<c>--[^\n]*)|(?P<s>'[^']*')|(?P<k>\b(?:SELECT|FROM|JOIN|USING|GROUP BY|ORDER BY|DESC|AS|WHERE|HAVING|AND|OR|ON|ROUND|SUM|COUNT)\b)|(?P<n>\b\d+(?:\.\d+)?\b)")
_JSON = re.compile(r"(?P<l>\"[^\"\n]*\"(?=\s*:))|(?P<s>\"[^\"\n]*\")|(?P<n>-?\b\d+(?:\.\d+)?\b)|(?P<k>\b(?:true|false|null)\b)")
_SHELL = re.compile(r"(?P<c>#[^\n]*)|(?P<s>\"[^\"\n]*\")|(?P<k>\b(?:python|pip|powershell|mongoimport)\b)|(?P<o>(?<=\s)--?[A-Za-z][\w-]*)|(?P<v>\$env:\w+)")


def resaltar(codigo: str) -> str:
    inicio = codigo.lstrip()
    if inicio.upper().startswith("SELECT"):
        patron = _SQL
    elif inicio.startswith("{"):
        patron = _JSON
    else:
        patron = _SHELL
    out, pos = [], 0
    for m in patron.finditer(codigo):
        out.append(e(codigo[pos:m.start()]))
        clase = m.lastgroup
        out.append(f'<span class="{clase}">{e(m.group(0))}</span>')
        pos = m.end()
    out.append(e(codigo[pos:]))
    return "".join(out)


# --------------------------------------------------------------------------- #
_CAP = re.compile(r"^(\d+)\.\s+(.*)$")
_SEC = re.compile(r"^(\d+)\.(\d+)\s+(.*)$")
_ANEXO = re.compile(r"^Anexo ([A-F])\.\s+(.*)$")
_ANEXO_SEC = re.compile(r"^([A-F])\.(\d+)\s+(.*)$")
_ALINEAR = {"izq": "izq", "der": "der", "centro": "cen"}
_FICHAS = {"Sí": ("ok", "✓ Sí"), "No": ("mal", "✗ No"), "Crítica": ("aviso", "Crítica"), "Informativa": ("info", "Informativa")}


def celda(t) -> str:
    """Contenido de una celda: texto con mini-marcado y, en las columnas de estado, una ficha con ícono."""
    s = str(t).strip()
    if s in _FICHAS:
        clase, rotulo = _FICHAS[s]
        return f'<span class="est est--{clase}">{rotulo}</span>'
    if s.startswith("Cumplida"):
        resto = s[len("Cumplida"):].lstrip(", ")
        return '<span class="est est--ok">✓ Cumplida</span>' + (f' <span class="salvedad">{md(resto)}</span>' if resto else "")
    return md(s)


class InformeHTML:
    """Mismo contrato que informe_lib.Informe, pero escribe HTML. Los capítulos (h1) y secciones (h2) se numeran como en el Word."""

    web = True

    def __init__(self, viz: dict | None = None, alts: dict | None = None, porque: dict | None = None, ganchos: list | None = None,
                 ecuaciones: dict | None = None, img_dir: Path | None = None) -> None:
        self.viz = viz or {}
        self.alts = alts or {}
        self.porque = porque or {}
        self.ganchos = ganchos or []
        self.ecuaciones = ecuaciones or {}
        self.img_dir = img_dir
        self.n_fig = self.n_tab = self.n_eq = 0
        self.figuras: list[dict] = []
        self.tablas: list[dict] = []
        self.refs: dict[str, str] = {}
        self.capitulos: list[dict] = []
        self.prelim: list[dict] = []
        self._cap: dict | None = None
        self._lista_refs = False
        self._ids: set[str] = set()

    # ------------------------------------------------------------------ estructura
    def _contenedor(self) -> list:
        if self._cap is not None:
            return self._cap["partes"]
        if not self.prelim:
            self.prelim.append({"id": "preliminar", "titulo": "", "partes": []})
        return self.prelim[-1]["partes"]

    def _emit(self, fragmento: str, cuenta: bool = True) -> None:
        if self._lista_refs and not fragmento.startswith('<li class="ref"'):
            self._contenedor().append("</ul>")
            self._lista_refs = False
        self._contenedor().append(fragmento)
        if cuenta and self._cap is not None:
            self._cap["palabras"] += palabras(fragmento)

    def _gancho(self, tipo: str, clave: str) -> None:
        for t, prefijo, fragmento in self.ganchos:
            if t == tipo and clave.startswith(prefijo):
                self._emit(fragmento, cuenta=False)

    def bloque(self, fragmento: str) -> None:
        """HTML ya hecho (componentes interactivos de la tesina)."""
        self._emit(fragmento, cuenta=False)

    def _unico(self, id_: str) -> str:
        base, k = id_, 2
        while id_ in self._ids:
            id_ = f"{base}-{k}"
            k += 1
        self._ids.add(id_)
        return id_

    def _cerrar(self) -> None:
        if self._lista_refs:
            self._contenedor().append("</ul>")
            self._lista_refs = False
        c = self._cap
        if c is None:
            return
        minutos = max(1, round(c["palabras"] / 190))
        meta = [f"≈ {minutos} min de lectura"]
        if c["secciones"]:
            meta.append(f"{len(c['secciones'])} secciones")
        if c["figs"]:
            meta.append(f"{c['figs']} figura{'s' if c['figs'] != 1 else ''}")
        if c["tabs"]:
            meta.append(f"{c['tabs']} tabla{'s' if c['tabs'] != 1 else ''}")
        c["minutos"] = minutos
        secs = ""
        if len(c["secciones"]) > 1:
            secs = '<nav class="cap-secs" aria-label="Secciones de este capítulo"><ol>' + "".join(
                f'<li><a href="#{i}"><span class="n">{n}</span>{md(t)}</a></li>' for i, n, t in c["secciones"]) + "</ol></nav>"
        cab = (f'<header class="cap-cab"><p class="cap-etq">{e(c["etq"])}</p><h2 class="cap-titulo" id="{c["id"]}-t">{md(c["titulo"])}</h2>'
               f'<p class="cap-meta">{" · ".join(meta)}</p>{secs}</header>')
        c["html"] = (f'<section class="capitulo capitulo--{c["tipo"]}" id="{c["id"]}" aria-labelledby="{c["id"]}-t" data-titulo="{e(sin_marcas(c["titulo"]))}">'
                     f'{cab}{"".join(c["partes"])}</section>')
        del c["partes"]
        self.capitulos.append(c)
        self._cap = None

    def finalizar(self) -> dict:
        self._cerrar()
        prelim = [{"id": p["id"], "titulo": p["titulo"], "html": "".join(p["partes"])} for p in self.prelim]
        return {"capitulos": self.capitulos, "prelim": prelim, "figuras": self.figuras, "tablas": self.tablas, "refs": self.refs}

    # ------------------------------------------------------------------ títulos
    def titulo_preliminar(self, t: str, salto: bool = True) -> None:
        self._cerrar()
        self.prelim.append({"id": slug(t), "titulo": t, "partes": []})

    def h1(self, t: str, salto: bool = True) -> None:
        self._cerrar()
        if m := _CAP.match(t):
            num, titulo = m.group(1), m.group(2)
            id_, etq, tipo = f"cap-{num}", f"Capítulo {num}", "capitulo"
        elif m := _ANEXO.match(t):
            letra, titulo = m.group(1), m.group(2)
            id_, etq, tipo, num = f"anexo-{letra.lower()}", f"Anexo {letra}", "anexo", letra
        else:
            titulo, id_, etq, tipo, num = t, slug(t), "", "otro", ""
        self._ids.add(id_)
        self._cap = {"id": id_, "etq": etq, "titulo": titulo, "tipo": tipo, "num": num, "partes": [], "secciones": [], "figs": 0, "tabs": 0, "palabras": 0}
        self._gancho("h1", t)

    def h2(self, t: str) -> None:
        if m := _SEC.match(t):
            num, titulo, id_ = f"{m.group(1)}.{m.group(2)}", m.group(3), f"sec-{m.group(1)}-{m.group(2)}"
        elif m := _ANEXO_SEC.match(t):
            num, titulo, id_ = f"{m.group(1)}.{m.group(2)}", m.group(3), f"sec-{m.group(1).lower()}-{m.group(2)}"
        else:
            num, titulo, id_ = "", t, f"sec-{slug(t)}"
        id_ = self._unico(id_)
        if self._cap is not None:
            self._cap["secciones"].append((id_, num, titulo))
        n = f'<span class="num">{num}</span>' if num else ""
        self._emit(f'<h3 class="sec-titulo" id="{id_}"><a class="ancla" href="#{id_}" aria-label="Enlace a esta sección">#</a>{n}{md(titulo)}</h3>')
        self._gancho("h2", t)

    def h3(self, t: str) -> None:
        base = (self._cap["id"] if self._cap else "p") + "-" + slug(t)
        id_ = self._unico(base)
        self._emit(f'<h4 class="sub-titulo" id="{id_}">{md(t)}</h4>')

    # ------------------------------------------------------------------ texto
    def p(self, texto_: str, alinear=None, size=None, color=None, negrita=False, cursiva=False, despues=None, antes=None, keep=False) -> None:
        if texto_.startswith("**Palabras clave:**"):
            claves = [k.strip().rstrip(".") for k in texto_[len("**Palabras clave:**"):].split(";") if k.strip()]
            self._emit('<p class="claves"><span>Palabras clave</span>' + "".join(f"<b>{e(k)}</b>" for k in claves) + "</p>")
            return
        clases = []
        if alinear == "justificado":
            clases.append("j")
        elif alinear == "centro":
            clases.append("c")
        if size is not None and size <= 10.5:
            clases.append("peq")
        cuerpo = md(texto_)
        if negrita:
            cuerpo = f"<strong>{cuerpo}</strong>"
        if cursiva:
            cuerpo = f"<em>{cuerpo}</em>"
        self._emit(f'<p{" class=" + chr(34) + " ".join(clases) + chr(34) if clases else ""}>{cuerpo}</p>')
        self._gancho("p", sin_marcas(texto_))

    def vinetas(self, items: list[str], nivel: int = 1) -> None:
        self._emit('<ul class="vinetas">' + "".join(f"<li>{md(i)}</li>" for i in items) + "</ul>")

    def numerada(self, items: list[str], inicio: int = 1) -> None:
        self._emit(f'<ol class="numerada" start="{inicio}">' + "".join(f"<li>{md(i)}</li>" for i in items) + "</ol>")

    def formula(self, texto_: str) -> None:
        self.n_eq += 1
        cuerpo = self.ecuaciones.get(texto_.strip()) or e(texto_)
        self._emit(f'<div class="ecuacion" id="eq-{self.n_eq}" role="math" aria-label="{e(texto_)}"><div class="ecuacion__cuerpo">{cuerpo}</div><span class="ecuacion__num">({self.n_eq})</span></div>')

    def recuadro(self, titulo: str, lineas: list[str], fondo: str = "F3F5FB", borde: str = "1E2A6B") -> None:
        if titulo == "En palabras sencillas":
            tipo = "sencilla"
        elif titulo == "Pregunta":
            tipo = "pregunta"
        elif titulo == "Mensaje final":
            tipo = "final"
        elif titulo == "Decisión":
            tipo = "decision"
        elif fondo.upper() == "FFF7E6":
            tipo = "aviso"
        else:
            tipo = "nota"
        self._emit(f'<aside class="nota nota--{tipo}"><p class="nota__tit">{e(titulo)}</p>' + "".join(f"<p>{md(l)}</p>" for l in lineas) + "</aside>")

    def codigo(self, texto_: str, size: float = 8.5) -> None:
        cuerpo = texto_.strip("\n")
        self._emit(f'<div class="codigo"><pre tabindex="0"><code>{resaltar(cuerpo)}</code></pre></div>', cuenta=False)

    # ------------------------------------------------------------------ referencias, glosario y preguntas
    def referencia(self, texto_: str) -> None:
        autor = re.match(r"([^,.]+)", texto_)
        anio = re.search(r"\((\d{4})\)", texto_)
        clave = slug((autor.group(1) if autor else "ref")) + (anio.group(1) if anio else "")
        clave = self._unico("ref-" + clave)
        self.refs[clave] = sin_marcas(texto_)
        if not self._lista_refs:
            self._emit('<ul class="referencias">', cuenta=False)
            self._lista_refs = True
        self._contenedor().append(f'<li class="ref" id="{clave}">{md(texto_)}</li>')

    def glosario(self, items: list[tuple[str, str]]) -> None:
        filas = "".join(f'<div class="gl" id="gl-{slug(t)}"><dt>{md(t)}</dt><dd>{md(d)}</dd></div>' for t, d in items)
        self._emit('<div class="glosario" data-filtrable><label class="filtro"><span>Filtrar términos</span>'
                   '<input type="search" placeholder="Escribe parte de un término o de su significado" autocomplete="off"></label>'
                   f'<dl>{filas}</dl><p class="sin-resultados" hidden>Ningún término coincide con el filtro.</p></div>')

    def pregunta(self, q: str, a: str) -> None:
        self._emit(f'<details class="faq"><summary>{md(q)}</summary><div class="faq__r"><p>{md(a)}</p></div></details>')

    # ------------------------------------------------------------------ tablas y figuras
    def tabla(self, filas: list[list], encabezados: list[str], anchos_cm: list[float], pie: str | None = None, fuente: float = 9.5,
              alinear: list[str] | None = None, negrita_col0: bool = False, resaltar_fila: set[int] | None = None, mantener: bool | None = None) -> None:
        self.n_tab += 1
        n = self.n_tab
        if self._cap is not None:
            self._cap["tabs"] += 1
        id_ = f"tab-{n}"
        alinear = alinear or ["izq"] + ["der"] * (len(encabezados) - 1)
        total = sum(anchos_cm) or 1
        cols = "".join(f'<col style="width:{100 * a / total:.1f}%">' for a in anchos_cm)
        ths = "".join(f'<th scope="col" class="{_ALINEAR[a]}">{md(h)}</th>' for h, a in zip(encabezados, alinear))
        cuerpo = []
        for i, fila in enumerate(filas):
            celdas = []
            for j, v in enumerate(fila):
                contenido = celda(v)
                if j == 0 and negrita_col0:
                    celdas.append(f'<th scope="row" class="{_ALINEAR[alinear[j]]}">{contenido}</th>')
                else:
                    celdas.append(f'<td class="{_ALINEAR[alinear[j]]}">{contenido}</td>')
            cuerpo.append(f'<tr{" class=" + chr(34) + "res" + chr(34) if resaltar_fila and i in resaltar_fila else ""}>{"".join(celdas)}</tr>')
        clases = "tabla" + (" tabla--densa" if fuente <= 8.5 else "")
        atributos = ' data-ordenable="1"' if len(filas) >= 14 else ""
        pie_txt = pie or ""
        self.tablas.append({"id": id_, "n": n, "pie": sin_marcas(pie_txt)})
        self._emit(f'<figure class="tabla-fig" id="{id_}"{atributos}><figcaption class="tabla-cap"><strong>Tabla {n}.</strong> {md(pie_txt)}</figcaption>'
                   f'<div class="tabla-marco" tabindex="0" role="region" aria-label="Tabla {n}, con desplazamiento horizontal si no cabe">'
                   f'<table class="{clases}"><colgroup>{cols}</colgroup><thead><tr>{ths}</tr></thead><tbody>{"".join(cuerpo)}</tbody></table></div></figure>')
        self._gancho("tabla", sin_marcas(pie_txt))

    def figura(self, ruta: Path, ancho_cm: float, pie: str, alt: str | None = None) -> None:
        self.n_fig += 1
        n = self.n_fig
        if self._cap is not None:
            self._cap["figs"] += 1
        nombre = Path(ruta).name
        id_ = f"fig-{n}"
        alt_ = self.alts.get(nombre) or alt or sin_marcas(pie)
        dim = ""
        if self.img_dir is not None and (self.img_dir / nombre).exists():
            with Image.open(self.img_dir / nombre) as im:
                dim = f' width="{im.width}" height="{im.height}"'
        img = f'<img class="fig__png" src="img/{e(nombre)}" alt="{e(alt_)}" loading="lazy" decoding="async"{dim}>'
        v = self.viz.get(nombre)
        if v:
            lienzo = f'<div class="viz" data-chart="{v}" role="group" aria-label="{e(alt_)}"></div>{img}'
            clase, datos = "fig fig--int", f' data-g="{v}" data-n="{n}"'
        else:
            lienzo, clase, datos = img, "fig", f' data-n="{n}"'
        porque = self.porque.get(nombre)
        detalle = f'<details class="porque"><summary>¿Por qué este gráfico?</summary><p>{md(porque)}</p></details>' if porque else ""
        self.figuras.append({"id": id_, "n": n, "pie": sin_marcas(pie), "archivo": nombre, "interactiva": bool(v)})
        self._emit(f'<figure class="{clase}" id="{id_}"{datos}><div class="fig__lienzo">{lienzo}</div>'
                   f'<figcaption><strong>Figura {n}.</strong> {md(pie)}</figcaption>{detalle}</figure>')
        self._gancho("figura", nombre)

    # ------------------------------------------------------------------ llamadas del Word que aquí no tienen efecto
    def salto(self) -> None:
        return None

    def indice(self) -> None:
        return None

    def guardar(self, ruta) -> None:
        return None
