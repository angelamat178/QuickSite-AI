"""Datos de ejemplo para la Fase 1 (interfaz sin modelo ni WordPress)."""
from datetime import datetime, timedelta

TIPOS_FICHA = ["Datos fijos", "Estilo", "Reglas", "Tema"]

FICHAS_INICIALES = [
    {
        "id": 1,
        "nombre": "Datos fijos",
        "tipo": "Datos fijos",
        "contenido": (
            "Nuestra empresa se dedica a la creación de contenido digital para "
            "negocios y marcas. Nuestro público objetivo son emprendedores, "
            "pequeñas y medianas empresas (pymes) y profesionales del marketing.\n\n"
            "El tono de voz es cercano, claro y profesional.\n\n"
            "Estructura habitual:\n- Título llamativo\n- Introducción breve\n"
            "- Desarrollo con subtítulos (H2, H3)\n- Conclusión con llamada a la acción"
        ),
        "activa": True,
    },
    {
        "id": 2,
        "nombre": "Estilo",
        "tipo": "Estilo",
        "contenido": "Cercano y claro, sin tecnicismos. Frases cortas. Tuteo al lector.",
        "activa": True,
    },
    {
        "id": 3,
        "nombre": "Reglas",
        "tipo": "Reglas",
        "contenido": "No citar leyes ni importes que no estén en los datos fijos. No inventar plazos.",
        "activa": True,
    },
    {
        "id": 4,
        "nombre": "Tema: trámites de tráfico",
        "tipo": "Tema",
        "contenido": "Cambio de titularidad, transferencias, bajas y duplicados de documentación de vehículos.",
        "activa": False,
    },
]

_AHORA = datetime.now()

HISTORIAL_INICIAL = [
    {
        "fecha": _AHORA - timedelta(days=2, hours=1),
        "titulo": "Cómo crear una página web rápida y profesional con WordPress",
        "palabra_clave": "crear página web wordpress",
        "estado": "Generada",
    },
    {
        "fecha": _AHORA - timedelta(days=3, hours=4),
        "titulo": "Los mejores plugins para WordPress",
        "palabra_clave": "mejores plugins wordpress",
        "estado": "Enviada como borrador",
    },
    {
        "fecha": _AHORA - timedelta(days=5, hours=2),
        "titulo": "Guía completa de SEO para principiantes",
        "palabra_clave": "seo para principiantes",
        "estado": "Generada",
    },
    {
        "fecha": _AHORA - timedelta(days=7, hours=6),
        "titulo": "Cómo elegir el mejor hosting para tu web",
        "palabra_clave": "mejor hosting",
        "estado": "Enviada como borrador",
    },
]
