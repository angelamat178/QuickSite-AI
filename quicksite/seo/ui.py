from __future__ import annotations

import json
from html import escape
from urllib.parse import urlparse

import streamlit as st
from sqlalchemy import text

from quicksite.seo.analytics import classify_conversion_state
from quicksite.seo.connectors import test_wordpress_readonly
from quicksite.seo.crawler import audit_url
from quicksite.seo.db import transaction
from quicksite.seo.repository import (
    create_site,
    list_pages,
    list_recommendations,
    list_sites,
    set_recommendation_status,
    upsert_page,
)
from quicksite.seo.rules import run_page_rules, seed_rules
from quicksite.seo.sitemap import fetch_sitemap_tree


CHART_COLORS = {
    "orange": "#FF7A1A", "amber": "#F6B85F", "blue": "#7AA2FF",
    "cyan": "#54C6D8", "green": "#48D6A5", "red": "#FF6B83",
    "purple": "#B49BFF", "muted": "#8190A5", "grid": "rgba(133,151,177,.15)",
    "paper": "rgba(0,0,0,0)", "text": "#EAF0F8",
}


def _theme_figure(fig, height=320):
    fig.update_layout(
        template="plotly_dark", height=height,
        paper_bgcolor=CHART_COLORS["paper"], plot_bgcolor=CHART_COLORS["paper"],
        font={"family": "Inter, Segoe UI, sans-serif", "size": 12, "color": CHART_COLORS["text"]},
        margin={"l": 12, "r": 12, "t": 18, "b": 8},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.01, "xanchor": "left", "x": 0},
        hoverlabel={"bgcolor": "#151D29", "bordercolor": "#344256", "font": {"color": "#F4F7FC"}},
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=CHART_COLORS["grid"], tickfont={"color": CHART_COLORS["muted"]})
    fig.update_yaxes(showgrid=True, gridcolor=CHART_COLORS["grid"], zeroline=False, tickfont={"color": CHART_COLORS["muted"]})
    return fig


def _load_metric_snapshots(engine, site_id):
    if not site_id:
        return []
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT source,metric_date,metrics_json,coverage FROM metric_snapshots WHERE site_profile_id=:s ORDER BY metric_date"), {"s": site_id})
        output = []
        for row in rows:
            item = dict(row._mapping)
            try:
                item["metrics"] = json.loads(item.pop("metrics_json") or "{}")
            except (ValueError, TypeError):
                item["metrics"] = {}
            output.append(item)
        return output


def _metric_value(metrics, *keys):
    lowered = {str(k).lower().replace(" ", "_"): v for k, v in metrics.items()}
    for key in keys:
        value = lowered.get(key.lower().replace(" ", "_"))
        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _visibility_figure(snapshots):
    """Return a two-axis visibility chart and whether its values are measured."""
    from datetime import date, timedelta
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    daily = {}
    for snap in snapshots:
        m = snap.get("metrics", {})
        clicks = _metric_value(m, "clicks", "organic_clicks")
        impressions = _metric_value(m, "impressions", "organic_impressions")
        if clicks is None and impressions is None:
            continue
        day = str(snap.get("metric_date", ""))[:10]
        if not day:
            continue
        bucket = daily.setdefault(day, {"clicks": 0.0, "impressions": 0.0, "has_clicks": False, "has_impressions": False})
        if clicks is not None:
            bucket["clicks"] += clicks; bucket["has_clicks"] = True
        if impressions is not None:
            bucket["impressions"] += impressions; bucket["has_impressions"] = True

    measured = bool(daily)
    if measured:
        x = sorted(daily)
        clicks = [daily[d]["clicks"] if daily[d]["has_clicks"] else None for d in x]
        impressions = [daily[d]["impressions"] if daily[d]["has_impressions"] else None for d in x]
    else:
        today = date.today()
        x = [(today - timedelta(days=13-i)).isoformat() for i in range(14)]
        clicks = [18, 21, 16, 24, 27, 25, 31, 29, 34, 30, 38, 41, 37, 45]
        impressions = [270, 292, 281, 315, 326, 341, 330, 368, 384, 372, 409, 423, 416, 451]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=x, y=impressions, name="Impresiones", mode="lines", line={"color": CHART_COLORS["blue"], "width": 2.5}, fill="tozeroy", fillcolor="rgba(122,162,255,.08)", connectgaps=False), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=clicks, name="Clics", mode="lines+markers", line={"color": CHART_COLORS["orange"], "width": 2.8}, marker={"size": 5, "color": CHART_COLORS["orange"]}, connectgaps=False), secondary_y=True)
    _theme_figure(fig, 340)
    fig.update_layout(legend={"orientation": "h", "yanchor": "bottom", "y": 1.01, "xanchor": "left", "x": 0})
    fig.update_yaxes(title_text="Impresiones", secondary_y=False, showgrid=True, gridcolor=CHART_COLORS["grid"])
    fig.update_yaxes(title_text="Clics", secondary_y=True, showgrid=False)
    return fig, measured


def _page_issues(pages):
    audited = [p for p in pages if p.get("last_crawled_at")]
    issues = {"Título ausente": 0, "Meta descripción ausente": 0, "H1 ausente": 0, "Canonical ausente": 0, "HTTP 4xx/5xx": 0}
    by_url = {}
    for p in audited:
        per_page = []
        if not (p.get("title") or "").strip(): issues["Título ausente"] += 1; per_page.append("Título ausente")
        if not (p.get("meta_description") or "").strip(): issues["Meta descripción ausente"] += 1; per_page.append("Meta descripción ausente")
        if not (p.get("h1") or "").strip(): issues["H1 ausente"] += 1; per_page.append("H1 ausente")
        if not (p.get("canonical_url") or "").strip(): issues["Canonical ausente"] += 1; per_page.append("Canonical ausente")
        try:
            status = int(p.get("http_status") or 0)
        except (TypeError, ValueError):
            status = 0
        if status >= 400: issues["HTTP 4xx/5xx"] += 1; per_page.append("HTTP 4xx/5xx")
        by_url[p.get("url", "—")] = per_page
    return audited, issues, by_url


def _chart_status(pages):
    import plotly.graph_objects as go
    audited, issues, by_url = _page_issues(pages)
    if audited:
        errors = sum(bool(by_url[p.get("url", "—")]) for p in audited)
        good = len(audited) - errors
        values = [good, errors]
        labels = ["Sin hallazgos en checklist", "Con hallazgos"]
        measured = True
    else:
        values = [54, 31, 15]
        labels = ["Correctas", "Necesitan mejoras", "Errores críticos"]
        measured = False
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=.74, sort=False,
        marker={"colors": [CHART_COLORS["green"], CHART_COLORS["orange"], CHART_COLORS["red"]][:len(values)], "line": {"color": "#10151E", "width": 3}},
        textinfo="percent", textfont={"size": 12, "color": CHART_COLORS["text"]},
        hovertemplate="%{label}<br>%{value} URLs (%{percent})<extra></extra>",
    )])
    fig.add_annotation(text=f"{len(audited) if measured else '—'}<br><span style='font-size:11px;color:#8190A5'>auditadas</span>", x=.5, y=.5, showarrow=False, font={"size": 26, "color": CHART_COLORS["text"]})
    _theme_figure(fig, 320)
    fig.update_layout(showlegend=True, legend={"orientation": "v", "yanchor": "middle", "y": .5, "xanchor": "left", "x": 1.0}, margin={"l": 8, "r": 90, "t": 12, "b": 8})
    return fig, measured, issues


def _issues_figure(pages):
    import plotly.graph_objects as go
    audited, issues, _ = _page_issues(pages)
    if audited:
        labels = list(issues.keys())
        values = list(issues.values())
        measured = True
    else:
        labels = ["Meta descripción", "Título SEO", "Enlaces internos", "H1", "Rendimiento"]
        values = [8, 6, 5, 3, 2]
        measured = False
    order = sorted(range(len(labels)), key=lambda i: values[i])
    fig = go.Figure(go.Bar(
        x=[values[i] for i in order], y=[labels[i] for i in order], orientation="h",
        marker={"color": [CHART_COLORS["red"] if values[i] > 0 else CHART_COLORS["green"] for i in order], "cornerradius": 5},
        text=[values[i] for i in order], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{x} URLs afectadas<extra></extra>",
    ))
    _theme_figure(fig, 320)
    fig.update_layout(showlegend=False, margin={"l": 4, "r": 28, "t": 12, "b": 8}, xaxis_title="URLs afectadas")
    fig.update_xaxes(rangemode="tozero")
    return fig, measured


def _inbound_figure(engine, site_id, pages):
    import plotly.graph_objects as go
    if site_id:
        with engine.connect() as conn:
            rows = [dict(r._mapping) for r in conn.execute(text("""SELECT p.url, COALESCE(p.title,p.url) AS label, COUNT(e.id) AS n
                FROM pages p LEFT JOIN link_edges e ON e.target_page_id=p.id
                WHERE p.site_profile_id=:s GROUP BY p.id,p.url,p.title ORDER BY n DESC LIMIT 8"""), {"s": site_id})]
            edge_count = conn.execute(text("SELECT COUNT(*) FROM link_edges WHERE site_profile_id=:s"), {"s": site_id}).scalar_one()
    else:
        rows, edge_count = [], 0
    measured = bool(edge_count)
    if measured:
        labels = [(r["label"] or r["url"] or "URL") for r in rows]
        values = [int(r["n"] or 0) for r in rows]
        labels = [s if len(s) <= 32 else s[:29] + "…" for s in labels]
    else:
        labels = ["Guía de WordPress", "SEO técnico", "Plugins esenciales", "Servicios", "Blog"]
        values = [12, 9, 7, 5, 3]
    fig = go.Figure(go.Bar(x=values[::-1], y=labels[::-1], orientation="h", marker={"color": CHART_COLORS["purple"], "cornerradius": 5}, text=values[::-1], textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>%{x} enlaces entrantes<extra></extra>"))
    _theme_figure(fig, 310)
    fig.update_layout(showlegend=False, margin={"l": 4, "r": 28, "t": 10, "b": 8}, xaxis_title="Enlaces entrantes")
    fig.update_xaxes(rangemode="tozero")
    return fig, measured, edge_count


def _render_chart(fig, key):
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "displaylogo": False}, key=key)


def _plot_card_heading(title, subtitle=None, demo=False):
    badge = '<span class="qs-demo-badge">EJEMPLO</span>' if demo else '<span class="qs-data-badge">DATOS DEL SITIO</span>'
    note = f'<div class="qs-chart-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="qs-chart-heading"><div><div class="qs-chart-title">{title}</div>{note}</div>{badge}</div>', unsafe_allow_html=True)


def _render_seo_dashboard(engine, site_id, site, sites):
    import plotly.graph_objects as go
    pages = list_pages(engine, site_id) if site_id else []
    recs = list_recommendations(engine, site_id) if site_id else []
    audited, issue_counts, by_url = _page_issues(pages)
    pending = sum(r.get("status") == "pending" for r in recs)
    complete = round((len(audited) / len(pages) * 100)) if pages else 0
    total_issues = sum(issue_counts.values())
    score = max(0, min(100, round(100 - total_issues / max(1, len(audited)) * 14))) if audited else None
    snapshots = _load_metric_snapshots(engine, site_id)
    trend, trend_measured = _visibility_figure(snapshots)
    status_fig, status_measured, issue_counts = _chart_status(pages)
    issues_fig, issues_measured = _issues_figure(pages)
    links_fig, links_measured, edge_count = _inbound_figure(engine, site_id, pages)

    site_label = escape(str(site.get("name", "Tu sitio"))) if site_id else "Espacio SEO"
    site_url = escape(str(site.get("base_url", "Configura un dominio para comenzar"))) if site_id else "Configuración inicial"
    st.markdown(f'''<section class="qs-seo-hero"><div class="qs-seo-hero-copy"><div class="qs-eyebrow">ORGANIC GROWTH · SEARCH VISIBILITY</div><h1>SEO workspace</h1><p>Entiende qué ocurre en tu web, detecta oportunidades y prioriza mejoras con evidencia.</p></div><div class="qs-hero-side"><div class="qs-pulse"></div><div><strong>{site_label}</strong><span>{site_url}</span></div></div></section>''', unsafe_allow_html=True)

    if not site_id:
        st.markdown('<div class="qs-inline-notice"><div><strong>Empieza conectando tu sitio</strong><span>Las gráficas de ejemplo muestran cómo se verá el panel. No representan datos reales ni métricas de Google.</span></div></div>', unsafe_allow_html=True)
        if st.button("＋ Configurar el primer sitio", type="primary", key="seo_dashboard_create_site"):
            st.session_state["seo_nav_request"] = "Sitios y fuentes"
            st.rerun()

    c1, c2, c3, c4, c5 = st.columns(5, gap="small")
    with c1:
        st.metric("URLs", len(pages), help="URLs importadas o añadidas al inventario de este sitio.")
    with c2:
        st.metric("Auditadas", f"{complete}%" if pages else "—", help="Porcentaje de URLs con una auditoría guardada.")
    with c3:
        st.metric("Índice checklist", f"{score}/100" if score is not None else "—", help="Indicador interno basado en los hallazgos de las URLs auditadas; no es una métrica de Google.")
    with c4:
        st.metric("Hallazgos", total_issues if audited else "—", help="Suma de campos ausentes y estados HTTP de las URLs auditadas.")
    with c5:
        st.metric("Por revisar", pending, help="Recomendaciones que todavía están pendientes de decisión.")

    st.markdown('<div class="qs-section-heading"><div><h2>Visibilidad orgánica</h2><p>Seguimiento de la evolución y del estado técnico, en un mismo lugar.</p></div></div>', unsafe_allow_html=True)
    left, right = st.columns([1.55, 1], gap="large")
    with left:
        with st.container(border=True):
            _plot_card_heading("Clics e impresiones", "Evolución diaria", demo=not trend_measured)
            _render_chart(trend, "seo_visibility_trend")
            st.caption("Fuente: snapshots guardados." if trend_measured else "Datos ilustrativos para mostrar el gráfico. Search Console todavía no está conectada.")
    with right:
        with st.container(border=True):
            _plot_card_heading("Estado del contenido", "Cobertura de auditoría", demo=not status_measured)
            _render_chart(status_fig, "seo_page_status")
            st.caption("Clasificación basada en el checklist de QuickSite." if status_measured else "Distribución ficticia. Importa URLs y audítalas para reemplazarla por datos reales.")

    left2, right2 = st.columns([1, 1], gap="large")
    with left2:
        with st.container(border=True):
            _plot_card_heading("Principales tipos de hallazgo", "Campos técnicos que conviene revisar", demo=not issues_measured)
            _render_chart(issues_fig, "seo_issues_by_type")
            st.caption("Recuento de URLs auditadas con cada condición." if issues_measured else "Ejemplo visual, sin datos reales de auditoría.")
    with right2:
        with st.container(border=True):
            _plot_card_heading("Enlazado interno", "Páginas con más enlaces entrantes", demo=not links_measured)
            _render_chart(links_fig, "seo_inbound_links")
            st.caption(f"{edge_count} relaciones de enlace detectadas." if links_measured else "Ejemplo visual. Audita varias páginas para construir el grafo de enlaces.")

    st.markdown('<div class="qs-section-heading"><div><h2>Tu siguiente paso</h2><p>Accesos directos a las acciones que desbloquean el análisis.</p></div></div>', unsafe_allow_html=True)
    action_cols = st.columns(3, gap="medium")
    actions = [
        ("01", "Importar páginas", "Cargar el sitemap y construir el inventario.", "Inventario", "＋ Abrir inventario"),
        ("02", "Auditar páginas", "Comprobar títulos, metas, H1, canonical y HTTP.", "Auditoría técnica", "⌕ Abrir auditoría"),
        ("03", "Priorizar mejoras", "Revisar recomendaciones con evidencia.", "Recomendaciones", "↗ Ver recomendaciones"),
    ]
    for col, (number, title, description, destination, button_label) in zip(action_cols, actions):
        with col.container(border=True):
            st.markdown(f'<div class="qs-action-number">{number}</div><div class="qs-action-title">{title}</div><div class="qs-action-description">{description}</div>', unsafe_allow_html=True)
            if st.button(button_label, key="seo_quick_" + number, use_container_width=True):
                st.session_state["seo_nav_request"] = destination
                st.rerun()

    st.markdown('<div class="qs-footnote"><strong>Importante:</strong> el score de checklist es un indicador interno orientativo, no una métrica de Google. La falta de datos conectados no equivale a cero tráfico ni a cero conversiones.</div>', unsafe_allow_html=True)


def render_seo_section(engine, render_editorial_interlinking=None) -> None:
    """Render SEO as a visual, data-aware section inside QuickSite."""
    requested_area = st.session_state.pop("seo_nav_request", None)
    if requested_area:
        st.session_state["quicksite_seo_area"] = requested_area
    st.markdown('<div class="qs-kicker">QUICKSITE / ORGANIC SEARCH</div>', unsafe_allow_html=True)
    areas = ["Resumen", "Sitios y fuentes", "Inventario", "Auditoría técnica", "Interlinking", "Recomendaciones", "Conversiones", "Conexiones"]
    area = st.radio("Área SEO", areas, horizontal=True, key="quicksite_seo_area", label_visibility="collapsed")
    sites = list_sites(engine)
    site_id = None
    site = {}
    if sites:
        labels = {f"{s['name']} · {s['base_url']}": s["id"] for s in sites}
        preferred = st.session_state.get("seo_active_site_id")
        default_index = next((i for i, label in enumerate(labels) if labels[label] == preferred), 0)
        selected = st.selectbox("Sitio activo", list(labels), index=default_index, key="quicksite_seo_profile")
        site_id = labels[selected]
        st.session_state["seo_active_site_id"] = site_id
        site = next(s for s in sites if s["id"] == site_id)
    else:
        st.caption("No hay un sitio configurado todavía. Puedes explorar los gráficos de ejemplo mientras configuras tu dominio.")

    if area == "Sitios y fuentes":
        st.subheader("Perfiles de sitio")
        st.write("Cada sitio tiene su propio inventario, evidencias, métricas y recomendaciones.")
        with st.form("seo_site_form", clear_on_submit=True):
            name = st.text_input("Nombre del sitio", placeholder="Mi sitio WordPress")
            base = st.text_input("URL base HTTPS", placeholder="https://ejemplo.com")
            sitemap = st.text_input("URL del sitemap", placeholder="https://ejemplo.com/sitemap_index.xml")
            gsc = st.text_input("Propiedad de Search Console (opcional)", placeholder="sc-domain:ejemplo.com")
            ga4 = st.text_input("ID de propiedad GA4 (opcional)")
            wp = st.text_input("URL base de WordPress (opcional)", placeholder="https://ejemplo.com")
            submitted = st.form_submit_button("Añadir sitio", type="primary")
        if submitted:
            try:
                if not name.strip():
                    raise ValueError("El nombre del sitio es obligatorio.")
                sid = create_site(engine, name, base, gsc, ga4, wp, sitemap)
                st.session_state["seo_active_site_id"] = sid
                st.success("Perfil creado. No se ha modificado la web.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        st.markdown("### Sitios configurados")
        if sites:
            st.dataframe(
                [{"Sitio": s["name"], "URL": s["base_url"], "Search Console": s["gsc_property"] or "Sin configurar", "GA4": s["ga4_property_id"] or "Sin configurar", "Sitemap": s["sitemap_url"] or "Sin configurar"} for s in sites],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Todavía no hay perfiles. Añade uno para empezar.")
        st.markdown("### Estado de las integraciones")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("WordPress", "Prueba de lectura")
        c2.metric("Search Console", "Pendiente")
        c3.metric("GA4", "Pendiente")
        c4.metric("Google Ads", "Pendiente")
        return

    if area == "Resumen":
        _render_seo_dashboard(engine, site_id, site, sites)
        return

    if area == "Inventario":
        st.subheader("Inventario central de URLs")
        if not site_id:
            st.info("Crea un sitio en **Sitios y fuentes** antes de importar URLs.")
            return
        sitemap_url = st.text_input("Sitemap XML", value=site.get("sitemap_url") or f"{site['base_url']}/sitemap.xml")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("Leer sitemap y guardar URLs", type="primary", use_container_width=True):
                try:
                    entries = fetch_sitemap_tree(sitemap_url)
                    count = 0
                    host = urlparse(site["base_url"]).hostname
                    for entry in entries:
                        if entry["kind"] != "page":
                            continue
                        if urlparse(entry["url"]).hostname != host:
                            continue
                        upsert_page(engine, site_id, entry["url"], source="sitemap")
                        count += 1
                    with transaction(engine) as conn:
                        conn.execute(text("UPDATE site_profiles SET sitemap_url=:u WHERE id=:i"), {"u": sitemap_url, "i": site_id})
                        conn.execute(text("INSERT INTO sync_runs(site_profile_id,source,status,finished_at,rows_read,message) VALUES(:s,'sitemap','success',CURRENT_TIMESTAMP,:n,:m)"), {"s": site_id, "n": count, "m": "Sitemap leído correctamente"})
                    st.success(f"Guardadas o actualizadas {count} URLs. La lista no confirma indexación.")
                except Exception as exc:
                    st.error(f"No se pudo importar el sitemap: {exc}")
        with col_b:
            st.caption("La lectura del sitemap no consulta Google ni modifica WordPress.")
        with st.form("seo_manual_url_form", clear_on_submit=True):
            url = st.text_input("Añadir una URL manual")
            title = st.text_input("Título conocido (opcional)")
            added = st.form_submit_button("Añadir URL")
        if added:
            try:
                if urlparse(url).hostname != urlparse(site["base_url"]).hostname:
                    raise ValueError("La URL debe pertenecer al dominio del sitio activo.")
                upsert_page(engine, site_id, url, title=title.strip() or None, source="manual")
                st.success("URL guardada en el inventario.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        pages = list_pages(engine, site_id)
        audited_pages = [p for p in pages if p.get("last_crawled_at")]
        inventory_cols = st.columns(3, gap="medium")
        inventory_cols[0].metric("URLs totales", len(pages))
        inventory_cols[1].metric("Con auditoría", len(audited_pages))
        inventory_cols[2].metric("Pendientes de auditar", max(0, len(pages) - len(audited_pages)))
        if pages:
            from collections import Counter
            import plotly.graph_objects as go
            source_counts = Counter((p.get("source") or "manual").replace("_", " ").title() for p in pages)
            chart_col, note_col = st.columns([1.1, 1.5], gap="large")
            with chart_col:
                with st.container(border=True):
                    _plot_card_heading("Origen de las URLs", "Cómo se ha construido el inventario")
                    fig = go.Figure(go.Pie(labels=list(source_counts), values=list(source_counts.values()), hole=.67,
                        marker={"colors": [CHART_COLORS["orange"], CHART_COLORS["blue"], CHART_COLORS["green"], CHART_COLORS["purple"]], "line": {"color": "#10151E", "width": 3}},
                        textinfo="percent", hovertemplate="%{label}<br>%{value} URLs<extra></extra>"))
                    _theme_figure(fig, 245)
                    fig.update_layout(showlegend=True, legend={"orientation":"h", "yanchor":"bottom", "y":-0.08, "xanchor":"left", "x":0}, margin={"l":4,"r":4,"t":8,"b":12})
                    _render_chart(fig, "seo_inventory_source")
            with note_col:
                with st.container(border=True):
                    _plot_card_heading("Cobertura de revisión", "No implica que una URL esté indexada")
                    coverage_fig = go.Figure(go.Bar(x=["Auditadas", "Pendientes"], y=[len(audited_pages), len(pages)-len(audited_pages)],
                        marker={"color":[CHART_COLORS["green"], CHART_COLORS["orange"]], "cornerradius":7}, text=[len(audited_pages), len(pages)-len(audited_pages)], textposition="outside"))
                    _theme_figure(coverage_fig, 245)
                    coverage_fig.update_layout(showlegend=False, margin={"l":4,"r":20,"t":8,"b":8}, yaxis_title="URLs")
                    coverage_fig.update_yaxes(rangemode="tozero")
                    _render_chart(coverage_fig, "seo_inventory_coverage")
        st.caption(f"{len(pages)} URLs inventariadas")
        if pages:
            filter_col, status_col = st.columns([2, 1], gap="medium")
            inventory_query = filter_col.text_input("Buscar por URL o título", placeholder="Escribe una ruta, palabra o título…", key="seo_inventory_query")
            audit_filter = status_col.selectbox("Estado de auditoría", ["Todas", "Auditadas", "Pendientes"], key="seo_inventory_audit_filter")
            visible_pages = [p for p in pages if (not inventory_query or inventory_query.lower() in (p.get("url", "") + " " + (p.get("title") or "")).lower()) and (audit_filter == "Todas" or (audit_filter == "Auditadas" and p.get("last_crawled_at")) or (audit_filter == "Pendientes" and not p.get("last_crawled_at")))]
            st.caption(f"Mostrando {len(visible_pages)} de {len(pages)} URLs")
            st.dataframe(
                [{"Título": p["title"] or "Sin título detectado", "URL": p["url"], "Origen": p["source"], "HTTP": p["http_status"] or "—", "Canonical": p["canonical_url"] or "—", "Última auditoría": p["last_crawled_at"] or "Pendiente"} for p in visible_pages],
                use_container_width=True,
                hide_index=True,
            )
        return

    if area == "Auditoría técnica":
        st.subheader("Auditoría técnica por URL")
        if not site_id:
            st.info("Crea un sitio antes de auditarlo.")
            return
        pages = list_pages(engine, site_id)
        if not pages:
            st.info("Importa el sitemap o añade URLs en Inventario.")
            return
        labels = {p["url"]: p["id"] for p in pages}
        selected_url = st.selectbox("URL a auditar", list(labels), key="seo_audit_url")
        if st.button("Ejecutar auditoría", type="primary"):
            try:
                result = audit_url(selected_url, urlparse(site["base_url"]).hostname)
                page_id = labels[selected_url]
                with transaction(engine) as conn:
                    conn.execute(text("""UPDATE pages SET title=:t,canonical_url=:c,meta_description=:m,robots=:r,http_status=:h,h1=:h1,word_count=:w,source='crawler',last_crawled_at=:d,updated_at=CURRENT_TIMESTAMP WHERE id=:id"""), {"t": result["title"], "c": result["canonical"], "m": result["meta_description"], "r": result["robots"], "h": result["http_status"], "h1": result["h1"], "w": result["word_count"], "d": result["crawled_at"], "id": page_id})
                    conn.execute(text("DELETE FROM link_edges WHERE source_page_id=:p"), {"p": page_id})
                    for link in result["links"]:
                        target = next((p for p in pages if p["url"].rstrip("/") == link["url"].rstrip("/")), None)
                        conn.execute(text("INSERT INTO link_edges(site_profile_id,source_page_id,target_page_id,target_url,anchor_text) VALUES(:s,:p,:t,:u,:a)"), {"s": site_id, "p": page_id, "t": target["id"] if target else None, "u": link["url"], "a": link["anchor"]})
                hits = run_page_rules(engine, site_id, page_id, result)
                st.success(f"Auditoría completada: HTTP {result['http_status']} · {len(result['links'])} enlaces internos detectados.")
                info_cols = st.columns(4, gap="small")
                info_cols[0].metric("HTTP", result["http_status"])
                info_cols[1].metric("Palabras", result["word_count"])
                info_cols[2].metric("Enlaces internos", len(result["links"]))
                info_cols[3].metric("Hallazgos", len(result["findings"]))
                check_rows = [
                    {"Comprobación": "Título SEO", "Estado": "Correcto" if result["title"] else "Revisar", "Valor detectado": result["title"] or "No detectado"},
                    {"Comprobación": "Meta descripción", "Estado": "Correcto" if result["meta_description"] else "Revisar", "Valor detectado": result["meta_description"] or "No detectada"},
                    {"Comprobación": "H1", "Estado": "Correcto" if result["h1"] else "Revisar", "Valor detectado": result["h1"] or "No detectado"},
                    {"Comprobación": "Canonical", "Estado": "Correcto" if result["canonical"] else "Revisar", "Valor detectado": result["canonical"] or "No detectado"},
                    {"Comprobación": "Robots", "Estado": "Informativo", "Valor detectado": result["robots"] or "Sin directiva robots explícita"},
                ]
                st.dataframe(check_rows, use_container_width=True, hide_index=True)
                if result["findings"]:
                    st.warning("Hay comprobaciones que conviene revisar: " + ", ".join(result["findings"]))
                else:
                    st.success("Las comprobaciones básicas de título, meta, H1 y encabezados han pasado.")
            except Exception as exc:
                st.error(f"Auditoría fallida: {exc}")
        with st.expander("Alcance y seguridad del rastreador"):
            st.write("Se audita una URL por acción, solo mediante HTTPS y dentro del dominio del perfil. Las redirecciones fuera del dominio se bloquean. Antes de automatizar lotes habrá que añadir respeto explícito a robots.txt, exclusiones y límites de carga.")
        return

    if area == "Interlinking":
        st.subheader("Interlinking y relaciones entre páginas")
        if not site_id:
            st.info("Crea un sitio antes de recopilar enlaces.")
            return
        pages = list_pages(engine, site_id)
        with engine.connect() as conn:
            edges = [dict(row._mapping) for row in conn.execute(text("""SELECT s.url AS origen, e.target_url AS destino, e.anchor_text AS ancla, e.status_code AS estado_http
                FROM link_edges e JOIN pages s ON s.id=e.source_page_id WHERE e.site_profile_id=:s ORDER BY s.url, e.target_url"""), {"s": site_id})]
            inbound = {row["url"]: row["n"] for row in conn.execute(text("""SELECT p.url, COUNT(e.id) AS n FROM pages p LEFT JOIN link_edges e ON e.target_page_id=p.id WHERE p.site_profile_id=:s GROUP BY p.id,p.url"""), {"s": site_id})}
        st.markdown('<div class="qs-section-heading"><div><h2>Mapa de enlaces internos</h2><p>Distribución de enlaces entrantes en las páginas conocidas.</p></div></div>', unsafe_allow_html=True)
        graph_col, data_col = st.columns([1, 1.35], gap="large")
        inbound_fig, inbound_measured, edge_count = _inbound_figure(engine, site_id, pages)
        with graph_col:
            with st.container(border=True):
                _plot_card_heading("Enlaces entrantes por página", "Cobertura del grafo", demo=not inbound_measured)
                _render_chart(inbound_fig, "seo_interlinking_inbound")
                st.caption(f"Fuente: {edge_count} enlaces observados." if inbound_measured else "Gráfico ilustrativo; todavía no hay relaciones de enlace guardadas.")
        with data_col:
            with st.container(border=True):
                _plot_card_heading("Relaciones detectadas", "Origen, destino y texto ancla")
                if edges:
                    st.dataframe(edges, use_container_width=True, hide_index=True, height=310)
                else:
                    st.markdown("**Aún no hay datos del rastreador.**")
                    st.write("Audita varias URLs del inventario. QuickSite guardará los enlaces internos detectados y actualizará este mapa.")
        if edges:
            st.markdown("### Páginas con más enlaces entrantes")
            st.dataframe([{"URL": p["url"], "Título": p.get("title") or "—", "Enlaces entrantes observados": inbound.get(p["url"], 0)} for p in pages], use_container_width=True, hide_index=True)
        if render_editorial_interlinking:
            with st.expander("Sugerir enlaces dentro de un artículo de QuickSite"):
                st.caption("Esta herramienta editorial conserva su inventario local actual. La unificación de ese inventario con el grafo SEO se hará en una fase posterior.")
                render_editorial_interlinking()
        return

    if area == "Recomendaciones":
        st.subheader("Recomendaciones con evidencia")
        if not site_id:
            st.info("Crea un sitio antes de generar recomendaciones.")
            return
        recs = list_recommendations(engine, site_id)
        if not recs:
            st.info("No hay recomendaciones todavía. Ejecuta una auditoría técnica.")
            return
        import plotly.graph_objects as go
        status_order = ["pending", "accepted", "completed", "dismissed"]
        status_labels = {"pending": "Por revisar", "accepted": "Aceptadas", "completed": "Completadas", "dismissed": "Descartadas"}
        status_counts = {key: sum(r.get("status") == key for r in recs) for key in status_order}
        impact_order = ["high", "medium", "low", "unknown", "potential"]
        impact_labels = {"high": "Alto", "medium": "Medio", "low": "Bajo", "unknown": "Sin clasificar", "potential": "Potencial"}
        impact_counts = {key: sum((r.get("impact") or "unknown").lower() == key for r in recs) for key in impact_order}
        chart_left, chart_right = st.columns(2, gap="large")
        with chart_left:
            with st.container(border=True):
                _plot_card_heading("Estado del backlog", "Seguimiento de las decisiones")
                status_fig = go.Figure(go.Pie(labels=[status_labels[k] for k in status_order], values=[status_counts[k] for k in status_order], hole=.68,
                    marker={"colors":[CHART_COLORS["orange"],CHART_COLORS["blue"],CHART_COLORS["green"],CHART_COLORS["muted"]],"line":{"color":"#10151E","width":3}},
                    textinfo="percent", hovertemplate="%{label}<br>%{value} recomendaciones<extra></extra>"))
                _theme_figure(status_fig, 255)
                status_fig.update_layout(margin={"l":4,"r":4,"t":10,"b":8})
                _render_chart(status_fig, "seo_recommendation_status")
        with chart_right:
            with st.container(border=True):
                _plot_card_heading("Impacto estimado", "Clasificación actual; no es tráfico recuperado")
                keys = [k for k in impact_order if impact_counts[k]]
                impact_fig = go.Figure(go.Bar(x=[impact_labels[k] for k in keys], y=[impact_counts[k] for k in keys], marker={"color":[CHART_COLORS["red"],CHART_COLORS["orange"],CHART_COLORS["blue"],CHART_COLORS["muted"],CHART_COLORS["purple"]][:len(keys)],"cornerradius":6}, text=[impact_counts[k] for k in keys], textposition="outside"))
                _theme_figure(impact_fig, 255)
                impact_fig.update_layout(showlegend=False, margin={"l":4,"r":12,"t":10,"b":8}, yaxis_title="Recomendaciones")
                impact_fig.update_yaxes(rangemode="tozero")
                _render_chart(impact_fig, "seo_recommendation_impact")
        filter_a, filter_b, filter_c = st.columns([1, 1, 1.8], gap="medium")
        status_filter_label = filter_a.selectbox("Estado", ["Todos", "Por revisar", "Aceptadas", "Completadas", "Descartadas"], key="seo_rec_status_filter")
        impact_filter_label = filter_b.selectbox("Impacto", ["Todos", "Alto", "Medio", "Bajo", "Sin clasificar", "Potencial"], key="seo_rec_impact_filter")
        rec_search = filter_c.text_input("Buscar recomendación", placeholder="Título, URL o regla…", key="seo_rec_search")
        status_reverse = {v: k for k, v in status_labels.items()}
        impact_reverse = {v: k for k, v in impact_labels.items()}
        visible_recs = [r for r in recs if
            (status_filter_label == "Todos" or r.get("status") == status_reverse.get(status_filter_label)) and
            (impact_filter_label == "Todos" or (r.get("impact") or "unknown").lower() == impact_reverse.get(impact_filter_label)) and
            (not rec_search or rec_search.lower() in (str(r.get("title", "")) + " " + str(r.get("url", "")) + " " + str(r.get("rule_id", ""))).lower())]
        st.markdown(f"### Revisión de acciones · {len(visible_recs)} resultados")
        if not visible_recs:
            st.info("Ninguna recomendación coincide con estos filtros.")
        for rec in visible_recs:
            with st.container(border=True):
                st.markdown(f"**{rec['title']}** · `{rec['status']}` · Confianza: {rec['confidence']}")
                st.write(rec["explanation"])
                st.caption(f"URL: {rec['url'] or '—'} · Regla: {rec['rule_id']} · Impacto: {rec['impact']} · Esfuerzo: {rec['effort']}")
                with st.expander("Ver evidencia"):
                    st.json(rec["evidence"])
                c1, c2, c3 = st.columns(3)
                if c1.button("Aceptar", key=f"seo_rec_accept_{rec['id']}"):
                    set_recommendation_status(engine, rec["id"], "accepted")
                    st.rerun()
                if c2.button("Descartar", key=f"seo_rec_dismiss_{rec['id']}"):
                    set_recommendation_status(engine, rec["id"], "dismissed")
                    st.rerun()
                if c3.button("Marcar completada", key=f"seo_rec_complete_{rec['id']}"):
                    set_recommendation_status(engine, rec["id"], "completed")
                    st.rerun()
        return

    if area == "Conversiones":
        st.subheader("Conversiones y formularios")
        st.info("Todavía no se importan eventos de GA4 ni envíos de formularios. Esta vista distingue falta de instrumentación de un cero medido.")
        if not site_id:
            st.info("Crea un sitio y configura la medición para poder vincular datos de conversión.")
            return
        with engine.connect() as conn:
            rows = [dict(row._mapping) for row in conn.execute(text("SELECT * FROM conversions WHERE site_profile_id=:s ORDER BY event_date DESC"), {"s": site_id})]
        measured_rows = [r for r in rows if r.get("measurement_status") == "measured"]
        total_forms = sum(int(r.get("count") or 0) for r in measured_rows)
        total_qualified = sum(int(r.get("qualified_count") or 0) for r in measured_rows)
        total_customers = sum(int(r.get("customer_count") or 0) for r in measured_rows)
        m1, m2, m3 = st.columns(3, gap="medium")
        m1.metric("Conversiones medidas", total_forms if measured_rows else "—")
        m2.metric("Cualificadas", total_qualified if measured_rows else "—")
        m3.metric("Clientes atribuidos", total_customers if measured_rows else "—")
        import plotly.graph_objects as go
        if measured_rows:
            from collections import defaultdict
            by_date = defaultdict(int)
            for row in measured_rows:
                by_date[str(row["event_date"])[:10]] += int(row.get("count") or 0)
            dates = sorted(by_date)
            conv_fig = go.Figure(go.Bar(x=dates, y=[by_date[d] for d in dates], marker={"color":CHART_COLORS["green"],"cornerradius":6}, hovertemplate="%{x}<br>%{y} conversiones<extra></extra>"))
            _theme_figure(conv_fig, 280)
            conv_fig.update_layout(showlegend=False, yaxis_title="Conversiones", margin={"l":4,"r":16,"t":12,"b":8})
            conv_fig.update_yaxes(rangemode="tozero")
            with st.container(border=True):
                _plot_card_heading("Conversiones registradas", "Suma diaria de filas instrumentadas")
                _render_chart(conv_fig, "seo_conversion_trend")
        else:
            with st.container(border=True):
                _plot_card_heading("Embudo de conversión", "Vista de referencia", demo=True)
                funnel_fig = go.Figure(go.Funnel(y=["Visitas", "Inicio de formulario", "Envío", "Cualificada", "Cliente"], x=[1000, 120, 48, 22, 9],
                    marker={"color":["#53647C",CHART_COLORS["blue"],CHART_COLORS["orange"],CHART_COLORS["purple"],CHART_COLORS["green"]]},
                    textinfo="value+percent initial", hovertemplate="%{label}: %{value}<extra></extra>"))
                _theme_figure(funnel_fig, 300)
                funnel_fig.update_layout(showlegend=False, margin={"l":12,"r":12,"t":12,"b":8})
                _render_chart(funnel_fig, "seo_conversion_demo_funnel")
                st.caption("Valores ficticios. GA4 y el seguimiento de formularios todavía no están conectados.")
        if rows:
            st.markdown("### Registros de conversión")
            st.dataframe([{"Fecha": r["event_date"], "Página ID": r["page_id"], "Evento": r["event_name"], "Envíos": r["count"], "Cualificados": r["qualified_count"], "Clientes": r["customer_count"], "Estado": classify_conversion_state(r["count"], r["measurement_status"]), "Fuente": r["source"]} for r in rows], use_container_width=True, hide_index=True)
        st.caption("No se guardan nombres, correos ni textos de formularios en este módulo. La ausencia de registros no equivale a cero conversiones.")
        return

    if area == "Conexiones":
        st.subheader("Conexiones e integraciones")
        st.warning("Las credenciales no se guardan en la base de datos. Actualmente solo está implementada la prueba de lectura de WordPress.")
        if not site_id:
            st.info("Crea un sitio antes de probar WordPress.")
            return
        with st.form("seo_wordpress_readonly"):
            wp_url = st.text_input("URL de WordPress HTTPS", value=site.get("wp_api_url") or site["base_url"])
            username = st.text_input("Usuario técnico de WordPress")
            app_password = st.text_input("Application Password", type="password")
            test = st.form_submit_button("Probar conexión (solo lectura)", type="primary")
        if test:
            try:
                info = test_wordpress_readonly(wp_url, username, app_password)
                st.success(f"Conexión de lectura correcta: {info['name']} (ID {info['id']}). No se ha escrito contenido.")
            except Exception as exc:
                st.error(str(exc))
        st.markdown("### Pendiente de conectar")
        c1, c2, c3 = st.columns(3)
        c1.markdown("**Google Search Console**\n\nOAuth, permisos y sincronización")
        c2.markdown("**Google Analytics 4**\n\nData API y eventos de formularios")
        c3.markdown("**Google Ads**\n\nAcceso API, costes y términos de búsqueda")
        st.caption("Rank Math requiere verificar qué metadatos expone la instalación y qué capacidades de escritura admite, por separado.")
        return
