# QuickSite — Contexto

**QuickSite** es una aplicación interna que genera **entradas de blog en castellano** para WordPress a partir de una petición en lenguaje natural (palabras clave, tema, tono, extras) y las deja en WordPress como **borrador**, listas para revisión humana. Nunca publica.

**Repositorio:** https://github.com/angelamat178/QuickSite-AI
**Equipo:** Ángel e Ismael · **Estado:** en desarrollo (Fase 0, preparación) · **Objetivo de la v1:** antes de diciembre de 2026

## Idea clave

- **IA local y gratuita** con Ollama, en un equipo propio. No salen datos a servicios externos.
- **Sin entrenar modelos.** El conocimiento de la empresa (datos fijos, estilo, reglas, temas) vive en **fichas de contexto** editables que se añaden al prompt. Cambiando de fichas, la misma herramienta sirve para otro tema o negocio.
- **Revisión humana siempre.** Los datos fijos (precios, plazos, horarios) no los puede inventar ni modificar el modelo.

## Cómo funciona

Petición del usuario → fichas de contexto activas → prompt → Ollama genera la entrada (JSON) → validación → previsualización y edición → imagen de stock con crédito → borrador en WordPress (con campos de Rank Math) → revisión y publicación humana.

## Interfaz

Aplicación con dos modos: **Construcción** (genera la entrada y la previsualiza) y **Chat** (conversación con la IA usando las fichas activas). Incluye gestor de fichas, historial de generaciones y botón para enviar el borrador a WordPress. Solo modo oscuro, con acento naranja.

## Alcance de la v1

Solo entradas de blog, en castellano, para WordPress con Elementor (versión base) y Rank Math SEO. Uso interno, máximo 3 personas.

## Tecnologías

Python · Streamlit · Ollama (local) · WordPress (API REST) · Rank Math SEO · Elementor · Pexels (imágenes) · Git y GitHub · Windows.

## Más información

El detalle del proyecto, la hoja de ruta y las decisiones están en el repositorio (`README.md` y carpeta `docs/`). Parte del contenido puede estar desactualizado mientras el proyecto está en desarrollo.
