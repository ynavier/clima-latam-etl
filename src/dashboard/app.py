"""
Clima LATAM — Dashboard Profesional
Glassmorphism · fondo solido · sin bordes de iframe visibles
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Clima LATAM", layout="wide", initial_sidebar_state="collapsed")

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Color unico de fondo — usado en la pagina Y en los iframes para que coincidan
PAGE_BG   = "#eef2ff"
CARD_BG   = "rgba(255,255,255,0.82)"
BLUR      = "blur(18px)"
BORDER    = "1px solid rgba(255,255,255,0.95)"
SHADOW    = "0 2px 20px rgba(99,102,241,0.09)"
SHADOW_LG = "0 4px 32px rgba(99,102,241,0.13)"

C = {
    "accent": "#6366f1", "accent2": "#818cf8",
    "hot":    "#f97316", "cold":    "#0ea5e9",
    "rain":   "#3b82f6", "wind":    "#8b5cf6",
    "green":  "#10b981", "yellow":  "#f59e0b", "red": "#ef4444",
    "text":   "#1e293b", "muted":   "#64748b", "dim": "#94a3b8",
    "grid":   "rgba(99,102,241,0.06)",
}

# CSS global
st.markdown(f"""
<style>
  html,body,
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],.main {{
    background:{PAGE_BG} !important;
    padding:0 !important; margin:0 !important; max-width:100% !important;
  }}
  .block-container {{
    padding:0 2.5rem !important; margin:0 auto !important; max-width:100% !important;
  }}
  /* Elimina todo espacio superior de Streamlit */
  [data-testid="stAppViewBlockContainer"] {{
    padding-top:0 !important;
  }}
  section[data-testid="stMain"] > div:first-child {{
    padding-top:0 !important;
  }}
  /* Eliminar TODA la UI nativa de Streamlit */
  [data-testid="stHeader"],
  [data-testid="stToolbar"],
  [data-testid="stDecoration"],
  [data-testid="stStatusWidget"],
  #MainMenu, header, footer {{ display:none !important; height:0 !important; }}

  /* Eliminar padding superior en todos los contenedores posibles */
  .stApp {{
    margin-top:0 !important;
    padding-top:0 !important;
  }}
  [data-testid="stAppViewContainer"] {{
    padding-top:0 !important;
    margin-top:0 !important;
  }}
  [data-testid="stAppViewBlockContainer"] {{
    padding-top:0 !important;
  }}
  [data-testid="stVerticalBlock"] > div:first-child {{
    margin-top:0 !important;
    padding-top:0 !important;
  }}
  iframe {{ border:none !important; display:block; background:{PAGE_BG} !important; }}

  /* ---------- Navbar ---------- */
  .navbar {{
    position:fixed; top:0; left:0; right:0; z-index:9999;
    display:flex; align-items:center; justify-content:space-between;
    padding:0 2.5rem; height:76px;
    background:{CARD_BG};
    backdrop-filter:{BLUR};
    -webkit-backdrop-filter:{BLUR};
    border-bottom:2px solid rgba(99,102,241,0.13);
    box-shadow:0 2px 24px rgba(99,102,241,0.08);
  }}
  .nav-brand {{ display:flex; align-items:center; gap:14px; }}
  .nav-dot {{
    width:12px; height:12px; border-radius:50%;
    background:{C['accent']};
    box-shadow:0 0 0 4px rgba(99,102,241,0.18);
    animation:pulse 2s ease-in-out infinite;
    flex-shrink:0;
  }}
  @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.35}} }}
  .nav-name {{ font-size:16px; font-weight:800; color:{C['text']};
               letter-spacing:.14em; text-transform:uppercase; }}
  .nav-sub  {{ font-size:10px; color:{C['muted']}; letter-spacing:.04em; margin-top:2px; }}
  .nav-stats {{ display:flex; gap:0; }}
  .nav-stat {{
    text-align:center; padding:0 28px;
    border-right:1px solid rgba(99,102,241,0.10);
  }}
  .nav-stat:last-child {{ border-right:none; }}
  .nav-val {{ font-size:24px; font-weight:700; color:{C['accent']};
              font-variant-numeric:tabular-nums; line-height:1; }}
  .nav-lbl {{ font-size:9px; color:{C['muted']};
              letter-spacing:.1em; text-transform:uppercase; margin-top:3px; }}
  .nav-right {{ display:flex; align-items:center; gap:8px; }}
  .badge {{
    font-size:9px; font-weight:600; letter-spacing:.07em;
    text-transform:uppercase; padding:5px 14px;
    border-radius:20px; border:1px solid; cursor:default; white-space:nowrap;
  }}
  .badge-accent {{ color:{C['accent']}; border-color:rgba(99,102,241,0.25);
                   background:rgba(99,102,241,0.07); }}
  .badge-green  {{ color:{C['green']};  border-color:rgba(16,185,129,0.25);
                   background:rgba(16,185,129,0.07);
                   display:flex; align-items:center; gap:5px; }}
  .badge-red    {{ color:{C['red']};    border-color:rgba(239,68,68,0.25);
                   background:rgba(239,68,68,0.07);
                   display:flex; align-items:center; gap:5px; }}
  .status-dot {{
    width:7px; height:7px; border-radius:50%;
    animation:pulse 1.5s ease-in-out infinite;
  }}
  .nav-date {{ font-size:10px; color:{C['muted']}; margin-right:6px; }}

  /* ---------- KPI cards ---------- */
  .kpi-row {{ display:grid; gap:10px; margin:12px 0 8px; }}
  .kpi {{
    background:{CARD_BG}; backdrop-filter:{BLUR};
    border:{BORDER}; border-radius:12px;
    padding:12px 16px 10px; position:relative; overflow:hidden;
    box-shadow:{SHADOW};
    animation:fadein .5s ease both;
  }}
  @keyframes fadein{{ from{{opacity:0;transform:translateY(8px)}} to{{opacity:1;transform:none}} }}
  .kpi:nth-child(1){{animation-delay:.05s}}
  .kpi:nth-child(2){{animation-delay:.10s}}
  .kpi:nth-child(3){{animation-delay:.15s}}
  .kpi:nth-child(4){{animation-delay:.20s}}
  .kpi:nth-child(5){{animation-delay:.25s}}
  .kpi::before {{
    content:''; position:absolute; top:0; left:0;
    width:3px; height:100%;
    background:var(--kc); border-radius:3px 0 0 3px;
  }}
  .kpi::after {{
    content:''; position:absolute; inset:0;
    background:radial-gradient(ellipse at top left,var(--kc-dim) 0%,transparent 55%);
    pointer-events:none;
  }}
  .kpi-lbl {{ font-size:8px; font-weight:700; color:{C['muted']};
               text-transform:uppercase; letter-spacing:.1em; margin-bottom:4px; }}
  .kpi-val {{ font-size:24px; font-weight:700; color:{C['text']};
               line-height:1; font-variant-numeric:tabular-nums; }}
  .kpi-unit{{ font-size:12px; color:{C['muted']}; margin-left:2px; }}
  .kpi-sub {{ font-size:9px; color:{C['dim']}; margin-top:3px; }}

  /* Gap entre KPIs y charts */
  .kpi-row {{ margin-bottom:10px !important; }}

  /* ---------- Section label ---------- */
  .sec {{ font-size:8.5px; font-weight:700; color:{C['muted']};
          text-transform:uppercase; letter-spacing:.12em;
          margin:18px 0 8px; padding-bottom:5px;
          border-bottom:1px solid rgba(99,102,241,0.10); }}

  /* ---------- Streamlit widget reset ---------- */
  .stTabs [data-baseweb="tab-list"] {{
    background:{CARD_BG}; backdrop-filter:{BLUR};
    border-bottom:1px solid rgba(99,102,241,0.12);
    padding:0 12px; gap:0;
  }}
  .stTabs [data-baseweb="tab"] {{
    color:{C['muted']}; font-size:11px; font-weight:600;
    letter-spacing:.1em; text-transform:uppercase;
    padding:11px 22px; border-radius:0;
  }}
  .stTabs [aria-selected="true"] {{
    background:transparent !important; color:{C['accent']} !important;
    border-bottom:2px solid {C['accent']} !important;
  }}
  /* ── Inputs: fondo claro forzado ── */
  [data-testid="stSelectbox"] > div > div,
  [data-testid="stSelectbox"] [data-baseweb="select"] > div,
  [data-baseweb="select"] > div:first-child,
  [data-testid="stDateInput"] input,
  [data-testid="stDateInput"] > div > div {{
    background:{CARD_BG} !important;
    color:{C['text']} !important;
    border:1px solid rgba(99,102,241,0.2) !important;
    border-radius:8px !important;
  }}
  /* Texto dentro de los inputs */
  [data-testid="stSelectbox"] span,
  [data-testid="stSelectbox"] p,
  [data-testid="stDateInput"] input {{
    color:{C['text']} !important;
  }}
  /* Dropdown menu */
  [data-baseweb="popover"] ul,
  [data-baseweb="popover"] [role="listbox"] {{
    background:white !important;
    border:1px solid rgba(99,102,241,0.15) !important;
    border-radius:10px !important;
  }}
  [data-baseweb="popover"] li:hover,
  [data-baseweb="menu-item"]:hover {{
    background:rgba(99,102,241,0.08) !important;
  }}
  /* ── Plotly charts con card glass ── */
  /* Apunta al contenedor padre del chart */
  div:has(> [data-testid="stPlotlyChart"]),
  div:has(> div > [data-testid="stPlotlyChart"]) {{
    background:{CARD_BG} !important;
    backdrop-filter:{BLUR} !important;
    -webkit-backdrop-filter:{BLUR} !important;
    border:{BORDER} !important;
    border-radius:14px !important;
    padding:10px 8px 6px !important;
    box-shadow:{SHADOW} !important;
    overflow:hidden !important;
  }}
  [data-testid="stPlotlyChart"] {{
    background:transparent !important;
    border:none !important;
    box-shadow:none !important;
    padding:0 !important;
  }}

  /* ── Dropdown popup claro ── */
  [data-baseweb="popover"] *,
  [data-baseweb="menu"] *,
  ul[role="listbox"],
  li[role="option"] {{
    background:white !important;
    color:{C['text']} !important;
  }}
  li[role="option"]:hover,
  li[role="option"][aria-selected="true"] {{
    background:rgba(99,102,241,0.1) !important;
    color:{C['accent']} !important;
  }}
  [data-baseweb="popover"] > div {{
    border:1px solid rgba(99,102,241,0.15) !important;
    border-radius:10px !important;
    box-shadow:0 8px 32px rgba(99,102,241,0.12) !important;
    overflow:hidden;
  }}

  /* ── Dataframe claro ── */
  [data-testid="stDataFrame"] {{
    border-radius:10px !important;
    overflow:hidden !important;
  }}

  /* ── Expander ── */
  [data-testid="stExpander"] {{
    background:{CARD_BG} !important;
    border:{BORDER} !important; border-radius:10px !important;
    box-shadow:{SHADOW} !important;
  }}
  [data-testid="stExpander"] summary,
  [data-testid="stExpander"] summary p {{
    color:{C['text']} !important;
    font-weight:600 !important;
  }}

  /* Clase inyectada por JS como fallback */
  .chart-card {{
    background:{CARD_BG} !important;
    backdrop-filter:{BLUR} !important;
    -webkit-backdrop-filter:{BLUR} !important;
    border:{BORDER} !important;
    border-radius:14px !important;
    padding:10px 8px 6px !important;
    box-shadow:{SHADOW} !important;
    overflow:hidden !important;
  }}
</style>
""", unsafe_allow_html=True)

# Script JS que aplica card glass a los charts (fallback para :has())
st.markdown("""
<script>
(function applyChartCards() {
  const G = "background:rgba(255,255,255,0.72);backdrop-filter:blur(18px);"
          + "-webkit-backdrop-filter:blur(18px);"
          + "border:1px solid rgba(255,255,255,0.95);"
          + "border-radius:14px;padding:10px 8px 6px;"
          + "box-shadow:0 2px 20px rgba(99,102,241,0.09);overflow:hidden;";
  function wrap() {
    document.querySelectorAll('[data-testid="stPlotlyChart"]').forEach(function(el) {
      var p = el.parentElement;
      if (p && !p.classList.contains('chart-card')) {
        p.classList.add('chart-card');
        p.setAttribute('style', G);
      }
    });
  }
  wrap();
  var obs = new MutationObserver(wrap);
  obs.observe(document.body, {childList: true, subtree: true});
})();
</script>
""", unsafe_allow_html=True)

# ── Datos ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    files = sorted(DATA_DIR.glob("clean/**/*.csv"))
    if not files: return pd.DataFrame()
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    return df

@st.cache_data(ttl=3600)
def load_reports() -> list[dict]:
    return [json.load(open(f, encoding="utf-8")) for f in sorted(DATA_DIR.glob("quality/*.json"))]

df      = load_data()
reports = load_reports()
if df.empty:
    st.warning("Sin datos. Ejecuta: python -m src.pipeline.extract.main")
    st.stop()

latest      = df["date"].max()
df_today    = df[df["date"] == latest].copy()
df_30d      = df[df["date"] >= latest - timedelta(days=30)].copy()
hottest     = df_today.loc[df_today["temperature_max"].idxmax()]
coldest     = df_today.loc[df_today["temperature_min"].idxmin()]
avg_temp    = round(df_today["temperature_mean"].mean(), 1)
rain_30d    = round(df_30d.groupby("city_name")["precipitation_sum"].sum().sum(), 0)
pipeline_ok = reports[-1]["overall_passed"] if reports else True
valid_rows  = reports[-1]["valid_rows"]  if reports else len(df)
total_rows  = reports[-1]["total_rows"]  if reports else len(df)
quality_pct = round(valid_rows / total_rows * 100, 1) if total_rows else 0

# ── NAVBAR (st.markdown — sin iframe) ────────────────────────────────────────
n_cities = df_today["city_name"].nunique()
s_class  = "badge-green" if pipeline_ok else "badge-red"
s_text   = "OPERACIONAL" if pipeline_ok else "ALERTA"
s_color  = C["green"] if pipeline_ok else C["red"]

st.markdown(f"""
<div style="height:76px;"></div>
<div class="navbar">
  <div class="nav-brand">
    <div class="nav-dot"></div>
    <div>
      <div class="nav-name">Clima LATAM</div>
      <div class="nav-sub">Sistema de Monitoreo Climatico · America Latina</div>
    </div>
  </div>
  <div class="nav-stats">
    <div class="nav-stat">
      <div class="nav-val">{n_cities}</div>
      <div class="nav-lbl">Ciudades</div>
    </div>
    <div class="nav-stat">
      <div class="nav-val">{avg_temp}</div>
      <div class="nav-lbl">Temp. Media °C</div>
    </div>
    <div class="nav-stat">
      <div class="nav-val">{quality_pct}</div>
      <div class="nav-lbl">Calidad %</div>
    </div>
    <div class="nav-stat">
      <div class="nav-val">{total_rows:,}</div>
      <div class="nav-lbl">Registros</div>
    </div>
  </div>
  <div class="nav-right">
    <span class="nav-date">{datetime.now().strftime("%A %d %b %Y")}</span>
    <span class="badge badge-accent">Pipeline ETL</span>
    <span class="badge badge-accent">BigQuery</span>
    <span class="badge badge-accent">dbt</span>
    <span class="badge {s_class}">
      <span class="status-dot" style="background:{s_color};box-shadow:0 0 6px {s_color};"></span>
      {s_text}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── KPI CARDS (st.markdown — sin iframe) ─────────────────────────────────────
def kpi_row(cards: list[dict]):
    parts = []
    for c in cards:
        color = c["color"]
        label = c["label"]
        value = c["value"]
        unit  = c.get("unit", "")
        sub   = c.get("sub", "")
        parts.append(
            f"<div class='kpi' style='--kc:{color};--kc-dim:{color}1a;'>"
            f"<div class='kpi-lbl'>{label}</div>"
            f"<div class='kpi-val'>{value}<span class='kpi-unit'>{unit}</span></div>"
            f"<div class='kpi-sub'>{sub}</div></div>"
        )
    cols = " ".join(parts)
    n = len(cards)
    st.markdown(
        f"<div class='kpi-row' style='grid-template-columns:repeat({n},1fr);'>{cols}</div>",
        unsafe_allow_html=True,
    )


# ── CONDITIONS PANEL (iframe con canvas) ─────────────────────────────────────
def render_conditions(row: pd.Series, height: int = 370):
    temp = float(row["temperature_mean"])
    hum  = float(row.get("humidity_mean", 60))
    wind = float(row["wind_speed_max"])
    uv   = float(row["uv_index_max"])

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:{PAGE_BG};font-family:'Segoe UI',system-ui,sans-serif;
  padding:0;overflow:hidden;height:{height}px;}}
.panel{{
  background:{CARD_BG};backdrop-filter:{BLUR};
  border:{BORDER};border-radius:12px;padding:16px;
  box-shadow:{SHADOW_LG};height:{height}px;overflow:hidden;
  display:flex;flex-direction:column;
}}
.cname{{font-size:15px;font-weight:700;color:{C['text']};text-align:center;}}
.csub{{font-size:9px;color:{C['muted']};text-transform:uppercase;
  letter-spacing:.08em;margin-bottom:8px;text-align:center;}}
.temp{{font-size:44px;font-weight:700;color:{C['accent']};line-height:1;
  font-variant-numeric:tabular-nums;text-align:center;}}
.tdesc{{font-size:10px;color:{C['muted']};margin:4px 0 0;text-align:center;}}
/* Cruz divisoria */
.cross-wrap{{
  flex:1;display:grid;
  grid-template-columns:1fr 1fr;
  grid-template-rows:1fr 1fr;
  margin-top:14px;
  position:relative;
}}
/* Linea horizontal de la cruz */
.cross-wrap::before{{
  content:'';position:absolute;
  left:12px;right:12px;
  top:50%;transform:translateY(-50%);
  height:1px;
  background:linear-gradient(90deg,transparent,rgba(99,102,241,0.18),rgba(99,102,241,0.18),transparent);
  z-index:1;
}}
/* Linea vertical de la cruz */
.cross-wrap::after{{
  content:'';position:absolute;
  top:12px;bottom:12px;
  left:50%;transform:translateX(-50%);
  width:1px;
  background:linear-gradient(180deg,transparent,rgba(99,102,241,0.18),rgba(99,102,241,0.18),transparent);
  z-index:1;
}}
.g{{
  display:flex;flex-direction:column;align-items:center;
  justify-content:center;padding:12px 8px;
}}
canvas{{display:block;}}
.gl{{font-size:8px;color:{C['muted']};text-transform:uppercase;
  letter-spacing:.1em;margin-top:5px;}}
.gv{{font-size:14px;font-weight:700;color:{C['text']};margin-top:2px;}}
</style></head><body>
<div class="panel">
  <div class="cname">{row['city_name']}</div>
  <div class="csub">{row['country']} · datos de hoy</div>
  <div class="temp" id="tv">--</div>
  <div class="tdesc">{row['weather_description']}</div>
  <div class="cross-wrap">
    <div class="g"><canvas id="gh" width="110" height="110"></canvas>
      <div class="gl">Humedad</div><div class="gv" id="vh">--</div></div>
    <div class="g"><canvas id="gw" width="110" height="110"></canvas>
      <div class="gl">Viento</div><div class="gv" id="vw">--</div></div>
    <div class="g"><canvas id="gu" width="110" height="110"></canvas>
      <div class="gl">UV</div><div class="gv" id="vu">--</div></div>
    <div class="g"><canvas id="gp" width="110" height="110"></canvas>
      <div class="gl">Lluvia hoy</div><div class="gv" id="vp">--</div></div>
  </div>
</div>
<script>
function arc(id,val,max,color){{
  var c=document.getElementById(id);if(!c)return;
  var s=110,cx=55,cy=55,r=36;          /* radio pequeño = margen 19px para el glow */
  var ctx=c.getContext('2d');
  ctx.clearRect(0,0,s,s);
  /* Track */
  ctx.beginPath();ctx.arc(cx,cy,r,.75*Math.PI,2.25*Math.PI);
  ctx.strokeStyle='rgba(99,102,241,0.09)';ctx.lineWidth=6;ctx.lineCap='round';ctx.stroke();
  if(val>0){{
    var e=.75*Math.PI+Math.min(val/max,1)*1.5*Math.PI;
    /* Glow layer — blur holgado, trazo fino */
    ctx.save();
    ctx.beginPath();ctx.arc(cx,cy,r,.75*Math.PI,e);
    ctx.strokeStyle=color;ctx.lineWidth=4;ctx.lineCap='round';
    ctx.shadowBlur=22;ctx.shadowColor=color;ctx.stroke();
    ctx.restore();
    /* Trazo limpio encima */
    ctx.beginPath();ctx.arc(cx,cy,r,.75*Math.PI,e);
    ctx.strokeStyle=color;ctx.lineWidth=4;ctx.lineCap='round';
    ctx.shadowBlur=0;ctx.stroke();
  }}
}}
var o={{t:0,h:0,w:0,u:0,p:{float(row.get('precipitation_sum',0))}}};
var tgt={{t:{temp},h:{hum},w:{wind},u:{uv},p:{float(row.get('precipitation_sum',0))}}};
gsap.to(o,{{...tgt,duration:1.3,ease:'power2.out',
  onUpdate:function(){{
    document.getElementById('tv').textContent=o.t.toFixed(1)+'°C';
    document.getElementById('vh').textContent=Math.round(o.h)+'%';
    document.getElementById('vw').textContent=Math.round(o.w)+' km/h';
    document.getElementById('vu').textContent=o.u.toFixed(1);
    document.getElementById('vp').textContent=o.p.toFixed(1)+' mm';
    arc('gh',o.h,100,'{C["cold"]}');
    arc('gw',o.w,120,'{C["wind"]}');
    arc('gu',o.u,12, '{C["yellow"]}');
    arc('gp',o.p,50, '{C["rain"]}');
  }}
}});
</script></body></html>"""
    components.html(html, height=height, scrolling=False)


# ── Plotly helpers ────────────────────────────────────────────────────────────
AX = dict(gridcolor=C["grid"], zerolinecolor=C["grid"],
          tickfont=dict(color=C["dim"], size=9), showgrid=True)
CFG = {"displayModeBar": False}

def base_layout(h: int, extra: dict = {}) -> dict:
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor":  "rgba(255,255,255,0.55)",
        "font":   dict(color=C["muted"], size=10, family="Segoe UI"),
        "margin": dict(l=8, r=8, t=28, b=8),
        "height": h,
        "hoverlabel": dict(bgcolor="rgba(255,255,255,0.95)",
                           font=dict(color=C["text"], size=11),
                           bordercolor="rgba(99,102,241,0.15)"),
        **extra,
    }


def fig_map(data: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lat=data["latitude"], lon=data["longitude"],
        text=data["city_name"],
        customdata=data[["temperature_max","temperature_min",
                          "precipitation_sum","weather_description","country"]].values,
        hovertemplate=(
            "<b>%{text}</b> · %{customdata[4]}<br>"
            "Max %{customdata[0]:.1f}°C / Min %{customdata[1]:.1f}°C<br>"
            "Lluvia %{customdata[2]:.1f} mm · %{customdata[3]}<extra></extra>"
        ),
        marker=dict(
            color=data["temperature_mean"],
            colorscale=[[0,"#38bdf8"],[.38,"#818cf8"],[.65,"#f97316"],[1,"#dc2626"]],
            cmin=data["temperature_mean"].min(),
            cmax=data["temperature_mean"].max(),
            size=11, sizemode="diameter",
            colorbar=dict(
                title=dict(text="°C", font=dict(color=C["muted"],size=10)),
                tickfont=dict(color=C["dim"],size=9),
                thickness=8, len=.7, x=1.01,
                bgcolor="rgba(255,255,255,0.6)",
                bordercolor="rgba(99,102,241,0.15)",
            ),
            line=dict(width=1.5, color="white"),
            opacity=.88,
        ),
        mode="markers",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=40, t=0, b=0),
        height=390,
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.95)",
                        font=dict(color=C["text"], size=11),
                        bordercolor="rgba(99,102,241,0.15)"),
        geo=dict(
            showland=True,      landcolor="#e8edf5",
            showocean=True,     oceancolor="#dbeafe",
            showcountries=True, countrycolor="#c8d3e8",
            showframe=False,    bgcolor="rgba(0,0,0,0)",
            showlakes=True,     lakecolor="#dbeafe",
            scope="world",
            lataxis_range=[-58, 34],
            lonaxis_range=[-119, -32],
            projection=dict(type="natural earth", scale=1.0),
        ),
    )
    return fig


def fig_bar(data: pd.DataFrame, x: str, y: str, cs: list, title: str, h: int = 200) -> go.Figure:
    r, g, b = 0, 0, 0
    base_c = cs[-1][1]
    try:
        r = int(base_c[1:3],16); g = int(base_c[3:5],16); b_val = int(base_c[5:7],16)
    except Exception:
        pass
    fig = go.Figure(go.Bar(
        x=data[x], y=data[y],
        marker=dict(color=data[y], colorscale=cs, line=dict(width=0), opacity=.82),
        hovertemplate="%{x}: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(**base_layout(h, {
        "title":      dict(text=title, font=dict(color=C["muted"],size=10), x=0),
        "bargap":     .28,
        "showlegend": False,
        "xaxis": {**AX, "showgrid": False,
                  "tickangle": -35, "tickfont": dict(color=C["dim"],size=8)},
        "yaxis": dict(**AX),
    }))
    return fig


def fig_area(data: pd.DataFrame, x: str, y: str, color: str,
             title: str, h: int = 200, **_) -> go.Figure:
    r, g, b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
    fig = go.Figure(go.Scatter(
        x=data[x], y=data[y], mode="lines", fill="tozeroy",
        line=dict(color=color, width=2),
        fillcolor=f"rgba({r},{g},{b},0.09)",
        hovertemplate="%{x|%d %b}: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(**base_layout(h, {
        "title":      dict(text=title, font=dict(color=C["muted"],size=10), x=0),
        "showlegend": False,
        "xaxis": {**AX, "showgrid": False},
        "yaxis": dict(**AX),
    }))
    return fig


def fig_trend(city_df: pd.DataFrame, h: int = 230) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=city_df["date"], y=city_df["temperature_max"], name="Max",
        mode="lines", line=dict(color=C["hot"],width=2),
        hovertemplate="%{x|%d %b}: %{y:.1f}°C<extra>Max</extra>"))
    fig.add_trace(go.Scatter(
        x=city_df["date"], y=city_df["temperature_min"], name="Min",
        mode="lines", line=dict(color=C["cold"],width=2),
        fill="tonexty", fillcolor="rgba(14,165,233,0.07)",
        hovertemplate="%{x|%d %b}: %{y:.1f}°C<extra>Min</extra>"))
    fig.add_trace(go.Scatter(
        x=city_df["date"], y=city_df["temperature_mean"], name="Media",
        mode="lines", line=dict(color=C["accent"],width=1.5,dash="dot"),
        hovertemplate="%{x|%d %b}: %{y:.1f}°C<extra>Media</extra>"))
    fig.update_layout(**base_layout(h, {
        "title": dict(text="Temperatura",
                      font=dict(color=C["muted"],size=10), x=0),
        "xaxis": {**AX, "showgrid": False},
        "yaxis": {**AX, "title": dict(text="°C", font=dict(color=C["dim"],size=9))},
        "legend": dict(
            orientation="v",
            x=1, y=1, xanchor="right", yanchor="top",
            font=dict(color=C["muted"], size=9),
            bgcolor="rgba(255,255,255,0.6)",
            bordercolor="rgba(99,102,241,0.1)",
            borderwidth=1,
        ),
        "hovermode": "x unified",
    }))
    return fig


def glass_chart(fig: go.Figure, height: int = 230) -> None:
    """
    Renderiza un Plotly figure dentro de una glass card.
    height = altura exacta del chart de Plotly.
    La card añade padding sin recortar el chart.
    """
    PAD_TOP, PAD_BOT, PAD_X = 10, 8, 6
    card_h  = height + PAD_TOP + PAD_BOT   # card total
    iframe_h = card_h + 10                  # iframe = card + margen inferior

    inner = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs="cdn",
        config={"displayModeBar": False, "responsive": True},
    )
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:{PAGE_BG};overflow:hidden;height:{iframe_h}px;}}
.card{{
  background:rgba(255,255,255,0.72);
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
  border:1px solid rgba(255,255,255,0.95);
  border-radius:14px;
  padding:{PAD_TOP}px {PAD_X}px {PAD_BOT}px;
  box-shadow:0 2px 20px rgba(99,102,241,0.09);
  overflow:hidden;
  height:{card_h}px;
}}
</style></head><body>
<div class="card">{inner}</div>
</body></html>"""
    components.html(html, height=iframe_h, scrolling=False)


# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["MONITOR GLOBAL", "ANALISIS POR CIUDAD", "PIPELINE // CALIDAD"])

# ══ TAB 1 ════════════════════════════════════════════════════════════════════
with tab1:
    # ── Preparar datos para el componente HTML ──────────────────────────────
    sidebar_cities = []
    for _, r2 in df_today.sort_values("temperature_mean", ascending=False).head(8).iterrows():
        sidebar_cities.append({
            "name":      str(r2["city_name"]),
            "country":   str(r2["country_code"]),
            "temp":      round(float(r2["temperature_mean"]), 1),
            "condition": str(r2["weather_description"]),
            "rain":      round(float(r2["precipitation_sum"]), 1),
            "lon":       round(float(r2["longitude"]), 2),
            "lat":       round(float(r2["latitude"]), 2),
        })

    trend_city_name = str(hottest["city_name"])
    df_trend = df[df["city_name"] == trend_city_name].sort_values("date").tail(8)
    trend_dates, trend_max, trend_min, trend_mean, trend_rain = [], [], [], [], []
    forecast_cards = []
    for _, r2 in df_trend.iterrows():
        d = r2["date"].strftime("%d %b")
        trend_dates.append(d)
        trend_max.append(round(float(r2["temperature_max"]), 1))
        trend_min.append(round(float(r2["temperature_min"]), 1))
        trend_mean.append(round(float(r2["temperature_mean"]), 1))
        trend_rain.append(round(float(r2["precipitation_sum"]), 1))
        forecast_cards.append({
            "date":      d,
            "temp_max":  round(float(r2["temperature_max"]), 1),
            "temp_min":  round(float(r2["temperature_min"]), 1),
            "condition": str(r2["weather_description"]),
            "rain":      round(float(r2["precipitation_sum"]), 1),
        })

    sel = hottest
    sel_temp   = round(float(sel["temperature_mean"]), 1)
    sel_max    = round(float(sel["temperature_max"]), 1)
    sel_min    = round(float(sel["temperature_min"]), 1)
    sel_hum    = round(float(sel.get("humidity_mean", 60)), 0)
    sel_wind   = round(float(sel["wind_speed_max"]), 0)
    sel_uv     = round(float(sel["uv_index_max"]), 1)
    sel_rain   = round(float(sel["precipitation_sum"]), 1)
    sel_name   = str(sel["city_name"])
    sel_cntry  = str(sel["country"])
    sel_cond   = str(sel["weather_description"])

    # Datos de lluvia y viento para panel derecho (top 6 paises)
    rain_countries = (df_30d.groupby("country")["precipitation_sum"]
                      .sum().nlargest(6).reset_index())
    rain_max_val = float(rain_countries["precipitation_sum"].max()) or 1
    right_rain = []
    for _, r2 in rain_countries.iterrows():
        right_rain.append({
            "name": str(r2["country"]),
            "val":  round(float(r2["precipitation_sum"]), 0),
            "pct":  round(float(r2["precipitation_sum"]) / rain_max_val * 100, 0),
        })

    # JSON para JS (sin backslashes en f-string)
    sc_json  = json.dumps(sidebar_cities)
    td_json  = json.dumps(trend_dates)
    tmx_json = json.dumps(trend_max)
    tmn_json = json.dumps(trend_min)
    tmean_json = json.dumps(trend_mean)
    train_json = json.dumps(trend_rain)
    fc_json    = json.dumps(forecast_cards)
    rr_json    = json.dumps(right_rain)

    # Datos del globo — todas las ciudades de hoy
    globe_lats, globe_lons, globe_temps, globe_names = [], [], [], []
    for _, r2 in df_today.iterrows():
        globe_lats.append(round(float(r2["latitude"]), 4))
        globe_lons.append(round(float(r2["longitude"]), 4))
        globe_temps.append(round(float(r2["temperature_mean"]), 1))
        globe_names.append(str(r2["city_name"]) + ", " + str(r2["country"]))
    g_lats_json  = json.dumps(globe_lats)
    g_lons_json  = json.dumps(globe_lons)
    g_temps_json = json.dumps(globe_temps)
    g_names_json = json.dumps(globe_names)
    g_tmin = round(float(df_today["temperature_mean"].min()), 1)
    g_tmax = round(float(df_today["temperature_mean"].max()), 1)

    # Choropleth: temperatura media por pais en ISO-3
    ISO2_TO_ISO3 = {
        'MX':'MEX','GT':'GTM','SV':'SLV','HN':'HND','NI':'NIC','CR':'CRI',
        'PA':'PAN','CO':'COL','VE':'VEN','EC':'ECU','PE':'PER','BO':'BOL',
        'CL':'CHL','AR':'ARG','PY':'PRY','UY':'URY','BR':'BRA','CU':'CUB',
        'DO':'DOM','PR':'PRI','HT':'HTI','JM':'JAM',
    }
    ctry_temp = (df_today.groupby("country_code")["temperature_mean"]
                 .mean().reset_index())
    ctry_temp["iso3"] = ctry_temp["country_code"].map(ISO2_TO_ISO3)
    ctry_temp = ctry_temp.dropna(subset=["iso3"])
    cho_iso3  = json.dumps(ctry_temp["iso3"].tolist())
    cho_temps = json.dumps([round(float(v),1) for v in ctry_temp["temperature_mean"]])

    G = "background:rgba(255,255,255,0.72);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,0.95);border-radius:14px;box-shadow:0 2px 20px rgba(99,102,241,0.09);"
    latest_str = latest.strftime('%A %d %b %Y')

    html_tab1 = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:{PAGE_BG};font-family:'Segoe UI',system-ui,sans-serif;padding:12px;overflow-x:hidden;}}

/* ── Grid: 2 filas — GLOBO primero ── */
.dash{{display:grid;grid-template-columns:210px 1fr 260px;grid-template-rows:auto auto;gap:12px;}}
.panel{{{G} padding:16px;overflow:hidden;opacity:0;transform:translateY(8px);}}
.lbl{{font-size:8.5px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;}}

/* FILA 1: sidebar | globo | nav */
.sidebar    {{grid-column:1;grid-row:1;}}
.globepanel {{{G} grid-column:2;grid-row:1;padding:14px;overflow:hidden;opacity:0;transform:translateY(8px);}}
.navpanel   {{{G} grid-column:3;grid-row:1;padding:0;overflow:hidden;opacity:0;transform:translateY(8px);display:flex;flex-direction:column;}}

/* FILA 2: ciudad | trend+hist | condiciones */
.citycard{{grid-column:1;grid-row:2;}}
.midcol  {{grid-column:2;grid-row:2;display:flex;flex-direction:column;gap:10px;
           background:none!important;border:none!important;box-shadow:none!important;
           backdrop-filter:none!important;padding:0!important;opacity:1!important;transform:none!important;}}
.midcol .panel{{opacity:0;transform:translateY(8px);}}
.rightcol{{grid-column:3;grid-row:2;display:flex;flex-direction:column;gap:10px;
           background:none!important;border:none!important;box-shadow:none!important;
           backdrop-filter:none!important;padding:0!important;opacity:1!important;transform:none!important;}}
.rightcol .panel{{opacity:0;transform:translateY(8px);}}
.navtop{{padding:14px 14px 8px;border-bottom:1px solid rgba(99,102,241,0.08);}}
.navlist{{flex:1;overflow-y:auto;padding:6px 8px 8px;}}
.navlist::-webkit-scrollbar{{width:3px;}}
.navlist::-webkit-scrollbar-track{{background:transparent;}}
.navlist::-webkit-scrollbar-thumb{{background:rgba(99,102,241,0.2);border-radius:2px;}}
.nitem{{
  display:flex;align-items:center;justify-content:space-between;
  padding:7px 10px;border-radius:8px;cursor:pointer;
  transition:all .18s;border:1px solid transparent;margin-bottom:2px;
}}
.nitem:hover{{background:rgba(99,102,241,0.08);border-color:rgba(99,102,241,0.15);}}
.nitem.act{{background:rgba(99,102,241,0.12);border-color:rgba(99,102,241,0.22);}}
.nn{{font-size:11px;font-weight:600;color:#1e293b;}}
.nc{{font-size:8.5px;color:#94a3b8;margin-top:1px;}}
.nt{{font-size:14px;font-weight:700;color:#6366f1;}}
.nco{{font-size:8px;color:{C['hot']};}}
.resetbtn{{
  margin:8px 14px 10px;padding:7px 12px;
  background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
  border-radius:8px;font-size:9px;font-weight:600;color:#6366f1;
  cursor:pointer;text-align:center;letter-spacing:.06em;
  transition:background .18s;
}}
.resetbtn:hover{{background:rgba(99,102,241,0.14);}}

/* Sidebar ciudades */
.ci{{display:flex;align-items:center;justify-content:space-between;
  padding:8px 10px;border-radius:9px;cursor:pointer;
  transition:background .18s;border:1px solid transparent;margin-bottom:3px;}}
.ci:hover{{background:rgba(99,102,241,0.08);border-color:rgba(99,102,241,0.15);}}
.ci.act{{background:rgba(99,102,241,0.11);border-color:rgba(99,102,241,0.22);}}
.cin{{font-size:11.5px;font-weight:600;color:#1e293b;}}
.cic{{font-size:9px;color:#94a3b8;margin-top:1px;}}
.cit{{font-size:15px;font-weight:700;color:#6366f1;text-align:right;}}
.cir{{font-size:8.5px;color:#3b82f6;text-align:right;margin-top:1px;}}

/* Ciudad principal */
.mcc{{font-size:22px;font-weight:800;color:#1e293b;}}
.mcs{{font-size:9.5px;color:#94a3b8;margin-bottom:10px;}}
.mct{{font-size:64px;font-weight:700;color:#6366f1;line-height:1;font-variant-numeric:tabular-nums;}}
.mcu{{font-size:23px;color:#94a3b8;vertical-align:top;margin-top:10px;display:inline-block;}}
.mcco{{font-size:12px;color:#64748b;margin:4px 0 10px;}}
.mchl{{display:flex;gap:14px;margin-bottom:12px;}}
.mchl span{{font-size:11.5px;font-weight:600;}}
.hot{{color:#f97316;}} .cold{{color:#0ea5e9;}}
.srow{{display:grid;grid-template-columns:1fr 1fr;gap:6px;}}
.sb{{background:rgba(99,102,241,0.06);border-radius:9px;padding:8px 10px;}}
.sbv{{font-size:16px;font-weight:700;color:#1e293b;}}
.sbl{{font-size:8px;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em;margin-top:2px;}}

/* Condiciones y barras */
.cg{{display:grid;grid-template-columns:1fr 1fr;gap:7px;}}
.ci2{{background:rgba(99,102,241,0.05);border-radius:9px;padding:11px;}}
.cv{{font-size:19px;font-weight:700;color:#1e293b;}}
.cl{{font-size:8px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-top:2px;}}
.pw{{margin-bottom:7px;}}
.pr{{display:flex;justify-content:space-between;font-size:9.5px;color:#64748b;margin-bottom:3px;}}
.pb{{height:5px;background:rgba(99,102,241,0.1);border-radius:3px;overflow:hidden;}}
.pf{{height:100%;border-radius:3px;}}

/* Historico */
.fc{{display:flex;align-items:center;gap:6px;padding:7px 10px;
  background:rgba(99,102,241,0.04);border-radius:7px;
  border:1px solid rgba(99,102,241,0.07);margin-bottom:4px;}}
.fd{{font-size:9.5px;font-weight:600;color:#64748b;min-width:42px;}}
.fcd{{font-size:9px;color:#94a3b8;flex:1;}}
.fmx{{font-size:11.5px;font-weight:700;color:#f97316;}}
.fmn{{font-size:11.5px;font-weight:600;color:#0ea5e9;margin-left:4px;}}
.fr{{font-size:8.5px;color:#3b82f6;min-width:32px;text-align:right;}}
</style></head><body>
<div class="dash">

  <!-- F1 COL1: SIDEBAR -->
  <div class="panel sidebar">
    <div class="lbl">Ciudades · hoy</div>
    <div id="clist" style="overflow-y:auto;max-height:380px;"></div>
  </div>

  <!-- F1 COL2: GLOBO (lo primero que ve el usuario) -->
  <div class="globepanel">
    <div class="lbl">Temperatura por zonas · arrastra para rotar · scroll para zoom</div>
    <div id="globe" style="width:100%;height:370px;"></div>
  </div>

  <!-- F1 COL3: NAV GLOBO -->
  <div class="navpanel">
    <div class="navtop">
      <div class="lbl" style="margin-bottom:4px;">Navegar al lugar</div>
      <div class="resetbtn" id="resetbtn">Vista LATAM</div>
    </div>
    <div class="navlist" id="navlist"></div>
  </div>

  <!-- F2 COL1: CIUDAD -->
  <div class="panel citycard">
    <div class="mcc">{sel_name}</div>
    <div class="mcs">{sel_cntry} &nbsp;·&nbsp; {latest_str}</div>
    <span class="mct" id="mct">--</span><span class="mcu">°C</span>
    <div class="mcco">{sel_cond}</div>
    <div class="mchl">
      <span class="hot">Max {sel_max}°C</span>
      <span class="cold">Min {sel_min}°C</span>
    </div>
    <div class="srow">
      <div class="sb"><div class="sbv" id="sh">--</div><div class="sbl">Humedad %</div></div>
      <div class="sb"><div class="sbv" id="sw">--</div><div class="sbl">Viento km/h</div></div>
      <div class="sb"><div class="sbv" id="su">--</div><div class="sbl">UV</div></div>
      <div class="sb"><div class="sbv" id="sr">--</div><div class="sbl">Lluvia mm</div></div>
    </div>
  </div>

  <!-- F2 COL2: TREND + HISTORICO -->
  <div class="midcol">
    <div class="panel">
      <div class="lbl">Tendencia · {trend_city_name}</div>
      <div id="trend" style="width:100%;height:185px;"></div>
    </div>
    <div class="panel" style="flex:1;">
      <div class="lbl">Historico reciente · {trend_city_name}</div>
      <div id="hlist" style="overflow-y:auto;max-height:240px;"></div>
    </div>
  </div>

  <!-- F2 COL3: CONDICIONES + LLUVIA -->
  <div class="rightcol">
    <div class="panel">
      <div class="lbl">Condiciones · {sel_name}</div>
      <div class="cg">
        <div class="ci2"><div class="cv" id="ch">--</div><div class="cl">Humedad</div></div>
        <div class="ci2"><div class="cv" id="cu">--</div><div class="cl">UV</div></div>
        <div class="ci2"><div class="cv" id="cw">--</div><div class="cl">Viento</div></div>
        <div class="ci2"><div class="cv" id="cr">--</div><div class="cl">Lluvia</div></div>
      </div>
    </div>
    <div class="panel" style="flex:1;">
      <div class="lbl">Lluvia acumulada · 30 dias</div>
      <div id="rbars"></div>
    </div>
  </div>

</div>
<script>
var cities={sc_json},forecast={fc_json},rain={rr_json};
var tdates={td_json},tmax2={tmx_json},tmin2={tmn_json},tmean2={tmean_json};
var choIso={cho_iso3},choT={cho_temps};
var glats={g_lats_json},glons={g_lons_json},gtemps={g_temps_json},gnames={g_names_json};
var gtmin={g_tmin},gtmax={g_tmax};
var sel_t={sel_temp},sel_h={sel_hum},sel_w={sel_wind},sel_u={sel_uv},sel_r={sel_rain};
// Full city data for navigation (all today cities)
var allCities={sc_json};

// ── Sidebar ──
var cl=document.getElementById('clist');
cities.forEach(function(c,i){{
  var d=document.createElement('div');
  d.className='ci'+(i===0?' act':'');
  d.innerHTML='<div><div class="cin">'+c.name+'</div><div class="cic">'+c.condition+'</div></div>'+
    '<div><div class="cit">'+c.temp+'°</div><div class="cir">'+c.rain+' mm</div></div>';
  cl.appendChild(d);
}});

// ── Rain bars ──
var rb=document.getElementById('rbars');
rain.forEach(function(r){{
  var d=document.createElement('div');d.className='pw';
  d.innerHTML='<div class="pr"><span>'+r.name+'</span><span>'+r.val+' mm</span></div>'+
    '<div class="pb"><div class="pf" style="width:0%;background:linear-gradient(90deg,#93c5fd,#3b82f6);" data-p="'+r.pct+'%"></div></div>';
  rb.appendChild(d);
}});

// ── Historico ──
var hl=document.getElementById('hlist');
forecast.forEach(function(f){{
  var d=document.createElement('div');d.className='fc';
  d.innerHTML='<div class="fd">'+f.date+'</div><div class="fcd">'+f.condition+'</div>'+
    '<span class="fmx">'+f.temp_max+'°</span><span class="fmn">'+f.temp_min+'°</span>'+
    '<div class="fr">'+f.rain+' mm</div>';
  hl.appendChild(d);
}});

// ── Globe ──
var cs=[[0,'#38bdf8'],[0.28,'#818cf8'],[0.55,'#f59e0b'],[0.78,'#f97316'],[1,'#dc2626']];
var initRot={{lon:-65,lat:-10,roll:0}};
var gLayout={{
  paper_bgcolor:'rgba(255,255,255,0)',
  plot_bgcolor:'rgba(255,255,255,0)',
  margin:{{l:0,r:55,t:0,b:0}},height:370,
  geo:{{
    projection:{{type:'orthographic',rotation:initRot}},
    showland:true,landcolor:'#e8edf5',
    showocean:true,oceancolor:'#dbeafe',
    showcountries:true,countrycolor:'#c8d3e8',
    showframe:false,
    bgcolor:'rgba(255,255,255,0)',
    showlakes:true,lakecolor:'#dbeafe',
    showcoastlines:true,coastlinecolor:'#b0bdd4',
  }},
  font:{{family:'Segoe UI',size:10,color:'#64748b'}},
  hoverlabel:{{bgcolor:'rgba(255,255,255,0.95)',font:{{color:'#1e293b',size:11}},bordercolor:'rgba(99,102,241,0.2)'}},
  transition:{{duration:600,easing:'cubic-in-out'}},
}};
Plotly.newPlot('globe',[
  {{type:'choropleth',locations:choIso,z:choT,colorscale:cs,zmin:gtmin,zmax:gtmax,
    showscale:true,
    colorbar:{{title:{{text:'°C',font:{{size:10,color:'#64748b'}}}},tickfont:{{size:9,color:'#94a3b8'}},
      thickness:8,len:.65,x:1.01,bgcolor:'rgba(255,255,255,0.5)',bordercolor:'rgba(99,102,241,0.1)'}},
    marker:{{line:{{color:'rgba(255,255,255,0.8)',width:0.8}}}},
    hovertemplate:'<b>%{{location}}</b><br>%{{z:.1f}}°C<extra></extra>'}},
  {{type:'scattergeo',lat:glats,lon:glons,text:gnames,customdata:gtemps,
    mode:'markers',
    marker:{{size:5,color:'rgba(255,255,255,0.8)',line:{{color:'rgba(100,116,139,0.5)',width:1}}}},
    hovertemplate:'<b>%{{text}}</b><br>%{{customdata:.1f}}°C<extra></extra>'}},
],gLayout,{{displayModeBar:false,responsive:true,scrollZoom:true}});

// Smooth fly-to function
function flyTo(lon,lat,scale){{
  Plotly.animate('globe',
    {{layout:{{'geo.projection.rotation':{{lon:lon,lat:lat,roll:0}},'geo.projection.scale':scale||1}}}},
    {{transition:{{duration:700,easing:'cubic-in-out'}},frame:{{duration:700,redraw:false}}}}
  );
}}

// ── Nav list (all sidebar cities) ──
var nl=document.getElementById('navlist');
cities.forEach(function(c,i){{
  var d=document.createElement('div');
  d.className='nitem'+(i===0?' act':'');
  d.dataset.lon=c.lon||0; d.dataset.lat=c.lat||0;
  d.innerHTML='<div><div class="nn">'+c.name+'</div><div class="nc">'+c.country+'</div></div>'+
    '<div style="text-align:right"><div class="nt">'+c.temp+'°</div></div>';
  d.onclick=function(){{
    document.querySelectorAll('.nitem').forEach(function(x){{x.classList.remove('act');}});
    d.classList.add('act');
    flyTo(c.lon||0,c.lat||0,2.8);
  }};
  nl.appendChild(d);
}});
document.getElementById('resetbtn').onclick=function(){{
  document.querySelectorAll('.nitem').forEach(function(x){{x.classList.remove('act');}});
  flyTo(-65,-10,1);
}};

// ── Trend ──
Plotly.newPlot('trend',[
  {{x:tdates,y:tmax2,name:'Max',mode:'lines',line:{{color:'#f97316',width:2}},hovertemplate:'%{{y:.1f}}°C<extra>Max</extra>'}},
  {{x:tdates,y:tmin2,name:'Min',mode:'lines',line:{{color:'#0ea5e9',width:2}},fill:'tonexty',fillcolor:'rgba(14,165,233,0.07)',hovertemplate:'%{{y:.1f}}°C<extra>Min</extra>'}},
  {{x:tdates,y:tmean2,name:'Media',mode:'lines',line:{{color:'#6366f1',width:1.5,dash:'dot'}},hovertemplate:'%{{y:.1f}}°C<extra>Media</extra>'}},
],{{
  paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(255,255,255,0.5)',
  margin:{{l:36,r:10,t:8,b:30}},height:195,
  showlegend:true,legend:{{orientation:'h',x:0,y:1.15,font:{{size:10,color:'#64748b'}}}},
  xaxis:{{gridcolor:'rgba(99,102,241,0.07)',tickfont:{{size:9,color:'#94a3b8'}},showgrid:false}},
  yaxis:{{gridcolor:'rgba(99,102,241,0.07)',tickfont:{{size:9,color:'#94a3b8'}},title:'°C'}},
  hovermode:'x unified',font:{{family:'Segoe UI',size:10,color:'#64748b'}},
}},{{displayModeBar:false,responsive:true}});

// ── GSAP ──
gsap.to('.panel,.globepanel,.navpanel',{{
  opacity:1,y:0,duration:.5,stagger:.06,ease:'power2.out',delay:.05,
  onComplete:function(){{
    var o={{t:0,h:0,w:0,u:0,r:0}};
    gsap.to(o,{{t:sel_t,h:sel_h,w:sel_w,u:sel_u,r:sel_r,duration:1.1,ease:'power2.out',
      onUpdate:function(){{
        document.getElementById('mct').textContent=o.t.toFixed(1);
        document.getElementById('sh').textContent=Math.round(o.h)+'%';
        document.getElementById('sw').textContent=Math.round(o.w);
        document.getElementById('su').textContent=o.u.toFixed(1);
        document.getElementById('sr').textContent=o.r.toFixed(1);
        document.getElementById('ch').textContent=Math.round(o.h)+'%';
        document.getElementById('cu').textContent=o.u.toFixed(1);
        document.getElementById('cw').textContent=Math.round(o.w)+' km/h';
        document.getElementById('cr').textContent=o.r.toFixed(1)+' mm';
      }}
    }});
    document.querySelectorAll('.pf').forEach(function(el){{
      gsap.to(el,{{width:el.dataset.p,duration:1,ease:'power2.out',delay:.2}});
    }});
  }}
}});
</script>
</body></html>"""

    components.html(html_tab1, height=1050, scrolling=False)


# ══ TAB 2 ════════════════════════════════════════════════════════════════════
with tab2:
    cs_col, cr1, cr2 = st.columns([2,1,1])
    with cs_col:
        cities  = sorted(df["city_name"].unique())
        city    = st.selectbox("Ciudad", cities,
                               index=cities.index("Lima") if "Lima" in cities else 0,
                               label_visibility="collapsed")
    with cr1:
        max_d   = latest.date()
        min_d   = df["date"].min().date()
        start_d = st.date_input("Desde",
                                value=max(min_d, max_d-timedelta(days=29)),
                                min_value=min_d, max_value=max_d,
                                label_visibility="collapsed")
    with cr2:
        end_d = st.date_input("Hasta", value=max_d,
                              min_value=min_d, max_value=max_d,
                              label_visibility="collapsed")

    df_city = df[
        (df["city_name"] == city) &
        (df["date"].dt.date >= start_d) &
        (df["date"].dt.date <= end_d)
    ].sort_values("date")

    if df_city.empty:
        st.warning("Sin datos para esta seleccion.")
        st.stop()

    meta = df_city.iloc[-1]
    kpi_row([
        {"label":"Temp. maxima","value":f"{df_city['temperature_max'].max():.1f}",
         "unit":"°C","sub":"en el periodo","color":C["hot"]},
        {"label":"Temp. minima","value":f"{df_city['temperature_min'].min():.1f}",
         "unit":"°C","sub":"en el periodo","color":C["cold"]},
        {"label":"Precipitacion total","value":f"{df_city['precipitation_sum'].sum():.0f}",
         "unit":"mm","sub":f"{int((df_city['precipitation_sum']>0).sum())} dias con lluvia",
         "color":C["rain"]},
        {"label":"Humedad media","value":f"{df_city['humidity_mean'].mean():.0f}",
         "unit":"%","sub":"promedio del periodo","color":C["accent"]},
        {"label":"UV maximo","value":f"{df_city['uv_index_max'].max():.1f}",
         "unit":"","sub":"indice UV pico","color":C["yellow"]},
    ])

    # Charts + panel condiciones
    # Calculamos la altura total de los graficos para igualar el panel lateral
    # Alturas del chart (sin card padding)
    TREND_H  = 190
    SMALL_H  = 165
    # Overhead de glass_chart: PAD_TOP(10) + PAD_BOT(8) + iframe_margin(10) = 28px por chart
    OVERHEAD = 28
    # Columna izquierda: trend + gap(8) + small
    # Columna derecha (condiciones) debe igualar esa altura total visible
    COND_H   = (TREND_H + OVERHEAD) + 8 + (SMALL_H + OVERHEAD)

    cm_col, cs2 = st.columns([3, 1], gap="small")
    with cm_col:
        glass_chart(fig_trend(df_city, h=TREND_H), height=TREND_H)
        cr_col, cw_col = st.columns(2, gap="small")
        with cr_col:
            glass_chart(
                fig_area(df_city, "date", "precipitation_sum", C["rain"],
                         "Precipitacion diaria (mm)", h=SMALL_H),
                height=SMALL_H,
            )
        with cw_col:
            glass_chart(
                fig_area(df_city, "date", "wind_speed_max", C["wind"],
                         "Viento maximo diario (km/h)", h=SMALL_H),
                height=SMALL_H,
            )
    with cs2:
        render_conditions(meta, height=COND_H)

    with st.expander("Ver datos del periodo"):
        st.dataframe(
            df_city[["date","temperature_max","temperature_min",
                      "precipitation_sum","wind_speed_max",
                      "humidity_mean","uv_index_max","weather_description"]]
            .sort_values("date", ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "date":                st.column_config.DateColumn("Fecha"),
                "temperature_max":     st.column_config.NumberColumn("Max °C",  format="%.1f"),
                "temperature_min":     st.column_config.NumberColumn("Min °C",  format="%.1f"),
                "precipitation_sum":   st.column_config.NumberColumn("Lluvia",  format="%.1f mm"),
                "wind_speed_max":      st.column_config.NumberColumn("Viento",  format="%.0f km/h"),
                    "humidity_mean":       st.column_config.NumberColumn("Humedad", format="%.0f%%"),
                    "uv_index_max":        st.column_config.NumberColumn("UV",      format="%.1f"),
                    "weather_description": st.column_config.TextColumn("Condicion"),
                },
            )


# ══ TAB 3 ════════════════════════════════════════════════════════════════════
with tab3:
    if not reports:
        st.warning("Sin reportes de calidad.")
        st.stop()

    r   = reports[-1]
    qp  = round(r["valid_rows"]/r["total_rows"]*100, 1) if r["total_rows"] else 0

    kpi_row([
        {"label":"Total registros","value":f"{r['total_rows']:,}",
         "unit":"","sub":"en esta ejecucion","color":C["accent"]},
        {"label":"Registros validos","value":f"{r['valid_rows']:,}",
         "unit":"","sub":f"{qp}% del total","color":C["green"]},
        {"label":"Con problemas","value":f"{r['invalid_rows']:,}",
         "unit":"","sub":"sin anomalias" if r["invalid_rows"]==0 else "revisar",
         "color":C["red"] if r["invalid_rows"]>0 else C["green"]},
        {"label":"Porcentaje nulos","value":f"{r['null_percentage']:.1f}",
         "unit":"%","sub":"umbral maximo: 10%","color":C["yellow"]},
    ])

    st.markdown("<div class='sec'>Checks de calidad · Pipeline</div>", unsafe_allow_html=True)
    ck_col, ar_col = st.columns([1,1], gap="large")

    with ck_col:
        s_ok = r["overall_passed"]
        sc   = C["green"] if s_ok else C["red"]
        st.markdown(
            f"<div style='display:inline-flex;align-items:center;gap:8px;"
            f"background:{sc}11;border:1px solid {sc}33;border-radius:20px;"
            f"padding:5px 16px;margin-bottom:12px;'>"
            f"<span style='width:7px;height:7px;border-radius:50%;background:{sc};"
            f"box-shadow:0 0 6px {sc};display:inline-block;'></span>"
            f"<span style='font-size:11px;font-weight:700;color:{sc};'>"
            f"{'PASS — Todos los checks superados' if s_ok else 'FAIL — Revisar checks'}"
            f"</span></div>",
            unsafe_allow_html=True,
        )
        for ch in r["checks"]:
            ok    = ch["passed"]
            bc    = C["green"] if ok else C["red"]
            label = ch["name"].replace("_"," ").title()
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;"
                f"padding:9px 14px;background:{CARD_BG};"
                f"backdrop-filter:{BLUR};border:{BORDER};border-radius:8px;"
                f"box-shadow:{SHADOW};margin-bottom:6px;'>"
                f"<span style='font-size:8.5px;font-weight:700;padding:3px 9px;"
                f"border-radius:20px;color:{bc};background:{bc}11;"
                f"border:1px solid {bc}33;'>{'PASS' if ok else 'FAIL'}</span>"
                f"<span style='font-size:11px;color:{C['text']};font-weight:500;'>{label}</span>"
                f"<span style='font-size:10px;color:{C['muted']};margin-left:auto;'>{ch['detail']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with ar_col:
        techs = "".join(
            f"<span style='font-size:8.5px;font-weight:600;padding:3px 11px;"
            f"border-radius:20px;color:{C['accent']};border:1px solid rgba(99,102,241,.22);"
            f"background:rgba(99,102,241,.07);letter-spacing:.06em;'>{t}</span> "
            for t in ["Python","httpx","pandas","BigQuery","dbt","Streamlit","GitHub Actions"]
        )
        st.markdown(
            f"<div style='background:{CARD_BG};backdrop-filter:{BLUR};"
            f"border:{BORDER};border-radius:12px;padding:20px;box-shadow:{SHADOW_LG};'>"
            f"<div style='font-size:9px;font-weight:700;color:{C['muted']};"
            f"text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>Arquitectura</div>"
            f"<div style='font-family:Courier New,monospace;font-size:11px;"
            f"color:{C['muted']};line-height:2.1;'>"
            f"<span style='color:{C['accent']};font-weight:700;'>Open-Meteo API</span>"
            f" · 100 ciudades · LATAM · sin costo<br>"
            f"&nbsp;&nbsp;&nbsp;↓ httpx async · retry con backoff<br>"
            f"<span style='color:{C['cold']};font-weight:600;'>Extract</span>"
            f" → raw/YYYY/MM/DD/weather_raw.json<br>"
            f"&nbsp;&nbsp;&nbsp;↓<br>"
            f"<span style='color:{C['cold']};font-weight:600;'>Validate</span>"
            f" → quality_report.json · 7 checks<br>"
            f"&nbsp;&nbsp;&nbsp;↓<br>"
            f"<span style='color:{C['cold']};font-weight:600;'>Transform</span>"
            f" → clean/YYYY/MM/DD/weather_clean.csv<br>"
            f"&nbsp;&nbsp;&nbsp;↓<br>"
            f"<span style='color:{C['cold']};font-weight:600;'>Load</span>"
            f" → BigQuery · particionado por fecha<br>"
            f"&nbsp;&nbsp;&nbsp;↓<br>"
            f"<span style='color:{C['cold']};font-weight:600;'>dbt</span>"
            f" → mart_daily_summary · mart_city_stats<br>"
            f"&nbsp;&nbsp;&nbsp;↓<br>"
            f"<span style='color:{C['green']};font-weight:700;'>Dashboard</span>"
            f" ← esta pagina</div>"
            f"<div style='margin-top:14px;display:flex;gap:6px;flex-wrap:wrap;'>{techs}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
