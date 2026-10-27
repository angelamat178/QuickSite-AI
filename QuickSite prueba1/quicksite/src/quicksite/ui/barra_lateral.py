import streamlit as st

from ui.estado import MAX_ACTIVAS, al_cambiar_activa, fichas_activas

SECCIONES = ["Generador", "Fichas", "Historial", "Ajustes"]
ICONOS = {"Generador": "💬", "Fichas": "📄", "Historial": "🕘", "Ajustes": "⚙️"}


def render_barra_lateral() -> None:
    with st.sidebar:
        st.markdown(
            "## ⚡ Quick<span style='color:#FF6A13'>Site</span>",
            unsafe_allow_html=True,
        )
        st.radio(
            "Navegación",
            SECCIONES,
            key="seccion",
            format_func=lambda s: f"{ICONOS[s]}  {s}",
            label_visibility="collapsed",
        )

        st.divider()
        col1, col2 = st.columns([3, 1])
        col1.markdown("**Fichas activas**")
        col2.markdown(f"{len(fichas_activas())}/{MAX_ACTIVAS}")
        for f in st.session_state.fichas:
            key = f"side_{f['id']}"
            st.toggle(f["nombre"], key=key, on_change=al_cambiar_activa, args=(f["id"], key))

        st.divider()
        st.caption("🟢 WordPress conectado (simulado)")
