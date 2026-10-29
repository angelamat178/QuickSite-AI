"""Pantalla Fichas de contexto: listar, buscar, crear, editar, duplicar y eliminar."""
from __future__ import annotations

import streamlit as st

from quicksite.core import datos_simulados as ds
from quicksite.ui import componentes as c
from quicksite.ui import estado as e


def render() -> None:
    ss = st.session_state
    izq, der = st.columns([1.05, 1], gap="large")

    with izq:
        with st.container(key="panel_lista"):
            st.markdown('<div class="qs-title-sm" style="font-size:1.35rem">Fichas de contexto</div>', unsafe_allow_html=True)
            st.markdown('<div class="qs-sub">Las fichas te permiten guardar información recurrente que la IA usará en tus artículos.</div>',
                        unsafe_allow_html=True)
            a, b = st.columns([3, 1.3], vertical_alignment="bottom")
            q = a.text_input("Buscar", key="f_buscar", placeholder="Buscar fichas...", label_visibility="collapsed")
            b.button("＋ Nueva ficha", type="primary", key="btn_nueva_ficha", on_click=e.nueva_ficha, use_container_width=True)
            qn = (q or "").strip().lower()
            vistas = [f for f in ss.fichas if not qn or qn in f["nombre"].lower() or qn in f["contenido"].lower()]
            if not vistas:
                st.markdown(c.estado_vacio("Sin resultados", "Ninguna ficha coincide con la búsqueda."), unsafe_allow_html=True)
            for f in vistas:
                with st.container(key=f"fc_{f['id']}"):
                    x, y = st.columns([5, 1.2], vertical_alignment="center")
                    x.markdown(c.ficha_card_html(f), unsafe_allow_html=True)
                    y.button("Editar", key=f"sel_{f['id']}", on_click=e.seleccionar_ficha, args=(f["id"],),
                             use_container_width=True)

    with der:
        with st.container(key="panel_editor"):
            f = e.buscar_ficha(ss.ficha_sel) if ss.ficha_sel else None
            if f is None:
                st.markdown(c.estado_vacio("Ninguna ficha seleccionada", "Elige una ficha o crea una nueva.", "documento"),
                            unsafe_allow_html=True)
                return
            fid = f["id"]
            st.markdown('<div class="qs-title-sm" style="font-size:1.35rem">Editar ficha</div>', unsafe_allow_html=True)
            st.text_input("Nombre de la ficha", value=f["nombre"], key=f"f_nombre_{fid}", max_chars=50)
            st.selectbox("Tipo", ds.TIPOS_FICHA, index=ds.TIPOS_FICHA.index(f["tipo"]) if f["tipo"] in ds.TIPOS_FICHA else 0,
                         key=f"f_tipo_{fid}")
            st.text_area("Contenido de la ficha", value=f["contenido"], key=f"f_cont_{fid}", max_chars=2000, height=300)
            clave = f"f_act_{fid}"
            ss[clave] = f["activa"]  # fuente de verdad única: la ficha
            st.toggle("Activa", key=clave, on_change=e.alternar_ficha, args=(fid, clave),
                      help="La ficha estará disponible para ser usada en el generador y el chat.")
            st.caption(f"La ficha estará disponible para ser usada en el generador y el chat. Máximo {ds.LIMITE_FICHAS_ACTIVAS} activas.")
            g, d, x = st.columns(3)
            g.button("Guardar", type="primary", key=f"btn_guardar_{fid}", on_click=e.guardar_ficha, args=(fid,),
                     use_container_width=True)
            d.button("Duplicar", key=f"btn_dup_{fid}", on_click=e.duplicar_ficha, args=(fid,), use_container_width=True)
            x.button("Eliminar", key=f"btn_del_{fid}", on_click=e.pedir_eliminar, args=(fid,), use_container_width=True)
            if ss.confirmar_eliminar == fid:
                st.warning(f"¿Eliminar la ficha «{f['nombre']}»? Esta acción no se puede deshacer.")
                s, n = st.columns(2)
                s.button("Sí, eliminar", type="primary", key=f"btn_si_{fid}", on_click=e.eliminar_ficha, args=(fid,),
                         use_container_width=True)
                n.button("Cancelar", key=f"btn_no_{fid}", on_click=e.cancelar_eliminar, use_container_width=True)
