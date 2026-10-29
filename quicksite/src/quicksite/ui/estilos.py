"""Hoja de estilos: modo oscuro con acento naranja, basada en las capturas de referencia.

Se apoya en las clases `st-key-<key>` que Streamlit (>=1.39) añade a los widgets con `key`
y en data-testid estables. Si una versión futura los cambia, la app sigue funcionando
(solo se degrada el aspecto).
"""
from __future__ import annotations

import streamlit as st

NARANJA = "#FF6A13"
FONDO = "#090B10"
PANEL = "#0F1218"
SECUNDARIO = "#141922"
BORDE = "#1E2430"
TEXTO = "#F1F3F7"
TEXTO2 = "#9AA3B2"
VERDE = "#4ADE95"
AZUL = "#5AB0FF"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{--or:#FF6A13;--bg:#090B10;--pn:#0F1218;--sc:#141922;--bd:#1E2430;--tx:#F1F3F7;--tx2:#9AA3B2;--ok:#4ADE95;--bl:#5AB0FF}
html,body,.stApp,[class*="st-"]{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif}
.stApp{background:var(--bg);color:var(--tx)}
[data-testid="stHeader"]{background:transparent;height:0}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{display:none!important}
[data-testid="stMainBlockContainer"]{padding:1.2rem 2rem 2rem;max-width:100%}
h1,h2,h3,h4{color:var(--tx);letter-spacing:-.01em}
.qs-ic{vertical-align:-3px;margin-right:6px;flex:none}

/* ---------- barra lateral ---------- */
[data-testid="stSidebar"]{background:var(--bg);border-right:1px solid var(--bd);min-width:272px;max-width:272px}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding:0 .6rem}
[data-testid="stSidebarHeader"],[data-testid="stSidebarCollapseButton"]{display:none}
.qs-logo{display:flex;align-items:center;gap:8px;font-size:1.65rem;font-weight:600;padding:1.1rem .4rem 1.1rem;color:var(--tx)}
.qs-logo b{color:var(--or);font-weight:700}
.qs-logo-ic{color:var(--or);display:inline-flex}.qs-logo-ic .qs-ic{margin:0;fill:var(--or)}
[data-testid="stSidebar"] .stButton>button{justify-content:flex-start;background:transparent;border:1px solid transparent;
  color:var(--tx);font-weight:500;padding:.62rem .9rem;border-radius:10px;width:100%;box-shadow:none}
[data-testid="stSidebar"] .stButton>button:hover{background:var(--sc);border-color:transparent;color:var(--tx)}
.qs-sep{border-top:1px solid var(--bd);margin:.9rem .4rem .8rem}
.qs-fa-h{display:flex;justify-content:space-between;font-weight:600;padding:0 .5rem .5rem}
.qs-fa-h span{color:var(--tx2);font-weight:500}
[data-testid="stSidebar"] [data-testid="stToggle"]{background:var(--pn);border:1px solid var(--bd);border-radius:10px;padding:.55rem .7rem;margin-bottom:.45rem}
[data-testid="stSidebar"] [data-testid="stToggle"] label{width:100%;justify-content:space-between;flex-direction:row-reverse}
.qs-wpstatus{display:flex;align-items:center;gap:10px;padding:1rem .6rem;margin-top:1rem}
.qs-wpic{color:var(--tx2)}.qs-wpname{font-weight:600;font-size:.85rem}
.qs-wpsub{font-size:.72rem;color:var(--tx2);display:flex;align-items:center;gap:6px}
.qs-dot{width:7px;height:7px;border-radius:50%;background:var(--ok);display:inline-block}

/* ---------- botones ---------- */
.stButton>button,.stFormSubmitButton>button,[data-testid^="stBaseButton"]{border-radius:10px;font-weight:600;
  border:1px solid var(--bd);background:var(--pn);color:var(--tx);transition:filter .15s,background .15s}
.stButton>button:hover,.stFormSubmitButton>button:hover{border-color:#2b3445;background:var(--sc);color:var(--tx)}
button[kind="primary"],button[kind="primaryFormSubmit"],[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-primaryFormSubmit"]{
  background:var(--or)!important;border-color:var(--or)!important;color:#fff!important}
button[kind="primary"]:hover,button[kind="primaryFormSubmit"]:hover,[data-testid="stBaseButton-primary"]:hover,[data-testid="stBaseButton-primaryFormSubmit"]:hover{filter:brightness(1.1)}

/* ---------- campos ---------- */
.stTextInput input,.stTextArea textarea,[data-baseweb="select"]>div,[data-baseweb="input"]{
  background:var(--pn)!important;border:1px solid var(--bd)!important;border-radius:10px!important;color:var(--tx)!important}
.stTextInput input:focus,.stTextArea textarea:focus{border-color:var(--or)!important;box-shadow:0 0 0 1px var(--or)!important}
[data-testid="stWidgetLabel"] p{font-weight:600;font-size:.88rem}
.stTextInput [data-testid="InputInstructions"],.stTextArea [data-testid="InputInstructions"]{color:var(--tx2)}
[data-testid="stToggle"] [data-checked="true"],[data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"]{background:var(--or)!important}
.stRadio [role="radiogroup"]{gap:.5rem}
.stRadio label[data-baseweb="radio"]{background:var(--pn);border:1px solid var(--bd);border-radius:999px;padding:.35rem .95rem;margin:0}
.stRadio label[data-baseweb="radio"]:has(input:checked){border-color:var(--or);color:var(--or)}
.stRadio label[data-baseweb="radio"]>div:first-child{display:none}
[data-testid="stForm"]{border:0;padding:0;background:transparent}
[data-testid="stTabs"] [role="tab"]{font-weight:600;color:var(--tx2)}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:var(--or)}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{background:var(--or)}
[data-testid="stExpander"]{border:1px solid var(--bd);border-radius:12px;background:var(--pn)}
[data-testid="stToast"]{background:var(--sc);border:1px solid var(--bd);color:var(--tx)}

/* ---------- cabeceras y paneles ---------- */
.qs-pagehead h1{font-size:2rem;font-weight:700;margin:0;padding:0}
.qs-sub{color:var(--tx2);font-size:.95rem;margin:.2rem 0 1rem}
.qs-panel,[data-testid="stVerticalBlockBorderWrapper"]:has(>div>[data-testid="stVerticalBlock"]>.qs-panel-mark){}
div[class*="st-key-panel_"]{background:var(--pn);border:1px solid var(--bd);border-radius:14px;padding:1.1rem 1.2rem}
.qs-title-sm{font-size:1.08rem;font-weight:700;margin:0 0 .6rem}
.qs-empty{text-align:center;color:var(--tx2);padding:2.5rem 1rem}
.qs-empty h4{margin:.6rem 0 .2rem;color:var(--tx)}.qs-empty p{margin:0;font-size:.9rem}

/* ---------- barra superior (modo) ---------- */
div[class*="st-key-modo_"] button{border-radius:8px;padding:.35rem 1.2rem;font-size:.85rem;background:var(--pn)}
div[class*="st-key-modo_"].qs-on button{background:var(--or);border-color:var(--or);color:#fff}

/* ---------- chat ---------- */
.qs-row{display:flex;gap:12px;margin:0 0 1rem;width:100%}
.qs-row-user{justify-content:flex-end}
.qs-bubble{border-radius:14px;padding:.8rem 1rem;font-size:.9rem;line-height:1.5;max-width:min(78%,640px)}
.qs-user{background:var(--sc);border:1px solid var(--bd)}
.qs-ia{background:var(--pn);border:1px solid var(--bd);max-width:min(88%,820px)}
.qs-ia p{margin:.2rem 0 .5rem}.qs-ia h2,.qs-ia h3{font-size:1.05rem;margin:.8rem 0 .3rem}
.qs-ia ul,.qs-ia ol{margin:.2rem 0 .6rem 1.1rem;padding:0}
.qs-time{font-size:.7rem;color:var(--tx2);text-align:right;margin-top:.3rem}
.qs-avatar{flex:none;width:38px;height:38px;border-radius:50%;background:#2a1a10;border:1px solid #4a2a16;color:var(--or);display:flex;align-items:center;justify-content:center}
.qs-avatar .qs-ic{margin:0}
.qs-art h3{font-size:1.25rem;margin:.1rem 0 .3rem}.qs-art hr{border:0;border-top:1px solid var(--bd);margin:.7rem 0}
.pend{background:rgba(255,106,19,.15);color:#ffb27d;border-radius:4px;padding:0 4px}

/* ---------- previsualización ---------- */
.qs-prev{font-size:.88rem;line-height:1.6;color:#d9dde6}
.qs-prev h1{font-size:1.55rem;line-height:1.2;margin:.5rem 0}
.qs-prev h2{font-size:1.02rem;margin:1rem 0 .3rem;color:var(--tx)}
.qs-prev p{margin:.2rem 0 .6rem}.qs-prev ul,.qs-prev ol{margin:.2rem 0 .6rem 1.2rem;padding:0}
.qs-prev-img{background:#171c26;border-radius:10px;height:150px;display:flex;align-items:center;justify-content:center;color:#5b6577;margin-bottom:.4rem}
.qs-prev-img-lg{height:190px;margin:.6rem 0 1rem}.qs-prev-img .qs-ic{margin:0}
.qs-caption{font-size:.72rem;color:var(--tx2);margin-bottom:.6rem}
.qs-tag{display:inline-block;font-size:.7rem;font-weight:600;padding:.12rem .55rem;border-radius:999px;border:1px solid transparent;margin-left:6px;vertical-align:middle}
.qs-tag-general{background:rgba(124,92,255,.15);color:#a995ff;border-color:rgba(124,92,255,.4)}
.qs-tag-estilo{background:rgba(74,222,149,.12);color:var(--ok);border-color:rgba(74,222,149,.4)}
.qs-tag-seo{background:rgba(90,176,255,.12);color:var(--bl);border-color:rgba(90,176,255,.4)}
.qs-tag-contenido{background:rgba(255,106,19,.12);color:#ff9a5c;border-color:rgba(255,106,19,.45)}
.qs-tag-cat{background:#1b2130;color:#b6c0d4;border-color:var(--bd);margin:0}
.qs-meta{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:.75rem;color:var(--tx2);margin:.3rem 0 .5rem}
.qs-meta i{font-style:normal}.qs-kw{font-size:.78rem;color:var(--tx2);margin-bottom:.6rem}.qs-kw b{color:#ffb27d}
.qs-faq{margin-top:1rem}
.qs-faq details{border:1px solid var(--bd);border-radius:8px;padding:.5rem .8rem;margin-bottom:.4rem;background:var(--pn)}
.qs-faq summary{cursor:pointer;font-weight:500}
.qs-skel{height:9px;border-radius:5px;background:#1b2130;margin:.55rem 0}.qs-skel-s{width:60%}
.qs-ghost{color:var(--tx)}

/* ---------- fichas ---------- */
.qs-fcard{display:flex;gap:14px;align-items:center;padding:.2rem 0}
.qs-ficon{width:42px;height:42px;border-radius:10px;background:#171c26;display:flex;align-items:center;justify-content:center;color:var(--tx2);flex:none}
.qs-ficon .qs-ic{margin:0}.qs-ftitle{font-weight:700;font-size:1rem}.qs-fdesc{color:var(--tx2);font-size:.85rem}
.qs-off{font-size:.68rem;color:var(--tx2);border:1px solid var(--bd);border-radius:999px;padding:.05rem .45rem;margin-left:6px}
div[class*="st-key-fc_"]{background:var(--pn);border:1px solid var(--bd);border-radius:12px;padding:.7rem .9rem;margin-bottom:.6rem}
div[class*="st-key-fc_"].qs-sel{border-color:var(--or);box-shadow:0 0 0 1px var(--or) inset}

/* ---------- historial ---------- */
.qs-th{color:var(--tx2);font-size:.85rem;font-weight:500}
.qs-cell{font-size:.85rem;line-height:1.45}.qs-cell b{font-weight:600}.qs-cell-kw{color:var(--tx2)}
.qs-estado{display:inline-flex;align-items:center;gap:2px;font-size:.75rem;font-weight:500;padding:.18rem .65rem;border-radius:999px;border:1px solid}
.qs-estado .qs-ic{margin-right:4px;vertical-align:-2px}
.qs-estado-ok{color:var(--ok);background:rgba(74,222,149,.1);border-color:rgba(74,222,149,.4)}
.qs-estado-env{color:var(--bl);background:rgba(90,176,255,.1);border-color:rgba(90,176,255,.4)}
div[class*="st-key-hrow_"]{border-bottom:1px solid var(--bd);padding:.55rem .4rem}
div[class*="st-key-hrow_"].qs-open{border:1px solid var(--or);border-radius:10px;background:var(--pn)}
div[class*="st-key-hhead"]{background:var(--pn);border-radius:10px;padding:.7rem .9rem}
.qs-hprev{display:flex;gap:1.4rem;padding:.6rem 0 .3rem}
.qs-hprev .qs-prev-img{width:270px;height:150px;flex:none}.qs-hprev h3{margin:.1rem 0 .4rem;font-size:1.1rem}
.qs-hprev small{color:var(--tx2);display:block;margin-top:.5rem;font-size:.75rem}
.qs-lbl{font-size:.75rem;color:var(--tx2)}
.qs-banner{border:1px dashed #4a2a16;background:rgba(255,106,19,.06);color:#ffb27d;border-radius:10px;padding:.5rem .8rem;font-size:.8rem;margin-bottom:.8rem}
"""

CSS += """
/* ---------- chips, estados y SEO ---------- */
.qs-chip{display:inline-block;font-size:.66rem;font-weight:600;padding:.05rem .5rem;border-radius:999px;margin-right:6px;border:1px solid transparent}
.qs-chip-or{color:#ff9a5c;background:rgba(255,106,19,.12);border-color:rgba(255,106,19,.45)}
.qs-chip-bl{color:var(--bl);background:rgba(90,176,255,.1);border-color:rgba(90,176,255,.4)}
.qs-chip-am{color:#f5c451;background:rgba(245,196,81,.1);border-color:rgba(245,196,81,.4)}
.qs-chip-modo{color:var(--tx2);border-color:var(--bd)}
.qs-chiprow{margin-bottom:.4rem}
.qs-estado-bor{color:#b6c0d4;background:#1b2130;border-color:var(--bd)}
.qs-estado-rev{color:#f5c451;background:rgba(245,196,81,.1);border-color:rgba(245,196,81,.4)}
.qs-estado-apr{color:#a995ff;background:rgba(124,92,255,.12);border-color:rgba(124,92,255,.4)}
.qs-seo{display:inline-block;font-size:.72rem;font-weight:700;padding:.15rem .55rem;border-radius:8px;border:1px solid}
.qs-seo-ok{color:var(--ok);background:rgba(74,222,149,.1);border-color:rgba(74,222,149,.4)}
.qs-seo-am{color:#f5c451;background:rgba(245,196,81,.1);border-color:rgba(245,196,81,.4)}
.qs-seo-ko{color:#ff7b7b;background:rgba(255,107,107,.1);border-color:rgba(255,107,107,.4)}
.qs-modehint{font-size:.78rem;color:var(--tx2);text-align:center;margin-top:.35rem}.qs-modehint b{color:var(--or)}
.qs-score{display:flex;align-items:center;gap:1rem;margin:.4rem 0 .8rem}
.qs-score-n{font-size:2.2rem;font-weight:700;line-height:1}.qs-score-n small{font-size:.9rem;color:var(--tx2);font-weight:500}
.qs-bar{flex:1;height:8px;border-radius:6px;background:#1b2130;overflow:hidden}.qs-bar i{display:block;height:100%;background:var(--or);border-radius:6px}
.qs-chk{list-style:none;margin:0;padding:0}.qs-chk li{display:flex;align-items:center;padding:.4rem 0;border-bottom:1px solid var(--bd);font-size:.88rem}
.qs-chk li.ok{color:var(--ok)}.qs-chk li.ko{color:#f5c451}.qs-chk li .qs-ic{margin-right:10px}

/* ---------- analítica ---------- */
.qs-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:.4rem 0 1rem}
.qs-kpi{background:var(--pn);border:1px solid var(--bd);border-radius:14px;padding:1rem 1.1rem}
.qs-kpi-l{color:var(--tx2);font-size:.82rem}.qs-kpi-v{font-size:1.8rem;font-weight:700;margin:.2rem 0}
.qs-kpi-d{font-size:.8rem;font-weight:600}.qs-kpi-d span{color:var(--tx2);font-weight:400}
.qs-kpi-d.up{color:var(--ok)}.qs-kpi-d.down{color:#ff7b7b}
.qs-chart svg text{fill:#9AA3B2;font-size:12px;font-family:Inter,system-ui,sans-serif}
.qs-tbl{width:100%;border-collapse:collapse;font-size:.84rem}
.qs-tbl th{text-align:left;color:var(--tx2);font-weight:500;padding:.5rem .6rem;border-bottom:1px solid var(--bd)}
.qs-tbl td{padding:.55rem .6rem;border-bottom:1px solid var(--bd)}
.qs-tbl .n{text-align:right;font-variant-numeric:tabular-nums}

/* ---------- filas de páginas / lote ---------- */
div[class*="st-key-prow_"],div[class*="st-key-mrow_"]{border-bottom:1px solid var(--bd);padding:.5rem .3rem}
div[class*="st-key-sug_"] button{font-size:.76rem;padding:.2rem .5rem;border-radius:999px;font-weight:500}
.qs-pt{font-weight:600;font-size:.9rem;line-height:1.3}.qs-ps{color:var(--tx2);font-size:.75rem}
"""


def aplicar(pagina: str, modo: str | None = None, ficha_sel: str | None = None,
            hist_abierto: str | None = None) -> None:
    """Inyecta el CSS y resalta navegación, modo activo y ficha seleccionada."""
    extra = [
        f'div.st-key-nav_{pagina} button{{background:rgba(255,106,19,.14)!important;'
        f'border:1px solid rgba(255,106,19,.45)!important;color:{NARANJA}!important}}'
    ]
    if modo:
        clave = "construccion" if modo == "Construcción" else "chat"
        extra.append(
            f'div.st-key-modo_{clave} button{{background:{NARANJA}!important;border-color:{NARANJA}!important;color:#fff!important}}'
        )
    if ficha_sel:
        extra.append(
            f'div.st-key-fc_{ficha_sel}{{border-color:{NARANJA}!important;box-shadow:0 0 0 1px {NARANJA} inset}}'
        )
    if hist_abierto:
        extra.append(
            f'div.st-key-hrow_{hist_abierto}{{border:1px solid {NARANJA}!important;border-radius:10px;background:{PANEL}}}'
        )
    st.markdown(f"<style>{CSS}{''.join(extra)}</style>", unsafe_allow_html=True)
