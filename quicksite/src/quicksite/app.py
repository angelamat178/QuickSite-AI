"""QuickSite · interfaz de demostración (datos simulados, sin conexiones externas).

Arranque (desde la carpeta `quicksite/`):
    streamlit run src/quicksite/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Permite `import quicksite` al lanzar con `streamlit run src/quicksite/app.py`.
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st  # noqa: E402

from quicksite.core import datos_simulados as ds  # noqa: E402
from quicksite.ui import analitica, componentes as c, estado as e, estilos, fichas, generador, historial, masivo, paginas  # noqa: E402

st.set_page_config(page_title="QuickSite", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

NAV = [("generador", "Generador"), ("paginas", "Páginas"), ("masivo", "En masa"), ("analitica", "Analítica SEO"),
       ("fichas", "Fichas"), ("historial", "Historial"), ("ajustes", "Ajustes")]
CON_SITIO = {"generador", "paginas", "masivo", "analitica", "fichas"}


def _barra_lateral() -> None:
    ss = st.session_state
    with st.sidebar:
        st.markdown(c.logo(), unsafe_allow_html=True)
        for clave, etiqueta in NAV:
            st.button(etiqueta, key=f"nav_{clave}", on_click=e.ir_a, args=(clave,), use_container_width=True)
        st.markdown('<div class="qs-sep"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="qs-fa-h">Fichas activas<span>{len(e.fichas_activas())}/{ds.LIMITE_FICHAS_ACTIVAS}</span></div>',
            unsafe_allow_html=True)
        for f in ss.fichas:
            clave = f"sb_{f['id']}"
            ss[clave] = f["activa"]  # fuente de verdad única: la ficha
            st.toggle(f["nombre"], key=clave, on_change=e.alternar_ficha, args=(f["id"], clave))
        st.markdown(c.estado_wp_html(), unsafe_allow_html=True)


def _barra_superior(con_modo: bool) -> None:
    _, centro, der = st.columns([1.2, 2, 1.2], vertical_alignment="center")
    with centro:
        if con_modo:
            a, b = st.columns(2)
            a.button("Construcción", key="modo_construccion", on_click=e.set_modo, args=("Construcción",), use_container_width=True)
            b.button("Chat", key="modo_chat", on_click=e.set_modo, args=("Chat",), use_container_width=True)
            st.markdown(c.modo_hint_html(st.session_state.modo), unsafe_allow_html=True)
    with der:
        c.selector_sitio()


def _ajustes() -> None:
    st.markdown(c.cabecera_pagina("Ajustes", "Configuración de la demostración."), unsafe_allow_html=True)
    with st.container(key="panel_ajustes"):
        st.markdown(
            '<div class="qs-banner">Esta es una demostración de la interfaz. No hay Ollama, WordPress ni Pexels conectados, '
            'no se piden credenciales y no se hace ninguna petición de red.</div>', unsafe_allow_html=True)
        st.selectbox("Sitio de WordPress (simulado)", ds.SITIOS_WP, key="sitio_ajustes")
        st.text_input("Modelo de Ollama", value="(sin conectar)", disabled=True)
        st.text_input("Clave de Pexels", value="(sin conectar)", disabled=True)
        st.caption("Estos campos se activarán al conectar los servicios reales.")


PANTALLAS = {"generador": generador.render, "paginas": paginas.render, "masivo": masivo.render,
             "analitica": analitica.render, "fichas": fichas.render, "historial": historial.render,
             "ajustes": _ajustes}


def main() -> None:
    e.iniciar()
    ss = st.session_state
    pagina = ss.pagina
    estilos.aplicar(
        pagina,
        modo=ss.modo if pagina == "generador" else None,
        ficha_sel=ss.ficha_sel if pagina == "fichas" else None,
        hist_abierto=ss.hist_abierto if pagina == "historial" else None,
    )
    _barra_lateral()
    if pagina in CON_SITIO:
        _barra_superior(pagina == "generador")
    PANTALLAS[pagina]()


main()
