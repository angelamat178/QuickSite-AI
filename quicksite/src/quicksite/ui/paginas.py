"""Páginas y borradores: lista con filtros y selección múltiple + editor con vista previa y flujo de estados."""
from __future__ import annotations

import streamlit as st

from quicksite.core import datos_simulados as ds
from quicksite.core import simulado as sim
from quicksite.ui import componentes as c
from quicksite.ui import estado as e

FILTROS = ["Todas"] + ds.ESTADOS_PAGINA


def _nueva() -> None:
    st.session_state.modo = "Construcción"
    st.session_state.pagina = "generador"
    e.descartar_borrador()


def _flujo(p: dict) -> None:
    """Botones del flujo Borrador → En revisión → Aprobada → Publicada."""
    pid, est = p["id"], p["estado"]
    if est == "Borrador":
        st.button("Enviar a revisión", type="primary", key=f"wf_{pid}", on_click=e.cambiar_estado,
                  args=([pid], "En revisión"), use_container_width=True)
    elif est == "En revisión":
        a, b = st.columns(2)
        a.button("Aprobar", type="primary", key=f"wf_{pid}", on_click=e.cambiar_estado, args=([pid], "Aprobada"),
                 use_container_width=True)
        b.button("Devolver a borrador", key=f"wf2_{pid}", on_click=e.cambiar_estado, args=([pid], "Borrador"),
                 use_container_width=True)
    elif est == "Aprobada":
        a, b = st.columns(2)
        a.button("Publicar (demo)", type="primary", key=f"wf_{pid}", on_click=e.cambiar_estado, args=([pid], "Publicada"),
                 use_container_width=True)
        b.button("Volver a revisión", key=f"wf2_{pid}", on_click=e.cambiar_estado, args=([pid], "En revisión"),
                 use_container_width=True)
    else:
        st.button("Despublicar (demo)", key=f"wf_{pid}", on_click=e.cambiar_estado, args=([pid], "Borrador"),
                  use_container_width=True)
    if e.tiene_pendientes(p) and est in ("Borrador", "En revisión"):
        st.caption("Hay marcadores [PENDIENTE]: complétalos para poder aprobar y publicar.")


def _editor(p: dict | None) -> None:
    ss = st.session_state
    with st.container(key="panel_editor_pag"):
        if p is None:
            st.markdown(c.estado_vacio("Ninguna página seleccionada", "Elige una página de la lista para editarla.", "documento"),
                        unsafe_allow_html=True)
            return
        pid, b, r = p["id"], p["b"], ss.pag_rev
        nota, checks = sim.puntuacion_seo(b)
        st.markdown('<div class="qs-title-sm" style="font-size:1.25rem">Editar página</div>', unsafe_allow_html=True)
        st.markdown(f'{c.etiqueta_estado(p["estado"])} {c.pill_seo(nota)} '
                    f'{c.chip_wp() if b["enviado"] else ""}', unsafe_allow_html=True)
        t_edit, t_prev, t_seo = st.tabs(["Editar", "Vista previa", "SEO"])
        with t_edit:
            st.text_input("Título", value=b["titulo"], key=f"pe_titulo_{pid}_{r}", max_chars=200)
            st.text_input("Slug (URL)", value=b["slug"], key=f"pe_slug_{pid}_{r}", max_chars=80)
            st.text_area("Meta descripción", value=b["meta_descripcion"], key=f"pe_meta_{pid}_{r}", max_chars=160, height=90)
            st.text_area("Cuerpo (## subtítulo, - lista, 1. numerada, **negrita**)", value=b["cuerpo"],
                         key=f"pe_cuerpo_{pid}_{r}", height=240)
            g, d, x = st.columns(3)
            g.button("Guardar", type="primary", key=f"pg_{pid}", on_click=e.guardar_pagina, args=(pid,), use_container_width=True)
            d.button("Duplicar", key=f"pd_{pid}", on_click=e.duplicar_pagina, args=(pid,), use_container_width=True)
            x.button("Eliminar", key=f"px_{pid}", on_click=e.pedir_eliminar_pagina, args=(pid,), use_container_width=True)
            if ss.confirmar_eliminar_pag == pid:
                st.warning(f"¿Eliminar «{b['titulo']}»? Esta acción no se puede deshacer.")
                s, n = st.columns(2)
                s.button("Sí, eliminar", type="primary", key=f"pxs_{pid}", on_click=e.eliminar_paginas, args=([pid],),
                         use_container_width=True)
                n.button("Cancelar", key=f"pxn_{pid}", on_click=e.cancelar_eliminar_pagina, use_container_width=True)
        with t_prev:
            with st.container(height=420, border=False):
                st.markdown(c.vista_previa_html(b), unsafe_allow_html=True)
        with t_seo:
            st.markdown(c.checklist_html(nota, checks), unsafe_allow_html=True)
        _flujo(p)
        st.button("Abrir en el generador (editar con IA)", key=f"pgen_{pid}", on_click=e.abrir_en_generador, args=(pid,),
                  use_container_width=True)
        st.caption("Simulación: publicar no envía nada a WordPress. Siempre decide una persona.")


def render() -> None:
    ss = st.session_state
    st.markdown(c.cabecera_pagina("Páginas y borradores",
                                  "Revisa, edita y publica todo lo que has generado, de una en una o en bloque."),
                unsafe_allow_html=True)
    cuentas = {f: (len(ss.paginas) if f == "Todas" else sum(p["estado"] == f for p in ss.paginas)) for f in FILTROS}
    a, b = st.columns([4, 1.2], vertical_alignment="center")
    a.radio("Estado", FILTROS, key="p_filtro", horizontal=True, label_visibility="collapsed",
            format_func=lambda f: f"{f} ({cuentas[f]})")
    b.button("＋ Nueva página", type="primary", key="btn_nueva_pag", on_click=_nueva, use_container_width=True)
    q = st.text_input("Buscar", key="p_buscar", placeholder="Buscar por título, ciudad o palabra clave...",
                      label_visibility="collapsed")
    filtro = ss.get("p_filtro") or "Todas"
    qn = (q or "").strip().lower()
    vistas = [p for p in ss.paginas
              if (filtro == "Todas" or p["estado"] == filtro)
              and (not qn or qn in p["b"]["titulo"].lower() or qn in p["b"].get("ciudad", "").lower()
                   or qn in p["b"]["palabra_clave"].lower())]

    izq, der = st.columns([1.5, 1], gap="large")
    with izq:
        with st.container(key="panel_lista_pag"):
            barra = st.columns([1.1, 1.1, 1, 1, 1.4, 0.9])
            barra[0].button("Seleccionar todo", key="pb_todas", on_click=e.accion_masa, args=("pag", "todas"), use_container_width=True)
            barra[1].button("Ninguna", key="pb_ninguna", on_click=e.accion_masa, args=("pag", "ninguna"), use_container_width=True)
            barra[2].button("A revisión", key="pb_rev", on_click=e.accion_masa, args=("pag", "revision"), use_container_width=True)
            barra[3].button("Aprobar", key="pb_apr", on_click=e.accion_masa, args=("pag", "aprobar"), use_container_width=True)
            barra[4].button("Publicar (demo)", key="pb_pub", on_click=e.accion_masa, args=("pag", "publicar"), use_container_width=True)
            barra[5].button("Borrar", key="pb_del", on_click=e.accion_masa, args=("pag", "eliminar"), use_container_width=True)
            if not vistas:
                st.markdown(c.estado_vacio("Sin resultados", "No hay páginas con ese filtro.", "documento"),
                            unsafe_allow_html=True)
            with st.container(height=520, border=False):
                for p in vistas:
                    pid, bb = p["id"], p["b"]
                    with st.container(key=f"prow_{pid}"):
                        cols = st.columns([0.35, 3.1, 1.25, 0.8, 0.9], vertical_alignment="center")
                        cols[0].checkbox("Seleccionar", key=f"psel_{pid}", label_visibility="collapsed")
                        sub = " · ".join(x for x in [bb.get("ciudad"), sim.fecha_corta(bb["fecha"]), f"{bb['palabras']} palabras"] if x)
                        cols[1].markdown(f'<div class="qs-pt">{c.esc(bb["titulo"])}</div><div class="qs-ps">/{c.esc(bb["slug"])} · {c.esc(sub)}</div>',
                                         unsafe_allow_html=True)
                        cols[2].markdown(c.etiqueta_estado(p["estado"]), unsafe_allow_html=True)
                        cols[3].markdown(c.pill_seo(sim.puntuacion_seo(bb)[0]), unsafe_allow_html=True)
                        cols[4].button("Editar", key=f"psel_btn_{pid}", on_click=e.seleccionar_pagina, args=(pid,),
                                       use_container_width=True)
    with der:
        _editor(e.buscar_pagina(ss.pagina_sel))
