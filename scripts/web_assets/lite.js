/* Radiografía socioeconómica de México · presentación (presentacion.html): láminas, navegación, notas y tarjetas con vistas.
   Se concatena después de charts.js (que aporta los datos, las gráficas, el globo y el estado de la entidad elegida). */

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
