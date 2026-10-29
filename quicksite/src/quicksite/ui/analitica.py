"""Analítica SEO · Search Console (DEMO con datos ficticios y siempre iguales)."""
from __future__ import annotations

import streamlit as st

from quicksite.core import datos_simulados as ds
from quicksite.ui import componentes as c
from quicksite.ui import estado as e

METRICAS = {"Clics": ("clics", 0), "Impresiones": ("impr", 0), "CTR (%)": ("ctr", 2), "Posición media": ("pos", 1)}


def _optimizar() -> None:
    st.toast("[DEMOSTRACIÓN] Optimización propuesta: mejorar título y meta descripción de la página. Nada se ha cambiado.", icon="🧪")


def _exportar() -> None:
    st.toast("[DEMOSTRACIÓN] Exportación simulada: no se ha generado ningún archivo.", icon="🧪")


def render() -> None:
    ss = st.session_state
    st.markdown(c.cabecera_pagina("Analítica SEO", "Rendimiento orgánico de tus páginas en Google Search Console."),
                unsafe_allow_html=True)
    a, b, d = st.columns([3, 1.2, 1.2], vertical_alignment="center")
    if ss.sc_conectado:
        a.markdown(f'<div class="qs-banner" style="margin:0">● Conectado a <b>{c.esc(ds.SC_PROPIEDAD)}</b> (simulado). '
                   'Datos de demostración.</div>', unsafe_allow_html=True)
    else:
        a.markdown('<div class="qs-banner" style="margin:0">Search Console no está conectado. Estás viendo datos de '
                   'DEMOSTRACIÓN.</div>', unsafe_allow_html=True)
    b.selectbox("Periodo", [7, 28, 90], key="sc_dias", format_func=lambda x: f"Últimos {x} días", label_visibility="collapsed")
    d.button("Desconectar" if ss.sc_conectado else "Conectar Search Console", type="secondary" if ss.sc_conectado else "primary",
             key="btn_sc", on_click=e.conectar_sc, use_container_width=True)

    s = ds.sc_serie(int(ss.sc_dias))
    tc, ti = sum(s["clics"]), sum(s["impr"])
    dl = ds.SC_DELTAS
    st.markdown(c.kpis_html([
        ("Clics totales", c.fmt_num(tc), *dl["clics"]),
        ("Impresiones totales", c.fmt_num(ti), *dl["impr"]),
        ("CTR medio", c.fmt_num(tc / ti * 100, 2) + " %", *dl["ctr"]),
        ("Posición media", c.fmt_num(sum(s["pos"]) / len(s["pos"]), 1), *dl["pos"]),
    ]), unsafe_allow_html=True)

    with st.container(key="panel_sc_grafico"):
        st.markdown('<div class="qs-title-sm">Evolución</div>', unsafe_allow_html=True)
        met = st.radio("Métrica", list(METRICAS), key="sc_metrica", horizontal=True, label_visibility="collapsed")
        clave, dec = METRICAS[met or "Clics"]
        st.markdown(c.grafico_svg(s["etiquetas"], s[clave], dec), unsafe_allow_html=True)
        if clave == "pos":
            st.caption("En posición media, un valor más bajo es mejor.")

    izq, der = st.columns(2, gap="large")
    with izq:
        with st.container(key="panel_sc_consultas"):
            st.markdown('<div class="qs-title-sm">Principales consultas</div>', unsafe_allow_html=True)
            st.markdown(c.tabla_html(
                ["Consulta", "Clics", "Impr.", "CTR", "Pos."],
                [[q, c.fmt_num(cl), c.fmt_num(im), c.fmt_num(cl / im * 100, 1) + " %", c.fmt_num(po, 1)]
                 for q, cl, im, po in ds.SC_CONSULTAS[:8]], num=(1, 2, 3, 4)), unsafe_allow_html=True)
    with der:
        with st.container(key="panel_sc_paginas"):
            st.markdown('<div class="qs-title-sm">Principales páginas</div>', unsafe_allow_html=True)
            st.markdown(c.tabla_html(
                ["Página", "Clics", "Impr.", "CTR", "Pos."],
                [[u, c.fmt_num(cl), c.fmt_num(im), c.fmt_num(cl / im * 100, 1) + " %", c.fmt_num(po, 1)]
                 for u, cl, im, po in ds.SC_PAGINAS], num=(1, 2, 3, 4)), unsafe_allow_html=True)

    with st.container(key="panel_sc_oportunidades"):
        st.markdown('<div class="qs-title-sm">Oportunidades · muchas impresiones, posición 8-20</div>', unsafe_allow_html=True)
        ops = sorted([x for x in ds.SC_CONSULTAS if 8 <= x[3] <= 20 and x[2] >= 9000], key=lambda x: -x[2])[:5]
        for q, cl, im, po in ops:
            cols = st.columns([3, 1.1, 1, 1.3, 1.1], vertical_alignment="center")
            cols[0].markdown(f'<div class="qs-pt">{c.esc(q)}</div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div class="qs-ps">{c.fmt_num(im)} impr.</div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div class="qs-ps">pos. {c.fmt_num(po, 1)}</div>', unsafe_allow_html=True)
            cols[3].button("Crear artículo", key=f"op_crear_{q}", on_click=e.crear_desde_consulta, args=(q,), use_container_width=True)
            cols[4].button("Optimizar", key=f"op_opt_{q}", on_click=_optimizar, use_container_width=True)
        x, y, _ = st.columns([1.6, 1.2, 2])
        x.button("✦  Preguntar a la IA sobre estos datos", type="primary", key="btn_ia_sc", on_click=e.preguntar_ia_analitica,
                 use_container_width=True)
        y.button("Exportar CSV (demo)", key="btn_exp_sc", on_click=_exportar, use_container_width=True)
