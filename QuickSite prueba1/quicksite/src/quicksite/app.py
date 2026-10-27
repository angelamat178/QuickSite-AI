"""Punto de entrada de QuickSite.

Arranque (desde la carpeta quicksite/):
    streamlit run src/quicksite/app.py
"""
import streamlit as st

from ui.ajustes import render_ajustes
from ui.barra_lateral import render_barra_lateral
from ui.estado import iniciar_estado
from ui.fichas import render_fichas
from ui.generador import render_generador
from ui.historial import render_historial

st.set_page_config(page_title="QuickSite", page_icon="⚡", layout="wide")

iniciar_estado()
render_barra_lateral()

PANTALLAS = {
    "Generador": render_generador,
    "Fichas": render_fichas,
    "Historial": render_historial,
    "Ajustes": render_ajustes,
}
PANTALLAS[st.session_state.seccion]()
