"""Estado de la sesión (st.session_state) y funciones compartidas por las pantallas.

En Streamlit el script se ejecuta de arriba abajo cada vez que el usuario toca algo.
`st.session_state` es la "memoria" que sobrevive entre ejecuciones.
"""
import copy

import streamlit as st

from core.datos_simulados import FICHAS_INICIALES, HISTORIAL_INICIAL
from core.generador_simulado import generar_borrador

MAX_ACTIVAS = 5


def iniciar_estado() -> None:
    """Crea los datos iniciales solo la primera vez."""
    if st.session_state.get("iniciado"):
        return
    st.session_state.fichas = copy.deepcopy(FICHAS_INICIALES)
    for f in st.session_state.fichas:
        sincronizar_toggles(f["id"], f["activa"])
    st.session_state.siguiente_id_ficha = max(f["id"] for f in st.session_state.fichas) + 1
    st.session_state.ficha_seleccionada = st.session_state.fichas[0]["id"]

    historial = []
    for i, e in enumerate(HISTORIAL_INICIAL, start=1):
        borrador = generar_borrador(e["titulo"], titulo=e["titulo"], palabra_clave=e["palabra_clave"])
        borrador["fecha"] = e["fecha"]
        historial.append({"id": i, "estado": e["estado"], "borrador": borrador})
    st.session_state.historial = historial

    st.session_state.mensajes_construccion = []
    st.session_state.mensajes_chat = [
        {"rol": "assistant", "texto": "¡Hola! Pregúntame lo que quieras o pídeme ideas para tu blog."}
    ]
    st.session_state.borrador = None
    st.session_state.seccion = "Generador"
    st.session_state.modo = "Construcción"
    st.session_state.iniciado = True


# ------------------------------------------------------------------ fichas
def buscar_ficha(ficha_id: int) -> dict | None:
    return next((f for f in st.session_state.fichas if f["id"] == ficha_id), None)


def fichas_activas() -> list[dict]:
    return [f for f in st.session_state.fichas if f["activa"]]


def sincronizar_toggles(ficha_id: int, valor: bool) -> None:
    """El interruptor de la barra lateral y el del editor muestran el mismo valor."""
    st.session_state[f"side_{ficha_id}"] = valor
    st.session_state[f"edit_act_{ficha_id}"] = valor


def al_cambiar_activa(ficha_id: int, key_origen: str) -> None:
    """Callback: se ejecuta ANTES de redibujar la página cuando se toca un interruptor."""
    ficha = buscar_ficha(ficha_id)
    nuevo = st.session_state[key_origen]
    if nuevo and not ficha["activa"] and len(fichas_activas()) >= MAX_ACTIVAS:
        st.toast(f"Máximo {MAX_ACTIVAS} fichas activas a la vez.", icon="⚠️")
        nuevo = False
    ficha["activa"] = nuevo
    sincronizar_toggles(ficha_id, nuevo)
