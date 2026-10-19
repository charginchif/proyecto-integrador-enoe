/* Radiografía socioeconómica de México · interacción del sitio (sin bibliotecas).
   Tema claro/oscuro, índice con sección actual, mapa de mosaicos, visor de figuras, herramientas de estudio (glosario, números,
   preguntas, autoevaluación, reflexión, lista de verificación) y modo presentación (una escena a la vez, guion, ruta corta y reloj). */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento: la página funciona igual */ } }
  };
  var raiz = document.documentElement;

  /* ---------- tema ---------- */
  var guardado = store.get('tema');
  if (guardado) raiz.setAttribute('data-theme', guardado);
  var bTema = $('#btn-tema');
  if (bTema) bTema.addEventListener('click', function () {
    var sistemaOscuro = window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches;
    var actual = raiz.getAttribute('data-theme') || (sistemaOscuro ? 'dark' : 'light');
    var nuevo = actual === 'dark' ? 'light' : 'dark';
    raiz.setAttribute('data-theme', nuevo);
    store.set('tema', nuevo);
  });

  /* ---------- índice lateral ---------- */
  var rail = $('.rail');
  var bInd = $('#btn-indice');
  if (bInd && rail) bInd.addEventListener('click', function () { rail.classList.toggle('abierto'); });
  $$('.rail a').forEach(function (a) { a.addEventListener('click', function () { if (rail) rail.classList.remove('abierto'); }); });
  var enlaces = {};
  $$('.rail a[href^="#"]').forEach(function (a) { enlaces[a.getAttribute('href').slice(1)] = a; });
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (items) {
      items.forEach(function (it) {
        if (!it.isIntersecting) return;
        var a = enlaces[it.target.id];
        if (!a) return;
        $$('.rail a.actual').forEach(function (x) { x.classList.remove('actual'); });
        a.classList.add('actual');
        var d = a.closest('details');
        if (d && !d.open) d.open = true;
      });
    }, { rootMargin: '-25% 0px -65% 0px' });
    $$('.escena[id], .seccion[id]').forEach(function (s) { io.observe(s); });
  }

  /* ---------- mapa de mosaicos ---------- */
  $$('.mosaico').forEach(function (m) {
    var info = m.parentNode.querySelector('.mapa-info');
    $$('.tile', m).forEach(function (t) {
      var mostrar = function () {
        if (!info) return;
        info.textContent = t.dataset.n + ': ' + t.dataset.v + ' % de informalidad (IC 95 %: ' + t.dataset.i + '); lugar ' + t.dataset.l + ' de 32.';
      };
      ['mouseenter', 'focus', 'click'].forEach(function (ev) { t.addEventListener(ev, mostrar); });
    });
  });

  /* ---------- visor de figuras ---------- */
  var visor = $('#visor');
  document.addEventListener('click', function (e) {
    var img = e.target.closest ? e.target.closest('figure.fig img') : null;
    if (!img || !visor || typeof visor.showModal !== 'function' || document.body.classList.contains('presentando-sin-visor')) return;
    var v = $('#visor-img');
    v.src = img.currentSrc || img.src;
    v.alt = img.alt;
    var cap = img.closest('figure').querySelector('figcaption');
    $('#visor-pie').textContent = cap ? cap.textContent : '';
    visor.showModal();
  });
  var bVc = $('#visor-cerrar');
  if (bVc) bVc.addEventListener('click', function () { visor.close(); });
  if (visor) visor.addEventListener('click', function (e) { if (e.target === visor) visor.close(); });

  /* ---------- botones de copiar código ---------- */
  $$('pre.codigo').forEach(function (pre) {
    var b = document.createElement('button');
    b.className = 'copiar'; b.type = 'button'; b.textContent = 'Copiar';
    b.addEventListener('click', function () {
      var cod = pre.querySelector('code');
      var listo = function (t) { b.textContent = t; setTimeout(function () { b.textContent = 'Copiar'; }, 1600); };
      var seleccionar = function () {
        var r = document.createRange(); r.selectNodeContents(cod);
        var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); listo('Seleccionado');
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(cod.innerText).then(function () { listo('Copiado'); }, seleccionar);
      } else { seleccionar(); }
    });
    pre.appendChild(b);
  });

  /* ---------- pestañas de estudio ---------- */
  $$('[role=tablist]').forEach(function (lista) {
    var tabs = $$('[role=tab]', lista);
    var activar = function (t) {
      tabs.forEach(function (x) {
        var on = x === t;
        x.setAttribute('aria-selected', on ? 'true' : 'false');
        x.tabIndex = on ? 0 : -1;
        var p = document.getElementById(x.getAttribute('aria-controls'));
        if (p) p.hidden = !on;
      });
    };
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { activar(t); });
      t.addEventListener('keydown', function (e) {
        var j = e.key === 'ArrowRight' ? (i + 1) % tabs.length : e.key === 'ArrowLeft' ? (i + tabs.length - 1) % tabs.length : -1;
        if (j >= 0) { tabs[j].focus(); activar(tabs[j]); e.preventDefault(); }
      });
    });
  });

  /* ---------- glosario y números clave: búsqueda y autoevaluación ---------- */
  var buscar = $('#gl-buscar');
  if (buscar) buscar.addEventListener('input', function () {
    var q = buscar.value.trim().toLowerCase();
    var hay = 0;
    $$('.term').forEach(function (t) { t.hidden = !!q && t.textContent.toLowerCase().indexOf(q) < 0; if (!t.hidden) hay++; });
    var v = $('#gl-vacio'); if (v) v.hidden = hay > 0;
  });
  var alternar = function (btn, contenedor, clase, items) {
    if (!btn || !contenedor) return;
    btn.addEventListener('click', function () {
      var on = btn.getAttribute('aria-pressed') !== 'true';
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      contenedor.classList.toggle(clase, on);
      $$(items, contenedor).forEach(function (x) { x.classList.remove('visto'); });
    });
    contenedor.addEventListener('click', function (e) {
      var it = e.target.closest ? e.target.closest(items) : null;
      if (it && contenedor.classList.contains(clase)) it.classList.toggle('visto');
    });
  };
  alternar($('#gl-auto'), $('#glosario'), 'autoeval', '.term');
  alternar($('#nm-tapar'), $('#numeros'), 'tapar', '.nm');

  /* ---------- preguntas de defensa ---------- */
  var qBuscar = $('#qa-buscar');
  if (qBuscar) qBuscar.addEventListener('input', function () {
    var q = qBuscar.value.trim().toLowerCase();
    var hay = 0;
    $$('#qa details').forEach(function (d) {
      var coincide = !q || d.textContent.toLowerCase().indexOf(q) >= 0;
      d.hidden = !coincide;
      if (coincide) hay++;
      if (q && coincide) d.open = true;
    });
    var v = $('#qa-vacio'); if (v) v.hidden = hay > 0;
  });
  var qTodo = $('#qa-todo');
  if (qTodo) qTodo.addEventListener('click', function () {
    var abrir = qTodo.getAttribute('aria-pressed') !== 'true';
    qTodo.setAttribute('aria-pressed', abrir ? 'true' : 'false');
    qTodo.textContent = abrir ? 'Contraer todo' : 'Expandir todo';
    $$('#qa details').forEach(function (d) { d.open = abrir; });
  });

  /* ---------- autoevaluación ---------- */
  var datosQuiz = [];
  try { datosQuiz = JSON.parse(($('#datos-quiz') || {}).textContent || '[]'); } catch (e) { datosQuiz = []; }
  var barajar = function (a) {
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  };
  var pintarQuiz = function () {
    var cont = $('#quiz'); if (!cont) return;
    cont.textContent = '';
    var resp = 0, aciertos = 0;
    var res = $('#quiz-res');
    var actualizar = function () {
      res.textContent = resp < datosQuiz.length ? 'Respondidas: ' + resp + ' de ' + datosQuiz.length + ' · Aciertos: ' + aciertos
        : 'Resultado: ' + aciertos + ' de ' + datosQuiz.length + (aciertos === datosQuiz.length ? ' (perfecto)' : aciertos >= datosQuiz.length * 0.8 ? ' (muy bien)' : ' (repasa las explicaciones)');
    };
    datosQuiz.forEach(function (p, i) {
      var f = document.createElement('fieldset'); f.className = 'preg';
      var lg = document.createElement('legend'); lg.textContent = (i + 1) + '. ' + p.q; f.appendChild(lg);
      var ex = document.createElement('p'); ex.className = 'explica'; ex.hidden = true; ex.textContent = p.e;
      barajar(p.o.map(function (t, k) { return { t: t, k: k }; })).forEach(function (o) {
        var l = document.createElement('label');
        var r = document.createElement('input'); r.type = 'radio'; r.name = 'q' + i;
        r.addEventListener('change', function () {
          $$('input', f).forEach(function (x) { x.disabled = true; });
          var ok = o.k === p.c;
          l.classList.add(ok ? 'bien' : 'mal');
          if (!ok) $$('label', f).forEach(function (x) { if (x.dataset.ok === '1') x.classList.add('bien'); });
          ex.hidden = false; resp++; if (ok) aciertos++; actualizar();
        });
        l.dataset.ok = o.k === p.c ? '1' : '0';
        l.appendChild(r); l.appendChild(document.createTextNode(' ' + o.t));
        f.appendChild(l);
      });
      f.appendChild(ex); cont.appendChild(f);
    });
    actualizar();
  };
  pintarQuiz();
  var bQ = $('#quiz-otra');
  if (bQ) bQ.addEventListener('click', pintarQuiz);

  /* ---------- lista de verificación y textos del equipo (se guardan en este navegador) ---------- */
  $$('input[data-chk]').forEach(function (c) {
    c.checked = store.get('chk-' + c.dataset.chk) === '1';
    c.addEventListener('change', function () { store.set('chk-' + c.dataset.chk, c.checked ? '1' : '0'); });
  });
  $$('textarea[data-guardar]').forEach(function (t) {
    var g = store.get('txt-' + t.dataset.guardar);
    if (g !== null) t.value = g;
    t.addEventListener('input', function () { store.set('txt-' + t.dataset.guardar, t.value); });
  });
  $$('[data-restablecer]').forEach(function (b) {
    b.addEventListener('click', function () {
      var t = document.getElementById(b.dataset.restablecer);
      t.value = t.defaultValue; store.set('txt-' + t.dataset.guardar, t.value);
    });
  });

  /* ---------- modo presentación ---------- */
  var P = { activo: false, ruta: 'completa', i: 0, lista: [], t0: 0, reloj: null };
  var barra = $('#pres'), panelNotas = $('#pres-notas');
  var app = document.getElementById('app') || document.body;
  var minutos = { corta: +(app.dataset.minCorta || 18), completa: +(app.dataset.minCompleta || 49) };
  var todas = function () { return $$('.escena[data-escena]'); };
  var construir = function () {
    P.lista = todas().filter(function (e) { return P.ruta === 'completa' || e.dataset.corta === '1'; });
  };
  var escenaVisible = function () {
    var mejor = null, d = 1e9;
    todas().forEach(function (e) { var r = e.getBoundingClientRect(); var dist = Math.abs(r.top); if (r.bottom > 0 && dist < d) { d = dist; mejor = e; } });
    return mejor;
  };
  var pintarReloj = function () {
    var s = Math.floor((Date.now() - P.t0) / 1000);
    var el = $('#pres-reloj');
    el.textContent = String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0') + ' / ' + minutos[P.ruta] + ' min';
    el.classList.toggle('pasado', s > minutos[P.ruta] * 60);
  };
  var ir = function (i) {
    if (!P.lista.length) return;
    P.i = Math.max(0, Math.min(P.lista.length - 1, i));
    todas().forEach(function (e) { e.classList.remove('activa'); });
    var e = P.lista[P.i];
    e.classList.add('activa');
    window.scrollTo(0, 0);
    $('#pres-pos').textContent = (P.i + 1) + ' / ' + P.lista.length;
    $('#pres-tit').textContent = (e.dataset.cap ? e.dataset.cap + ' · ' : '') + (e.dataset.titulo || '');
    var g = e.querySelector('.guion');
    var quien = e.dataset.quien ? 'Propuesta: presenta ' + e.dataset.quien : 'Guion';
    panelNotas.textContent = '';
    var h = document.createElement('h4'); h.textContent = 'Guion · ' + quien + (e.dataset.min ? ' · ' + e.dataset.min + ' min' : ''); panelNotas.appendChild(h);
    $$('.guion__txt', g || document).forEach(function (p) { var q = document.createElement('p'); q.textContent = p.textContent; panelNotas.appendChild(q); });
    if (!g) { var q = document.createElement('p'); q.textContent = 'Esta escena no tiene guion escrito.'; panelNotas.appendChild(q); }
  };
  var etiquetaRuta = function () {
    $('#pres-ruta').setAttribute('aria-pressed', P.ruta === 'corta' ? 'true' : 'false');
    $('#pres-ruta').textContent = P.ruta === 'corta' ? 'Ruta: corta ★ (R)' : 'Ruta: completa (R)';
  };
  var entrar = function (ruta) {
    if (P.activo) return;
    if (ruta === 'corta' || ruta === 'completa') P.ruta = ruta;
    if (barra) etiquetaRuta();
    var actual = escenaVisible();
    P.activo = true; construir();
    document.body.classList.add('presentando');
    var i = P.lista.indexOf(actual); P.i = i < 0 ? 0 : i;
    P.t0 = Date.now(); pintarReloj(); P.reloj = setInterval(pintarReloj, 1000);
    ir(P.i);
    var fs = document.documentElement.requestFullscreen;
    if (fs) { try { var pr = fs.call(document.documentElement); if (pr && pr.catch) pr.catch(function () {}); } catch (e) { /* algunos visores no lo permiten */ } }
  };
  var salir = function () {
    if (!P.activo) return;
    var e = P.lista[P.i];
    P.activo = false; clearInterval(P.reloj);
    document.body.classList.remove('presentando');
    todas().forEach(function (x) { x.classList.remove('activa'); });
    panelNotas.hidden = true; $('#pres-notas-btn').setAttribute('aria-pressed', 'false');
    if (document.fullscreenElement && document.exitFullscreen) { try { document.exitFullscreen(); } catch (er) { /* nada */ } }
    if (e) e.scrollIntoView();
  };
  var alternarNotas = function () {
    var on = panelNotas.hidden;
    panelNotas.hidden = !on;
    $('#pres-notas-btn').setAttribute('aria-pressed', on ? 'true' : 'false');
  };
  var cambiarRuta = function () {
    var actual = P.lista[P.i];
    P.ruta = P.ruta === 'completa' ? 'corta' : 'completa';
    etiquetaRuta();
    construir();
    var i = P.lista.indexOf(actual);
    if (i < 0) { var todasL = todas(); var k = todasL.indexOf(actual); while (i < 0 && k < todasL.length) { i = P.lista.indexOf(todasL[k++]); } }
    ir(i < 0 ? P.lista.length - 1 : i); pintarReloj();
  };
  var bPresentar = $$('[data-presentar]');
  bPresentar.forEach(function (b) { b.addEventListener('click', function () { entrar(b.dataset.presentar); }); });
  if (barra) {
    $('#pres-ant').addEventListener('click', function () { ir(P.i - 1); });
    $('#pres-sig').addEventListener('click', function () { ir(P.i + 1); });
    $('#pres-salir').addEventListener('click', salir);
    $('#pres-notas-btn').addEventListener('click', alternarNotas);
    $('#pres-ruta').addEventListener('click', cambiarRuta);
  }
  document.addEventListener('keydown', function (e) {
    if (!P.activo || e.ctrlKey || e.metaKey || e.altKey) return;
    var tag = (e.target && e.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    var k = e.key;
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ') { ir(P.i + 1); e.preventDefault(); }
    else if (k === 'ArrowLeft' || k === 'PageUp') { ir(P.i - 1); e.preventDefault(); }
    else if (k === 'Home') { ir(0); e.preventDefault(); }
    else if (k === 'End') { ir(P.lista.length - 1); e.preventDefault(); }
    else if (k === 'n' || k === 'N') { alternarNotas(); }
    else if (k === 'r' || k === 'R') { cambiarRuta(); }
    else if (k === 'Escape' && !(visor && visor.open)) { salir(); }
  });
  document.addEventListener('click', function (e) {          /* enlaces internos dentro del modo presentación */
    if (!P.activo) return;
    var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if (!a) return;
    var dest = document.getElementById(a.getAttribute('href').slice(1));
    var esc = dest && dest.closest ? dest.closest('.escena') : null;
    var i = esc ? P.lista.indexOf(esc) : -1;
    e.preventDefault();
    if (i >= 0) ir(i);
  });
  if (location.hash === '#presentar' || location.hash === '#presentar-corta') { setTimeout(function () { entrar(location.hash === '#presentar-corta' ? 'corta' : 'completa'); }, 300); }
})();
