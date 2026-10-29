"""Piezas HTML reutilizables.

Regla: todo texto variable pasa por `esc()` o proviene de `simulado.texto_a_html`
(que escapa). Los fragmentos se devuelven sin saltos de línea ni sangrías para que
el parser de Markdown de Streamlit no los trate como bloques de código.
"""
from __future__ import annotations

import html
import re

import streamlit as st

from quicksite.core import datos_simulados as ds
from quicksite.core import simulado as sim


def esc(t) -> str:
    return html.escape(str(t), quote=True).replace("$", "&#36;")


def _h(s: str) -> str:
    return re.sub(r"\n\s*", "", s)


# ---------------------------------------------------------------- iconos
ICONOS = {
    "rayo": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "imagen": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    "usuario": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "documento": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/>',
    "calendario": '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "reloj": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "enviar": '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
    "etiqueta": '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/>',
    "escudo": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "bombilla": '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.2 1 2V17h6v-.3c0-.8.4-1.5 1-2A7 7 0 0 0 12 2z"/>',
    "chispa": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
    "alerta": '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "grafico": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "wp": '<circle cx="12" cy="12" r="10"/><path d="M4 9l4.5 12M9 4.5L14.5 20M12.5 6l4.8 12.5M19.5 8c.9 1.3 1.5 2.9 1.5 4"/>',
}
ICONO_TIPO = {"General": "documento", "Estilo": "etiqueta", "SEO": "escudo", "Contenido": "bombilla"}


def icono(nombre: str, tam: int = 16) -> str:
    return (f'<svg class="qs-ic" width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONOS[nombre]}</svg>')


# ---------------------------------------------------------- piezas sueltas
def logo() -> str:
    return _h(f'<div class="qs-logo"><span class="qs-logo-ic">{icono("rayo", 26)}</span>'
              f'<span>Quick<b>Site</b></span></div>')


def etiqueta_tipo(tipo: str) -> str:
    return f'<span class="qs-tag qs-tag-{esc(tipo.lower())}">{esc(tipo)}</span>'


_ESTADOS = {"Generada": ("ok", "check"), "Enviada como borrador": ("env", "enviar"), "Borrador": ("bor", "documento"),
            "En revisión": ("rev", "reloj"), "Aprobada": ("apr", "check"), "Publicada": ("ok", "check")}


def etiqueta_estado(estado: str) -> str:
    cls, ic = _ESTADOS.get(estado, ("bor", "documento"))
    return f'<span class="qs-estado qs-estado-{cls}">{icono(ic, 13)}{esc(estado)}</span>'


def pill_seo(nota: int) -> str:
    cls = "ok" if nota >= 80 else "am" if nota >= 60 else "ko"
    return f'<span class="qs-seo qs-seo-{cls}">SEO {nota}</span>'


def chip_wp() -> str:
    return '<span class="qs-chip qs-chip-bl">En WordPress</span>'


def estado_vacio(titulo: str, texto: str, icono_nombre: str = "documento") -> str:
    return _h(f'<div class="qs-empty">{icono(icono_nombre, 28)}<h4>{esc(titulo)}</h4><p>{esc(texto)}</p></div>')


def cabecera_pagina(titulo: str, subtitulo: str = "") -> str:
    sub = f'<p class="qs-sub">{esc(subtitulo)}</p>' if subtitulo else ""
    return _h(f'<div class="qs-pagehead"><h1>{esc(titulo)}</h1>{sub}</div>')


def selector_sitio() -> None:
    """Selector de sitio WordPress (solo demostración, sin conexión real)."""
    st.selectbox("Sitio de WordPress", ds.SITIOS_WP, key="sitio", label_visibility="collapsed")


def estado_wp_html() -> str:
    return _h('<div class="qs-wpstatus"><span class="qs-wpic">' + icono("wp", 30) + '</span>'
              '<div><div class="qs-wpname">WordPress</div>'
              '<div class="qs-wpsub"><span class="qs-dot"></span>Modo demostración · sin conexión</div></div></div>')


# --------------------------------------------------------------- chat
_TAGS = {"accion": ("Cambios aplicados", "or"), "consulta": ("Consulta", "bl"), "aviso": ("Modo Chat · sin cambios", "am")}


def burbuja_usuario(texto: str, hora: str, modo: str | None = None) -> str:
    t = esc(texto).replace("\n", "<br>")
    m = f'<span class="qs-chip qs-chip-modo">{esc(modo)}</span>' if modo else ""
    return _h(f'<div class="qs-row qs-row-user"><div class="qs-bubble qs-user"><div>{t}</div>'
              f'<div class="qs-time">{m}{esc(hora)} {icono("usuario", 12)}</div></div></div>')


def burbuja_ia(contenido_html: str, hora: str, tag: str | None = None) -> str:
    chip = ""
    if tag in _TAGS:
        lbl, cls = _TAGS[tag]
        chip = f'<div class="qs-chiprow"><span class="qs-chip qs-chip-{cls}">{lbl}</span></div>'
    return _h(f'<div class="qs-row qs-row-ia"><div class="qs-avatar">{icono("rayo", 18)}</div>'
              f'<div class="qs-bubble qs-ia">{chip}{contenido_html}<div class="qs-time">{esc(hora)}</div></div></div>')


def texto_a_burbuja(texto: str) -> str:
    """Texto plano -> HTML seguro para una burbuja de la IA (admite [PENDIENTE: ...])."""
    return "<p>" + sim._inline(texto) + "</p>"


def mensajes_html(msgs: list[dict]) -> str:
    partes = []
    for m in msgs:
        if m["rol"] == "user":
            partes.append(burbuja_usuario(m["texto"], m["hora"], m.get("modo")))
        else:
            partes.append(burbuja_ia(m["html"], m["hora"], m.get("tag")))
    return "".join(partes) or estado_vacio("Sin mensajes", "Escribe algo para empezar.", "chispa")


def resumen_borrador_html(b: dict) -> str:
    return _h(f'<div class="qs-art"><h3>{esc(b["titulo"])}</h3><p class="qs-sub">{esc(b["meta_descripcion"])}</p>'
              f'<hr>{b["cuerpo_html"]}</div>')


# ------------------------------------------------------------ previsualización
def vista_previa_html(b: dict) -> str:
    faq = ""
    if b["faq"]:
        items = "".join(
            f'<details><summary>{esc(f["q"])}</summary><div>{sim._inline(f["a"])}</div></details>'
            for f in b["faq"]
        )
        faq = f'<div class="qs-faq"><h2>Preguntas frecuentes</h2>{items}</div>'
    return _h(
        f'<div class="qs-prev">'
        f'<div class="qs-prev-img">{icono("imagen", 40)}</div>'
        f'<div class="qs-caption">Imagen de stock (Pexels) pendiente · búsqueda: {esc(b["imagen_busqueda"])}</div>'
        f'<span class="qs-tag qs-tag-cat">{esc(b["categoria"])}</span>'
        f'<h1>{esc(b["titulo"])}</h1>'
        f'<div class="qs-meta"><span>{icono("calendario", 13)}{esc(sim.fecha_corta(b["fecha"]))}</span>'
        f'<i>•</i><span>{icono("reloj", 13)}{b["lectura"]} min de lectura</span>'
        f'<i>•</i><span>{icono("usuario", 13)}QuickSite</span></div>'
        f'<div class="qs-kw">Palabra clave: <b>{esc(b["palabra_clave"])}</b></div>'
        f'<div class="qs-body">{b["cuerpo_html"]}</div>{faq}</div>'
    )


def esqueleto_html() -> str:
    def lineas(n: int) -> str:
        return "".join(f'<div class="qs-skel{" qs-skel-s" if i == n - 1 else ""}"></div>' for i in range(n))

    return _h(
        f'<div class="qs-prev"><h1 class="qs-ghost">Título del artículo</h1>'
        f'<div class="qs-meta"><span>{icono("calendario", 13)}Fecha de publicación</span><i>•</i>'
        f'<span>{icono("documento", 13)}Categoría</span></div>'
        f'<div class="qs-prev-img qs-prev-img-lg">{icono("imagen", 40)}</div>{lineas(4)}'
        f'<h2>H2: Subtítulo de la sección</h2>{lineas(4)}<h2>H2: Otro subtítulo</h2>{lineas(4)}</div>'
    )


def ficha_card_html(f: dict) -> str:
    return _h(
        f'<div class="qs-fcard"><div class="qs-ficon">{icono(ICONO_TIPO.get(f["tipo"], "documento"), 20)}</div>'
        f'<div><div class="qs-ftitle">{esc(f["nombre"])} {etiqueta_tipo(f["tipo"])}'
        f'{"" if f["activa"] else " <span class=qs-off>inactiva</span>"}</div>'
        f'<div class="qs-fdesc">{esc(f["descripcion"])}</div></div></div>'
    )


# ------------------------------------------------------------ modo / SEO
def modo_hint_html(modo: str) -> str:
    if modo == "Construcción":
        return '<div class="qs-modehint"><b>Agente</b> · la IA modifica la previsualización</div>'
    return '<div class="qs-modehint"><b>Consulta</b> · la IA responde sobre la preview u otros temas, sin modificarla</div>'


def checklist_html(nota: int, checks: list[tuple[bool, str]]) -> str:
    items = "".join(
        f'<li class="{"ok" if ok else "ko"}">{icono("check" if ok else "alerta", 15)}{esc(lbl)}</li>'
        for ok, lbl in checks)
    return _h(f'<div class="qs-score"><div class="qs-score-n">{nota}<small>/100</small></div>'
              f'<div class="qs-bar"><i style="width:{nota}%"></i></div></div><ul class="qs-chk">{items}</ul>')


# --------------------------------------------------------- analítica
def fmt_num(v: float, dec: int = 0) -> str:
    return f"{v:,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def kpis_html(items: list[tuple[str, str, str, bool]]) -> str:
    """items: (etiqueta, valor, variación, mejora)."""
    cards = "".join(
        f'<div class="qs-kpi"><div class="qs-kpi-l">{esc(l)}</div><div class="qs-kpi-v">{esc(v)}</div>'
        f'<div class="qs-kpi-d {"up" if good else "down"}">{esc(d)} <span>vs. periodo anterior</span></div></div>'
        for l, v, d, good in items)
    return _h(f'<div class="qs-kpis">{cards}</div>')


def grafico_svg(etiquetas: list[str], valores: list[float], dec: int = 0) -> str:
    W, H, L, R, T, B = 820, 270, 54, 14, 14, 30
    lo, hi = min(valores), max(valores)
    span = (hi - lo) or 1
    lo_a = max(0.0, lo - span * 0.2)
    hi_a = hi + span * 0.1
    n = len(valores)

    def x(i): return L + (W - L - R) * i / max(n - 1, 1)
    def y(v): return T + (H - T - B) * (1 - (v - lo_a) / (hi_a - lo_a))

    grid = ""
    for k in range(5):
        v = lo_a + (hi_a - lo_a) * k / 4
        yy = y(v)
        grid += (f'<line x1="{L}" y1="{yy:.1f}" x2="{W - R}" y2="{yy:.1f}" stroke="#1E2430"/>'
                 f'<text x="{L - 8}" y="{yy + 4:.1f}" text-anchor="end">{fmt_num(v, dec)}</text>')
    paso = max(1, n // 6)
    xl = "".join(f'<text x="{x(i):.1f}" y="{H - 8}" text-anchor="middle">{esc(etiquetas[i])}</text>'
                 for i in range(0, n, paso))
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(valores))
    area = f"{L},{H - B} " + pts + f" {x(n - 1):.1f},{H - B}"
    return _h(
        f'<div class="qs-chart"><svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Gráfico de evolución">'
        f'<defs><linearGradient id="qsg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FF6A13" stop-opacity=".35"/>'
        f'<stop offset="1" stop-color="#FF6A13" stop-opacity="0"/></linearGradient></defs>'
        f'{grid}{xl}<polygon points="{area}" fill="url(#qsg)"/>'
        f'<polyline points="{pts}" fill="none" stroke="#FF6A13" stroke-width="2.4" stroke-linejoin="round"/></svg></div>')


def tabla_html(cabeceras: list[str], filas: list[list], num: tuple = ()) -> str:
    th = "".join(f'<th class="{"n" if i in num else ""}">{esc(h)}</th>' for i, h in enumerate(cabeceras))
    tr = "".join(
        "<tr>" + "".join(f'<td class="{"n" if i in num else ""}">{esc(v)}</td>' for i, v in enumerate(f)) + "</tr>"
        for f in filas)
    return _h(f'<table class="qs-tbl"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>')
