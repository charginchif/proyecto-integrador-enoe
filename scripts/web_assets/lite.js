/* Radiografía socioeconómica de México · versión ligera e interactiva.
   Gráficas dibujadas con SVG propio (sin librerías) a partir del JSON incrustado en la página (#datos). Reglas de visualización:
   barras desde cero con extremo redondeado, líneas de 2 px, puntos con anillo del color de la superficie, rejilla hairline, etiquetas selectivas,
   globo de datos al pasar el cursor o enfocar, una tabla equivalente por gráfica y colores tomados de variables CSS (cambian con el tema). */
(function () {
  'use strict';

  const D = JSON.parse(document.getElementById('datos').textContent);
  const NS = 'http://www.w3.org/2000/svg';
  const MENOS = '−';
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  /* ---------- formato ---------- */
  const num = (v, d) => Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }).replace('-', MENOS);
  const f0 = (v) => num(v, 0), f1 = (v) => num(v, 1), f2 = (v) => num(v, 2);
  const pc = (v, d) => num(v, d == null ? 1 : d) + ' %';
  const signo = (v, d) => (v > 0 ? '+' : '') + num(v, d == null ? 1 : d);
  const pesos = (v) => '$' + num(v, 2);
  const ic = (a, b, d) => num(a, d == null ? 1 : d) + ' a ' + num(b, d == null ? 1 : d);

  /* ---------- color ---------- */
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  function lumin(hex) {
    const m = /^#?([0-9a-f]{6})$/i.exec(hex);
    if (!m) return 0.5;
    const v = parseInt(m[1], 16);
    const c = [(v >> 16) & 255, (v >> 8) & 255, v & 255].map((x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  const contraste = (a, b) => { const la = lumin(a), lb = lumin(b); return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05); };
  const tintaSobre = (fondo) => (contraste(fondo, '#ffffff') >= contraste(fondo, css('--ink')) ? '#ffffff' : css('--ink'));

  /* ---------- SVG y medición de texto ---------- */
  function sv(tag, attrs, padre) {
    const e = document.createElementNS(NS, tag);
    if (attrs) for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (padre) padre.appendChild(e);
    return e;
  }
  function tx(padre, x, y, texto, clase, ancla) {
    const e = sv('text', { x: x, y: y, dy: '.35em', class: clase || null, 'text-anchor': ancla || 'start' }, padre);
    e.textContent = texto;
    return e;
  }
  const lienzo = document.createElement('canvas').getContext('2d');
  const FUENTE = '"IBM Plex Sans","Segoe UI",system-ui,sans-serif';
  function medir(texto, peso, tam) { lienzo.font = (peso || 500) + ' ' + (tam || 13) + 'px ' + FUENTE; return lienzo.measureText(texto).width; }

  function niceStep(rango, n) { const raw = rango / n, mag = Math.pow(10, Math.floor(Math.log10(raw))), r = raw / mag; return (r < 1.5 ? 1 : r < 3 ? 2 : r < 7 ? 5 : 10) * mag; }
  function marcas(a, b, n) { const st = niceStep(b - a, n || 5), t = []; for (let v = Math.ceil(a / st) * st; v <= b + st * 1e-6; v += st) t.push(+v.toFixed(10)); return t; }

  /* barra con la esquina redondeada solo en el extremo de datos (4 px) y recta en la línea base */
  function barraRedonda(x0, y, w, h, r) {
    const dir = w < 0 ? -1 : 1, aw = Math.abs(w);
    if (aw < 0.5) return '';
    const rr = Math.min(r, aw / 2, h / 2), xe = x0 + dir * aw;
    return 'M' + x0 + ',' + y + ' H' + (xe - dir * rr) + ' Q' + xe + ',' + y + ' ' + xe + ',' + (y + rr) + ' V' + (y + h - rr) + ' Q' + xe + ',' + (y + h) + ' ' + (xe - dir * rr) + ',' + (y + h) + ' H' + x0 + ' Z';
  }

  /* ---------- globo de datos ---------- */
  const globo = document.createElement('div');
  globo.className = 'globo';
  globo.setAttribute('role', 'tooltip');
  document.body.appendChild(globo);
  function llenarGlobo(titulo, filas, nota) {
    globo.textContent = '';
    if (titulo) { const b = document.createElement('b'); b.textContent = titulo; globo.appendChild(b); }
    (filas || []).forEach((f) => {
      const d = document.createElement('div'); d.className = 'f';
      const a = document.createElement('span');
      if (f.k) { const k = document.createElement('i'); k.className = 'k'; k.style.background = f.k; a.appendChild(k); }
      a.appendChild(document.createTextNode(f.l));
      const v = document.createElement('strong'); v.textContent = f.v;
      d.appendChild(a); d.appendChild(v); globo.appendChild(d);
    });
    if (nota) { const n = document.createElement('small'); n.textContent = nota; globo.appendChild(n); }
  }
  function colocarGlobo(x, y) {
    globo.classList.add('on');
    const r = globo.getBoundingClientRect();
    let nx = x + 14, ny = y + 16;
    if (nx + r.width > innerWidth - 8) nx = x - r.width - 14;
    if (ny + r.height > innerHeight - 8) ny = y - r.height - 14;
    globo.style.left = Math.max(8, nx) + 'px';
    globo.style.top = Math.max(8, ny) + 'px';
  }
  function ocultarGlobo() { globo.classList.remove('on'); }
  /* enlaza un nodo SVG/HTML con su globo: cursor, foco por teclado y salida */
  function conGlobo(nodo, fnDatos) {
    nodo.addEventListener('pointermove', (ev) => { const d = fnDatos(); llenarGlobo(d.t, d.f, d.n); colocarGlobo(ev.clientX, ev.clientY); });
    nodo.addEventListener('pointerleave', ocultarGlobo);
    nodo.addEventListener('focus', () => { const d = fnDatos(), r = nodo.getBoundingClientRect(); llenarGlobo(d.t, d.f, d.n); colocarGlobo(r.left + r.width / 2, r.top); });
    nodo.addEventListener('blur', ocultarGlobo);
  }

  /* ---------- estado global: la entidad elegida resalta en todas las gráficas ---------- */
  const S = { estado: null };
  const porId = {};
  D.estados.forEach((e) => { porId[e.id] = e; });
  const charts = [];
  const GRAF = {};
  function renderTodo() { charts.forEach((c) => c.render()); }
  function setEstado(id, forzar) {
    S.estado = forzar || id !== S.estado ? id : null;
    const sel = $('#sel-estado'), fic = $('#sel-ficha');
    if (sel) sel.value = S.estado == null ? '' : String(S.estado);
    if (fic) fic.value = String(S.estado == null ? 20 : S.estado);
    const chip = $('#chip-estado');
    if (chip) { chip.classList.toggle('on', S.estado != null); $('span', chip).textContent = S.estado == null ? '' : porId[S.estado].n; }
    renderTodo();
    pintarFicha();
  }

  function montar(el) {
    const f = GRAF[el.dataset.chart];
    if (!f) return;
    const inst = {
      el: el, tab: null, w: 0,
      render() {
        if (el.getClientRects().length === 0) return;
        const w = Math.floor(el.clientWidth);
        if (w < 40) return;
        this.w = w;
        el.textContent = '';
        this.tab = f(el, w, this) || null;
      },
    };
    charts.push(inst);
    new ResizeObserver(() => { if (Math.floor(el.clientWidth) !== inst.w) inst.render(); }).observe(el);
    inst.render();
  }

  /* ======================================================================================================================================
     Gráficas
     ====================================================================================================================================== */

  /* ---- barras horizontales (embudo, premio por nivel, informalidad por nivel, brecha por nivel, Oaxaca-Blinder) ---- */
  function barrasH(el, W, cfg) {
    const rows = cfg.rows, rowH = cfg.rowH || 34, barH = Math.min(24, cfg.barH || 22);
    let lw = 0;
    rows.forEach((r) => { lw = Math.max(lw, medir(r.label, 500, 13)); });
    const mL = cfg.sinEtiquetas ? 8 : Math.min(Math.ceil(lw) + 16, Math.max(120, W * 0.44));
    const mR = cfg.mR == null ? 66 : cfg.mR, mT = 4, mB = cfg.sinEje ? 4 : 26;
    const H = mT + rows.length * rowH + mB;
    const svg = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': cfg.aria || '' }, el);
    const x0 = mL, x1 = W - mR, d0 = cfg.dom[0], d1 = cfg.dom[1];
    const sx = (v) => x0 + (v - d0) / (d1 - d0) * (x1 - x0);
    const base = sx(Math.max(d0, Math.min(0, d1)));
    const g = sv('g', { class: 'eje' }, svg);
    (cfg.ticks || marcas(d0, d1, 5)).forEach((t) => {
      const x = sx(t);
      sv('line', { x1: x, x2: x, y1: mT, y2: mT + rows.length * rowH, class: 'rej' }, g);
      if (!cfg.sinEje) tx(g, x, H - 9, cfg.tickFmt ? cfg.tickFmt(t) : f0(t), null, 'middle');
    });
    sv('line', { x1: base, x2: base, y1: mT, y2: mT + rows.length * rowH, class: 'base' }, svg);
    if (cfg.ref) {
      const xr = sx(cfg.ref.v);
      sv('line', { x1: xr, x2: xr, y1: mT, y2: mT + rows.length * rowH, class: 'ref' }, svg);
      tx(svg, xr + 4, mT + 8, cfg.ref.label, 't-ref');
    }
    rows.forEach((r, i) => {
      const yc = mT + i * rowH + rowH / 2, y = yc - barH / 2;
      const gr = sv('g', { 'data-i': i }, svg);
      if (!cfg.sinEtiquetas) tx(gr, x0 - 10, yc, r.label, 't-cat' + (r.sel ? ' sel' : ''), 'end');
      const w = sx(r.v) - base;
      const p = sv('path', { d: barraRedonda(base, y, w, barH, 4), class: r.cls || 'm-s1' }, gr);
      if (cfg.enfasis && !r.key) p.setAttribute('opacity', '.55');
      let xFin = base + w;
      if (r.lo != null) {
        sv('line', { x1: sx(r.lo), x2: sx(r.hi), y1: yc, y2: yc, class: 'ic ic-gris' }, gr);
        sv('line', { x1: sx(r.lo), x2: sx(r.lo), y1: yc - 5, y2: yc + 5, class: 'ic ic-gris' }, gr);
        sv('line', { x1: sx(r.hi), x2: sx(r.hi), y1: yc - 5, y2: yc + 5, class: 'ic ic-gris' }, gr);
        xFin = r.v >= 0 ? Math.max(xFin, sx(r.hi)) : Math.min(xFin, sx(r.lo));
      }
      if (r.lab || cfg.etiquetas) tx(gr, r.v >= 0 ? xFin + 7 : xFin - 7, yc, r.txt || cfg.fmt(r.v), 't-val', r.v >= 0 ? 'start' : 'end');
      const hit = sv('rect', { x: 0, y: mT + i * rowH, width: W, height: rowH, class: 'fila-hit', tabindex: 0, role: 'img', 'aria-label': r.label + ': ' + (r.txt || cfg.fmt(r.v)) }, gr);
      conGlobo(hit, () => ({ t: r.label, f: r.tip || [{ l: cfg.medida || 'Valor', v: r.txt || cfg.fmt(r.v), k: null }], n: r.nota }));
    });
    return () => ({ cols: cfg.cols, num: cfg.colsNum, rows: cfg.filasTabla ? cfg.filasTabla() : rows.map((r) => [r.label, r.txt || cfg.fmt(r.v)]) });
  }

  /* ---- 100 % apilado: calidad del ingreso ---- */
  GRAF.calidad = function (el, W) {
    const claves = ['A', 'B', 'C', 'D'], nombres = { A: 'Monto exacto', B: 'Solo un rango de salarios mínimos', C: 'No recibe ingresos', D: 'No especificó' };
    const col = { A: '--s1', B: '--s2', C: '--s3', D: '--s4' }, cls = { A: 'm-s1 seg-a', B: 'm-s2 seg-b', C: 'm-s3 seg-c', D: 'm-s4 seg-d' };
    const filas = D.calidad, rowH = 36, barH = 24, hueco = 14;
    let lw = 0; filas.forEach((r) => { lw = Math.max(lw, medir(r.n, 500, 13)); });
    const mL = Math.min(Math.ceil(lw) + 16, Math.max(120, W * 0.3)), mR = 8, mT = 4, mB = 26;
    let y = mT; const ys = filas.map((r, i) => { if (i && r.g !== filas[i - 1].g) y += hueco; const v = y; y += rowH; return v; });
    const H = y + mB - mT + 4;
    const svg = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': 'Composición del ingreso por grupo de declaración' }, el);
    const x0 = mL, x1 = W - mR, sx = (v) => x0 + v / 100 * (x1 - x0), g = sv('g', { class: 'eje' }, svg);
    [0, 25, 50, 75, 100].forEach((t) => { const x = sx(t); sv('line', { x1: x, x2: x, y1: mT, y2: y, class: 'rej' }, g); tx(g, x, H - 9, t + ' %', null, 'middle'); });
    filas.forEach((r, i) => {
      const yc = ys[i] + rowH / 2, yb = yc - barH / 2, gr = sv('g', null, svg);
      tx(gr, x0 - 10, yc, r.n, 't-cat', 'end');
      let acum = 0;
      claves.forEach((k) => {
        const a = sx(acum), b = sx(acum + r[k]);
        const xa = a + (acum > 0 ? 1 : 0), xb = b - (acum + r[k] < 99.9 ? 1 : 0);          // 2 px de superficie entre segmentos
        const seg = sv('rect', { x: xa, y: yb, width: Math.max(0, xb - xa), height: barH, class: cls[k], tabindex: 0, role: 'img', 'aria-label': r.n + ', ' + nombres[k] + ': ' + pc(r[k]) }, gr);
        if (xb - xa >= medir(pc(r[k], 0), 600, 12.5) + 12) tx(gr, (xa + xb) / 2, yc, pc(r[k], 0), 't-dentro ' + cls[k].split(' ')[1], 'middle').setAttribute('fill', tintaSobre(css(col[k])));
        conGlobo(seg, () => ({ t: r.n, f: claves.map((q) => ({ l: q + ' · ' + nombres[q], v: pc(r[q]), k: 'var(' + col[q] + ')' })) }));
        acum += r[k];
      });
    });
    return () => ({ cols: ['Población', 'A · Monto exacto', 'B · Solo rango', 'C · No recibe ingresos', 'D · No especificó'], num: [1, 2, 3, 4], rows: filas.map((r) => [r.n, pc(r.A), pc(r.B), pc(r.C), pc(r.D)]) });
  };

  /* ---- embudo de datos ---- */
  GRAF.embudo = function (el, W) {
    const rows = D.embudo.map((e) => ({ label: e.n, v: e.v, key: !!e.k, lab: !!e.k, txt: f0(e.v), tip: [{ l: 'Registros', v: f0(e.v) }, { l: 'Del total', v: pc(e.v / D.embudo[0].v * 100) }] }));
    return barrasH(el, W, {
      rows: rows, dom: [0, 450000], ticks: [0, 100000, 200000, 300000, 400000], tickFmt: (t) => (t ? f0(t / 1000) + ' mil' : '0'), fmt: f0, rowH: 31, barH: 20, enfasis: true, mR: 90,
      aria: 'Embudo de datos', cols: ['Etapa', 'Registros'], colsNum: [1], filasTabla: () => D.embudo.map((e) => [e.n, f0(e.v)]),
    });
  };

  /* ---- validación con cifras del INEGI (tabla con estado) ---- */
  GRAF.validacion = function (el) {
    const marco = document.createElement('div'); marco.className = 'tabla-val-marco';
    const t = document.createElement('table'); t.className = 'tabla-val';
    const cab = t.createTHead().insertRow();
    ['Indicador', 'Proyecto', 'INEGI', 'Estado'].forEach((h, i) => { const c = document.createElement('th'); c.textContent = h; if (i === 1 || i === 2) c.className = 'n'; cab.appendChild(c); });
    const cu = t.createTBody();
    D.validacion.forEach((v) => {
      const r = cu.insertRow();
      [v.n, f1(v.p), f1(v.o)].forEach((s, i) => { const c = r.insertCell(); c.textContent = s; if (i > 0) c.className = 'n'; });
      const est = r.insertCell(); est.className = v.ok ? 'ok' : 'mal'; est.textContent = v.ok ? '✓' : '✗';
      const palabra = document.createElement('span'); palabra.className = 'est-txt'; palabra.textContent = v.ok ? ' Coincide' : ' No coincide'; est.appendChild(palabra);   // en pantallas angostas solo queda la marca
    });
    marco.appendChild(t); el.appendChild(marco);
    return () => ({ cols: ['Indicador', 'Proyecto', 'INEGI', 'Estado'], num: [1, 2], rows: D.validacion.map((v) => [v.n, f1(v.p), f1(v.o), v.ok ? 'Coincide' : 'No coincide']) });
  };

  /* ---- curva del ingreso por hora según la escolaridad (hombres y mujeres, escala logarítmica) ---- */
  GRAF.curva = function (el, W) {
    const datos = D.curva, H = clamp(Math.round(innerHeight * 0.42), 270, 460);
    const mL = 54, mR = 82, mT = 10, mB = 44, x0 = mL, x1 = W - mR, y0 = mT, y1 = H - mB;
    const sx = (a) => x0 + a / 21 * (x1 - x0), ly = Math.log;
    const sy = (v) => y1 - (ly(v) - ly(20)) / (ly(200) - ly(20)) * (y1 - y0);
    const svg = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': 'Mediana del ingreso por hora según años de escolaridad, hombres y mujeres' }, el);
    const g = sv('g', { class: 'eje' }, svg);
    [20, 30, 40, 60, 80, 120, 180].forEach((t) => { sv('line', { x1: x0, x2: x1, y1: sy(t), y2: sy(t), class: 'rej' }, g); tx(g, x0 - 8, sy(t), '$' + t, null, 'end'); });
    [0, 3, 6, 9, 12, 16, 18, 21].forEach((t) => tx(g, sx(t), y1 + 16, String(t), null, 'middle'));
    tx(g, (x0 + x1) / 2, H - 8, 'Años de escolaridad', 't-ref', 'middle');
    sv('line', { x1: x0, x2: x1, y1: y1, y2: y1, class: 'base' }, svg);
    if (W >= 620) [[6, 'primaria'], [9, 'secundaria'], [12, 'media sup.'], [16, 'licenciatura']].forEach((n) => tx(svg, sx(n[0]), y1 - 9, n[1], 't-ref', 'middle'));
    [['h', 'l-s1', 'm-s1', 'Hombres'], ['m', 'l-s2', 'm-s2', 'Mujeres']].forEach((s) => {
      const pts = datos.filter((d) => d[s[0]] != null);
      sv('path', { d: pts.map((d, i) => (i ? 'L' : 'M') + sx(d.a) + ',' + sy(d[s[0]])).join(' '), class: 'linea ' + s[1] }, svg);
      pts.forEach((d) => sv('circle', { cx: sx(d.a), cy: sy(d[s[0]]), r: 4, class: 'punto-m ' + s[2] }, svg));
      const u = pts[pts.length - 1];
      tx(svg, sx(u.a) + 9, sy(u[s[0]]), s[3], 't-dir', 'start');
    });
    const cruz = sv('line', { y1: y0, y2: y1, class: 'cruz', visibility: 'hidden' }, svg);
    const cap = sv('rect', { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: 'transparent', tabindex: 0, role: 'img', 'aria-label': 'Curva; use la tabla para leer los valores' }, svg);
    const mover = (ev) => {
      const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) * (W / r.width), a = clamp(Math.round((px - x0) / (x1 - x0) * 21), 0, 21);
      let d = datos.filter((q) => q.a === a)[0]; if (!d) return;
      cruz.setAttribute('x1', sx(a)); cruz.setAttribute('x2', sx(a)); cruz.setAttribute('visibility', 'visible');
      const f = [];
      if (d.h != null) f.push({ l: 'Hombres', v: pesos(d.h), k: 'var(--s1)' });
      if (d.m != null) f.push({ l: 'Mujeres', v: pesos(d.m), k: 'var(--s2)' });
      if (d.h != null && d.m != null) f.push({ l: 'Mujeres / hombres', v: num(d.m / d.h * 100, 0) + ' %' });
      llenarGlobo(a + ' años de escolaridad', f, 'Mediana por hora · n = ' + f0((d.nh || 0) + (d.nm || 0)));
      colocarGlobo(ev.clientX, ev.clientY);
    };
    cap.addEventListener('pointermove', mover);
    cap.addEventListener('pointerleave', () => { cruz.setAttribute('visibility', 'hidden'); ocultarGlobo(); });
    return () => ({ cols: ['Años de escolaridad', 'Hombres ($/hora)', 'Mujeres ($/hora)'], num: [1, 2], rows: datos.map((d) => [d.a, d.h != null ? pesos(d.h) : '', d.m != null ? pesos(d.m) : '']) });
  };

  /* ---- premio salarial por nivel (frente a primaria incompleta) ---- */
  GRAF.premio = function (el, W) {
    const clases = ['m-q1', 'm-q2', 'm-q3', 'm-q4'];
    const rows = D.premio.map((p, i) => ({ label: p.n, v: p.v, lo: p.lo, hi: p.hi, cls: clases[i], lab: true, txt: '+' + f0(p.v) + ' %',
      tip: [{ l: 'Premio', v: '+' + f1(p.v) + ' %' }, { l: 'IC 95 %', v: ic(p.lo, p.hi) + ' %' }, { l: 'Personas en la muestra', v: f0(p.N) }], nota: 'Frente a no terminar la primaria, con edad, sexo y entidad iguales' }));
    return barrasH(el, W, {
      rows: rows, dom: [0, 110], ticks: [0, 25, 50, 75, 100], tickFmt: (t) => '+' + t + ' %', fmt: (v) => '+' + f0(v) + ' %', rowH: 52, barH: 24, aria: 'Premio salarial por nivel de estudios', mR: 70,
      cols: ['Nivel de estudios', 'Premio', 'IC 95 %'], colsNum: [1, 2], filasTabla: () => D.premio.map((p) => [p.n, '+' + f1(p.v) + ' %', ic(p.lo, p.hi) + ' %']),
    });
  };

  /* ---- puntos con intervalo (escalera de controles y ranking de correlación) ---- */
  function puntosH(el, W, cfg) {
    const rows = cfg.rows, rowH = cfg.rowH, mT = cfg.derechaTit ? 20 : 4, mB = 28;
    let lw = 0; rows.forEach((r) => { lw = Math.max(lw, medir(r.label, 500, 13)); });
    const mL = Math.min(Math.ceil(lw) + 16, Math.max(110, W * 0.4)), mR = cfg.mR || 14, H = mT + rows.length * rowH + mB;
    const svg = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': cfg.aria }, el);
    const x0 = mL, x1 = W - mR - (cfg.derecha ? cfg.derecha : 0), d0 = cfg.dom[0], d1 = cfg.dom[1], sx = (v) => x0 + (v - d0) / (d1 - d0) * (x1 - x0);
    const g = sv('g', { class: 'eje' }, svg), alto = rows.length * rowH;
    (cfg.ticks || marcas(d0, d1, 5)).forEach((t) => { const x = sx(t); sv('line', { x1: x, x2: x, y1: mT, y2: mT + alto, class: 'rej' }, g); tx(g, x, H - 10, cfg.tickFmt ? cfg.tickFmt(t) : f0(t), null, 'middle'); });
    if (cfg.cero != null) sv('line', { x1: sx(cfg.cero), x2: sx(cfg.cero), y1: mT, y2: mT + alto, class: 'base' }, svg);
    if (cfg.derechaTit) tx(svg, W - 4, 8, cfg.derechaTit, 't-ref', 'end');
    rows.forEach((r, i) => {
      const yc = mT + i * rowH + rowH / 2, gr = sv('g', null, svg);
      if (r.sel) sv('rect', { x: 0, y: mT + i * rowH, width: W, height: rowH, class: 'fila-sel' }, gr);
      tx(gr, x0 - 10, yc, r.label, 't-cat' + (r.sel || r.key ? ' sel' : ''), 'end');
      sv('line', { x1: sx(r.lo), x2: sx(r.hi), y1: yc, y2: yc, class: 'ic ' + (r.gris ? 'ic-gris' : (r.lcls || 'l-s1')) }, gr);
      sv('circle', { cx: sx(r.v), cy: yc, r: cfg.radio || 5, class: 'punto-m ' + (r.gris ? 'm-gris' : (r.cls || 'm-s1')) }, gr);
      if (r.txt) tx(gr, sx(r.hi) + 8, yc, r.txt, 't-val', 'start');
      if (r.der) tx(gr, W - 4, yc, r.der, 't-ref', 'end');
      const hit = sv('rect', { x: 0, y: mT + i * rowH, width: W, height: rowH, class: 'fila-hit', tabindex: 0, role: 'img', 'aria-label': r.label + ': ' + cfg.fmt(r.v) }, gr);
      conGlobo(hit, () => ({ t: r.label, f: r.tip, n: r.nota }));
      if (cfg.alClic) hit.addEventListener('click', () => cfg.alClic(r));
    });
    return () => ({ cols: cfg.cols, num: cfg.colsNum, rows: cfg.filasTabla() });
  }

  /* ---- escalera de controles de la brecha por hora ---- */
  GRAF.escalera = function (el, W) {
    const rows = D.escalera.map((e) => {
      const g6 = e.id === 'G6';
      return { label: e.n, v: e.v, lo: e.lo, hi: e.hi, key: e.id === 'G1', gris: g6, txt: ['G0', 'G1', 'G5', 'G6'].indexOf(e.id) >= 0 ? pc(e.v) : null,
        tip: [{ l: 'Brecha por hora', v: pc(e.v) }, { l: 'IC 95 %', v: ic(e.lo, e.hi) + ' %' }, { l: 'R² del modelo', v: f2(e.r2) }],
        nota: g6 ? 'No se interpreta: el ingreso por hora ya divide entre horas (sesgo de división)' : e.id === 'G1' ? 'A igual escolaridad: la métrica del protocolo' : 'Cada fila agrega controles a la anterior' };
    });
    return puntosH(el, W, {
      rows: rows, rowH: clamp(Math.round(innerHeight * 0.052), 32, 46), dom: [0, 20], ticks: [0, 5, 10, 15, 20], tickFmt: (t) => t + ' %', cero: 0, mR: 60, radio: 6, fmt: pc,
      aria: 'Brecha por hora al agregar controles', cols: ['Modelo (controles acumulados)', 'Brecha por hora', 'IC 95 %', 'R²'], colsNum: [1, 2, 3],
      filasTabla: () => D.escalera.map((e) => [e.id + ' ' + e.n, pc(e.v), ic(e.lo, e.hi) + ' %', f2(e.r2)]),
    });
  };

  /* ---- brecha por nivel de estudios: dos paneles (por hora y por mes) con intervalo ---- */
  GRAF.brechaNivel = function (el, W) {
    const filas = D.brecha_nivel, rowH = 40, barH = 22, mT = 22, mB = 28, mL = Math.min(Math.ceil(Math.max.apply(null, filas.map((r) => medir(r.n, 500, 13)))) + 16, W * 0.3);
    const gap = 26, ancho = (W - mL - gap - 10) / 2, H = mT + filas.length * rowH + mB;
    const svg = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': 'Brecha por hora y por mes según el nivel de estudios' }, el);
    const paneles = [{ k: 'h', tit: 'Por hora', dom: [0, 17], ticks: [0, 5, 10, 15], ox: mL }, { k: 'm', tit: 'Por mes', dom: [0, 52], ticks: [0, 10, 20, 30, 40, 50], ox: mL + ancho + gap }];
    filas.forEach((r, i) => tx(svg, mL - 10, mT + i * rowH + rowH / 2, r.n, 't-cat' + (r.n === 'Total' ? ' sel' : ''), 'end'));
    paneles.forEach((p) => {
      const sx = (v) => p.ox + v / p.dom[1] * ancho, g = sv('g', { class: 'eje' }, svg);
      tx(svg, p.ox, 6, p.tit + ' (% menos que los hombres)', 't-ref', 'start');
      p.ticks.forEach((t) => { sv('line', { x1: sx(t), x2: sx(t), y1: mT, y2: mT + filas.length * rowH, class: 'rej' }, g); tx(g, sx(t), H - 10, t + ' %', null, 'middle'); });
      sv('line', { x1: sx(0), x2: sx(0), y1: mT, y2: mT + filas.length * rowH, class: 'base' }, svg);
      filas.forEach((r, i) => {
        const yc = mT + i * rowH + rowH / 2, d = r[p.k], gr = sv('g', null, svg);
        sv('path', { d: barraRedonda(sx(0), yc - barH / 2, sx(d[0]) - sx(0), barH, 4), class: 'm-s1' }, gr);
        sv('line', { x1: sx(d[1]), x2: sx(d[2]), y1: yc, y2: yc, class: 'ic ic-gris' }, gr);
        sv('line', { x1: sx(d[1]), x2: sx(d[1]), y1: yc - 5, y2: yc + 5, class: 'ic ic-gris' }, gr);
        sv('line', { x1: sx(d[2]), x2: sx(d[2]), y1: yc - 5, y2: yc + 5, class: 'ic ic-gris' }, gr);
        tx(gr, sx(d[2]) + 7, yc, f1(d[0]), 't-val', 'start');
        const hit = sv('rect', { x: p.ox - 4, y: mT + i * rowH, width: ancho + 8, height: rowH, class: 'fila-hit', tabindex: 0, role: 'img', 'aria-label': r.n + ', ' + p.tit + ': ' + pc(d[0]) }, gr);
        conGlobo(hit, () => ({ t: r.n, f: [{ l: 'Por hora', v: pc(r.h[0]) }, { l: 'Por mes', v: pc(r.m[0]) }, { l: 'Menos horas pagadas', v: pc(r.t[0]) }, { l: 'Hombres / mujeres ($/hora)', v: pesos(r.ih) + ' / ' + pesos(r.im) }], n: 'IC 95 % por hora: ' + ic(r.h[1], r.h[2]) + ' %' }));
      });
    });
    return () => ({ cols: ['Nivel', 'Por hora', 'IC 95 % (hora)', 'Por mes', 'IC 95 % (mes)', 'Mujeres trabajan menos horas'], num: [1, 2, 3, 4, 5],
      rows: filas.map((r) => [r.n, pc(r.h[0]), ic(r.h[1], r.h[2]) + ' %', pc(r.m[0]), ic(r.m[1], r.m[2]) + ' %', pc(r.t[0])]) });
  };

  /* ---- brecha por percentil del ingreso (línea con banda de intervalo) ---- */
  GRAF.cuantiles = function (el, W) {
    const d = D.cuantiles, H = clamp(Math.round(innerHeight * 0.4), 260, 430), mL = 54, mR = 24, mT = 14, mB = 44, x0 = mL, x1 = W - mR, y0 = mT, y1 = H - mB;
    const sx = (i) => x0 + 40 + i / (d.length - 1) * (x1 - x0 - 80), sy = (v) => y1 - (v + 6) / 18 * (y1 - y0);
    const svg = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': 'Brecha por hora en distintos percentiles del ingreso' }, el);
    const g = sv('g', { class: 'eje' }, svg);
    [-5, 0, 5, 10].forEach((t) => { sv('line', { x1: x0, x2: x1, y1: sy(t), y2: sy(t), class: t === 0 ? 'base' : 'rej' }, g); tx(g, x0 - 8, sy(t), t + ' %', null, 'end'); });
    d.forEach((q, i) => tx(g, sx(i), y1 + 18, 'P' + q.p, null, 'middle'));
    tx(g, (x0 + x1) / 2, H - 6, 'Posición en la distribución del ingreso por hora (P10 = quien menos gana)', 't-ref', 'middle');
    const arriba = d.map((q, i) => sx(i) + ',' + sy(q.hi)), abajo = d.map((q, i) => sx(i) + ',' + sy(q.lo)).reverse();
    sv('polygon', { points: arriba.concat(abajo).join(' '), class: 'banda' }, svg);
    sv('path', { d: d.map((q, i) => (i ? 'L' : 'M') + sx(i) + ',' + sy(q.v)).join(' '), class: 'linea l-s1' }, svg);
    d.forEach((q, i) => {
      sv('circle', { cx: sx(i), cy: sy(q.v), r: 5, class: 'punto-m m-s1' }, svg);
      tx(svg, sx(i), sy(q.hi) - 12, pc(q.v), 't-val', 'middle');
      const hit = sv('circle', { cx: sx(i), cy: sy(q.v), r: 22, class: 'fila-hit', tabindex: 0, role: 'img', 'aria-label': 'P' + q.p + ': ' + pc(q.v) }, svg);
      conGlobo(hit, () => ({ t: 'Percentil ' + q.p, f: [{ l: 'Brecha por hora', v: pc(q.v) }, { l: 'IC 95 %', v: ic(q.lo, q.hi) + ' %' }, { l: 'Hombres', v: pesos(q.h) + '/h' }, { l: 'Mujeres', v: pesos(q.m) + '/h' }], n: q.pv < 0.05 ? 'Significativa (p ' + (q.pv < 0.001 ? '< 0.001' : '= ' + f2(q.pv)) + ')' : 'No significativa (p = ' + f2(q.pv) + ')' }));
    });
    return () => ({ cols: ['Percentil', 'Hombres ($/h)', 'Mujeres ($/h)', 'Brecha', 'IC 95 %', 'Valor p'], num: [1, 2, 3, 4, 5],
      rows: d.map((q) => ['P' + q.p, pesos(q.h), pesos(q.m), pc(q.v), ic(q.lo, q.hi) + ' %', q.pv < 0.001 ? '< 0.001' : f2(q.pv)]) });
  };

  /* ---- descomposición de Oaxaca-Blinder ---- */
  GRAF.oaxaca = function (el, W) {
    const rows = D.oaxaca.map((o, i) => ({ label: o.n, v: o.v, lo: o.lo, hi: o.hi, cls: o.v < 0 ? 'm-s1' : 'm-rojo', lab: true, txt: signo(o.v, 1),
      tip: [{ l: 'Puntos logarítmicos', v: signo(o.v, 2) }, { l: 'IC 95 %', v: ic(o.lo, o.hi, 2) }], nota: i === 1 ? 'Las mujeres tienen mejores características medidas (sobre todo escolaridad)' : i === 2 ? 'A iguales características, se les paga menos; no prueba discriminación' : 'Brecha por hora entre hombres y mujeres' }));
    return barrasH(el, W, {
      rows: rows, dom: [-5.5, 9.5], ticks: [-4, -2, 0, 2, 4, 6, 8], tickFmt: (t) => (t > 0 ? '+' : '') + String(t).replace('-', MENOS), fmt: (v) => signo(v, 1), rowH: 56, barH: 24, mR: 56,
      aria: 'Descomposición de Oaxaca-Blinder', cols: ['Componente', 'Puntos logarítmicos', 'IC 95 %'], colsNum: [1, 2], filasTabla: () => D.oaxaca.map((o) => [o.n, signo(o.v, 2), ic(o.lo, o.hi, 2)]),
    });
  };

  /* ---- dispersión por entidad con intervalo vertical ---- */
  function dispersion(el, W, cfg) {
    const H = cfg.H || clamp(Math.round(innerHeight * 0.44), 280, 480), mL = 58, mR = 18, mT = 12, mB = 50, x0 = mL, x1 = W - mR, y0 = mT, y1 = H - mB;
    const sx = (v) => x0 + (v - cfg.xd[0]) / (cfg.xd[1] - cfg.xd[0]) * (x1 - x0), sy = (v) => y1 - (v - cfg.yd[0]) / (cfg.yd[1] - cfg.yd[0]) * (y1 - y0);
    const svg = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'group', 'aria-label': cfg.aria }, el);
    const g = sv('g', { class: 'eje' }, svg);
    marcas(cfg.yd[0], cfg.yd[1], 5).forEach((t) => { sv('line', { x1: x0, x2: x1, y1: sy(t), y2: sy(t), class: 'rej' }, g); tx(g, x0 - 8, sy(t), cfg.yFmt(t), null, 'end'); });
    marcas(cfg.xd[0], cfg.xd[1], 6).forEach((t) => tx(g, sx(t), y1 + 17, cfg.xFmt(t), null, 'middle'));
    tx(g, (x0 + x1) / 2, H - 9, cfg.xTit, 't-ref', 'middle');
    const yt = tx(g, 12, (y0 + y1) / 2, cfg.yTit, 't-ref', 'middle'); yt.setAttribute('transform', 'rotate(-90 12 ' + (y0 + y1) / 2 + ')');
    sv('line', { x1: x0, x2: x1, y1: y1, y2: y1, class: 'base' }, svg);
    if (cfg.ref) { sv('line', { x1: x0, x2: x1, y1: sy(cfg.ref.v), y2: sy(cfg.ref.v), class: 'ref' }, svg); tx(svg, x1, sy(cfg.ref.v) - 9, cfg.ref.label, 't-ref', 'end'); }
    if (cfg.tendencia) {
      const n = cfg.pts.length, mx = cfg.pts.reduce((a, p) => a + p.x, 0) / n, my = cfg.pts.reduce((a, p) => a + p.y, 0) / n;
      const b = cfg.pts.reduce((a, p) => a + (p.x - mx) * (p.y - my), 0) / cfg.pts.reduce((a, p) => a + (p.x - mx) * (p.x - mx), 0), a0 = my - b * mx;
      sv('line', { x1: sx(cfg.xd[0] + 0.15), y1: sy(a0 + b * (cfg.xd[0] + 0.15)), x2: sx(cfg.xd[1] - 0.15), y2: sy(a0 + b * (cfg.xd[1] - 0.15)), class: 'ref' }, svg);
    }
    const marcasPts = cfg.pts.map((p) => {
      const gr = sv('g', null, svg);
      sv('line', { x1: sx(p.x), x2: sx(p.x), y1: sy(p.lo), y2: sy(p.hi), class: 'ic ic-gris', opacity: '.4' }, gr);
      const c = sv('circle', { cx: sx(p.x), cy: sy(p.y), r: 6, class: 'punto-m ' + (p.cls || 'm-s1') + (S.estado != null && S.estado !== p.id ? ' atenuado' : '') }, gr);
      return { p: p, c: c, gr: gr };
    });
    if (S.estado != null) {
      const m = marcasPts.filter((q) => q.p.id === S.estado)[0];
      if (m) { m.c.setAttribute('r', 9); m.c.setAttribute('class', 'punto-m ' + (m.p.cls || 'm-s1') + ' destaca'); svg.appendChild(m.gr); }
    }
    Array.from(new Set((cfg.etiquetas || []).concat(S.estado != null ? [S.estado] : []))).forEach((id) => {
      const q = marcasPts.filter((m) => m.p.id === id)[0]; if (!q) return;
      const der = sx(q.p.x) > x1 - 90;
      tx(svg, sx(q.p.x) + (der ? -11 : 11), sy(q.p.y) - 11, porId[id].n, 't-val t-halo', der ? 'end' : 'start');
    });
    const cap = sv('rect', { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: 'transparent', style: 'cursor:pointer' }, svg);
    let cerca = null;
    const buscar = (ev) => {
      const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) * (W / r.width), py = (ev.clientY - r.top) * (W / r.width);
      let mejor = null, dmin = 1e9;
      cfg.pts.forEach((p) => { const d = Math.hypot(sx(p.x) - px, sy(p.y) - py); if (d < dmin) { dmin = d; mejor = p; } });
      return dmin < 42 ? mejor : null;
    };
    cap.addEventListener('pointermove', (ev) => {
      const p = buscar(ev);
      if (cerca) cerca.c.classList.remove('m-hover');
      cerca = p ? marcasPts.filter((m) => m.p.id === p.id)[0] : null;
      if (cerca) { cerca.c.classList.add('m-hover'); const d = cfg.tip(p); llenarGlobo(porId[p.id].n, d.f, d.n); colocarGlobo(ev.clientX, ev.clientY); } else ocultarGlobo();
    });
    cap.addEventListener('pointerleave', () => { if (cerca) cerca.c.classList.remove('m-hover'); ocultarGlobo(); });
    cap.addEventListener('click', (ev) => { const p = buscar(ev); if (p) setEstado(p.id); });
    return () => ({ cols: cfg.cols, num: cfg.colsNum, rows: cfg.filasTabla() });
  }

  const nombreCuartil = { 1: 'Q1 · ingreso más bajo', 2: 'Q2', 3: 'Q3', 4: 'Q4 · ingreso más alto' };
  GRAF.dispEstados = function (el, W) {
    const pts = D.estados.map((e) => ({ id: e.id, x: e.mln[0], y: e.ret[0], lo: e.ret[1], hi: e.ret[2], cls: 'm-q' + e.q, q: e.q, e: e }));
    const maxE = pts.reduce((a, p) => (p.y > a.y ? p : a)), minE = pts.reduce((a, p) => (p.y < a.y ? p : a));
    return dispersion(el, W, {
      pts: pts, xd: [34, 74], yd: [2, 11], xFmt: (v) => '$' + v, yFmt: (v) => v + ' %', xTit: 'Ingreso mediano por hora del estado', yTit: 'Aumento del ingreso por año de estudio',
      ref: { v: D.k.ret[0], label: 'Nacional ' + pc(D.k.ret[0]) }, etiquetas: [maxE.id, minE.id], aria: 'Rendimiento de estudiar frente al ingreso mediano de cada estado',
      tip: (p) => ({ f: [{ l: 'Aumento por año de estudio', v: pc(p.e.ret[0], 2) }, { l: 'IC 95 %', v: ic(p.e.ret[1], p.e.ret[2]) + ' %' }, { l: 'Ingreso mediano por hora', v: pesos(p.e.mln[0]) }, { l: 'Cuartil de ingreso', v: nombreCuartil[p.q] }] }),
      cols: ['Entidad', 'Ingreso mediano ($/h)', 'Cuartil', 'Aumento por año', 'IC 95 %'], colsNum: [1, 3, 4],
      filasTabla: () => D.estados.slice().sort((a, b) => b.ret[0] - a.ret[0]).map((e) => [e.n, pesos(e.mln[0]), 'Q' + e.q, pc(e.ret[0], 2), ic(e.ret[1], e.ret[2]) + ' %']),
    });
  };

  GRAF.rankRho = function (el, W) {
    const orden = D.estados.slice().sort((a, b) => b.rho[0] - a.rho[0]);
    const extremos = [orden[0].id, orden[orden.length - 1].id];
    const rows = orden.map((e) => ({ label: e.n, v: e.rho[0], lo: e.rho[1], hi: e.rho[2], sel: S.estado === e.id, id: e.id, txt: extremos.indexOf(e.id) >= 0 ? f2(e.rho[0]) : null,
      der: e.rho[3] + ' (' + e.rho[4] + '–' + e.rho[5] + ')', tip: [{ l: 'Correlación ρ', v: f2(e.rho[0]) }, { l: 'IC 95 %', v: ic(e.rho[1], e.rho[2], 2) }, { l: 'Lugar (intervalo)', v: e.rho[3] + ' (' + e.rho[4] + ' a ' + e.rho[5] + ')' }],
      nota: e.rho[5] - e.rho[4] > 14 ? 'Su lugar no se distingue del de varios estados vecinos en el ranking' : 'Lugar bien definido' }));
    const out = puntosH(el, W, {
      rows: rows, rowH: clamp(Math.floor(innerHeight * 0.46 / 32), 12, 18), dom: [0.1, 0.6], ticks: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6], tickFmt: f1, fmt: f2, derecha: 78, derechaTit: 'Lugar (intervalo)', mR: 6, radio: 4.6,
      aria: 'Correlación entre escolaridad e ingreso por hora en cada estado, con intervalo y lugar',
      alClic: (r) => setEstado(r.id), cols: ['Lugar', 'Entidad', 'ρ', 'IC 95 %', 'Intervalo del lugar'], colsNum: [0, 2],
      filasTabla: () => orden.map((e) => [e.rho[3], e.n, f2(e.rho[0]), ic(e.rho[1], e.rho[2], 2), e.rho[4] + ' a ' + e.rho[5]]),
    });
    return out;
  };

  /* ---- informalidad por nivel y región (barras) ---- */
  GRAF.tilNivel = function (el, W) {
    const clases = ['m-q1', 'm-q2', 'm-q3', 'm-q4'];
    const rows = D.til_nivel.map((n, i) => ({ label: n.n, v: n.v, lo: n.lo, hi: n.hi, cls: clases[i], lab: true, txt: f0(n.v) + ' %', tip: [{ l: 'Informalidad (TIL1)', v: pc(n.v) }, { l: 'IC 95 %', v: ic(n.lo, n.hi) + ' %' }] }));
    return barrasH(el, W, { rows: rows, dom: [0, 100], ticks: [0, 50, 100], tickFmt: (t) => t + ' %', fmt: (v) => f0(v) + ' %', rowH: 40, barH: 22, mR: 52, medida: 'Informalidad', aria: 'Informalidad por nivel de estudios',
      cols: ['Nivel de estudios', 'Informalidad', 'IC 95 %'], colsNum: [1, 2], filasTabla: () => D.til_nivel.map((n) => [n.n, pc(n.v), ic(n.lo, n.hi) + ' %']) });
  };

  GRAF.dispTil = function (el, W) {
    const pts = D.estados.map((e) => ({ id: e.id, x: e.esc[0], y: e.til[0], lo: e.til[1], hi: e.til[2], e: e }));
    const alto = pts.reduce((a, p) => (p.y > a.y ? p : a)), bajo = pts.reduce((a, p) => (p.y < a.y ? p : a)), masEscolar = pts.reduce((a, p) => (p.x > a.x ? p : a));
    return dispersion(el, W, {
      pts: pts, xd: [8.5, 13], yd: [25, 85], xFmt: (v) => String(v), yFmt: (v) => v + ' %', xTit: 'Años de escolaridad promedio de los ocupados del estado', yTit: 'Informalidad laboral (TIL1)', tendencia: true,
      etiquetas: [alto.id, bajo.id, masEscolar.id], aria: 'Informalidad frente a la escolaridad promedio de cada estado',
      tip: (p) => ({ f: [{ l: 'Informalidad', v: pc(p.e.til[0]) }, { l: 'IC 95 %', v: ic(p.e.til[1], p.e.til[2]) + ' %' }, { l: 'Escolaridad promedio', v: f1(p.e.esc[0]) + ' años' }], n: 'Lugar ' + p.e.til[3] + ' de 32 en informalidad' }),
      cols: ['Entidad', 'Escolaridad promedio (años)', 'Informalidad', 'IC 95 %'], colsNum: [1, 2], filasTabla: () => D.estados.slice().sort((a, b) => b.til[0] - a.til[0]).map((e) => [e.n, f1(e.esc[0]), pc(e.til[0]), ic(e.til[1], e.til[2]) + ' %']),
    });
  };

  /* ---- mosaico de estados (cartograma: cada estado ocupa el mismo área) ---- */
  const METRICAS = {
    til: { nombre: 'Informalidad laboral (TIL1)', get: (e) => e.til[0], ic: (e) => [e.til[1], e.til[2]], fmt: (v) => f1(v) + ' %', corto: (v) => String(Math.round(v)), rango: (e) => 'lugar ' + e.til[3] + ' de 32 (1 = más informal)' },
    esc: { nombre: 'Años de escolaridad promedio de los ocupados', get: (e) => e.esc[0], ic: (e) => [e.esc[1], e.esc[2]], fmt: (v) => f1(v) + ' años', corto: (v) => v.toFixed(1) },
    ret: { nombre: 'Aumento del ingreso por año de estudio', get: (e) => e.ret[0], ic: (e) => [e.ret[1], e.ret[2]], fmt: (v) => f1(v) + ' %', corto: (v) => v.toFixed(1) },
    mln: { nombre: 'Ingreso mediano por hora', get: (e) => e.mln[0], ic: (e) => [e.mln[1], e.mln[2]], fmt: (v) => pesos(v), corto: (v) => String(Math.round(v)), rango: (e) => 'lugar ' + e.mln[3] + ' de 32 (1 = menor ingreso)' },
    bh: { nombre: 'Brecha por hora (mujeres frente a hombres)', get: (e) => e.bh[0], ic: (e) => [e.bh[1], e.bh[2]], fmt: (v) => f1(v) + ' %', corto: (v) => v.toFixed(0), rango: (e) => (e.bh[1] <= 0 ? 'no significativa (el intervalo incluye 0)' : 'significativa') },
  };
  function mosaico(el, cfg) {
    const m = METRICAS[cfg.metrica()], vs = D.estados.map((e) => m.get(e)), vmin = Math.min.apply(null, vs), vmax = Math.max.apply(null, vs);
    const marco = document.createElement('div'); marco.className = 'mosaico-marco';
    const mosa = document.createElement('div'); mosa.className = 'mosaico'; mosa.setAttribute('role', 'group'); mosa.setAttribute('aria-label', m.nombre + ' por entidad federativa, un mosaico por estado');
    const info = document.createElement('p'); info.className = 'mosaico-info'; info.setAttribute('aria-live', 'polite');
    const porDefecto = cfg.textoInicial || 'Pasa el cursor o toca un mosaico.';
    const decir = (e) => {
      info.textContent = '';
      const b = document.createElement('b'); b.textContent = e.n + ': '; info.appendChild(b);
      const i = m.ic(e);
      info.appendChild(document.createTextNode(m.fmt(m.get(e)) + (i ? ' (IC 95 %: ' + f1(i[0]) + ' a ' + f1(i[1]) + ')' : '') + (m.rango ? ' · ' + m.rango(e) : '')));
    };
    D.estados.forEach((e) => {
      const v = m.get(e), t = vmax === vmin ? 0 : (v - vmin) / (vmax - vmin);
      const b = document.createElement('button'); b.type = 'button'; b.className = 'tile' + (t > 0.55 ? ' alto' : '') + (S.estado === e.id ? ' sel' : '');
      b.style.gridColumn = String(e.col + 1); b.style.gridRow = String(e.fila + 1); b.style.setProperty('--t', t.toFixed(3));
      b.setAttribute('aria-label', e.n + ': ' + m.fmt(v));
      const a = document.createElement('span'); a.textContent = e.a; const s = document.createElement('small'); s.textContent = m.corto(v);
      b.appendChild(a); b.appendChild(s);
      conGlobo(b, () => { const ii = m.ic(e); return { t: e.n, f: [{ l: m.nombre, v: m.fmt(v) }].concat(ii ? [{ l: 'IC 95 %', v: f1(ii[0]) + ' a ' + f1(ii[1]) }] : []), n: m.rango ? m.rango(e) : null }; });
      b.addEventListener('pointerenter', () => decir(e));
      b.addEventListener('focus', () => decir(e));
      b.addEventListener('click', () => { setEstado(e.id); });
      mosa.appendChild(b);
    });
    const esc = document.createElement('div'); esc.className = 'escala';
    const l1 = document.createElement('span'); l1.textContent = m.fmt(vmin); const barra = document.createElement('i'); const l2 = document.createElement('span'); l2.textContent = m.fmt(vmax);
    esc.appendChild(l1); esc.appendChild(barra); esc.appendChild(l2);
    marco.appendChild(mosa); marco.appendChild(esc); marco.appendChild(info);
    if (S.estado != null) decir(porId[S.estado]); else info.textContent = porDefecto;
    el.appendChild(marco);
    return () => ({ cols: ['Entidad', 'Informalidad (%)', 'Años de escolaridad', 'Aumento por año de estudio (%)', 'Ingreso mediano ($/h)', 'Brecha por hora (%)'], num: [1, 2, 3, 4, 5],
      rows: D.estados.slice().sort((a, b) => a.n.localeCompare(b.n, 'es')).map((e) => [e.n, f1(e.til[0]), f1(e.esc[0]), f1(e.ret[0]), pesos(e.mln[0]), f1(e.bh[0])]) });
  }
  GRAF.mosaicoPortada = (el) => mosaico(el, { metrica: () => 'til', textoInicial: 'Pasa el cursor o toca un mosaico para ver el dato del estado.' });
  GRAF.mosaicoQ3 = (el) => mosaico(el, { metrica: () => ($('#sel-metrica') || { value: 'til' }).value, textoInicial: 'Elige un indicador y toca un estado.' });

  /* ---- gráficas pequeñas de la lámina de respuestas ---- */
  function miniBarras(el, W, filas, maximo) {
    const h = 12, gap = 8, mL = Math.min(86, W * 0.4), H = filas.length * (h + gap) - gap, svg = sv('svg', { viewBox: '0 0 ' + W + ' ' + H, 'aria-hidden': 'true' }, el);
    filas.forEach((f, i) => {
      const y = i * (h + gap);
      tx(svg, mL - 8, y + h / 2, f.t, 't-mini', 'end');
      sv('path', { d: barraRedonda(mL, y, f.v / maximo * (W - mL - 34), h, 3), class: f.cls }, svg);
      tx(svg, mL + f.v / maximo * (W - mL - 34) + 6, y + h / 2, f.txt, 't-mini t-mini--v', 'start');
    });
  }
  const NIVELES_CORTOS = ['Primaria inc.', 'Primaria', 'Secundaria', 'Media sup. o más'], Q = ['m-q1', 'm-q2', 'm-q3', 'm-q4'];
  GRAF.miniPremio = (el, W) => miniBarras(el, W, D.premio.map((p, i) => ({ t: ['Primaria', 'Secundaria', 'Media sup.', 'Licenciatura'][i], v: p.v, cls: Q[i], txt: '+' + f0(p.v) + ' %' })), 100);
  GRAF.miniTil = (el, W) => miniBarras(el, W, D.til_nivel.map((p, i) => ({ t: NIVELES_CORTOS[i], v: p.v, cls: Q[i], txt: f0(p.v) + ' %' })), 100);
  GRAF.miniEscalera = (el, W) => miniBarras(el, W, [{ t: 'Por hora', v: D.k.g1[0], cls: 'm-s1', txt: f1(D.k.g1[0]) + ' %' }, { t: 'Por mes', v: D.k.bm[0], cls: 'm-s1', txt: f1(D.k.bm[0]) + ' %' }], 30);

  /* ======================================================================================================================================
     Lámina de ingeniería: la misma pregunta en SQL y en MongoDB
     ====================================================================================================================================== */
  function lineas(destino, lins) {
    destino.textContent = '';
    lins.forEach((ln, i) => {
      if (i) destino.appendChild(document.createTextNode('\n'));
      ln.forEach((t) => {
        if (typeof t === 'string') destino.appendChild(document.createTextNode(t));
        else { const s = document.createElement('span'); s.className = t[1]; s.textContent = t[0]; destino.appendChild(s); }
      });
    });
  }
  function pintarFicha() {
    const caja = $('#ficha-mongo');
    if (!caja) return;
    const id = S.estado == null ? 20 : S.estado, e = porId[id], d = D.mongo[String(id)];
    const K = (t) => [t, 'k'], T = (t) => [JSON.stringify(t), 's'], N = (t) => [JSON.stringify(t), 'n'];
    lineas($('#ficha-sql'), [[K('SELECT'), ' entidad, ROUND(til1_pct, 2) AS til1_pct'], [K('FROM'), ' v_til_entidad'], [K('WHERE'), ' cve_ent = ', N(id), ';']]);
    const r = $('#ficha-res'); r.textContent = ''; const b = document.createElement('b'); b.textContent = e.n; r.appendChild(b); r.appendChild(document.createTextNode('  ·  til1_pct = ' + f2(d.informalidad.til1_pct)));
    lineas(caja, [
      [K('db.entidades.findOne'), '({ cve_ent: ', N(id), ' })'], ['{'],
      ['  entidad: ', T(d.entidad), ', region: ', T(d.region), ','],
      ['  informalidad: { til1_pct: ', N(d.informalidad.til1_pct), ', ic95: ', [JSON.stringify(d.informalidad.ic95), 'n'], ', lugar: ', N(d.informalidad.lugar), ' },'],
      ['  rendimiento_escolaridad: { pct_por_anio: ', N(d.rendimiento_escolaridad.pct_por_anio), ' },'],
      ['  brecha_genero: { hora_pct: ', N(d.brecha_genero.hora_pct), ', mensual_pct: ', N(d.brecha_genero.mensual_pct), ' }'], ['}'],
    ]);
  }

  /* ======================================================================================================================================
     Ruta KDD y arquitectura
     ====================================================================================================================================== */
  const FASES = [
    { n: 'Selección', sem: 'Sem. 1', sub: 'Fuente y validación', num: f0(D.n.registros), nl: 'registros reales de la ENOE 2025-T4 (INEGI)', chips: ['7 de 7 cifras oficiales reproducidas', 'Huella SHA-256 de cada archivo', 'Diccionario de datos'], ir: 'e-datos' },
    { n: 'Preprocesamiento', sem: 'Sem. 4', sub: 'Limpieza documentada', num: D.n.pruebas_datos + ' de ' + D.n.pruebas_datos, nl: 'pruebas automáticas de calidad cumplidas', chips: ['99 años y 0 horas pasan a faltante', 'Atípicos P0.5 a P99.5 por entidad', '«Ingreso 0» separado en 4 grupos'], ir: 'e-limpieza' },
    { n: 'Transformación', sem: 'Sem. 4 · 6', sub: 'Variables y base de datos', num: String(D.n.variables_derivadas), nl: 'variables derivadas, en una base SQLite en estrella', chips: ['ln(ingreso por hora)', 'Imputación por rango (sensibilidad)', 'MongoDB para servir cada entidad'], ir: 'e-ingenieria' },
    { n: 'Minería y análisis', sem: 'Sem. 2 · 3 · 5', sub: 'Estadística y gráficas', num: f0(D.k.B), nl: 'réplicas Rao-Wu: errores que respetan el diseño de la encuesta', chips: ['Spearman y Mincer', 'Brecha con Holm y d de Cohen', 'Oaxaca-Blinder'], ir: 'e-q1' },
    { n: 'Interpretación', sem: 'Sem. 5', sub: 'Comunicar y recomendar', num: '3 de 3', nl: 'preguntas contestadas y métricas de éxito cumplidas', chips: ['Asociaciones, no causalidad', 'Un solo trimestre', 'Informe visual y presentación'], ir: 'e-respuestas' },
  ];
  const NODOS = [
    { t: 'Microdatos INEGI', s: 'CSV · SDEMT y COE2T', d: '419,038 y 344,166 filas; huella SHA-256 al leer cada archivo.' },
    { t: 'Pipeline ETL', s: 'Python · reproducible', d: 'Extrae, limpia, transforma y valida en unos 10 segundos; idempotente y con una sola semilla.' },
    { t: 'SQLite', s: 'esquema en estrella', d: f0(D.n.filas_fact) + ' filas × ' + D.n.cols_fact + ' columnas, 10 dimensiones, llaves y restricciones. Sirve para analizar: JOIN y agregaciones ponderadas.' },
    { t: 'MongoDB', s: 'un documento por entidad', d: '32 documentos con indicadores e intervalos anidados: una lectura por clave, sin JOIN, para servir la ficha de cada estado.' },
    { t: 'Tablero y página', s: 'HTML interactivo', d: 'Leen los documentos de las entidades: mapa, ranking y fichas.' },
  ];
  function vincularKdd() {
    const botones = $$('.fase'), det = $('#fase-detalle');
    if (!botones.length || !det) return;
    const mostrar = (i) => {
      botones.forEach((b, j) => b.setAttribute('aria-pressed', i === j ? 'true' : 'false'));
      const f = FASES[i];
      det.textContent = '';
      const num = document.createElement('div'); num.className = 'num'; num.textContent = f.num; const sm = document.createElement('small'); sm.textContent = f.nl; num.appendChild(sm);
      const ul = document.createElement('ul'); ul.className = 'chips'; f.chips.forEach((c) => { const li = document.createElement('li'); li.className = 'chip'; li.textContent = c; ul.appendChild(li); });
      const a = document.createElement('a'); a.className = 'btn'; a.href = '#' + f.ir; a.textContent = 'Ver la evidencia ▸';
      a.addEventListener('click', (ev) => { ev.preventDefault(); irA(f.ir); });
      det.appendChild(num); det.appendChild(ul); det.appendChild(a);
    };
    botones.forEach((b, i) => b.addEventListener('click', () => mostrar(i)));
    mostrar(0);
  }
  function vincularArquitectura() {
    const nodos = $$('.nodo'), det = $('#nodo-detalle');
    if (!nodos.length || !det) return;
    const mostrar = (i) => { nodos.forEach((n, j) => n.setAttribute('aria-pressed', i === j ? 'true' : 'false')); det.textContent = NODOS[i].d; };
    nodos.forEach((n, i) => n.addEventListener('click', () => mostrar(i)));
    mostrar(2);
  }

  /* ======================================================================================================================================
     Calculadora, tarjetas (vistas y tabla), navegación y notas
     ====================================================================================================================================== */
  function vincularCalculadora() {
    const rg = $('#calc-rango'), sal = $('#calc-res'), nota = $('#calc-ic');
    if (!rg) return;
    const calc = () => {
      const n = +rg.value, r = D.k.ret;
      const efecto = (p) => (Math.pow(1 + p / 100, n) - 1) * 100;
      sal.textContent = '+' + f0(efecto(r[0])) + ' %';
      nota.textContent = n + (n === 1 ? ' año más de estudio' : ' años más de estudio') + ' · IC 95 %: +' + f0(efecto(r[1])) + ' a +' + f0(efecto(r[2])) + ' %. Es una asociación, no un efecto causal.';
    };
    rg.addEventListener('input', calc);
    calc();
  }
  function vincularTarjetas() {
    $$('.tarjeta').forEach((card) => {
      const seg = $('.seg', card), vistas = $$('.vista', card), btnTabla = $('.ver-tabla', card), tab = $('.tabla-vista', card);
      const instVisible = () => { const v = vistas.filter((x) => !x.hidden)[0] || card; return charts.filter((c) => v.contains(c.el) && c.tab)[0]; };
      const llenarTabla = () => {
        const inst = instVisible(); if (!inst) return;
        const t = inst.tab(); tab.textContent = '';
        const tb = document.createElement('table'), cab = tb.createTHead().insertRow();
        t.cols.forEach((c, i) => { const th = document.createElement('th'); th.textContent = c; if ((t.num || []).indexOf(i) >= 0) th.className = 'n'; cab.appendChild(th); });
        const cu = tb.createTBody();
        t.rows.forEach((fila) => { const r = cu.insertRow(); fila.forEach((v, i) => { const c = r.insertCell(); c.textContent = String(v); if ((t.num || []).indexOf(i) >= 0) c.className = 'n'; }); });
        tab.appendChild(tb);
      };
      if (seg) {
        const botones = $$('button', seg);
        botones.forEach((b) => b.addEventListener('click', () => {
          botones.forEach((x) => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
          vistas.forEach((v) => { v.hidden = v.dataset.vista !== b.dataset.vista; });
          const pista = $('.pista', card), vis = vistas.filter((v) => !v.hidden)[0];
          if (pista && vis && vis.dataset.pista) pista.textContent = vis.dataset.pista;
          charts.forEach((c) => { if (card.contains(c.el)) c.render(); });
          if (card.classList.contains('con-tabla')) llenarTabla();
        }));
      }
      if (btnTabla) btnTabla.addEventListener('click', () => {
        const on = !card.classList.contains('con-tabla');
        if (on) llenarTabla();
        card.classList.toggle('con-tabla', on);
        btnTabla.setAttribute('aria-pressed', on ? 'true' : 'false');
        btnTabla.textContent = on ? 'Ver gráfica' : 'Ver tabla';
        tab.hidden = !on;
      });
      /* la leyenda de la calidad del ingreso resalta una categoría y atenúa las demás */
      $$('.leyenda button[data-k]', card).forEach((b) => {
        const poner = (k) => { if (k) card.setAttribute('data-foco', k); else card.removeAttribute('data-foco'); };
        b.addEventListener('pointerenter', () => { if (!card.dataset.fijo) poner(b.dataset.k); });
        b.addEventListener('pointerleave', () => { if (!card.dataset.fijo) poner(null); });
        b.addEventListener('focus', () => { if (!card.dataset.fijo) poner(b.dataset.k); });
        b.addEventListener('blur', () => { if (!card.dataset.fijo) poner(null); });
        b.addEventListener('click', () => {
          const igual = card.dataset.fijo === b.dataset.k;
          $$('.leyenda button[data-k]', card).forEach((x) => x.classList.remove('on'));
          if (igual) { delete card.dataset.fijo; poner(null); } else { card.dataset.fijo = b.dataset.k; poner(b.dataset.k); b.classList.add('on'); }
        });
      });
    });
  }

  const escenas = $$('.escena');
  let actual = 0;
  function marcar(i) {                                       // indica en los puntos, el contador y las notas cuál es la lámina actual
    actual = i;
    $$('.punto').forEach((b, j) => b.setAttribute('aria-current', j === i ? 'true' : 'false'));
    const pos = $('#pos'); if (pos) pos.textContent = (i + 1) + ' / ' + escenas.length;
    pintarNotas();
  }
  function ir(i) {
    i = clamp(i, 0, escenas.length - 1);
    marcar(i);
    escenas[i].scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
  }
  function irA(id) { const i = escenas.findIndex((e) => e.id === id); if (i >= 0) ir(i); }
  function pintarNotas() {
    const e = escenas[actual], g = $('#guion');
    if (!g || !e) return;
    $('h4', g).textContent = 'Notas · ' + (e.dataset.titulo || '') + (e.dataset.quien ? ' · propuesta: presenta ' + e.dataset.quien : '');
    $('p', g).textContent = e.dataset.guion || '';
  }
  function vincularNavegacion() {
    const puntos = $('#puntos');
    escenas.forEach((e, i) => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'punto'; b.title = e.dataset.titulo || ''; b.setAttribute('aria-label', 'Lámina ' + (i + 1) + ': ' + (e.dataset.titulo || ''));
      b.addEventListener('click', () => ir(i)); puntos.appendChild(b);
    });
    const obs = new IntersectionObserver((items) => {
      items.forEach((it) => { if (it.isIntersecting && it.intersectionRatio > 0.45) marcar(escenas.indexOf(it.target)); });
    }, { threshold: [0.45, 0.6] });
    escenas.forEach((e) => obs.observe(e));
    marcar(0);
    $('#sig').addEventListener('click', () => ir(actual + 1));
    $('#ant').addEventListener('click', () => ir(actual - 1));
    document.addEventListener('keydown', (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      const tag = (ev.target && ev.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      const k = ev.key;
      if (k === 'ArrowDown' || k === 'PageDown' || k === 'ArrowRight' || (k === ' ' && tag !== 'BUTTON' && tag !== 'A' && tag !== 'SUMMARY')) { ir(actual + 1); ev.preventDefault(); }
      else if (k === 'ArrowUp' || k === 'PageUp' || k === 'ArrowLeft') { ir(actual - 1); ev.preventDefault(); }
      else if (k === 'Home') { ir(0); ev.preventDefault(); }
      else if (k === 'End') { ir(escenas.length - 1); ev.preventDefault(); }
      else if (k === 'n' || k === 'N') alternarNotas();
      else if (k === 'f' || k === 'F') pantallaCompleta();
      else if (k === 'Escape') { const g = $('#guion'); if (g && !g.hidden) alternarNotas(); }
    });
  }
  function alternarNotas() {
    const g = $('#guion'), b = $('#btn-notas');
    g.hidden = !g.hidden; b.setAttribute('aria-pressed', g.hidden ? 'false' : 'true');
    if (!g.hidden) pintarNotas();
  }
  function pantallaCompleta() {
    try {
      if (document.fullscreenElement) document.exitFullscreen();
      else { const p = document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); if (p && p.catch) p.catch(() => {}); }
    } catch (e) { /* algunos visores no permiten pantalla completa */ }
  }
  function vincularControles() {
    const sel = $('#sel-estado'), fic = $('#sel-ficha'), lista = D.estados.slice().sort((a, b) => a.n.localeCompare(b.n, 'es'));
    const opciones = (s, conVacio) => {
      if (!s) return;
      if (conVacio) { const o = document.createElement('option'); o.value = ''; o.textContent = 'Entidad: todas'; s.appendChild(o); }
      lista.forEach((e) => { const o = document.createElement('option'); o.value = String(e.id); o.textContent = e.n; s.appendChild(o); });
    };
    opciones(sel, true); opciones(fic, false);
    if (fic) fic.value = '20';
    if (sel) sel.addEventListener('change', () => setEstado(sel.value === '' ? null : +sel.value, true));
    if (fic) fic.addEventListener('change', () => setEstado(+fic.value, true));
    const chip = $('#chip-estado'); if (chip) $('button', chip).addEventListener('click', () => setEstado(null, true));
    const met = $('#sel-metrica'); if (met) met.addEventListener('change', () => charts.forEach((c) => { if (c.el.dataset.chart === 'mosaicoQ3') c.render(); }));
    $('#btn-notas').addEventListener('click', alternarNotas);
    $('#btn-pantalla').addEventListener('click', pantallaCompleta);
    const tema = $('#btn-tema');
    const aplicarTema = (t) => { document.documentElement.setAttribute('data-theme', t); try { localStorage.setItem('enoe-tema', t); } catch (e) { /* sin almacenamiento */ } setTimeout(renderTodo, 30); };
    tema.addEventListener('click', () => {
      const actualOscuro = document.documentElement.getAttribute('data-theme') === 'dark' || (!document.documentElement.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
      aplicarTema(actualOscuro ? 'light' : 'dark');
    });
    try { const guardado = localStorage.getItem('enoe-tema'); if (guardado === 'dark' || guardado === 'light') document.documentElement.setAttribute('data-theme', guardado); } catch (e) { /* nada */ }
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => setTimeout(renderTodo, 30));
    $$('[data-ir]').forEach((a) => a.addEventListener('click', (ev) => { ev.preventDefault(); const i = escenas.findIndex((e) => e.id === a.dataset.ir); if (i >= 0) ir(i); }));
    $$('a[href^="#e-"]').forEach((a) => a.addEventListener('click', (ev) => { const i = escenas.findIndex((e) => '#' + e.id === a.getAttribute('href')); if (i >= 0) { ev.preventDefault(); ir(i); } }));
  }

  /* ---------- arranque ---------- */
  function iniciar() {
    $$('.viz[data-chart]').forEach(montar);
    vincularKdd(); vincularArquitectura(); vincularCalculadora(); vincularTarjetas(); vincularControles(); vincularNavegacion();
    pintarFicha();
    let t = null;
    addEventListener('resize', () => { clearTimeout(t); t = setTimeout(renderTodo, 120); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(renderTodo);
    if (location.hash) { const i = escenas.findIndex((e) => '#' + e.id === location.hash); if (i > 0) setTimeout(() => ir(i), 60); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
