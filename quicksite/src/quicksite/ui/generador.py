"""Pantalla Generador: UNA conversación y UNA previsualización.

El interruptor Construcción/Chat no abre dos funciones distintas: indica a la IA cómo actuar.
  · Construcción = agente: sus respuestas modifican la previsualización.
  · Chat         = consulta: responde sobre la preview o cualquier tema, sin modificarla.
"""
from __future__ import annotations

import copy

import streamlit as st

from quicksite.core import datos_simulados as ds
from quicksite.core import simulado as sim
from quicksite.ui import componentes as c
from quicksite.ui import estado as e

SUG_CONSTRUCCION = [("Acortar", "Acorta el artículo"), ("Otro título", "Propón otro título"),
                    ("Añadir FAQ", "Añade una pregunta frecuente"), ("Costes y plazos", "Añade una sección de costes y plazos")]
SUG_CHAT = [("Puntuación SEO", "¿Qué puntuación SEO tiene la preview?"), ("Resumir", "Resume la preview"),
            ("Palabras", "¿Cuántas palabras tiene?"), ("Cambiar título", "Cambia el título")]


# ------------------------------------------------------------------ acciones
def _generar() -> None:
    ss = st.session_state
    peticion = (ss.get("g_tema") or "").strip()
    if not peticion:
        st.toast("Escribe primero el tema o idea del artículo.", icon="⚠️")
        return
    longitud = next(k for k, lbl, *_ in ds.LONGITUDES if lbl == ss.g_longitud)
    b = sim.generar_borrador(peticion, ss.g_tono, longitud, ss.get("g_kw", ""), e.fichas_activas(), categoria="Guía")
    e.nuevo_borrador(b)
    ss.conv = []
    e.msg_usuario(peticion, "Construcción")
    e.msg_ia(c.resumen_borrador_html(b), "accion")
    ss.g_tema = ""


def _aplicar_refinado(texto: str) -> None:
    ss = st.session_state
    nuevo, resp = sim.refinar_borrador(ss.borrador, texto)
    cambio = nuevo is not ss.borrador
    if cambio:
        ss.prev_borrador = copy.deepcopy(ss.borrador)
        ss.borrador = nuevo
        ss.rev += 1
        e.sincronizar_historial(nuevo)
        e.sincronizar_pagina(nuevo)
    e.msg_ia(c.texto_a_burbuja(resp), "accion" if cambio else None)


def _enviar_texto(texto: str | None) -> None:
    ss = st.session_state
    texto = (texto or "").strip()
    if not texto:
        return
    e.msg_usuario(texto, ss.modo)
    if ss.modo == "Chat":
        resp, tag = sim.consulta(texto, len(e.fichas_activas()), ss.borrador)
        e.msg_ia(c.texto_a_burbuja(resp), tag)
    elif ss.borrador is None:
        b = sim.generar_borrador(texto, ss.get("g_tono") or "Profesional", "medio", "", e.fichas_activas(), categoria="Guía")
        e.nuevo_borrador(b)
        e.msg_ia(c.resumen_borrador_html(b), "accion")
    else:
        _aplicar_refinado(texto)


def _enviar() -> None:
    _enviar_texto(st.session_state.get("g_msg"))


def _agente(texto: str) -> None:
    """Acción explícita del editor: siempre actúa como agente, esté el modo que esté."""
    if st.session_state.borrador is None:
        return
    e.msg_usuario(texto, "Construcción")
    _aplicar_refinado(texto)


def _deshacer() -> None:
    ss = st.session_state
    if ss.prev_borrador is None:
        return
    ss.borrador = ss.prev_borrador
    ss.prev_borrador = None
    ss.rev += 1
    e.sincronizar_historial(ss.borrador)
    e.sincronizar_pagina(ss.borrador)
    e.msg_ia("<p>He deshecho el último cambio.</p>", "accion")


def _resolver_pendientes() -> None:
    ss = st.session_state
    b = ss.borrador
    if b is None:
        return
    if not sim.tiene_pendientes(b):
        st.toast("No hay marcadores [PENDIENTE] en la preview.", icon="✅")
        return
    ss.prev_borrador = copy.deepcopy(b)
    e.msg_usuario("Resuelve los marcadores [PENDIENTE] con los datos de las fichas", "Construcción")
    sim.completar_pendientes(b)
    ss.rev += 1
    e.sincronizar_historial(b)
    e.msg_ia("<p>[DEMOSTRACIÓN] He sustituido los marcadores por un texto neutro. Con un modelo real los "
             "rellenaría con los datos de tus fichas; revísalo antes de publicar.</p>", "accion")


def _aplicar_edicion() -> None:
    ss = st.session_state
    b = ss.borrador
    if b is None:
        return
    r = ss.rev
    titulo = (ss.get(f"e_titulo_{r}") or "").strip()
    if not titulo:
        st.toast("El título no puede estar vacío.", icon="⚠️")
        return
    b["titulo"] = titulo[:200]
    b["meta_descripcion"] = (ss.get(f"e_meta_{r}") or "")[:160]
    b["palabra_clave"] = (ss.get(f"e_kw_{r}") or "").strip()[:100]
    b["cuerpo"] = ss.get(f"e_cuerpo_{r}") or ""
    sim.recalcular(b)
    e.sincronizar_historial(b)
    st.toast("Cambios aplicados a la previsualización.", icon="✅")


# ------------------------------------------------------------------- vistas
def _formulario() -> None:
    """Estado inicial: sin borrador. Formulario a la izquierda, esqueleto a la derecha."""
    izq, der = st.columns([1.15, 1], gap="large")
    with izq:
        st.markdown(c.cabecera_pagina(
            "Genera un artículo para tu blog",
            "Escribe un tema y deja que la IA cree un artículo optimizado para WordPress, listo para publicar."),
            unsafe_allow_html=True)
        with st.container(key="panel_form"):
            t1, t2 = st.tabs(["Con IA", "Desde plantilla"])
            with t1:
                st.text_input("Tema o idea del artículo *", key="g_tema", max_chars=200,
                              placeholder="Ej.: Beneficios del marketing de contenidos para pequeñas empresas")
                st.markdown('<div class="qs-lbl">Tono de voz</div>', unsafe_allow_html=True)
                st.radio("Tono de voz", ds.TONOS, key="g_tono", horizontal=True, label_visibility="collapsed")
                st.markdown('<div class="qs-lbl">Longitud del artículo</div>', unsafe_allow_html=True)
                st.radio("Longitud", [x[1] for x in ds.LONGITUDES], index=1, key="g_longitud",
                         horizontal=True, label_visibility="collapsed")
                st.text_input("Palabras clave (opcional)", key="g_kw", max_chars=100,
                              placeholder="Añade algunas palabras clave separadas por comas")
                with st.expander("Opciones avanzadas · Meta descripción, categoría, idioma, etc."):
                    st.caption("Disponible cuando se conecte el modelo. En la demo se usa categoría «Guía» e idioma castellano.")
                st.button("✦  Generar artículo", type="primary", on_click=_generar, key="btn_generar")
            with t2:
                st.markdown(c.estado_vacio("Plantillas", "Para crear muchas páginas con la misma plantilla usa «En masa»."),
                            unsafe_allow_html=True)
                st.button("Ir a generación en masa", key="btn_ir_masivo", on_click=e.ir_a, args=("masivo",))
    with der:
        with st.container(key="panel_vista_vacia"):
            st.markdown('<div class="qs-title-sm">Vista previa del artículo</div>', unsafe_allow_html=True)
            st.markdown(c.esqueleto_html(), unsafe_allow_html=True)


def _panel_preview(b: dict) -> None:
    ss = st.session_state
    with st.container(key="panel_prev"):
        if b is None:
            st.markdown('<div class="qs-title-sm">Previsualización</div>', unsafe_allow_html=True)
            st.markdown(c.esqueleto_html(), unsafe_allow_html=True)
            st.caption("Aún no hay artículo. En Construcción, descríbelo en la conversación y la IA lo creará aquí.")
            return
        nota, checks = sim.puntuacion_seo(b)
        h1, h2 = st.columns([3, 1], vertical_alignment="center")
        h1.markdown('<div class="qs-title-sm">Previsualización</div>', unsafe_allow_html=True)
        h2.markdown(c.pill_seo(nota), unsafe_allow_html=True)
        t_prev, t_edit, t_seo = st.tabs(["Previsualización", "Editar", "SEO"])
        with t_prev:
            st.markdown(c.vista_previa_html(b), unsafe_allow_html=True)
        with t_edit:
            st.caption("Acciones rápidas de la IA (siempre actúan sobre la preview):")
            q = st.columns(4)
            q[0].button("Reescribir intro", key="q_intro", on_click=_agente, args=("Reescribe la introducción",), use_container_width=True)
            q[1].button("Mejorar meta", key="q_meta", on_click=_agente, args=("Mejora la meta descripción",), use_container_width=True)
            q[2].button("Acortar", key="q_acortar", on_click=_agente, args=("Acorta el artículo",), use_container_width=True)
            q[3].button("Añadir FAQ", key="q_faq", on_click=_agente, args=("Añade una pregunta frecuente",), use_container_width=True)
            r = ss.rev
            with st.form(f"form_editar_{r}", border=False):
                st.text_input("Título del artículo", value=b["titulo"], key=f"e_titulo_{r}", max_chars=200)
                st.text_area("Meta descripción", value=b["meta_descripcion"], key=f"e_meta_{r}", max_chars=160, height=100)
                st.text_input("Palabra clave", value=b["palabra_clave"], key=f"e_kw_{r}", max_chars=100)
                st.text_area("Cuerpo (## subtítulo, - lista, 1. numerada, **negrita**)", value=b["cuerpo"],
                             key=f"e_cuerpo_{r}", height=260)
                st.form_submit_button("Aplicar cambios", type="primary", on_click=_aplicar_edicion)
        with t_seo:
            st.markdown(c.checklist_html(nota, checks), unsafe_allow_html=True)
            st.button("Resolver marcadores [PENDIENTE] (demo)", key="btn_pend", on_click=_resolver_pendientes,
                      use_container_width=True, disabled=not sim.tiene_pendientes(b))
        for a in b["avisos"]:
            st.markdown(f'<div class="qs-banner">{c.esc(a)}</div>', unsafe_allow_html=True)
        if b["enviado"]:
            st.success("[DEMOSTRACIÓN] Enviado como borrador (simulado). Lo verás en «Páginas».")
        x, y = st.columns(2)
        x.button("Enviar a WordPress como borrador", type="primary", key="btn_enviar_wp",
                 on_click=e.enviar_simulado, use_container_width=True)
        y.button("Ver en Páginas", key="btn_ver_paginas", on_click=e.ir_a, args=("paginas",), use_container_width=True)
        st.caption("Simulación: no se hace ninguna petición a WordPress ni se publica nada.")


def _vista_unificada() -> None:
    ss = st.session_state
    b = ss.borrador
    izq, der = st.columns([1.1, 1], gap="large")
    with izq:
        with st.container(height=470, border=False, key="scroll_msgs"):
            st.markdown(c.mensajes_html(ss.conv), unsafe_allow_html=True)
        sugs = SUG_CHAT if ss.modo == "Chat" else (SUG_CONSTRUCCION if b is not None else [])
        if sugs:
            cols = st.columns(len(sugs))
            for i, (col, (lbl, txt)) in enumerate(zip(cols, sugs)):
                col.button(lbl, key=f"sug_{ss.modo}_{i}", on_click=_enviar_texto, args=(txt,), use_container_width=True)
        if ss.modo == "Chat":
            ph = "Pregunta sobre la preview o cualquier otro tema..."
        elif b is None:
            ph = "Describe el artículo que quieres crear..."
        else:
            ph = "Escribe una instrucción para modificar la preview..."
        with st.form("form_conv", clear_on_submit=True, border=False):
            a, bt = st.columns([6, 1.2], vertical_alignment="bottom")
            a.text_input("Mensaje", key="g_msg", label_visibility="collapsed", placeholder=ph)
            bt.form_submit_button("Enviar", type="primary", use_container_width=True, on_click=_enviar)
        n1, n2, _ = st.columns([1.3, 1.3, 2])
        n1.button("Nuevo artículo", key="btn_nuevo", on_click=e.descartar_borrador, use_container_width=True)
        if ss.prev_borrador is not None:
            n2.button("↶ Deshacer cambio", key="btn_deshacer", on_click=_deshacer, use_container_width=True)
    with der:
        _panel_preview(b)


def render() -> None:
    ss = st.session_state
    if ss.modo == "Construcción" and ss.borrador is None and len(ss.conv) <= 1:
        _formulario()
    else:
        _vista_unificada()
