import time
from datetime import datetime

import streamlit as st

from core.generador_simulado import generar_borrador, responder_chat
from ui.estado import fichas_activas


def render_generador() -> None:
    # Selector de modo centrado
    _, centro, _ = st.columns([2, 2, 2])
    with centro:
        st.segmented_control(
            "Modo", ["Construcción", "Chat"], key="modo", label_visibility="collapsed", width="stretch"
        )

    if st.session_state.modo == "Chat":
        _render_chat()
    else:  # "Construcción" (o None si se desmarca)
        _render_construccion()


# ---------------------------------------------------------------- Construcción
def _render_construccion() -> None:
    col_chat, col_prev = st.columns([3, 2], gap="large")

    with col_chat:
        caja = st.container(height=520, border=False)
        with caja:
            if not st.session_state.mensajes_construccion:
                st.info("Escribe una petición, por ejemplo: «Entrada sobre cómo cambiar el nombre de un coche».")
            for m in st.session_state.mensajes_construccion:
                with st.chat_message(m["rol"], avatar="⚡" if m["rol"] == "assistant" else None):
                    st.markdown(m["texto"])
                    st.caption(m["hora"])

        peticion = st.chat_input("Escribe una instrucción o mejora el contenido...", key="input_construccion")
        if peticion:
            hora = datetime.now().strftime("%H:%M")
            st.session_state.mensajes_construccion.append({"rol": "user", "texto": peticion, "hora": hora})
            with st.spinner("Generando borrador..."):
                time.sleep(1)  # simula que el modelo tarda
                borrador = generar_borrador(peticion)
            st.session_state.borrador = borrador
            st.session_state.historial.insert(
                0, {"id": max([e["id"] for e in st.session_state.historial], default=0) + 1,
                    "estado": "Generada", "borrador": borrador}
            )
            st.session_state.mensajes_construccion.append(
                {"rol": "assistant", "hora": datetime.now().strftime("%H:%M"),
                 "texto": f"He generado el borrador **{borrador['titulo']}**. Puedes editarlo en el panel de la derecha."}
            )
            st.rerun()

    with col_prev:
        _render_previsualizacion()


def _render_previsualizacion() -> None:
    b = st.session_state.borrador
    with st.container(border=True):
        st.subheader("Previsualización")
        if b is None:
            st.caption("Aquí aparecerá el borrador cuando generes una entrada.")
            return

        tab_editar, tab_prev = st.tabs(["Editar", "Previsualización"])

        with tab_editar:
            # Con `key`, Streamlit recuerda lo que escribe el usuario; guardamos el valor en el borrador.
            b["titulo"] = st.text_input("Título del artículo", value=b["titulo"], max_chars=200, key=f"titulo_{b['id']}")
            b["meta_descripcion"] = st.text_area(
                "Meta descripción", value=b["meta_descripcion"], max_chars=160, key=f"meta_{b['id']}"
            )
            b["palabra_clave"] = st.text_input("Palabra clave", value=b["palabra_clave"], max_chars=100, key=f"kw_{b['id']}")
            b["cuerpo_html"] = st.text_area("Cuerpo (HTML)", value=b["cuerpo_html"], height=220, key=f"cuerpo_{b['id']}")

        with tab_prev:
            st.caption(f"{b['categoria']} · {b['fecha']:%d/%m/%Y} · {b['minutos_lectura']} min de lectura")
            st.markdown(f"### {b['titulo']}")
            st.caption(f"🖼️ Imagen de stock (búsqueda: {b['imagen_busqueda']})")
            st.markdown(b["cuerpo_html"], unsafe_allow_html=True)
            with st.expander("Preguntas frecuentes"):
                for q in b["faq"]:
                    st.markdown(f"**{q['pregunta']}**\n\n{q['respuesta']}")

        for aviso in b["avisos"]:
            st.warning(aviso, icon="⚠️")

        if st.button("Enviar a WordPress como borrador", type="primary", icon=":material/send:", width="stretch"):
            _marcar_enviada(b["id"])
            st.success("Borrador enviado a WordPress (simulado). QuickSite nunca publica: revísalo en WordPress.")


def _marcar_enviada(borrador_id: str) -> None:
    for e in st.session_state.historial:
        if e["borrador"]["id"] == borrador_id:
            e["estado"] = "Enviada como borrador"


# ------------------------------------------------------------------------ Chat
def _render_chat() -> None:
    activas = fichas_activas()
    caja = st.container(height=480, border=False)
    with caja:
        for m in st.session_state.mensajes_chat:
            with st.chat_message(m["rol"], avatar="⚡" if m["rol"] == "assistant" else None):
                st.markdown(m["texto"])

    with st.expander(f"Contexto: {len(activas)} fichas activas"):
        for f in activas:
            st.markdown(f"- {f['nombre']}")

    mensaje = st.chat_input("Escribe tu mensaje o pide un nuevo artículo...", key="input_chat")
    if mensaje:
        st.session_state.mensajes_chat.append({"rol": "user", "texto": mensaje})
        respuesta = responder_chat(mensaje, [f["nombre"] for f in activas])
        st.session_state.mensajes_chat.append({"rol": "assistant", "texto": respuesta})
        st.rerun()
