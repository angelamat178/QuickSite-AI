import streamlit as st

ESTADOS = ["Todos los estados", "Generada", "Enviada como borrador"]


def _abrir(entrada_id: int) -> None:
    entrada = next(e for e in st.session_state.historial if e["id"] == entrada_id)
    st.session_state.borrador = entrada["borrador"]
    st.session_state.seccion = "Generador"
    st.session_state.modo = "Construcción"


def _reenviar(entrada_id: int) -> None:
    entrada = next(e for e in st.session_state.historial if e["id"] == entrada_id)
    entrada["estado"] = "Enviada como borrador"
    st.toast("Borrador reenviado a WordPress (simulado)", icon="📤")


def render_historial() -> None:
    st.title("Historial")
    st.caption("Consulta y gestiona todas las entradas que has generado con QuickSite.")

    c1, c2 = st.columns([3, 1])
    busqueda = c1.text_input(
        "Buscar", placeholder="Buscar por título o palabra clave...", label_visibility="collapsed"
    )
    estado = c2.selectbox("Estado", ESTADOS, label_visibility="collapsed")

    entradas = sorted(st.session_state.historial, key=lambda e: e["borrador"]["fecha"], reverse=True)
    mostradas = 0
    for e in entradas:
        b = e["borrador"]
        if estado != ESTADOS[0] and e["estado"] != estado:
            continue
        if busqueda.lower() not in f"{b['titulo']} {b['palabra_clave']}".lower():
            continue
        mostradas += 1
        with st.container(border=True):
            col_fecha, col_titulo, col_estado, col_abrir, col_reenviar = st.columns([2, 5, 3, 1.5, 2])
            col_fecha.caption(f"{b['fecha']:%d/%m/%Y %H:%M}")
            col_titulo.markdown(f"**{b['titulo']}**")
            col_titulo.caption(b["palabra_clave"])
            if e["estado"] == "Generada":
                col_estado.markdown(":green-badge[✓ Generada]")
            else:
                col_estado.markdown(":blue-badge[➤ Enviada como borrador]")
            col_abrir.button("Abrir", key=f"abrir_{e['id']}", type="primary", on_click=_abrir, args=(e["id"],))
            col_reenviar.button("Reenviar", key=f"reenviar_{e['id']}", on_click=_reenviar, args=(e["id"],))
            with st.expander("Vista previa"):
                st.write(b["meta_descripcion"])
                st.caption(f"{b['minutos_lectura']} min de lectura · Palabra clave: {b['palabra_clave']}")

    if mostradas == 0:
        st.info("No hay entradas que coincidan con los filtros.")
