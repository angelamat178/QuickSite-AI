import streamlit as st

from core.datos_simulados import TIPOS_FICHA
from ui.estado import al_cambiar_activa, buscar_ficha, sincronizar_toggles


# ---- callbacks (se ejecutan al pulsar el botón, antes de redibujar) ----
def _seleccionar(ficha_id: int) -> None:
    st.session_state.ficha_seleccionada = ficha_id


def _nueva() -> None:
    nuevo_id = st.session_state.siguiente_id_ficha
    st.session_state.siguiente_id_ficha += 1
    st.session_state.fichas.append(
        {"id": nuevo_id, "nombre": "Nueva ficha", "tipo": TIPOS_FICHA[0], "contenido": "", "activa": False}
    )
    sincronizar_toggles(nuevo_id, False)
    st.session_state.ficha_seleccionada = nuevo_id


def _guardar(ficha_id: int) -> None:
    f = buscar_ficha(ficha_id)
    f["nombre"] = st.session_state[f"nombre_{ficha_id}"].strip() or "Sin nombre"
    f["tipo"] = st.session_state[f"tipo_{ficha_id}"]
    f["contenido"] = st.session_state[f"contenido_{ficha_id}"]
    st.toast("Ficha guardada", icon="✅")


def _duplicar(ficha_id: int) -> None:
    original = buscar_ficha(ficha_id)
    nuevo_id = st.session_state.siguiente_id_ficha
    st.session_state.siguiente_id_ficha += 1
    st.session_state.fichas.append(
        {**original, "id": nuevo_id, "nombre": f"{original['nombre']} (copia)"[:50], "activa": False}
    )
    sincronizar_toggles(nuevo_id, False)
    st.session_state.ficha_seleccionada = nuevo_id


def _eliminar(ficha_id: int) -> None:
    st.session_state.fichas = [f for f in st.session_state.fichas if f["id"] != ficha_id]
    for k in (f"side_{ficha_id}", f"edit_act_{ficha_id}"):
        st.session_state.pop(k, None)
    if st.session_state.fichas:
        st.session_state.ficha_seleccionada = st.session_state.fichas[0]["id"]
    st.toast("Ficha eliminada", icon="🗑️")


# ---------------------------------------------------------------- pantalla
def render_fichas() -> None:
    st.title("Fichas de contexto")
    st.caption("Las fichas guardan información recurrente que la IA usará en tus artículos.")

    col_lista, col_editor = st.columns(2, gap="large")

    with col_lista:
        c1, c2 = st.columns([3, 2])
        busqueda = c1.text_input("Buscar", placeholder="Buscar fichas...", label_visibility="collapsed")
        c2.button("Nueva ficha", icon=":material/add:", type="primary", on_click=_nueva, width="stretch")

        for f in st.session_state.fichas:
            texto = f"{f['nombre']} {f['tipo']} {f['contenido']}".lower()
            if busqueda.lower() not in texto:
                continue
            seleccionada = f["id"] == st.session_state.ficha_seleccionada
            with st.container(border=True):
                st.button(
                    f"{f['nombre']}  ·  {f['tipo']}",
                    key=f"sel_{f['id']}",
                    on_click=_seleccionar,
                    args=(f["id"],),
                    type="primary" if seleccionada else "secondary",
                    width="stretch",
                )
                resumen = f["contenido"].replace("\n", " ")
                st.caption(resumen[:90] + ("…" if len(resumen) > 90 else "") if resumen else "Sin contenido")

    with col_editor:
        f = buscar_ficha(st.session_state.ficha_seleccionada)
        with st.container(border=True):
            st.subheader("Editar ficha")
            if f is None:
                st.info("Selecciona o crea una ficha.")
                return
            fid = f["id"]
            st.text_input("Nombre de la ficha", value=f["nombre"], max_chars=50, key=f"nombre_{fid}")
            st.selectbox("Tipo", TIPOS_FICHA, index=TIPOS_FICHA.index(f["tipo"]), key=f"tipo_{fid}")
            st.text_area("Contenido de la ficha", value=f["contenido"], max_chars=2000, height=280, key=f"contenido_{fid}")
            key_act = f"edit_act_{fid}"
            st.toggle(
                "Activa",
                key=key_act,
                help="La ficha estará disponible para el generador y el chat.",
                on_change=al_cambiar_activa,
                args=(fid, key_act),
            )
            b1, b2, b3 = st.columns(3)
            b1.button("Guardar", icon=":material/save:", type="primary", on_click=_guardar, args=(fid,), width="stretch")
            b2.button("Duplicar", icon=":material/content_copy:", on_click=_duplicar, args=(fid,), width="stretch")
            b3.button("Eliminar", icon=":material/delete:", on_click=_eliminar, args=(fid,), width="stretch")
