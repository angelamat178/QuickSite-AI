import streamlit as st


def render_ajustes() -> None:
    st.title("Ajustes")
    st.caption("Pantalla provisional. Los valores reales se leerán del archivo `.env` (nunca se sube a Git).")
    with st.container(border=True):
        st.text_input("OLLAMA_URL", value="http://localhost:11434", disabled=True)
        st.text_input("OLLAMA_MODELO", value="(por definir)", disabled=True)
        st.text_input("WP_URL", value="https://tu-web.com", disabled=True)
        st.text_input("WP_USUARIO", value="usuario", disabled=True)
        st.text_input("WP_APP_PASSWORD", value="••••••••", type="password", disabled=True)
