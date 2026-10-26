/* Radiografía socioeconómica de México · tesina web: figuras interactivas del texto, navegación, búsqueda, tablas y componentes.
   Se concatena después de charts.js, que aporta los datos (D), las gráficas compartidas (GRAF), el globo de datos y el estado de la entidad elegida. */

/* ======================================================================================================================================
   Gráficas propias de la tesina (las demás vienen de charts.js)
   ====================================================================================================================================== */
function leyendaColores(el, items) {
  const d = document.createElement('div'); d.className = 'leyenda-q';
  items.forEach((it) => {
    const s = document.createElement('span'), i = document.createElement('i');
    if (it.clase) i.className = it.clase;
    if (it.hueco) { i.style.background = 'transparent'; i.style.border = '2px solid var(--s1)'; }
    s.appendChild(i); s.appendChild(document.createTextNode(it.texto)); d.appendChild(s);
  });
  el.appendChild(d);
}

/* leyenda de la calidad del ingreso (en la presentación la arma la página) */
const calidadBase = GRAF.calidad;
GRAF.calidad = function (el, W, inst) {
  const t = calidadBase(el, W, inst);
  leyendaColores(el, [{ clase: 'sw-s1', texto: 'A · Monto exacto' }, { clase: 'sw-s2', texto: 'B · Solo un rango de salarios mínimos' }, { clase: 'sw-s3', texto: 'C · No recibe ingresos' }, { clase: 'sw-s4', texto: 'D · No especificó' }]);
  return t;
};

/* aumento del ingreso por año de estudio en cada entidad, ordenadas, con el cuartil de ingreso del estado como color */
GRAF.retornoEstados = function (el, W) {
  const orden = D.estados.slice().sort((a, b) => b.ret[0] - a.ret[0]);
  const rows = orden.map((e, i) => ({
    label: e.n, v: e.ret[0], lo: e.ret[1], hi: e.ret[2], id: e.id, sel: S.estado === e.id, cls: 'm-q' + e.q, lineaGris: true, txt: i === 0 || i === orden.length - 1 ? f1(e.ret[0]) + ' %' : null,
    tip: [{ l: 'Aumento por año de estudio', v: pc(e.ret[0], 2) }, { l: 'IC 95 %', v: ic(e.ret[1], e.ret[2]) + ' %' }, { l: 'Ingreso mediano por hora', v: pesos(e.mln[0]) }, { l: 'Cuartil de ingreso del estado', v: nombreCuartil[e.q] }],
    nota: 'Un clic lo resalta en las demás figuras',
  }));
  const out = puntosH(el, W, {
    rows: rows, rowH: FIJO ? 17 : 15, dom: [2, 11], ticks: [2, 4, 6, 8, 10], tickFmt: (t) => t + ' %', fmt: (v) => pc(v, 1), mR: 34, radio: 4.8, ref: { v: D.k.ret[0], label: 'Nacional ' + pc(D.k.ret[0]) },
    ejeTit: 'Aumento del ingreso por hora por cada año de estudio (%), con IC 95 %',
    aria: 'Aumento del ingreso por año de estudio en cada entidad, con intervalo de confianza', alClic: (r) => setEstado(r.id),
    cols: ['Entidad', 'Aumento por año (%)', 'IC 95 %', 'Ingreso mediano ($/h)', 'Cuartil'], colsNum: [1, 3],
    filasTabla: () => orden.map((e) => [e.n, f2(e.ret[0]), ic(e.ret[1], e.ret[2], 2), pesos(e.mln[0]), 'Q' + e.q]),
  });
  leyendaColores(el, [1, 2, 3, 4].map((q) => ({ clase: 'sw-q' + q, texto: nombreCuartil[q] })));
  return out;
};

/* escolaridad promedio frente a ingreso mediano por hora (cada punto es una entidad) */
GRAF.escIngreso = function (el, W) {
  const pts = D.estados.map((e) => ({ id: e.id, x: e.esc[0], y: e.mln[0], lo: e.mln[1], hi: e.mln[2], cls: 'm-q' + e.q, q: e.q, e: e }));
  const alto1 = pts.reduce((a, p) => (p.y > a.y ? p : a)), bajo1 = pts.reduce((a, p) => (p.y < a.y ? p : a)), masEsc = pts.reduce((a, p) => (p.x > a.x ? p : a));
  const out = dispersion(el, W, {
    pts: pts, xd: [8.4, 13], yd: [30, 78], xFmt: (v) => String(v), yFmt: (v) => '$' + v, xTit: 'Años de escolaridad promedio de los ocupados del estado', yTit: 'Ingreso mediano por hora', tendencia: true,
    etiquetas: [alto1.id, bajo1.id, masEsc.id], aria: 'Ingreso mediano por hora frente a la escolaridad promedio de cada estado',
    tip: (p) => ({ f: [{ l: 'Ingreso mediano por hora', v: pesos(p.e.mln[0]) }, { l: 'IC 95 %', v: '$' + ic(p.e.mln[1], p.e.mln[2]) }, { l: 'Escolaridad promedio', v: f1(p.e.esc[0]) + ' años' }, { l: 'Cuartil de ingreso', v: nombreCuartil[p.q] }] }),
    cols: ['Entidad', 'Escolaridad promedio (años)', 'Ingreso mediano ($/h)', 'Cuartil'], colsNum: [1, 2],
    filasTabla: () => D.estados.slice().sort((a, b) => b.mln[0] - a.mln[0]).map((e) => [e.n, f1(e.esc[0]), pesos(e.mln[0]), 'Q' + e.q]),
  });
  leyendaColores(el, [1, 2, 3, 4].map((q) => ({ clase: 'sw-q' + q, texto: nombreCuartil[q] })));
  return out;
};

/* robustez de la brecha por hora ante las decisiones del análisis (S0 a S9) */
GRAF.robustez = function (el, W) {
  const corto = W < 560;
  const rows = D.robustez.map((r) => {
    const mensual = r.id === 'S6';
    return {
      label: corto ? r.id : r.n, v: r.v, lo: r.lo, hi: r.hi, gris: mensual, txt: pc(r.v),
      tip: [{ l: 'Brecha por hora', v: pc(r.v) }, { l: 'IC 95 %', v: ic(r.lo, r.hi) + ' %' }, { l: 'Valor p', v: r.p < 0.001 ? '< 0.001' : f2(r.p) }, { l: 'Personas', v: f0(r.N) }],
      nota: r.d + (r.id === 'S3' ? ' · sesga hacia cero por construcción' : mensual ? ' · es otro estimando: incluye la diferencia de horas' : ''),
    };
  });
  const out = puntosH(el, W, {
    rows: rows, rowH: 34, dom: [-1.5, 30], ticks: [0, 5, 10, 15, 20, 25, 30], tickFmt: (t) => t + ' %', fmt: (v) => pc(v, 1), cero: 0, mR: 56, radio: 5.2,
    ejeTit: '% menos que ganan las mujeres por hora (IC 95 %)',
    aria: 'Brecha por hora bajo diez especificaciones del análisis, con intervalo de confianza',
    cols: ['Especificación', 'Qué cambia', 'Brecha (%)', 'IC 95 %', 'Valor p', 'Personas'], colsNum: [2, 3, 4, 5],
    filasTabla: () => D.robustez.map((r) => [r.n, r.d, f1(r.v), ic(r.lo, r.hi), r.p < 0.001 ? '< 0.001' : f2(r.p), f0(r.N)]),
  });
  leyendaColores(el, [{ clase: 'sw-s1', texto: 'Brecha por hora' }, { clase: 'sw-gris', texto: 'Ingreso mensual (otro estimando)' }]);
  return out;
};

/* brecha por hora en subgrupos: punto relleno = significativa tras la corrección de Holm; hueco = no significativa */
GRAF.subgrupos = function (el, W) {
  const filas = [], base = D.subgrupos.filter((s) => !(s.dim === 'Grupo de edad' && s.cat === '65+'));       // 65+ tiene un intervalo tan amplio que no cabe en la escala: queda en la tabla
  let dim = null;
  base.forEach((s) => {
    if (s.dim !== dim) { dim = s.dim; filas.push({ cab: dim }); }
    filas.push({
      label: s.cat, v: s.v, lo: s.lo, hi: s.hi, hueco: !s.sig, txt: pc(s.v),
      tip: [{ l: 'Brecha por hora', v: pc(s.v) }, { l: 'IC 95 %', v: ic(s.lo, s.hi) + ' %' }, { l: 'p con Holm (en su dimensión)', v: s.pv < 0.001 ? '< 0.001' : f2(s.pv) }, { l: 'Hombres / mujeres en la muestra', v: f0(s.nh) + ' / ' + f0(s.nm) }],
      nota: s.sig ? 'Significativa tras la corrección de Holm' : 'No significativa tras la corrección de Holm',
    });
  });
  const out = puntosH(el, W, {
    rows: filas, rowH: 24, dom: [-2.5, 17], ticks: [0, 5, 10, 15], tickFmt: (t) => t + ' %', fmt: (v) => pc(v, 1), cero: 0, mR: 50, radio: 5,
    ejeTit: '% menos que ganan las mujeres por hora (IC 95 %)',
    aria: 'Brecha por hora en subgrupos de la población, con intervalo de confianza',
    cols: ['Dimensión', 'Categoría', 'Brecha (%)', 'IC 95 %', 'Significativa (Holm)', 'Hombres', 'Mujeres'], colsNum: [2, 3, 5, 6],
    filasTabla: () => D.subgrupos.map((s) => [s.dim, s.cat, f1(s.v), ic(s.lo, s.hi), s.sig ? 'Sí' : 'No', f0(s.nh), f0(s.nm)]),
  });
  leyendaColores(el, [{ clase: 'sw-s1', texto: 'Significativa (Holm, p < 0.05)' }, { hueco: true, texto: 'No significativa' }]);
  return out;
};

/* descomposición de Oaxaca-Blinder completa: total, explicada, cada grupo de características y no explicada */
GRAF.oaxacaCompleto = function (el, W) {
  const nota = { total: 'Brecha por hora entre hombres y mujeres', explicada: 'Lo que explican las diferencias en las características medidas; es negativa porque las mujeres tienen mejores características',
    comp: 'Contribución de este grupo de características a la parte explicada', noexp: 'A iguales características, se les paga menos; no prueba discriminación' };
  const rows = D.oaxaca_full.map((o) => ({
    label: (o.t === 'comp' ? '· ' : '') + o.n, v: o.v, lo: o.lo, hi: o.hi, cls: o.v < 0 ? 'm-s1' : 'm-rojo', lab: true, txt: signo(o.v, 1), sel: o.t !== 'comp',
    tip: [{ l: 'Puntos logarítmicos', v: signo(o.v, 2) }, { l: 'IC 95 %', v: ic(o.lo, o.hi, 2) }], nota: nota[o.t],
  }));
  const out = barrasH(el, W, {
    rows: rows, dom: [-5.5, 9.5], ticks: [-4, -2, 0, 2, 4, 6, 8], tickFmt: (t) => (t > 0 ? '+' : '') + String(t).replace('-', MENOS), fmt: (v) => signo(v, 1), rowH: 38, barH: 22, mR: 56,
    aria: 'Descomposición de Oaxaca-Blinder de la brecha por hora', cols: ['Componente', 'Puntos logarítmicos', 'IC 95 %'], colsNum: [1, 2],
    filasTabla: () => D.oaxaca_full.map((o) => [o.n, signo(o.v, 2), ic(o.lo, o.hi, 2)]),
  });
  leyendaColores(el, [{ clase: 'sw-rojo', texto: 'Aumenta la brecha (desventaja de las mujeres)' }, { clase: 'sw-s1', texto: 'Reduce la brecha (ventaja de las mujeres)' }]);
  return out;
};

/* cartograma de mosaicos con un indicador a elegir */
let metricaMosaico = 'til';
GRAF.mosaicoTil = (el) => mosaico(el, { metrica: () => metricaMosaico, textoInicial: 'Pasa el cursor o toca un mosaico; con un clic se resalta en las demás figuras.' });

/* ======================================================================================================================================
   Figuras: interactiva o imagen, tabla de datos y ampliación
   ====================================================================================================================================== */
const FUENTE_FIG = 'Fuente: INEGI, ENOE 2025-T4 (SDEMT y COE2T); estimaciones ponderadas con fac_tri; IC 95 % por bootstrap de Rao-Wu.';
const CON_CLIC = ['rankRho', 'retornoEstados', 'escIngreso', 'dispTil', 'mosaicoTil'];

function copiar(texto, origen, b, etiqueta, ok) {
  const fin = () => { b.textContent = ok; setTimeout(() => { b.textContent = etiqueta; }, 1400); };
  const seleccionar = () => { try { const r = document.createRange(); r.selectNodeContents(origen); const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = 'Selecciona y copia (Ctrl+C)'; setTimeout(() => { b.textContent = etiqueta; }, 2600); } catch (e) { /* nada */ } };
  try { if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(texto).then(fin, seleccionar); else seleccionar(); } catch (e) { seleccionar(); }
}
function boton(texto, clase, fn) {
  const b = document.createElement('button'); b.type = 'button'; if (clase) b.className = clase; b.textContent = texto;
  if (fn) b.addEventListener('click', fn);
  return b;
}
function abrirVisor(src, alt, pie) {
  const v = $('#visor'); if (!v) return;
  $('#visor-img', v).src = src; $('#visor-img', v).alt = alt || ''; $('#visor-pie', v).textContent = pie || '';
  v.hidden = false; $('#visor-cerrar', v).focus();
}
function tablaDe(t) {
  const tb = document.createElement('table'), cab = tb.createTHead().insertRow();
  t.cols.forEach((c, i) => { const th = document.createElement('th'); th.textContent = c; if ((t.num || []).indexOf(i) >= 0) th.className = 'n'; cab.appendChild(th); });
  const cu = tb.createTBody();
  t.rows.forEach((fila) => { const r = cu.insertRow(); fila.forEach((v, i) => { const c = r.insertCell(); c.textContent = String(v); if ((t.num || []).indexOf(i) >= 0) c.className = 'n'; }); });
  return tb;
}
function iniciarFiguras() {
  $$('figure.fig').forEach((fig) => {
    const png = $('.fig__png', fig), interactiva = fig.classList.contains('fig--int'), lienzo = $('.fig__lienzo', fig), cap = $('figcaption', fig);
    const barra = document.createElement('div'); barra.className = 'fig__barra';
    const etq = document.createElement('span'); etq.className = 'fig__etq'; etq.textContent = 'Figura ' + fig.dataset.n + (interactiva ? ' · interactiva' : '');
    const herr = document.createElement('div'); herr.className = 'fig__herr';
    barra.appendChild(etq); barra.appendChild(herr); fig.insertBefore(barra, fig.firstChild);
    const ampliar = () => abrirVisor(png.currentSrc || png.src, png.alt, cap ? cap.textContent : '');
    if (png) png.addEventListener('click', ampliar);
    if (!interactiva) { herr.appendChild(boton('Ampliar', 'ver-tabla', ampliar)); return; }
    fig.classList.add('js');
    const viz = $('.viz', fig), g = fig.dataset.g;
    const seg = document.createElement('div'); seg.className = 'seg'; seg.setAttribute('role', 'group'); seg.setAttribute('aria-label', 'Cómo mostrar la figura');
    const bInt = boton('Interactiva', '', null), bImg = boton('Imagen', '', null);
    [bInt, bImg].forEach((b) => seg.appendChild(b));
    const pon = (img) => {
      fig.classList.toggle('ver-png', img); bInt.setAttribute('aria-pressed', img ? 'false' : 'true'); bImg.setAttribute('aria-pressed', img ? 'true' : 'false');
      if (!img) { const inst = charts.filter((c) => c.el === viz)[0]; if (inst) inst.render(); }
    };
    bInt.addEventListener('click', () => pon(false)); bImg.addEventListener('click', () => pon(true)); pon(false);
    herr.appendChild(seg);
    if (g === 'mosaicoTil') {
      const sel = document.createElement('select'); sel.className = 'sel'; sel.id = 'sel-mosaico'; sel.setAttribute('aria-label', 'Indicador que colorea el mosaico');
      Object.keys(METRICAS).forEach((k) => { const o = document.createElement('option'); o.value = k; o.textContent = METRICAS[k].nombre; sel.appendChild(o); });
      sel.addEventListener('change', () => { metricaMosaico = sel.value; const inst = charts.filter((c) => c.el === viz)[0]; if (inst) inst.render(); });
      herr.appendChild(sel);
    }
    const tab = document.createElement('div'); tab.className = 'fig__tabla'; tab.hidden = true; lienzo.parentNode.insertBefore(tab, lienzo.nextSibling);
    const bt = boton('Ver tabla', 'ver-tabla', null); bt.setAttribute('aria-pressed', 'false');
    bt.addEventListener('click', () => {
      const on = !fig.classList.contains('con-tabla');
      if (on) { const inst = charts.filter((c) => c.el === viz)[0]; if (inst && inst.tab) { tab.textContent = ''; tab.appendChild(tablaDe(inst.tab())); } }
      fig.classList.toggle('con-tabla', on); tab.hidden = !on; bt.setAttribute('aria-pressed', on ? 'true' : 'false'); bt.textContent = on ? 'Ver gráfica' : 'Ver tabla';
      if (!on) { const inst = charts.filter((c) => c.el === viz)[0]; if (inst) inst.render(); }
    });
    herr.appendChild(bt);
    const ay = document.createElement('p'); ay.className = 'fig__ayuda';
    ay.textContent = (CON_CLIC.indexOf(g) >= 0 ? 'Pasa el cursor para ver los datos; un clic en una entidad la resalta en todas las figuras. ' : 'Pasa el cursor (o enfoca con el teclado) para ver los datos. ')
      + (g === 'subgrupos' ? 'No se grafica el grupo de 65 años o más (muestra muy pequeña, intervalo muy amplio); aparece en la tabla. ' : '') + FUENTE_FIG;
    lienzo.appendChild(ay);
    montar(viz);
  });
  const portada = $('.portada .viz'); if (portada) montar(portada);
}

/* ======================================================================================================================================
   Ficha flotante de la entidad elegida
   ====================================================================================================================================== */
function pintarDock(id) {
  const d = $('#dock'); if (!d) return;
  if (id == null) { d.hidden = true; d.textContent = ''; return; }
  const e = porId[id];
  d.hidden = false; d.textContent = '';
  const cab = document.createElement('div'); cab.className = 'dock__cab';
  const t = document.createElement('div'), h = document.createElement('p'), r = document.createElement('p');
  h.className = 'dock__tit'; h.textContent = e.n; r.className = 'dock__reg'; r.textContent = 'Región ' + e.r + ' · ingreso Q' + e.q;
  t.appendChild(h); t.appendChild(r);
  const b = boton('×', '', () => setEstado(null, true)); b.setAttribute('aria-label', 'Quitar la entidad elegida');
  cab.appendChild(t); cab.appendChild(b); d.appendChild(cab);
  const dl = document.createElement('dl');
  const fila = (k, v, sub) => {
    const a = document.createElement('dt'), c = document.createElement('dd'); a.textContent = k; c.textContent = v;
    if (sub) { const s = document.createElement('span'); s.className = 'ic95'; s.textContent = sub; c.appendChild(s); }
    dl.appendChild(a); dl.appendChild(c);
  };
  fila('Informalidad (TIL1)', pc(e.til[0]), 'IC 95 %: ' + ic(e.til[1], e.til[2]) + ' · lugar ' + e.til[3] + ' de 32');
  fila('Escolaridad promedio', f1(e.esc[0]) + ' años');
  fila('Aumento por año de estudio', pc(e.ret[0], 2), 'IC 95 %: ' + ic(e.ret[1], e.ret[2]) + ' %');
  fila('Correlación ρ (Spearman)', f2(e.rho[0]), 'lugar ' + e.rho[3] + ' (' + e.rho[4] + ' a ' + e.rho[5] + ')');
  fila('Ingreso mediano por hora', pesos(e.mln[0]));
  fila('Brecha de género por hora', pc(e.bh[0]), 'IC 95 %: ' + ic(e.bh[1], e.bh[2]) + ' %');
  d.appendChild(dl);
}

/* ======================================================================================================================================
   Navegación: índice lateral, miga, progreso, búsqueda
   ====================================================================================================================================== */
const norm = (s) => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

function iniciarNavegacion() {
  const indice = $('#indice'), prog = $('#progreso'), miga = $('#miga'), arriba = $('#arriba'), barra = $('#barra');
  const marcas = [];
  $$('.prelim').forEach((s) => marcas.push({ el: $('.prelim-t', s) || s, id: s.id, etq: ($('.prelim-t', s) || s).textContent, cap: null }));
  $$('.capitulo').forEach((c) => {
    marcas.push({ el: $('.cap-titulo', c), id: c.id, etq: ($('.cap-etq', c).textContent ? $('.cap-etq', c).textContent + ' · ' : '') + $('.cap-titulo', c).textContent, cap: c.id, capTit: c.dataset.titulo });
    $$('.sec-titulo', c).forEach((h) => marcas.push({ el: h, id: h.id, etq: tituloSec(h), cap: c.id }));
  });
  const enlace = (id) => $('a[data-id="' + id + '"]', indice);
  let activo = null;
  function actualizar() {
    const alto_ = document.documentElement.scrollHeight - innerHeight, y = window.scrollY;
    if (prog) prog.style.transform = 'scaleX(' + (alto_ > 0 ? clamp(y / alto_, 0, 1) : 0) + ')';
    if (arriba) arriba.hidden = y < innerHeight * 0.9;
    const limite = (barra ? barra.offsetHeight : 52) + 36;
    let cur = null;
    for (let i = 0; i < marcas.length; i++) { if (marcas[i].el.getBoundingClientRect().top <= limite) cur = marcas[i]; else break; }
    const id = cur ? cur.id : null;
    if (id === activo) return;
    activo = id;
    $$('a.activo', indice).forEach((a) => a.classList.remove('activo'));
    $$('.cap.abierto', indice).forEach((c) => c.classList.remove('abierto'));
    if (cur) {
      const a = enlace(cur.id);
      if (a) {
        a.classList.add('activo');
        const cap = a.closest('.cap'); if (cap) cap.classList.add('abierto');
        const r = a.getBoundingClientRect(), ri = indice.getBoundingClientRect();
        if (r.top < ri.top + 40 || r.bottom > ri.bottom - 40) indice.scrollTop += r.top - ri.top - ri.height / 3;
      }
      if (miga) {
        miga.textContent = '';
        if (cur.cap && cur.cap !== cur.id) { const b = document.createElement('b'); b.textContent = cur.capTit || ((marcas.filter((m) => m.id === cur.cap)[0] || {}).capTit) || ''; miga.appendChild(b); miga.appendChild(document.createTextNode(' › ' + cur.etq)); }
        else miga.textContent = cur.etq;
      }
    } else if (miga) miga.textContent = '';
  }
  let pend = false;
  addEventListener('scroll', () => { if (!pend) { pend = true; requestAnimationFrame(() => { pend = false; actualizar(); }); } }, { passive: true });
  addEventListener('resize', actualizar);
  actualizar();
  /* panel lateral en pantallas angostas */
  const abrir = $('#btn-indice'), cerrar = $('#btn-cerrar-indice');
  const velo = document.createElement('div'); velo.className = 'velo'; velo.hidden = true; document.body.appendChild(velo);
  const poner = (on) => { document.body.classList.toggle('indice-abierto', on); velo.hidden = !on; if (abrir) abrir.setAttribute('aria-expanded', on ? 'true' : 'false'); };
  if (abrir) abrir.addEventListener('click', () => poner(!document.body.classList.contains('indice-abierto')));
  if (cerrar) cerrar.addEventListener('click', () => poner(false));
  velo.addEventListener('click', () => poner(false));
  indice.addEventListener('click', (ev) => { if (ev.target.closest('a') && matchMedia('(max-width: 1100px)').matches) poner(false); });
  if (arriba) arriba.addEventListener('click', () => window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }));
}

function tituloSec(h) { const n = $('.num', h), t = Array.from(h.childNodes).filter((x) => !(x.nodeType === 1 && (x.matches('.ancla') || x.matches('.num')))).map((x) => x.textContent).join('').trim(); return (n ? n.textContent + ' ' : '') + t; }
function iniciarBuscador() {
  const caja = $('#buscador'), entrada = $('#buscar-texto'), lista = $('#buscar-res');
  let indiceTxt = null, seleccion = 0, resultados = [];
  const construir = () => {
    indiceTxt = [];
    $$('.prelim, .capitulo').forEach((cap) => {
      const capTit = cap.dataset.titulo || ($('.prelim-t', cap) || {}).textContent || '';
      let sec = capTit, secId = cap.id;
      $$('.prelim-t, .sec-titulo, .sub-titulo, p, li, figcaption, .faq__r, .gl, .tabla-cap', cap).forEach((el) => {
        if (el.matches('.sec-titulo')) { sec = tituloSec(el); secId = el.id; }
        if (el.closest('.cap-nav, .cap-secs, .toc-gen, .toc-lista, .buscador, .indice, .claves')) return;
        const txt = el.textContent.replace(/\s+/g, ' ').trim();
        if (txt.length < 12 && !el.matches('.sec-titulo, .sub-titulo, .prelim-t')) return;
        indiceTxt.push({ el: el, cap: capTit, sec: sec, secId: secId, txt: txt, n: norm(txt), t: el.matches('.sec-titulo, .sub-titulo, .prelim-t') ? 1 : 0 });
      });
    });
  };
  const pintar = () => {
    lista.textContent = '';
    resultados.forEach((r, i) => {
      const li = document.createElement('li'); if (i === seleccion) li.className = 'sel';
      const a = document.createElement('a'); a.href = '#' + (r.el.id || r.secId);
      const b = document.createElement('b'); b.textContent = (r.cap === r.sec ? r.cap : r.cap + ' › ' + r.sec).slice(0, 110);
      const s = document.createElement('span');
      const pos = Math.max(0, r.n.indexOf(r.q0)), ini = Math.max(0, pos - 50), frag = r.txt.slice(ini, ini + 170), m = norm(frag).indexOf(r.q0), mas = ini + 170 < r.txt.length ? ' …' : '';
      s.appendChild(document.createTextNode(ini > 0 ? '… ' : ''));
      if (m >= 0) {                                                  // se marca la primera palabra buscada dentro del fragmento
        s.appendChild(document.createTextNode(frag.slice(0, m)));
        const k = document.createElement('mark'); k.textContent = frag.slice(m, m + r.q0.length); s.appendChild(k);
        s.appendChild(document.createTextNode(frag.slice(m + r.q0.length) + mas));
      } else s.appendChild(document.createTextNode(frag + mas));
      a.appendChild(b); a.appendChild(s);
      a.addEventListener('click', (ev) => { ev.preventDefault(); ir(r); });
      li.appendChild(a); lista.appendChild(li);
    });
    if (!resultados.length && entrada.value.trim()) { const li = document.createElement('li'); const s = document.createElement('span'); s.style.padding = '.6rem .7rem'; s.textContent = 'Sin resultados.'; li.appendChild(s); lista.appendChild(li); }
  };
  const buscar = () => {
    const q = norm(entrada.value).trim();
    if (q.length < 2) { resultados = []; pintar(); return; }
    const qs = q.split(/\s+/);
    resultados = indiceTxt.filter((x) => qs.every((w) => x.n.indexOf(w) >= 0)).map((x) => Object.assign({ q0: qs[0], qs: qs, score: (x.t ? 10 : 0) + (x.n.indexOf(q) >= 0 ? 5 : 0) }, x))
      .sort((a, b) => b.score - a.score).slice(0, 30);
    seleccion = 0; pintar();
  };
  const cerrar = () => { caja.hidden = true; entrada.value = ''; lista.textContent = ''; document.body.style.overflow = ''; };
  const abrir = () => { if (!indiceTxt) construir(); caja.hidden = false; document.body.style.overflow = 'hidden'; entrada.focus(); entrada.select(); };
  const ir = (r) => {
    cerrar();
    r.el.scrollIntoView({ block: 'center', behavior: 'auto' });
    r.el.classList.remove('destello'); void r.el.offsetWidth; r.el.classList.add('destello');
    try { history.replaceState(null, '', '#' + (r.el.id || r.secId)); } catch (e) { /* algunos visores no permiten cambiar la dirección */ }
  };
  $('#btn-buscar').addEventListener('click', abrir);
  caja.addEventListener('click', (ev) => { if (ev.target === caja) cerrar(); });
  entrada.addEventListener('input', buscar);
  entrada.addEventListener('keydown', (ev) => {
    if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') { ev.preventDefault(); seleccion = clamp(seleccion + (ev.key === 'ArrowDown' ? 1 : -1), 0, Math.max(0, resultados.length - 1)); pintar(); const s = $('li.sel', lista); if (s) s.scrollIntoView({ block: 'nearest' }); }
    else if (ev.key === 'Enter' && resultados[seleccion]) { ev.preventDefault(); ir(resultados[seleccion]); }
  });
  document.addEventListener('keydown', (ev) => {
    const tag = (ev.target && ev.target.tagName) || '';
    if (ev.key === 'Escape') { if (!caja.hidden) cerrar(); const v = $('#visor'); if (v && !v.hidden) v.hidden = true; return; }
    if (((ev.key === 'k' || ev.key === 'K') && (ev.ctrlKey || ev.metaKey)) || (ev.key === '/' && tag !== 'INPUT' && tag !== 'TEXTAREA' && tag !== 'SELECT')) { ev.preventDefault(); abrir(); }
  });
}

/* ======================================================================================================================================
   Tablas, glosario, preguntas, código y definiciones emergentes
   ====================================================================================================================================== */
function valorCelda(td) {
  const t = td.textContent.trim().replace(/−/g, '-').replace(/[,$%\s]/g, '');
  const m = t.match(/-?\d+(?:\.\d+)?/);
  return m && /^[-\d.<>]/.test(t) ? parseFloat(m[0]) : null;
}
function iniciarTablas() {
  const porNombre = {};
  D.estados.forEach((e) => { porNombre[norm(e.n)] = e.id; });
  $$('.tabla-fig').forEach((fig) => {
    const tabla = $('table', fig), cuerpo = $('tbody', tabla), filas = $$('tr', cuerpo);
    filas.forEach((tr) => { for (let i = 0; i < Math.min(2, tr.cells.length); i++) { const id = porNombre[norm(tr.cells[i].textContent.trim())]; if (id != null) { tr.dataset.ent = id; tr.style.cursor = 'pointer'; tr.title = 'Clic para resaltar esta entidad en las figuras'; tr.addEventListener('click', () => setEstado(id)); break; } } });
    if (fig.hasAttribute('data-ordenable')) {
      $$('thead th', tabla).forEach((th, j) => {
        th.tabIndex = 0;
        const ordenar = () => {
          const asc = th.getAttribute('aria-sort') !== 'ascending';
          $$('thead th', tabla).forEach((x) => x.removeAttribute('aria-sort')); th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
          const datos = filas.map((tr, i) => ({ tr: tr, i: i, v: valorCelda(tr.cells[j]), s: tr.cells[j].textContent.trim() }));
          const numerico = datos.every((x) => x.v != null);
          datos.sort((a, b) => (numerico ? a.v - b.v : a.s.localeCompare(b.s, 'es')) * (asc ? 1 : -1) || a.i - b.i);
          datos.forEach((x) => cuerpo.appendChild(x.tr));
        };
        th.addEventListener('click', ordenar);
        th.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); ordenar(); } });
      });
    }
    if (filas.length >= 30) {
      const lb = document.createElement('label'); lb.className = 'tabla-filtro';
      const inp = document.createElement('input'); inp.type = 'search'; inp.id = 'filtro-' + fig.id; inp.placeholder = 'Filtrar por entidad…'; inp.setAttribute('aria-label', 'Filtrar la tabla');
      lb.appendChild(inp); fig.insertBefore(lb, $('.tabla-marco', fig));
      inp.addEventListener('input', () => { const q = norm(inp.value).trim(); filas.forEach((tr) => { tr.hidden = q && norm(tr.textContent).indexOf(q) < 0; }); });
    }
  });
  alEstado.push((id) => $$('tr[data-ent]').forEach((tr) => tr.classList.toggle('sel-ent', id != null && +tr.dataset.ent === id)));
}

function iniciarTextos() {
  /* glosario con filtro */
  $$('.glosario').forEach((g, k) => {
    const inp = $('input', g), items = $$('.gl', g), vacio = $('.sin-resultados', g);
    inp.id = 'filtro-glosario' + (k ? '-' + k : '');
    inp.addEventListener('input', () => { const q = norm(inp.value).trim(); let n = 0; items.forEach((it) => { const ok = !q || norm(it.textContent).indexOf(q) >= 0; it.hidden = !ok; if (ok) n++; }); vacio.hidden = n > 0; });
  });
  /* preguntas frecuentes: expandir o contraer todas las de un bloque */
  $$('h4.sub-titulo').forEach((h) => {
    const fq = []; let s = h.nextElementSibling;
    while (s && s.classList.contains('faq')) { fq.push(s); s = s.nextElementSibling; }
    if (fq.length < 2) return;
    const d = document.createElement('div'); d.className = 'faq-herr';
    const b = boton('Expandir todas', 'btn btn--chico', null);
    b.addEventListener('click', () => { const abrir = fq.some((x) => !x.open); fq.forEach((x) => { x.open = abrir; }); b.textContent = abrir ? 'Contraer todas' : 'Expandir todas'; });
    d.appendChild(b); h.parentNode.insertBefore(d, h.nextSibling);
  });
  /* bloques de código: botón de copiar */
  $$('.codigo').forEach((c) => {
    const code = $('code', c); if (!code || c.closest('.interactivo')) return;
    const b = boton('Copiar', 'codigo__copiar', null);
    b.addEventListener('click', () => copiar(code.textContent, code, b, 'Copiar', 'Copiado'));
    c.appendChild(b);
  });
  const bc = $('#btn-copiar-cita');
  if (bc) bc.addEventListener('click', () => copiar($('#cita-texto').textContent, $('#cita-texto'), bc, 'Copiar cita', 'Copiada'));
  /* definiciones emergentes de los términos del glosario */
  $$('abbr.termino').forEach((a) => {
    const g = document.getElementById(a.dataset.g); if (!g) return;
    const mostrar = (x, y) => { llenarGlobo($('dt', g).textContent, [], $('dd', g).textContent); globo.classList.add('def'); colocarGlobo(x, y); };
    a.addEventListener('pointerenter', (ev) => mostrar(ev.clientX, ev.clientY));
    a.addEventListener('pointermove', (ev) => colocarGlobo(ev.clientX, ev.clientY));
    a.addEventListener('pointerleave', () => { ocultarGlobo(); globo.classList.remove('def'); });
    a.addEventListener('focus', () => { const r = a.getBoundingClientRect(); mostrar(r.left + r.width / 2, r.bottom); });
    a.addEventListener('blur', () => { ocultarGlobo(); globo.classList.remove('def'); });
  });
  /* los globos de las gráficas no deben conservar el estilo de definición */
  globo.addEventListener('transitionend', () => { if (!globo.classList.contains('on')) globo.classList.remove('def'); });
}

/* ======================================================================================================================================
   Componentes interactivos del texto, selector de entidad y tema
   ====================================================================================================================================== */
function iniciarComponentes() {
  const rg = $('#calc-rango');
  if (rg) {
    const sal = $('#calc-res'), nota = $('#calc-ic'), n_ = $('#calc-n'), r = D.k.ret;
    const calc = () => {
      const n = +rg.value, efecto = (p) => (Math.pow(1 + p / 100, n) - 1) * 100;
      n_.textContent = n; sal.textContent = '+' + f0(efecto(r[0])) + ' %';
      nota.textContent = n + (n === 1 ? ' año más de estudio' : ' años más de estudio') + ' se asocian con un ingreso por hora mayor en esa proporción (IC 95 %: +' + f0(efecto(r[1])) + ' a +' + f0(efecto(r[2])) + ' %), a igual edad, sexo, entidad y tamaño de localidad. Es una asociación, no un efecto causal.';
    };
    rg.addEventListener('input', calc); calc();
  }
  const lista = D.estados.slice().sort((a, b) => a.n.localeCompare(b.n, 'es'));
  const llenar = (s, conVacio) => {
    if (!s) return;
    if (conVacio) { const o = document.createElement('option'); o.value = ''; o.textContent = 'Entidad: todas'; s.appendChild(o); }
    lista.forEach((e) => { const o = document.createElement('option'); o.value = String(e.id); o.textContent = e.n; s.appendChild(o); });
  };
  const fic = $('#sel-ficha');
  $$('select[data-sel-estado]').forEach((sel) => { llenar(sel, true); sel.addEventListener('change', () => setEstado(sel.value === '' ? null : +sel.value, true)); });
  llenar(fic, false);
  if (fic) fic.value = '20';
  if (fic) fic.addEventListener('change', () => setEstado(+fic.value, true));
  const chip = $('#chip-estado'); if (chip) $('button', chip).addEventListener('click', () => setEstado(null, true));
  alEstado.push(pintarDock);
  /* tema claro u oscuro */
  const aplicar = (t) => { document.documentElement.setAttribute('data-theme', t); try { localStorage.setItem('enoe-tema', t); } catch (e) { /* sin almacenamiento */ } setTimeout(renderTodo, 30); };
  $('#btn-tema').addEventListener('click', () => {
    const oscuro = document.documentElement.getAttribute('data-theme') === 'dark' || (!document.documentElement.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
    aplicar(oscuro ? 'light' : 'dark');
  });
  try { const g = localStorage.getItem('enoe-tema'); if (g === 'dark' || g === 'light') document.documentElement.setAttribute('data-theme', g); } catch (e) { /* nada */ }
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => setTimeout(renderTodo, 30));
  const v = $('#visor');
  if (v) { $('#visor-cerrar', v).addEventListener('click', () => { v.hidden = true; }); v.addEventListener('click', (ev) => { if (ev.target === v) v.hidden = true; }); }
}

/* ---------- arranque ---------- */
function iniciar() {
  iniciarComponentes();
  iniciarFiguras();
  iniciarTablas();
  iniciarTextos();
  iniciarNavegacion();
  iniciarBuscador();
  pintarFicha();
  let t = null;
  addEventListener('resize', () => { clearTimeout(t); t = setTimeout(renderTodo, 140); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(renderTodo);
  if (location.hash.length > 1) setTimeout(() => { const el = document.getElementById(decodeURIComponent(location.hash.slice(1))); if (el) el.scrollIntoView({ behavior: 'auto', block: 'start' }); }, 500);
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
