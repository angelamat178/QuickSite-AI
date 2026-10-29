"""Estado de sesión de Streamlit y acciones (callbacks) de la interfaz."""
from __future__ import annotations

import copy
import html as _html
import uuid
from datetime import timedelta

import streamlit as st

from quicksite.core import datos_simulados as ds
from quicksite.core import simulado as sim

MSG_INICIAL_CHAT = (
    "¡Hola! Soy QuickSite en <strong>modo demostración</strong>. En <strong>Construcción</strong> actúo como "
    "agente y modifico la previsualización; en <strong>Chat</strong> solo respondo y consulto, sin tocarla."
)


def iniciar() -> None:
    ss = st.session_state
    if ss.get("_iniciado"):
        return
    ss.pagina = "generador"
    ss.modo = "Construcción"
    ss.fichas = copy.deepcopy(ds.FICHAS_INICIALES)
    ss.ficha_sel = ss.fichas[0]["id"]
    ss.historial = ds.historial_inicial()
    ss.borrador = None
    ss.prev_borrador = None
    ss.rev = 0
    ss.conv = [_bienvenida()]
    ss.paginas = _paginas_iniciales()
    ss.pagina_sel = None
    ss.confirmar_eliminar_pag = None
    ss.pag_rev = 0
    ss.lote_n = 2
    ss.m_lote = []
    ss.m_idx = 0
    ss.m_plantilla = ds.PLANTILLAS_MASIVO[0]["nombre"]
    ss.m_n = 8
    ss.m_vars = "\n".join(ds.CIUDADES[:8])
    ss.m_tono = "Profesional"
    ss.m_long = ds.LONGITUDES[0][1]
    ss.m_fichas = True
    ss.sc_conectado = False
    ss.sc_dias = 28
    ss.hist_abierto = None
    ss.confirmar_eliminar = None
    ss.wp_demo_activo = True  # simulado: nunca hay conexión real
    ss._iniciado = True


# ------------------------------------------------------------------ fichas
def buscar_ficha(fid: str) -> dict | None:
    return next((f for f in st.session_state.fichas if f["id"] == fid), None)


def fichas_activas() -> list[dict]:
    return [f for f in st.session_state.fichas if f["activa"]]


def ir_a(pagina: str) -> None:
    st.session_state.pagina = pagina


def set_modo(modo: str) -> None:
    st.session_state.modo = modo
    st.session_state.pagina = "generador"


def alternar_ficha(fid: str, clave: str) -> None:
    """Callback de los interruptores. Respeta el límite de fichas activas."""
    ss = st.session_state
    ficha = buscar_ficha(fid)
    if ficha is None:
        return
    quiere = bool(ss.get(clave, False))
    if quiere:
        otras = sum(1 for f in ss.fichas if f["activa"] and f["id"] != fid)
        if otras >= ds.LIMITE_FICHAS_ACTIVAS:
            ss[clave] = False
            st.toast(f"Límite alcanzado: máximo {ds.LIMITE_FICHAS_ACTIVAS} fichas activas.", icon="⚠️")
            return
    ficha["activa"] = quiere


def seleccionar_ficha(fid: str) -> None:
    st.session_state.ficha_sel = fid
    st.session_state.confirmar_eliminar = None


def nueva_ficha() -> None:
    ss = st.session_state
    fid = "ficha_" + uuid.uuid4().hex[:6]
    ss.fichas.append({
        "id": fid, "nombre": "Nueva ficha", "tipo": "General",
        "descripcion": "Ficha sin contenido todavía.", "contenido": "", "activa": False,
    })
    seleccionar_ficha(fid)


def guardar_ficha(fid: str) -> None:
    ss = st.session_state
    f = buscar_ficha(fid)
    if f is None:
        return
    nombre = (ss.get(f"f_nombre_{fid}") or "").strip()
    if not nombre:
        st.toast("El nombre de la ficha no puede estar vacío.", icon="⚠️")
        return
    f["nombre"] = nombre[:50]
    f["tipo"] = ss.get(f"f_tipo_{fid}", f["tipo"])
    f["contenido"] = ss.get(f"f_cont_{fid}", f["contenido"])
    primera = " ".join(f["contenido"].split())[:90]
    f["descripcion"] = primera or "Ficha sin contenido todavía."
    st.toast("Ficha guardada.", icon="✅")


def duplicar_ficha(fid: str) -> None:
    f = buscar_ficha(fid)
    if f is None:
        return
    c = copy.deepcopy(f)
    c["id"] = "ficha_" + uuid.uuid4().hex[:6]
    c["nombre"] = (f["nombre"] + " (copia)")[:50]
    c["activa"] = False
    st.session_state.fichas.append(c)
    seleccionar_ficha(c["id"])
    st.toast("Ficha duplicada (inactiva).", icon="✅")


def pedir_eliminar(fid: str) -> None:
    st.session_state.confirmar_eliminar = fid


def cancelar_eliminar() -> None:
    st.session_state.confirmar_eliminar = None


def eliminar_ficha(fid: str) -> None:
    ss = st.session_state
    ss.fichas = [f for f in ss.fichas if f["id"] != fid]
    ss.confirmar_eliminar = None
    ss.ficha_sel = ss.fichas[0]["id"] if ss.fichas else None
    st.toast("Ficha eliminada.", icon="🗑️")


# --------------------------------------------------------------- borrador
def nuevo_borrador(b: dict) -> None:
    """Instala un borrador nuevo y lo registra en el historial."""
    ss = st.session_state
    ss.rev += 1
    ss.borrador = b
    ss.prev_borrador = None
    entrada = sim.entrada_historial(b)
    b["hist_id"] = entrada["id"]
    ss.historial.insert(0, entrada)


def sincronizar_historial(b: dict) -> None:
    for h in st.session_state.historial:
        if h["id"] == b.get("hist_id"):
            nueva = sim.entrada_historial(b)
            h.update(titulo=nueva["titulo"], lectura=nueva["lectura"], resumen=nueva["resumen"],
                     estado=nueva["estado"])


def descartar_borrador() -> None:
    ss = st.session_state
    ss.borrador = None
    ss.prev_borrador = None
    ss.conv = [_bienvenida()]
    ss.rev += 1


def enviar_simulado() -> None:
    """Simula el envío a WordPress. No hace ninguna petición de red."""
    ss = st.session_state
    b = ss.borrador
    if b is None:
        return
    b["enviado"] = True
    sincronizar_historial(b)
    if buscar_pagina(b.get("pag_id")) is None:
        registrar_pagina(b, "Borrador")
    sitio = ss.get("sitio", ds.SITIOS_WP[0])
    st.toast(f"[DEMOSTRACIÓN] Envío simulado a «{sitio}». No se ha enviado ni publicado nada.", icon="🧪")


def reenviar(hid: str) -> None:
    for h in st.session_state.historial:
        if h["id"] == hid:
            h["estado"] = "Enviada como borrador"
            st.toast("[DEMOSTRACIÓN] Reenvío simulado. No se ha enviado nada a WordPress.", icon="🧪")
            return


# ------------------------------------------------------------ conversación
def _bienvenida() -> dict:
    return {"rol": "ia", "html": f"<p>{MSG_INICIAL_CHAT}</p>", "hora": sim.hora(), "tag": None}


def msg_usuario(texto: str, modo: str | None = None) -> None:
    st.session_state.conv.append({"rol": "user", "texto": texto, "hora": sim.hora(), "modo": modo})


def msg_ia(html: str, tag: str | None = None) -> None:
    st.session_state.conv.append({"rol": "ia", "html": html, "hora": sim.hora(), "tag": tag})


# ------------------------------------------------------------------ páginas
def _paginas_iniciales() -> list[dict]:
    pl = ds.PLANTILLAS_MASIVO[0]
    out = []
    ahora = sim.ahora()
    ciudades = [("Barcelona", "Publicada", 3), ("Madrid", "Publicada", 5), ("Valencia", "En revisión", 1),
                ("Sevilla", "Borrador", 0), ("Bilbao", "Borrador", 0)]
    for i, (ciudad, estado, dias) in enumerate(ciudades):
        b = sim.generar_masivo(pl, [ciudad])[0]
        out.append((b, estado, dias, "L1"))
    genericas = [("cómo elegir el mejor hosting para tu web", "Publicada", 8),
                 ("cómo crear una página web rápida con WordPress", "Borrador", 2),
                 ("cómo mejorar el SEO de tu web", "En revisión", 4)]
    for tema, estado, dias in genericas:
        out.append((sim.generar_borrador(tema, "Profesional", "medio", "", None), estado, dias, None))
    paginas = []
    for i, (b, estado, dias, lote) in enumerate(out):
        if estado in ("Publicada", "Aprobada"):
            sim.completar_pendientes(b)
            b["enviado"] = True
        b["fecha"] = ahora - timedelta(days=dias)
        pid = f"p{i + 1}"
        b["pag_id"] = pid
        paginas.append({"id": pid, "estado": estado, "lote": lote, "b": b})
    return paginas


def buscar_pagina(pid: str | None) -> dict | None:
    return next((p for p in st.session_state.paginas if p["id"] == pid), None) if pid else None


def tiene_pendientes(p: dict) -> bool:
    return sim.tiene_pendientes(p["b"])


def registrar_pagina(b: dict, estado: str = "Borrador", lote: str | None = None) -> dict:
    ss = st.session_state
    p = {"id": "p" + uuid.uuid4().hex[:6], "estado": estado, "lote": lote, "b": b}
    b["pag_id"] = p["id"]
    ss.paginas.insert(0, p)
    return p


def sincronizar_pagina(b: dict) -> None:
    p = buscar_pagina(b.get("pag_id"))
    if p:
        p["b"] = b


def seleccionar_pagina(pid: str) -> None:
    st.session_state.pagina_sel = pid
    st.session_state.confirmar_eliminar_pag = None


def cambiar_estado(pids: list[str], destino: str) -> None:
    """Cambia el estado respetando las reglas: sin [PENDIENTE] para aprobar y solo se publica lo aprobado."""
    ss = st.session_state
    ok = bloq_pend = bloq_estado = 0
    for pid in pids:
        p = buscar_pagina(pid)
        if p is None:
            continue
        if destino in ("Aprobada", "Publicada") and tiene_pendientes(p):
            bloq_pend += 1
            continue
        if destino == "Publicada" and p["estado"] != "Aprobada":
            bloq_estado += 1
            continue
        p["estado"] = destino
        if destino == "Publicada":
            p["b"]["enviado"] = True
        ok += 1
    partes = []
    if ok:
        partes.append(f"{ok} página(s) → «{destino}»")
    if bloq_pend:
        partes.append(f"{bloq_pend} con [PENDIENTE] sin cambiar")
    if bloq_estado:
        partes.append(f"{bloq_estado} sin aprobar sin cambiar")
    pref = "[DEMOSTRACIÓN] " if destino == "Publicada" and ok else ""
    st.toast(pref + (" · ".join(partes) or "Nada que cambiar."), icon="✅" if ok else "⚠️")
    ss.pag_rev += 1


def completar_pendientes_ids(pids: list[str]) -> None:
    n = 0
    for pid in pids:
        p = buscar_pagina(pid)
        if p and tiene_pendientes(p):
            sim.completar_pendientes(p["b"])
            n += 1
    st.session_state.pag_rev += 1
    st.toast(f"[DEMOSTRACIÓN] Marcadores resueltos en {n} página(s) con texto neutro de las fichas.", icon="🧪")


def enviar_wp(pids: list[str]) -> None:
    n = 0
    for pid in pids:
        p = buscar_pagina(pid)
        if p:
            p["b"]["enviado"] = True
            n += 1
    sitio = st.session_state.get("sitio", ds.SITIOS_WP[0])
    st.session_state.pag_rev += 1
    st.toast(f"[DEMOSTRACIÓN] {n} borrador(es) enviados a «{sitio}» (simulado). No se ha publicado nada.", icon="🧪")


def eliminar_paginas(pids: list[str]) -> None:
    ss = st.session_state
    ss.paginas = [p for p in ss.paginas if p["id"] not in pids]
    ss.m_lote = [i for i in ss.m_lote if i not in pids]
    if ss.pagina_sel in pids:
        ss.pagina_sel = None
    ss.confirmar_eliminar_pag = None
    ss.pag_rev += 1
    st.toast(f"{len(pids)} página(s) eliminada(s).", icon="🗑️")


def pedir_eliminar_pagina(pid: str) -> None:
    st.session_state.confirmar_eliminar_pag = pid


def cancelar_eliminar_pagina() -> None:
    st.session_state.confirmar_eliminar_pag = None


def duplicar_pagina(pid: str) -> None:
    p = buscar_pagina(pid)
    if p is None:
        return
    b = copy.deepcopy(p["b"])
    b["titulo"] = (b["titulo"] + " (copia)")[:200]
    b["hist_id"] = None
    b["enviado"] = False
    sim.recalcular(b)
    nuevo = registrar_pagina(b, "Borrador", p["lote"])
    seleccionar_pagina(nuevo["id"])
    st.session_state.pag_rev += 1
    st.toast("Página duplicada como borrador.", icon="✅")


def guardar_pagina(pid: str) -> None:
    ss = st.session_state
    p = buscar_pagina(pid)
    if p is None:
        return
    r = ss.pag_rev
    titulo = (ss.get(f"pe_titulo_{pid}_{r}") or "").strip()
    if not titulo:
        st.toast("El título no puede estar vacío.", icon="⚠️")
        return
    b = p["b"]
    b["titulo"] = titulo[:200]
    b["meta_descripcion"] = (ss.get(f"pe_meta_{pid}_{r}") or "")[:160]
    b["cuerpo"] = ss.get(f"pe_cuerpo_{pid}_{r}") or ""
    slug = (ss.get(f"pe_slug_{pid}_{r}") or "").strip()
    sim.recalcular(b)
    if slug:
        b["slug"] = sim._slug(slug)
    ss.pag_rev += 1
    st.toast("Cambios guardados en la página.", icon="✅")


def abrir_en_generador(pid: str) -> None:
    ss = st.session_state
    p = buscar_pagina(pid)
    if p is None:
        return
    ss.borrador = p["b"]
    ss.prev_borrador = None
    ss.rev += 1
    ss.conv = []
    msg_ia(f"<p>He cargado <strong>{_html.escape(p['b']['titulo'])}</strong> en la previsualización. "
           "En <strong>Construcción</strong> puedes pedirme cambios; en <strong>Chat</strong>, consultas sobre ella.</p>")
    ss.modo = "Construcción"
    ss.pagina = "generador"


# --------------------------------------------------------------- acciones en masa
def _ids_ambito(ambito: str) -> tuple[list[str], str]:
    ss = st.session_state
    if ambito == "lote":
        return [i for i in ss.m_lote if buscar_pagina(i)], "msel_"
    return [p["id"] for p in ss.paginas], "psel_"


def accion_masa(ambito: str, accion: str) -> None:
    ss = st.session_state
    ids, pref = _ids_ambito(ambito)
    if accion in ("todas", "ninguna"):
        for i in ids:
            ss[pref + i] = accion == "todas"
        return
    sel = [i for i in ids if ss.get(pref + i)]
    if not sel:
        st.toast("Selecciona al menos una página.", icon="⚠️")
        return
    if accion == "revision":
        cambiar_estado(sel, "En revisión")
    elif accion == "aprobar":
        cambiar_estado(sel, "Aprobada")
    elif accion == "publicar":
        cambiar_estado(sel, "Publicada")
    elif accion == "rellenar":
        completar_pendientes_ids(sel)
    elif accion == "wp":
        enviar_wp(sel)
    elif accion == "eliminar":
        eliminar_paginas(sel)


# ----------------------------------------------------------------- generación en masa
def parsear_variables(texto: str) -> list[str]:
    vistas: list[str] = []
    for linea in (texto or "").splitlines():
        v = " ".join(linea.split())[:60]
        if v and v.lower() not in {x.lower() for x in vistas}:
            vistas.append(v)
    return vistas


def rellenar_ciudades() -> None:
    ss = st.session_state
    ss.m_vars = "\n".join(ds.CIUDADES[: int(ss.m_n)])


def generar_lote() -> None:
    ss = st.session_state
    variables = parsear_variables(ss.get("m_vars"))
    if not variables:
        st.toast("Añade al menos una variable (una por línea).", icon="⚠️")
        return
    if len(variables) > ds.LIMITE_MASIVO:
        st.toast(f"Máximo {ds.LIMITE_MASIVO} páginas por lote: se usan las {ds.LIMITE_MASIVO} primeras.", icon="⚠️")
        variables = variables[: ds.LIMITE_MASIVO]
    pl = next(p for p in ds.PLANTILLAS_MASIVO if p["nombre"] == ss.m_plantilla)
    longitud = next(k for k, lbl, *_ in ds.LONGITUDES if lbl == ss.m_long)
    fichas = fichas_activas() if ss.get("m_fichas") else []
    lote = f"L{ss.lote_n}"
    ss.lote_n += 1
    nuevas = [registrar_pagina(b, "Borrador", lote) for b in sim.generar_masivo(pl, variables, ss.m_tono, longitud, fichas)]
    ss.m_lote = [p["id"] for p in nuevas]
    ss.m_idx = 0
    for p in nuevas:
        ss[f"msel_{p['id']}"] = False
    st.toast(f"[DEMOSTRACIÓN] {len(nuevas)} páginas generadas en el lote {lote}. Revísalas antes de publicar.", icon="🧪")


def revisar(idx: int) -> None:
    st.session_state.m_idx = idx


def mover_revision(delta: int) -> None:
    ss = st.session_state
    n = len([i for i in ss.m_lote if buscar_pagina(i)])
    if n:
        ss.m_idx = (ss.m_idx + delta) % n


def aprobar_y_siguiente(pid: str) -> None:
    cambiar_estado([pid], "Aprobada")
    if buscar_pagina(pid) and buscar_pagina(pid)["estado"] == "Aprobada":
        mover_revision(1)


# ------------------------------------------------------------ Search Console (demo)
def conectar_sc() -> None:
    ss = st.session_state
    ss.sc_conectado = not ss.sc_conectado
    st.toast("[DEMOSTRACIÓN] Conexión con Search Console " + ("simulada." if ss.sc_conectado else "cerrada."), icon="🧪")


def crear_desde_consulta(consulta: str) -> None:
    ss = st.session_state
    ss.pagina = "generador"
    ss.modo = "Construcción"
    ss.borrador = None
    ss.prev_borrador = None
    ss.rev += 1
    ss.conv = [_bienvenida()]
    ss.g_tema = f"Artículo sobre {consulta}"
    st.toast("Consulta cargada en el generador. Pulsa «Generar artículo».", icon="✅")


def preguntar_ia_analitica() -> None:
    ss = st.session_state
    pregunta = "¿Qué oportunidades SEO ves en mis datos de Search Console?"
    ss.pagina = "generador"
    ss.modo = "Chat"
    msg_usuario(pregunta, "Chat")
    texto, tag = sim.consulta(pregunta, len(fichas_activas()), ss.borrador)
    msg_ia("<p>" + sim._inline(texto) + "</p>", tag)
