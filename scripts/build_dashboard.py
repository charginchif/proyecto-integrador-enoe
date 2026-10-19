"""Construye el tablero interactivo (un solo archivo HTML, sin internet) a partir de las fichas por entidad.

    python scripts/build_dashboard.py

Lee data/processed/mongo/entidades.json (la colección «entidades» exportada por scripts/run_mongo.py) y las tablas
nacionales de results/. El HTML incluye plotly.js incrustado, así que abre sin conexión.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enoe import config as C, load_mongo as L  # noqa: E402

SALIDA = C.ROOT / "tablero" / "tablero_enoe.html"


def datos() -> dict:
    ent = json.loads((L.DIR_MONGO / "entidades.json").read_text(encoding="utf-8"))
    for e in ent:
        _, _, _, _, col, fila = C.ENTIDADES[e["cve_ent"]]
        e["mosaico"] = {"col": col, "fila": fila}
    r = C.RESULTS
    bn = pd.read_csv(r / "brecha_nivel.csv", encoding="utf-8-sig")
    cal = pd.read_csv(r / "calidad_ingreso.csv", encoding="utf-8-sig")
    resumen = json.loads((r / "resumen.json").read_text(encoding="utf-8"))
    cal_nac = {g: float(cal[(cal.grupo == g) & (cal.poblacion == "Total")]["pct"].iloc[0]) for g in "ABCD"}
    return {
        "entidades": ent,
        "nacional": {
            "til1": resumen["til1"]["nacional"], "retorno": resumen["retorno"]["nacional_pct"],
            "brecha_hora": resumen["brecha"]["total_hora"], "brecha_mens": resumen["brecha"]["total_mens"],
            "calidad": cal_nac,
            "brecha_nivel": bn[["nivel", "brecha_hora_pct", "brecha_hora_inf", "brecha_hora_sup", "brecha_mens_pct", "brecha_mens_inf", "brecha_mens_sup"]].to_dict("records"),
        },
        "meta": {"periodo": C.PERIODO_ETIQUETA, "B": resumen["B"], "n_universo": resumen["muestras"]["universo"], "n_salarial": resumen["muestras"]["salarial"]},
    }


PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tablero ENOE 2025-T4</title>
<style>
:root{color-scheme:light;--surface:#fcfcfb;--page:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--base:#c3c2b7;--blue:#2a78d6;--orange:#eb6834;--aqua:#1baf7a;--yellow:#eda100;--red:#e34948;--border:rgba(11,11,11,.10)}
@media (prefers-color-scheme: dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--surface:#1a1a19;--page:#0d0d0d;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--base:#383835;--blue:#3987e5;--orange:#d95926;--aqua:#199e70;--yellow:#c98500;--red:#e66767;--border:rgba(255,255,255,.10)}}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.45}
.wrap{max-width:1180px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:1.5rem;margin:0 0 4px}
.sub{color:var(--ink2);margin:0 0 16px;font-size:.95rem}
.filtros{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 16px;margin-bottom:14px}
.filtros label{font-size:.85rem;color:var(--ink2)}
select{font:inherit;color:var(--ink);background:var(--surface);border:1px solid var(--base);border-radius:8px;padding:6px 10px}
.seg{display:flex;flex-wrap:wrap;gap:6px}
.seg button{font:inherit;font-size:.85rem;color:var(--ink);background:var(--surface);border:1px solid var(--base);border-radius:999px;padding:5px 12px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--blue);border-color:var(--blue);color:#fff}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:14px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 14px}
.kpi .l{font-size:.78rem;color:var(--ink2)}
.kpi .v{font-size:1.9rem;font-weight:650;letter-spacing:-.01em;margin:2px 0}
.kpi .d{font-size:.78rem;color:var(--muted)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:860px){.grid{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 14px 6px;min-width:0}
.card h2{font-size:1rem;margin:0}
.card p.s{font-size:.8rem;color:var(--ink2);margin:2px 0 6px}
.full{grid-column:1/-1}
.leyenda{display:flex;align-items:center;gap:8px;font-size:.78rem;color:var(--ink2);margin:2px 0 6px}
.leyenda .barra{height:10px;width:200px;border-radius:5px}
details{margin-top:14px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:10px 14px}
summary{cursor:pointer;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:.82rem;margin-top:8px}
th,td{padding:5px 8px;border-bottom:1px solid var(--grid);text-align:right;white-space:nowrap}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}
th{cursor:pointer;color:var(--ink2);position:sticky;top:0;background:var(--surface)}
tr.sel td{background:rgba(42,120,214,.12);font-weight:600}
tbody tr{cursor:pointer}
.tablewrap{max-height:420px;overflow:auto}
pre{background:var(--page);padding:10px;border-radius:8px;overflow:auto;font-size:.75rem;max-height:340px}
.nota{font-size:.78rem;color:var(--muted);margin-top:14px}
</style>
</head>
<body>
<div class="wrap">
<h1>¿Cuánto rinde estudiar en México?</h1>
<p class="sub">Escolaridad, ingreso, informalidad y brecha de género por entidad · ENOE 2025-T4 (INEGI) · Equipo 1, Ciencia de Datos, UNE Plantel Centro</p>

<div class="filtros">
  <div><label for="ent">Entidad</label><br><select id="ent"></select></div>
  <div><label>Indicador del mapa y del ranking</label><div class="seg" id="seg"></div></div>
</div>

<div class="kpis" id="kpis"></div>

<div class="grid">
  <div class="card"><h2 id="t-mapa"></h2><p class="s">Cada estado ocupa la misma área. Haz clic en un mosaico para elegirlo.</p>
    <div class="leyenda"><span id="lmin"></span><span class="barra" id="barra"></span><span id="lmax"></span></div>
    <div id="mapa" style="height:410px"></div></div>
  <div class="card"><h2 id="t-rank"></h2><p class="s">Punto = estimación; línea = intervalo de confianza al 95 %. El estado elegido va resaltado.</p><div id="rank" style="height:560px"></div></div>
  <div class="card"><h2>Donde se estudia más, hay menos informalidad</h2><p class="s">Años de escolaridad promedio de los ocupados vs. tasa de informalidad (una entidad por punto).</p><div id="sc1" style="height:340px"></div></div>
  <div class="card"><h2>Los estados más escolarizados pagan más por hora</h2><p class="s">Años de escolaridad promedio vs. mediana del ingreso por hora ($).</p><div id="sc2" style="height:340px"></div></div>
  <div class="card"><h2>Brecha de género por nivel de instrucción (nacional)</h2><p class="s">% menos que ganan las mujeres que los hombres, con IC 95 %. Por hora es pequeña; por mes, grande (las mujeres trabajan menos horas pagadas).</p><div id="brecha" style="height:340px"></div></div>
  <div class="card"><h2 id="t-cal"></h2><p class="s">¿Quién da el monto exacto de su ingreso? Cuando no lo da, el dato falta o solo se conoce un rango.</p><div id="cal" style="height:340px"></div></div>
</div>

<details><summary>Vista de tabla de las 32 entidades (equivalente accesible de las gráficas; clic en el encabezado para ordenar)</summary>
<div class="tablewrap"><table id="tabla"><thead></thead><tbody></tbody></table></div></details>

<details><summary>Documento de la colección <code>entidades</code> (así se guarda y se consulta por entidad en MongoDB)</summary><pre id="doc"></pre></details>

<p class="nota">Estimaciones ponderadas con <code>fac_tri</code>; intervalos por bootstrap de Rao-Wu con __B__ réplicas. Universo: __NU__ ocupados de 15+ años; muestra salarial: __NS__ observaciones (ocupados de 15 a 65 años con monto exacto de ingreso).
Las relaciones entre estados no implican causalidad individual. Fuente: INEGI, ENOE 2025-T4 (SDEMT y COE2T). Cálculos del equipo.</p>
</div>

<script>__PLOTLY__</script>
<script>
const D = __DATA__;
const SEQ = ["#cde2fb","#b7d3f6","#9ec5f4","#86b6ef","#6da7ec","#5598e7","#3987e5","#2a78d6","#256abf","#1c5cab","#184f95","#104281","#0d366b"];
const fmt = (v, d=1) => v==null||isNaN(v) ? "—" : v.toLocaleString("es-MX",{minimumFractionDigits:d,maximumFractionDigits:d});
const M = {
  til1: {n:"Informalidad laboral (TIL1)", u:"%", v:e=>e.informalidad.til1_pct, ci:e=>e.informalidad.ic95, d:1, mayor:"más informalidad"},
  ret:  {n:"Rendimiento por año de escolaridad", u:"%", v:e=>e.rendimiento_escolaridad.pct_por_anio, ci:e=>e.rendimiento_escolaridad.ic95, d:1, mayor:"estudiar rinde más"},
  med:  {n:"Mediana del ingreso por hora", u:"$", v:e=>e.ingreso_hora.mediana_pesos, ci:e=>e.ingreso_hora.ic95, d:0, mayor:"se paga más por hora"},
  rho:  {n:"Correlación escolaridad-ingreso (Spearman)", u:"", v:e=>e.correlacion_spearman.rho, ci:e=>e.correlacion_spearman.ic95, d:2, mayor:"vínculo más fuerte"},
  bre:  {n:"Brecha de género por hora", u:"%", v:e=>e.brecha_genero.hora_pct, ci:e=>e.brecha_genero.hora_ic95, d:1, mayor:"mayor desventaja de las mujeres"},
};
let metrica = "til1", sel = null;
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const E = D.entidades;
const lum = hex => { const c = hex.replace("#",""); const r=parseInt(c.slice(0,2),16)/255,g=parseInt(c.slice(2,4),16)/255,b=parseInt(c.slice(4,6),16)/255; return .2126*r+.7152*g+.0722*b; };
function colorSeq(t){ t=Math.max(0,Math.min(1,t)); const x=t*(SEQ.length-1), i=Math.floor(x), f=x-i; if(i>=SEQ.length-1) return SEQ[SEQ.length-1];
  const a=SEQ[i], b=SEQ[i+1]; const p=h=>[1,3,5].map(k=>parseInt(h.slice(k,k+2),16)); const A=p(a),B=p(b);
  return "#"+A.map((v,k)=>Math.round(v+(B[k]-v)*f).toString(16).padStart(2,"0")).join(""); }
const base = () => ({paper_bgcolor:css("--surface"), plot_bgcolor:css("--surface"), font:{family:"system-ui, Segoe UI, sans-serif", size:12, color:css("--ink2")}, margin:{l:50,r:14,t:8,b:44}});
const ejes = (extra={}) => Object.assign({gridcolor:css("--grid"), zerolinecolor:css("--base"), linecolor:css("--base"), tickcolor:css("--muted"), tickfont:{color:css("--muted")}}, extra);
const cfg = {displayModeBar:false, responsive:true};

function nombreSel(){ return sel==null ? "Nacional" : E.find(e=>e.cve_ent===sel).entidad; }

function kpis(){
  const n = D.nacional, e = sel==null ? null : E.find(x=>x.cve_ent===sel);
  const k = e ? [
    ["Informalidad laboral (TIL1)", fmt(e.informalidad.til1_pct)+" %", `IC95 ${fmt(e.informalidad.ic95[0])}–${fmt(e.informalidad.ic95[1])} · lugar ${e.informalidad.lugar} de 32 (1 = más informal)`],
    ["Escolaridad promedio", fmt(e.escolaridad.anios_medios_ocupados)+" años", `ocupados de 15+ · IC95 ${fmt(e.escolaridad.ic95[0])}–${fmt(e.escolaridad.ic95[1])}`],
    ["Mediana del ingreso por hora", "$"+fmt(e.ingreso_hora.mediana_pesos,0), `IC95 $${fmt(e.ingreso_hora.ic95[0],0)}–$${fmt(e.ingreso_hora.ic95[1],0)} · cuartil ${e.ingreso_hora.cuartil}`],
    ["Rendimiento por año de estudio", fmt(e.rendimiento_escolaridad.pct_por_anio)+" %", `IC95 ${fmt(e.rendimiento_escolaridad.ic95[0])}–${fmt(e.rendimiento_escolaridad.ic95[1])} · nacional ${fmt(n.retorno.est)} %`],
    ["Brecha de género por hora", fmt(e.brecha_genero.hora_pct)+" %", `IC95 ${fmt(e.brecha_genero.hora_ic95[0])}–${fmt(e.brecha_genero.hora_ic95[1])} · nacional ${fmt(n.brecha_hora.brecha_hora_pct)} %`],
    ["Brecha de género mensual", fmt(e.brecha_genero.mensual_pct)+" %", `IC95 ${fmt(e.brecha_genero.mensual_ic95[0])}–${fmt(e.brecha_genero.mensual_ic95[1])} · nacional ${fmt(n.brecha_mens.brecha_mens_pct)} %`],
  ] : [
    ["Informalidad laboral nacional", fmt(n.til1.est)+" %", `IC95 ${fmt(n.til1.ic_inf)}–${fmt(n.til1.ic_sup)} · coincide con el 55.0 % del INEGI`],
    ["Rendimiento por año de estudio", fmt(n.retorno.est)+" %", `IC95 ${fmt(n.retorno.ic_inf)}–${fmt(n.retorno.ic_sup)}`],
    ["Brecha de género por hora", fmt(n.brecha_hora.brecha_hora_pct)+" %", `IC95 ${fmt(n.brecha_hora.brecha_hora_inf)}–${fmt(n.brecha_hora.brecha_hora_sup)}`],
    ["Brecha de género mensual", fmt(n.brecha_mens.brecha_mens_pct)+" %", `IC95 ${fmt(n.brecha_mens.brecha_mens_inf)}–${fmt(n.brecha_mens.brecha_mens_sup)}`],
    ["Declaran monto exacto de ingreso", fmt(n.calidad.A,0)+" %", `${fmt(n.calidad.B,0)} % solo rango · ${fmt(n.calidad.D,0)} % no especifica`],
  ];
  document.getElementById("kpis").innerHTML = k.map(x=>`<div class="kpi"><div class="l">${x[0]}</div><div class="v">${x[1]}</div><div class="d">${x[2]}</div></div>`).join("");
}

function mapa(){
  const m = M[metrica], vals = E.map(m.v), lo = Math.min(...vals), hi = Math.max(...vals);
  const shapes=[], ann=[], px=[], py=[], tx=[], cd=[];
  E.forEach(e=>{
    const t=(m.v(e)-lo)/(hi-lo), c=colorSeq(t), x=e.mosaico.col, y=-e.mosaico.fila, esSel=e.cve_ent===sel;
    shapes.push({type:"rect",x0:x+.04,x1:x+.96,y0:y+.04,y1:y+.96,fillcolor:c,line:{color:esSel?css("--ink"):c,width:esSel?3:0},layer:"below"});
    const tc = lum(c)<.5 ? "#ffffff" : "#0b0b0b";
    ann.push({x:x+.5,y:y+.64,text:"<b>"+e.abreviatura+"</b>",showarrow:false,font:{size:11,color:tc}});
    ann.push({x:x+.5,y:y+.3,text:fmt(m.v(e),m.d),showarrow:false,font:{size:10,color:tc}});
    px.push(x+.5); py.push(y+.5); tx.push(`<b>${e.entidad}</b><br>${m.n}: ${m.u==="$"?"$":""}${fmt(m.v(e),m.d)}${m.u==="%"?" %":""}<br>IC95 ${fmt(m.ci(e)[0],m.d)} – ${fmt(m.ci(e)[1],m.d)}`); cd.push(e.cve_ent);
  });
  document.getElementById("lmin").textContent = fmt(lo,m.d)+(m.u==="%"?" %":""); document.getElementById("lmax").textContent = fmt(hi,m.d)+(m.u==="%"?" %":"");
  document.getElementById("barra").style.background = `linear-gradient(90deg, ${SEQ.join(",")})`;
  document.getElementById("t-mapa").textContent = m.n+" por entidad";
  const lay = Object.assign(base(), {shapes, annotations:ann, xaxis:{visible:false,range:[-.2,11.2],fixedrange:true}, yaxis:{visible:false,range:[-5.3,1.2],scaleanchor:"x",fixedrange:true}, margin:{l:4,r:4,t:4,b:4}, showlegend:false});
  Plotly.react("mapa",[{type:"scatter",mode:"markers",x:px,y:py,text:tx,customdata:cd,hovertemplate:"%{text}<extra></extra>",marker:{size:46,opacity:.001,color:css("--blue")}}],lay,cfg).then(g=>{
    g.removeAllListeners && g.removeAllListeners("plotly_click"); g.on("plotly_click",d=>{ seleccionar(d.points[0].customdata); }); });
}

function ranking(){
  const m = M[metrica], arr = E.slice().sort((a,b)=>m.v(a)-m.v(b));
  const x = arr.map(m.v), y = arr.map(e=>e.entidad);
  const azul = css("--blue");
  const cols = arr.map(e=> sel==null||e.cve_ent===sel ? azul : azul+"88");
  const sizes = arr.map(e=> e.cve_ent===sel ? 13 : 8);
  document.getElementById("t-rank").textContent = "Ranking: "+m.n.toLowerCase();
  Plotly.react("rank",[{type:"scatter",mode:"markers",x,y,marker:{color:cols,size:sizes,line:{color:css("--surface"),width:2}},
    error_x:{type:"data",symmetric:false,array:arr.map(e=>m.ci(e)[1]-m.v(e)),arrayminus:arr.map(e=>m.v(e)-m.ci(e)[0]),color:azul+"99",thickness:1.5,width:0},
    hovertemplate:"<b>%{y}</b><br>%{x:.2f}<extra></extra>"}],
    Object.assign(base(),{height:560,margin:{l:128,r:14,t:6,b:42},xaxis:ejes({title:{text:m.n+(m.u==="%"?" (%)":m.u==="$"?" ($)":"")}}),yaxis:ejes({automargin:true,dtick:1,tickfont:{size:10,color:css("--muted")},showgrid:false}),showlegend:false,
      annotations: sel==null?[]:[{x:m.v(E.find(e=>e.cve_ent===sel)),y:E.find(e=>e.cve_ent===sel).entidad,text:E.find(e=>e.cve_ent===sel).entidad,xanchor:"left",showarrow:false,xshift:14,font:{color:css("--ink"),size:11}}]}),cfg)
    .then(g=>{ g.removeAllListeners && g.removeAllListeners("plotly_click"); g.on("plotly_click",d=>{ const e=E.find(z=>z.entidad===d.points[0].y); seleccionar(e.cve_ent); }); });
}

function dispersion(div, fx, fy, ytitle, yfmt, yaxisTick){
  const xs=E.map(fx), ys=E.map(fy), n=xs.length, mx=xs.reduce((a,b)=>a+b)/n, my=ys.reduce((a,b)=>a+b)/n;
  const b=xs.reduce((s,x,i)=>s+(x-mx)*(ys[i]-my),0)/xs.reduce((s,x)=>s+(x-mx)**2,0), a=my-b*mx;
  const x0=Math.min(...xs)-.1, x1=Math.max(...xs)+.1, azul=css("--blue");
  const cols=E.map(e=> sel==null||e.cve_ent===sel ? azul : azul+"88"), sz=E.map(e=>e.cve_ent===sel?14:9);
  const txt=E.map(e=>e.cve_ent===sel?e.entidad:"");
  Plotly.react(div,[
    {type:"scatter",mode:"lines",x:[x0,x1],y:[a+b*x0,a+b*x1],line:{color:css("--base"),width:2},hoverinfo:"skip"},
    {type:"scatter",mode:"markers+text",x:xs,y:ys,text:txt,textposition:"top center",textfont:{color:css("--ink"),size:11},
     marker:{color:cols,size:sz,line:{color:css("--surface"),width:2}},customdata:E.map(e=>e.entidad),hovertemplate:"<b>%{customdata}</b><br>Escolaridad: %{x:.1f} años<br>"+yfmt+"<extra></extra>"}],
    Object.assign(base(),{showlegend:false,xaxis:ejes({title:{text:"Años de escolaridad promedio"}}),yaxis:ejes(Object.assign({title:{text:ytitle}},yaxisTick||{}))}),cfg)
    .then(g=>{ g.removeAllListeners && g.removeAllListeners("plotly_click"); g.on("plotly_click",d=>{ if(d.points[0].curveNumber===1) seleccionar(E.find(z=>z.entidad===d.points[0].customdata).cve_ent); }); });
}

function brecha(){
  const b = D.nacional.brecha_nivel, nombres=b.map(r=>r.nivel.replace(/^\d\.\s*/,"").replace("Medio superior y superior","Medio sup. y sup."));
  const azul=css("--blue"), naranja=css("--orange");
  const tr=(k,color,nm)=>({type:"bar",name:nm,x:nombres,y:b.map(r=>r["brecha_"+k+"_pct"]),marker:{color},width:.34,
     error_y:{type:"data",symmetric:false,array:b.map(r=>r["brecha_"+k+"_sup"]-r["brecha_"+k+"_pct"]),arrayminus:b.map(r=>r["brecha_"+k+"_pct"]-r["brecha_"+k+"_inf"]),color:css("--ink2"),thickness:1.2,width:3},
     hovertemplate:"%{x}<br>"+nm+": %{y:.1f} %<extra></extra>"});
  Plotly.react("brecha",[tr("hora",azul,"Por hora"),tr("mens",naranja,"Por mes")],
    Object.assign(base(),{barmode:"group",bargap:.25,legend:{orientation:"h",y:1.12,x:0},xaxis:ejes({showgrid:false,tickfont:{size:10,color:css("--muted")}}),yaxis:ejes({title:{text:"% menos que ganan las mujeres"},ticksuffix:" %",rangemode:"tozero"})}),cfg);
}

function calidad(){
  const e = sel==null?null:E.find(x=>x.cve_ent===sel), n=D.nacional.calidad;
  const filas = e ? [["Nacional",n],[e.entidad,e.calidad_ingreso_pct]] : [["Nacional",n]];
  const cfgG = [["A","Monto exacto",css("--blue")],["B","Solo rango de salarios mínimos",css("--orange")],["C","No recibe ingresos",css("--aqua")],["D","No especificó",css("--yellow")]];
  document.getElementById("t-cal").textContent = "¿Quién declara su ingreso? "+(e?"Nacional vs. "+e.entidad:"Nacional");
  Plotly.react("cal", cfgG.map(([g,nm,c])=>({type:"bar",orientation:"h",name:nm,y:filas.map(f=>f[0]),x:filas.map(f=>f[1][g]),marker:{color:c,line:{color:css("--surface"),width:2}},
      text:filas.map(f=>f[1][g]>=7?fmt(f[1][g],0)+" %":""),textposition:"inside",insidetextfont:{color:g==="D"?"#0b0b0b":"#ffffff",size:11},hovertemplate:"%{y}<br>"+nm+": %{x:.1f} %<extra></extra>"})),
    Object.assign(base(),{barmode:"stack",legend:{orientation:"h",y:-.28,x:0,font:{size:10}},xaxis:ejes({range:[0,100],ticksuffix:" %"}),yaxis:ejes({showgrid:false,autorange:"reversed"}),margin:{l:110,r:14,t:8,b:84}}),cfg);
}

const COLS = [["entidad","Entidad",e=>e.entidad,0],["region","Región",e=>e.region,0],["til1","TIL1 (%)",e=>e.informalidad.til1_pct,1],["esc","Escolaridad (años)",e=>e.escolaridad.anios_medios_ocupados,1],
  ["med","Ingreso/hora ($)",e=>e.ingreso_hora.mediana_pesos,0],["ret","Rend. por año (%)",e=>e.rendimiento_escolaridad.pct_por_anio,1],["rho","Spearman",e=>e.correlacion_spearman.rho,2],
  ["bh","Brecha hora (%)",e=>e.brecha_genero.hora_pct,1],["bm","Brecha mes (%)",e=>e.brecha_genero.mensual_pct,1]];
let orden = ["entidad",1];
function tabla(){
  const th = document.querySelector("#tabla thead"), tb = document.querySelector("#tabla tbody");
  th.innerHTML = "<tr>"+COLS.map(c=>`<th data-k="${c[0]}">${c[1]}${orden[0]===c[0]?(orden[1]>0?" ▲":" ▼"):""}</th>`).join("")+"</tr>";
  const col = COLS.find(c=>c[0]===orden[0]), arr = E.slice().sort((a,b)=>{const x=col[2](a),y=col[2](b); return (typeof x==="string"?x.localeCompare(y,"es"):x-y)*orden[1];});
  tb.innerHTML = arr.map(e=>`<tr data-c="${e.cve_ent}" class="${e.cve_ent===sel?"sel":""}">`+COLS.map(c=>`<td>${c[3]===0&&typeof c[2](e)==="string"?c[2](e):fmt(c[2](e),c[3])}</td>`).join("")+"</tr>").join("");
  th.querySelectorAll("th").forEach(h=>h.onclick=()=>{ orden = orden[0]===h.dataset.k?[orden[0],-orden[1]]:[h.dataset.k,1]; tabla(); });
  tb.querySelectorAll("tr").forEach(r=>r.onclick=()=>seleccionar(+r.dataset.c));
}

function seleccionar(c){ sel = (sel===c) ? null : c; document.getElementById("ent").value = sel==null?"":String(sel); render(); }
function render(){
  kpis(); mapa(); ranking();
  dispersion("sc1", e=>e.escolaridad.anios_medios_ocupados, e=>e.informalidad.til1_pct, "Informalidad laboral (%)", "TIL1: %{y:.1f} %", {ticksuffix:" %"});
  dispersion("sc2", e=>e.escolaridad.anios_medios_muestra_salarial, e=>e.ingreso_hora.mediana_pesos, "Mediana del ingreso por hora ($)", "Mediana: $%{y:.0f}", {tickprefix:"$"});
  brecha(); calidad(); tabla();
  document.getElementById("doc").textContent = JSON.stringify(sel==null?{nota:"Elige una entidad para ver su documento"}:E.find(e=>e.cve_ent===sel),null,1);
}
document.getElementById("ent").innerHTML = '<option value="">Nacional (todas)</option>'+E.slice().sort((a,b)=>a.entidad.localeCompare(b.entidad,"es")).map(e=>`<option value="${e.cve_ent}">${e.entidad}</option>`).join("");
document.getElementById("ent").onchange = ev => { sel = ev.target.value===""?null:+ev.target.value; render(); };
const seg = document.getElementById("seg");
Object.entries(M).forEach(([k,m])=>{ const b=document.createElement("button"); b.textContent=m.n; b.setAttribute("aria-pressed",k===metrica); b.onclick=()=>{ metrica=k; seg.querySelectorAll("button").forEach(x=>x.setAttribute("aria-pressed",x===b)); render(); }; seg.appendChild(b); });
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);
render();
</script>
</body>
</html>
"""


def main() -> None:
    import plotly.offline

    d = datos()
    html = (PLANTILLA.replace("__PLOTLY__", plotly.offline.get_plotlyjs())
            .replace("__DATA__", json.dumps(d, ensure_ascii=False))
            .replace("__B__", str(d["meta"]["B"]))
            .replace("__NU__", f"{d['meta']['n_universo']:,}")
            .replace("__NS__", f"{d['meta']['n_salarial']:,}"))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(html, encoding="utf-8")
    print(f"Tablero escrito en {SALIDA} ({SALIDA.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
