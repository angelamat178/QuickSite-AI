"""Datos de demostración de la interfaz.

IMPORTANTE: todo lo de este módulo es ilustrativo. No es contenido validado
ni debe usarse en producción.
"""
from __future__ import annotations

from datetime import datetime, timedelta

LIMITE_FICHAS_ACTIVAS = 5
TIPOS_FICHA = ["General", "Estilo", "SEO", "Contenido"]
SITIOS_WP = ["Mi Sitio WordPress", "Sitio de pruebas"]
TONOS = ["Profesional", "Conversacional", "Informativo", "Persuasivo", "Creativo"]

# (clave, etiqueta, palabras aproximadas, nº de secciones intermedias)
LONGITUDES = [
    ("corto", "Corto (300–600 palabras)", 450, 2),
    ("medio", "Medio (600–1200 palabras)", 900, 3),
    ("largo", "Largo (1200+ palabras)", 1500, 5),
]

ESTADOS = ["Generada", "Enviada como borrador"]

FICHAS_INICIALES = [
    {
        "id": "datos_fijos",
        "nombre": "Datos fijos",
        "tipo": "General",
        "descripcion": "Información de la empresa, público objetivo, tono de voz y detalles que se mantienen en todos los artículos.",
        "contenido": (
            "Nuestra empresa se dedica a la creación de contenido digital para negocios y marcas. "
            "Nuestro público objetivo son emprendedores, pequeñas y medianas empresas (pymes) y "
            "profesionales del marketing.\n\n"
            "El tono de voz es cercano, claro y profesional. Siempre buscamos aportar valor con "
            "información útil, práctica y fácil de aplicar.\n\n"
            "La estructura de los artículos suele ser:\n"
            "- Título llamativo\n"
            "- Introducción breve\n"
            "- Desarrollo con subtítulos (H2, H3)\n"
            "- Conclusión con llamada a la acción."
        ),
        "activa": True,
    },
    {
        "id": "estilo",
        "nombre": "Estilo",
        "tipo": "Estilo",
        "descripcion": "Guía de estilo, tono, estructura y formato de los artículos.",
        "contenido": (
            "- Frases cortas.\n- Voz activa.\n- Sin tecnicismos innecesarios.\n"
            "- Trato de tú al lector.\n- Párrafos de un máximo de cuatro líneas."
        ),
        "activa": True,
    },
    {
        "id": "reglas",
        "nombre": "Reglas",
        "tipo": "SEO",
        "descripcion": "Buenas prácticas, normas y restricciones de contenido.",
        "contenido": (
            "- No inventar precios, plazos ni datos legales.\n"
            "- Utilizar los datos fijos como fuente de información.\n"
            "- Un H1 por entrada.\n- Incluir la palabra clave en el primer párrafo."
        ),
        "activa": True,
    },
    {
        "id": "tema",
        "nombre": "Tema",
        "tipo": "Contenido",
        "descripcion": "Temas, palabras clave y enfoques recurrentes para los artículos.",
        "contenido": (
            "- Trámites de vehículos.\n- Gestión administrativa.\n- Marketing digital para pymes."
        ),
        "activa": False,
    },
]


def historial_inicial() -> list[dict]:
    """Siete entradas de demostración con fechas relativas a hoy."""
    ahora = datetime.now()

    def f(dias: int, h: int, m: int) -> datetime:
        return (ahora - timedelta(days=dias)).replace(hour=h, minute=m, second=0, microsecond=0)

    base = [
        (f(2, 14, 32), "Cómo crear una página web rápida y profesional con WordPress",
         ["wordpress", "página web", "web rápida", "diseño web"], "Generada", 6,
         "Crear una página web ya no es solo cosa de grandes empresas. Con WordPress puedes tener tu "
         "propio sitio web de forma rápida, sencilla y profesional, sin necesidad de conocimientos "
         "avanzados de programación. En este artículo te explicamos, paso a paso, cómo hacerlo."),
        (f(3, 16, 17), "Los mejores plugins para WordPress en 2026",
         ["plugins", "wordpress", "seo", "mejores plugins"], "Enviada como borrador", 7,
         "Los plugins amplían lo que puede hacer tu web. Repasamos criterios para elegir los que "
         "realmente necesitas y evitar los que solo ralentizan el sitio."),
        (f(5, 11, 3), "Guía completa de SEO para principiantes",
         ["seo", "posicionamiento", "wordpress", "marketing digital"], "Generada", 9,
         "El SEO es el conjunto de prácticas que ayudan a que tu web aparezca mejor en los "
         "buscadores. Esta guía recorre las bases para empezar con buen pie."),
        (f(7, 9, 45), "Cómo elegir el mejor hosting para tu web",
         ["hosting", "wordpress", "rendimiento", "seguridad"], "Generada", 5,
         "El hosting condiciona la velocidad y la seguridad de tu sitio. Te contamos qué aspectos "
         "comparar antes de decidirte."),
        (f(9, 15, 22), "Diseño web con Elementor: trucos y consejos",
         ["elementor", "diseño web", "wordpress"], "Enviada como borrador", 6,
         "Elementor permite maquetar páginas de forma visual. Reunimos trucos para trabajar con "
         "orden y mantener un diseño coherente."),
        (f(12, 12, 8), "Estrategias de marketing digital para pequeñas empresas",
         ["marketing digital", "pymes", "estrategias"], "Generada", 8,
         "Las pequeñas empresas también pueden competir online. Estas son estrategias de marketing "
         "digital que se adaptan a presupuestos y equipos reducidos."),
        (f(15, 10, 30), "Qué es un CMS y por qué importa para tu negocio",
         ["cms", "wordpress", "negocio"], "Generada", 4,
         "Un CMS es el sistema que te permite crear y gestionar el contenido de tu web sin "
         "programar. Veamos por qué es clave para tu negocio."),
    ]
    return [
        {
            "id": f"h{i + 1}", "fecha": fecha, "titulo": titulo, "palabras_clave": kws,
            "estado": estado, "lectura": lectura, "resumen": resumen,
        }
        for i, (fecha, titulo, kws, estado, lectura, resumen) in enumerate(base)
    ]


# ------------------------------------------------------------------ en masa
CIUDADES = [
    "Barcelona", "Madrid", "Valencia", "Sevilla", "Bilbao", "Zaragoza", "Málaga", "Murcia", "Palma",
    "Las Palmas de Gran Canaria", "Alicante", "Córdoba", "Valladolid", "Vigo", "Gijón",
    "L'Hospitalet de Llobregat", "Vitoria-Gasteiz", "A Coruña", "Granada", "Elche", "Oviedo", "Badalona",
    "Cartagena", "Terrassa", "Jerez de la Frontera", "Sabadell", "Móstoles", "Santa Cruz de Tenerife",
    "Pamplona", "Almería", "Alcalá de Henares", "Fuenlabrada", "Leganés", "San Sebastián", "Getafe",
    "Burgos", "Albacete", "Santander", "Castellón de la Plana", "Alcorcón", "San Cristóbal de La Laguna",
    "Logroño", "Badajoz", "Salamanca", "Huelva", "Marbella", "Lleida", "Tarragona", "León", "Cádiz",
]
LIMITE_MASIVO = 50

PLANTILLAS_MASIVO = [
    {"id": "bajas", "nombre": "Bajas de vehículos en {ciudad}",
     "tema": "bajas de vehículos en {ciudad}", "kw": "baja de vehículos {ciudad}"},
    {"id": "nombre", "nombre": "Cambio de nombre de un coche en {ciudad}",
     "tema": "cómo cambiar el nombre de un coche en {ciudad}", "kw": "cambio de titularidad coche {ciudad}"},
    {"id": "gestoria", "nombre": "Gestoría para pymes en {ciudad}",
     "tema": "gestoría para pymes en {ciudad}", "kw": "gestoría pymes {ciudad}"},
]

ESTADOS_PAGINA = ["Borrador", "En revisión", "Aprobada", "Publicada"]

# ------------------------------------------------- Search Console (DEMO)
# (consulta, clics, impresiones, posición media). Datos ficticios de demostración.
SC_CONSULTAS = [
    ("baja de vehículos barcelona", 1840, 21300, 3.8),
    ("dar de baja un coche", 1210, 48900, 7.4),
    ("baja definitiva vehículo", 960, 17400, 5.1),
    ("cambiar nombre coche", 870, 39200, 9.6),
    ("baja temporal coche madrid", 640, 12800, 6.2),
    ("cambio de titularidad vehículo", 590, 41500, 11.3),
    ("baja de vehículos valencia", 430, 9700, 8.9),
    ("cuánto cuesta dar de baja un coche", 380, 15600, 12.7),
    ("gestoría baja vehículos sevilla", 260, 5100, 6.8),
    ("plugins wordpress seo", 210, 18900, 14.2),
    ("hosting wordpress rápido", 150, 12100, 16.5),
    ("marketing digital pymes", 120, 9400, 18.1),
]
SC_PAGINAS = [
    ("/bajas-de-vehiculos-en-barcelona", 2310, 26100, 4.1),
    ("/bajas-de-vehiculos-en-madrid", 1620, 22800, 5.7),
    ("/como-cambiar-el-nombre-de-un-coche", 1180, 43900, 8.8),
    ("/bajas-de-vehiculos-en-valencia", 760, 15200, 9.4),
    ("/guia-completa-de-seo-para-principiantes", 420, 21800, 13.0),
    ("/los-mejores-plugins-para-wordpress", 260, 19700, 14.9),
]
SC_PROPIEDAD = "sc-domain:midominio.com"
SC_DELTAS = {"clics": ("+12,4 %", True), "impr": ("+8,1 %", True), "ctr": ("+0,3 pp", True), "pos": ("−0,6", True)}


def sc_serie(dias: int) -> dict:
    """Serie diaria determinista (sin azar) para la demo."""
    import math
    hoy = datetime.now()
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    et, clics, impr, pos = [], [], [], []
    for i in range(dias):
        d = hoy - timedelta(days=dias - 1 - i)
        t = i / max(dias - 1, 1)
        finde = d.weekday() >= 5
        c = round(300 + 220 * t + 45 * math.sin(i * 0.9) - (70 if finde else 0))
        et.append(f"{d.day} {meses[d.month - 1]}")
        clics.append(c)
        impr.append(round(c * 13.5 + 650 * math.sin(i * 0.5 + 1)))
        pos.append(round(9.6 - 2.4 * t + 0.35 * math.sin(i * 0.7), 1))
    ctr = [round(c / i * 100, 2) for c, i in zip(clics, impr)]
    return {"etiquetas": et, "clics": clics, "impr": impr, "ctr": ctr, "pos": pos}
