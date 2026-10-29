"""Pantalla Generador · modo Chat (conversación simulada con las fichas activas)."""
from __future__ import annotations

import streamlit as st

from quicksite.core import simulado as sim
from quicksite.ui import componentes as c
from quicksite.ui import estado as e


def _enviar() -> None:
    ss = st.session_state
    texto = (ss.get("chat_msg") or "").strip()
    if not texto:
        return
    hora = sim.hora()
    n = len(e.fichas_activas())
    ss.msgs_chat.append({"rol": "user", "texto": texto, "hora": hora})
    ss.msgs_chat.append({"rol": "ia", "html": c.texto_a_burbuja(sim.respuesta_chat(texto, n)), "hora": hora})
    ss.chat_msg = ""


def render() -> None:
    ss = st.session_state
    _, centro, _ = st.columns([0.4, 5, 0.4])
    with centro:
        with st.container(height=600, border=False, key="scroll_chat"):
            st.markdown(c.mensajes_html(ss.msgs_chat), unsafe_allow_html=True)
        activas = e.fichas_activas()
        with st.container(key="panel_chat_in"):
            with st.expander(f"Contexto: {len(activas)} fichas activas"):
                if activas:
                    for f in activas:
                        st.markdown(f"- **{f['nombre']}** · {f['tipo']}")
                else:
                    st.caption("No hay fichas activas. Actívalas en la barra lateral.")
            with st.form("form_chat", clear_on_submit=False, border=False):
                a, b = st.columns([6, 1.2], vertical_alignment="bottom")
                a.text_input("Mensaje", key="chat_msg", label_visibility="collapsed",
                             placeholder="Escribe tu mensaje o pide un nuevo artículo...")
                b.form_submit_button("Enviar", type="primary", use_container_width=True, on_click=_enviar)
