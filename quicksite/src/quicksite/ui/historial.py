"""Pantalla Historial: tabla con filtros, fila desplegable con vista previa y acciones simuladas."""
from __future__ import annotations

from datetime import timedelta

import streamlit as st

from quicksite.core import simulado as sim
from quicksite.ui import componentes as c
from quicksite.ui import estado as e

PERIODOS = {"Últimos 7 días": 7, "Últimos 30 días": 30, "Todo el historial": None}
ESTADOS = ["Todos los estados", "Generada", "Enviada como borrador"]
ANCHOS = [1.15, 3, 2.4, 1.9, 0.95, 1.1, 0.4]


def _alternar(hid: str) -> None:
    ss = st.session_state
    ss.hist_abierto = None if ss.hist_abierto == hid else hid


def _abrir(hid: str) -> None:
    st.session_state.hist_abierto = hid


def render() -> None:
    ss = st.session_state
    st.markdown(c.cabecera_pagina("Historial", "Consulta y gestiona todos los artículos que has generado con QuickSite."),
                unsafe_allow_html=True)

    a, b, d = st.columns([3, 1.5, 1.5])
    q = a.text_input("Buscar", key="h_buscar", placeholder="Buscar por título o palabra clave...", label_visibility="collapsed")
    est = b.selectbox("Estado", ESTADOS, key="h_estado", label_visibility="collapsed")
    per = d.selectbox("Periodo", list(PERIODOS), index=1, key="h_periodo", label_visibility="collapsed")

    dias = PERIODOS[per]
    limite = sim.ahora() - timedelta(days=dias) if dias else None
    qn = (q or "").strip().lower()
    filas = [
        h for h in ss.historial
        if (est == ESTADOS[0] or h["estado"] == est)
        and (limite is None or h["fecha"] >= limite)
        and (not qn or qn in h["titulo"].lower() or any(qn in k.lower() for k in h["palabras_clave"]))
    ]

    with st.container(key="hhead"):
        cols = st.columns(ANCHOS)
        for col, t in zip(cols, ["Fecha", "Título", "Palabras clave", "Estado", "", "Acciones", ""]):
            col.markdown(f'<div class="qs-th">{t}</div>', unsafe_allow_html=True)

    if not filas:
        st.markdown(c.estado_vacio("Sin resultados", "No hay artículos que coincidan con los filtros.", "reloj"),
                    unsafe_allow_html=True)
        return

    for h in filas:
        hid = h["id"]
        abierto = ss.hist_abierto == hid
        with st.container(key=f"hrow_{hid}"):
            cols = st.columns(ANCHOS, vertical_alignment="center")
            cols[0].markdown(
                f'<div class="qs-cell">{c.esc(sim.fecha_corta(h["fecha"]))}<br>{h["fecha"].strftime("%H:%M")}</div>',
                unsafe_allow_html=True)
            cols[1].markdown(f'<div class="qs-cell"><b>{c.esc(h["titulo"])}</b></div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div class="qs-cell qs-cell-kw">{c.esc(", ".join(h["palabras_clave"]))}</div>',
                             unsafe_allow_html=True)
            cols[3].markdown(c.etiqueta_estado(h["estado"]), unsafe_allow_html=True)
            cols[4].button("Abrir", type="primary", key=f"abrir_{hid}", on_click=_abrir, args=(hid,),
                           use_container_width=True)
            cols[5].button("Reenviar", key=f"reenv_{hid}", on_click=e.reenviar, args=(hid,), use_container_width=True)
            cols[6].button("⌃" if abierto else "⌄", key=f"chev_{hid}", on_click=_alternar, args=(hid,))
            if abierto:
                st.markdown(
                    f'<div class="qs-hprev"><div class="qs-prev-img">{c.icono("imagen", 40)}</div><div>'
                    f'<div class="qs-lbl">Vista previa del artículo</div><h3>{c.esc(h["titulo"])}</h3>'
                    f'<div class="qs-cell">{c.esc(h["resumen"])}</div>'
                    f'<small>{h["lectura"]} min de lectura &nbsp;•&nbsp; {c.esc(sim.fecha_corta(h["fecha"]))} &nbsp;•&nbsp; '
                    f'Palabras clave: {c.esc(", ".join(h["palabras_clave"]))}</small></div></div>',
                    unsafe_allow_html=True)
