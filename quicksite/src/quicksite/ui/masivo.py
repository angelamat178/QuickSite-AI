"""Generación en masa: una plantilla + una variable (p. ej. ciudad) → de 1 a 50 páginas, con cola de revisión."""
from __future__ import annotations

import streamlit as st

from quicksite.core import datos_simulados as ds
from quicksite.core import simulado as sim
from quicksite.ui import componentes as c
from quicksite.ui import estado as e


def _config() -> None:
    ss = st.session_state
    with st.container(key="panel_masivo_cfg"):
        st.markdown('<div class="qs-title-sm">1 · Plantilla y variables</div>', unsafe_allow_html=True)
        st.selectbox("Plantilla base", [p["nombre"] for p in ds.PLANTILLAS_MASIVO], key="m_plantilla")
        st.text_area("Variable {ciudad} · una por línea", key="m_vars", height=190)
        n = len(e.parsear_variables(ss.get("m_vars")))
        st.markdown(f'<div class="qs-lbl">{n} variable(s) detectada(s) · máximo {ds.LIMITE_MASIVO} por lote</div>',
                    unsafe_allow_html=True)
        a, b = st.columns([2.2, 1], vertical_alignment="bottom")
        a.slider("Rellenar con las N ciudades más grandes", 1, ds.LIMITE_MASIVO, key="m_n")
        b.button("Rellenar", key="btn_rellenar", on_click=e.rellenar_ciudades, use_container_width=True)
        st.markdown('<div class="qs-lbl">Tono de voz</div>', unsafe_allow_html=True)
        st.radio("Tono", ds.TONOS, key="m_tono", horizontal=True, label_visibility="collapsed")
        st.markdown('<div class="qs-lbl">Longitud</div>', unsafe_allow_html=True)
        st.radio("Longitud", [x[1] for x in ds.LONGITUDES], key="m_long", horizontal=True, label_visibility="collapsed")
        st.checkbox(f"Usar las {len(e.fichas_activas())} fichas activas como contexto", key="m_fichas")
        st.markdown('<div class="qs-banner">Todas las páginas comparten estructura. Los datos locales se dejan como '
                    '[PENDIENTE] para que cada una sea distinta y no se inventen datos.</div>', unsafe_allow_html=True)
        st.button(f"✦  Generar {n} página(s)" if n else "✦  Generar páginas", type="primary", key="btn_lote",
                  on_click=e.generar_lote, disabled=n == 0, use_container_width=True)
        st.caption("Demo: el resultado es instantáneo y siempre el mismo. No se llama a ningún modelo.")


def _resultados() -> None:
    ss = st.session_state
    paginas = [p for p in (e.buscar_pagina(i) for i in ss.m_lote) if p]
    with st.container(key="panel_masivo_res"):
        st.markdown('<div class="qs-title-sm">2 · Revisión del lote</div>', unsafe_allow_html=True)
        if not paginas:
            st.markdown(c.estado_vacio("Aún no hay lote", "Configura la plantilla y pulsa «Generar». Las páginas aparecerán aquí para revisarlas.",
                                       "documento"), unsafe_allow_html=True)
            return
        notas = [sim.puntuacion_seo(p["b"])[0] for p in paginas]
        k = [("Generadas", str(len(paginas)), "", True),
             ("SEO medio", f"{round(sum(notas) / len(notas))}", "", True),
             ("Con [PENDIENTE]", str(sum(e.tiene_pendientes(p) for p in paginas)), "", False),
             ("Aprobadas / publicadas", str(sum(p["estado"] in ("Aprobada", "Publicada") for p in paginas)), "", True)]
        st.markdown(
            '<div class="qs-kpis">' + "".join(
                f'<div class="qs-kpi"><div class="qs-kpi-l">{c.esc(l)}</div><div class="qs-kpi-v">{c.esc(v)}</div></div>'
                for l, v, _, _ in k) + '</div>', unsafe_allow_html=True)
        acc = st.columns([1.1, 1.5, 0.9, 1.5, 1.2])
        acc[0].button("Seleccionar todas", key="mb_todas", on_click=e.accion_masa, args=("lote", "todas"), use_container_width=True)
        acc[1].button("Rellenar datos (fichas)", key="mb_rell", on_click=e.accion_masa, args=("lote", "rellenar"), use_container_width=True)
        acc[2].button("Aprobar", key="mb_apr", on_click=e.accion_masa, args=("lote", "aprobar"), use_container_width=True)
        acc[3].button("Enviar a WP (borrador)", key="mb_wp", on_click=e.accion_masa, args=("lote", "wp"), use_container_width=True)
        acc[4].button("Publicar (demo)", type="primary", key="mb_pub", on_click=e.accion_masa, args=("lote", "publicar"),
                      use_container_width=True)
        with st.container(height=300, border=False):
            for i, p in enumerate(paginas):
                pid, bb = p["id"], p["b"]
                with st.container(key=f"mrow_{pid}"):
                    cols = st.columns([0.35, 1.5, 2.6, 0.8, 1.2, 0.9], vertical_alignment="center")
                    cols[0].checkbox("Seleccionar", key=f"msel_{pid}", label_visibility="collapsed")
                    cols[1].markdown(f'<div class="qs-pt">{c.esc(bb.get("ciudad", ""))}</div>', unsafe_allow_html=True)
                    pend = " · ⚠ [PENDIENTE]" if e.tiene_pendientes(p) else ""
                    cols[2].markdown(f'<div class="qs-ps">{c.esc(bb["titulo"])}{pend}</div>', unsafe_allow_html=True)
                    cols[3].markdown(c.pill_seo(sim.puntuacion_seo(bb)[0]), unsafe_allow_html=True)
                    cols[4].markdown(c.etiqueta_estado(p["estado"]), unsafe_allow_html=True)
                    cols[5].button("Revisar", key=f"mrev_{pid}", on_click=e.revisar, args=(i,), use_container_width=True)
        idx = min(max(ss.m_idx, 0), len(paginas) - 1)
        p = paginas[idx]
        st.markdown(f'<div class="qs-lbl" style="margin-top:.8rem">Revisando {idx + 1} de {len(paginas)} · '
                    f'{c.esc(p["b"].get("ciudad", ""))}</div>', unsafe_allow_html=True)
        with st.container(height=300, border=False):
            st.markdown(c.vista_previa_html(p["b"]), unsafe_allow_html=True)
        r = st.columns(4)
        r[0].button("◀ Anterior", key="mr_ant", on_click=e.mover_revision, args=(-1,), use_container_width=True)
        r[1].button("Siguiente ▶", key="mr_sig", on_click=e.mover_revision, args=(1,), use_container_width=True)
        r[2].button("Aprobar y siguiente", type="primary", key="mr_apr", on_click=e.aprobar_y_siguiente, args=(p["id"],),
                    use_container_width=True)
        r[3].button("Editar en Páginas", key="mr_edit", on_click=_editar, args=(p["id"],), use_container_width=True)


def _editar(pid: str) -> None:
    e.seleccionar_pagina(pid)
    e.ir_a("paginas")


def render() -> None:
    st.markdown(c.cabecera_pagina(
        "Generación en masa",
        "Crea de 1 a 50 páginas a partir de una misma plantilla cambiando una variable (por ejemplo, la ciudad) y revísalas en bloque."),
        unsafe_allow_html=True)
    izq, der = st.columns([1, 1.6], gap="large")
    with izq:
        _config()
    with der:
        _resultados()
