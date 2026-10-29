"""Lógica de demostración que sustituye temporalmente a Ollama.

Principio: este módulo NUNCA inventa precios, plazos, horarios ni datos legales.
Donde haría falta un dato fijo deja un marcador [PENDIENTE: ...] que debe
rellenarse desde las fichas de contexto y revisarse antes de publicar.

El cuerpo del artículo se guarda como texto con marcado ligero (`cuerpo`):
    ## Título de sección      -> h2
    - elemento                -> lista
    1. elemento               -> lista numerada
    **negrita**               -> strong
    [PENDIENTE: ...]          -> marcador resaltado
Todo el texto se escapa antes de convertirse a HTML (`texto_a_html`), por lo
que `cuerpo_html` siempre es seguro de insertar.
"""
from __future__ import annotations

import html as _html
import math
import re
import unicodedata
import uuid
from datetime import datetime

from quicksite.core import datos_simulados as ds

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MARCA_PENDIENTE = "[PENDIENTE:"
TXT_COSTES = (
    "[PENDIENTE: importes, tasas y plazos tomados de tus datos fijos. "
    "QuickSite no los inventa; no publiques esta sección sin completarla.]"
)
TXT_FAQ_PENDIENTE = "[PENDIENTE: respuesta basada en tus datos fijos.]"


# ---------------------------------------------------------------- utilidades
def ahora() -> datetime:
    return datetime.now()


def hora(d: datetime | None = None) -> str:
    return (d or ahora()).strftime("%H:%M")


def fecha_corta(d: datetime) -> str:
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def _norm(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _slug(texto: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", _norm(texto)).strip("-")
    return s[:60].strip("-") or "entrada"


_PREFIJO = re.compile(
    r"^\s*(?:(?:escribe|redacta|genera|crea|haz)(?:me)?\s+)?(?:una?\s+)?"
    r"(?:entrada|art[ií]culo|post|texto)\s+(?:de\s+blog\s+)?(?:sobre|acerca\s+de|de)\s+",
    re.IGNORECASE,
)


def _limpiar_tema(peticion: str) -> str:
    t = _PREFIJO.sub("", (peticion or "").strip())
    t = re.sub(r"\s+", " ", t).strip(" .:;!¡")
    return t[:120]


def _es_coche(texto: str) -> bool:
    return bool(re.search(
        r"\b(coche|coches|vehiculo|vehiculos|automovil|moto|matricula|trafico|dgt)\b", _norm(texto)
    ))


def _cap(t: str) -> str:
    return t[:1].upper() + t[1:] if t else t


def _titulo(tema: str) -> str:
    base = _cap(tema)
    if _norm(base).startswith("como ") and "paso a paso" not in _norm(base):
        return f"{base} paso a paso"
    if _norm(base).startswith("como "):
        return base
    return f"{base}: guía práctica"


# ------------------------------------------------------- marcado -> HTML
def _inline(t: str) -> str:
    t = _html.escape(t, quote=True).replace("$", "&#36;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[PENDIENTE:([^\]]*)\]", r'<span class="pend">[PENDIENTE:\1]</span>', t)
    return t


def texto_a_html(texto: str) -> str:
    """Convierte el marcado ligero en HTML seguro (todo se escapa antes)."""
    out: list[str] = []
    lista: str | None = None

    def cerrar() -> None:
        nonlocal lista
        if lista:
            out.append(f"</{lista}>")
            lista = None

    for linea in (texto or "").splitlines():
        l = linea.strip()
        if not l:
            cerrar()
            continue
        if l.startswith("## "):
            cerrar()
            out.append(f"<h2>{_inline(l[3:])}</h2>")
        elif l.startswith("- "):
            if lista != "ul":
                cerrar()
                out.append("<ul>")
                lista = "ul"
            out.append(f"<li>{_inline(l[2:])}</li>")
        elif re.match(r"^\d+\.\s", l):
            if lista != "ol":
                cerrar()
                out.append("<ol>")
                lista = "ol"
            item = re.sub(r"^\d+\.\s", "", l)
            out.append(f"<li>{_inline(item)}</li>")
        else:
            cerrar()
            out.append(f"<p>{_inline(l)}</p>")
    cerrar()
    return "".join(out)


def _texto_plano(html_str: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_str)).strip()


def _lectura(html_str: str) -> int:
    palabras = len(_texto_plano(html_str).split())
    return max(1, math.ceil(palabras / 200))


def recalcular(b: dict) -> dict:
    """Recalcula los campos derivados tras editar `titulo`, `cuerpo` o `faq`."""
    b["cuerpo_html"] = texto_a_html(b["cuerpo"])
    b["palabras"] = len(_texto_plano(b["cuerpo_html"]).split())
    b["lectura"] = _lectura(b["cuerpo_html"])
    b["slug"] = _slug(b["titulo"])
    b["meta_titulo"] = b["titulo"][:60]
    b["avisos"] = _avisos(b)
    return b


def _avisos(b: dict) -> list[str]:
    avisos = ["Borrador de demostración: no hay modelo conectado; el texto es genérico."]
    if MARCA_PENDIENTE in b["cuerpo"] or any(MARCA_PENDIENTE in f["a"] for f in b["faq"]):
        avisos.append("Hay marcadores [PENDIENTE]: completa esos datos desde las fichas antes de enviar.")
    avisos.append("Revisión humana obligatoria antes de publicar en WordPress.")
    return avisos


# ------------------------------------------------------------ generación
_TONO_FRASE = {
    "Profesional": "Lo abordamos con rigor y de forma ordenada.",
    "Conversacional": "Vamos a verlo juntos, sin prisas y sin tecnicismos.",
    "Informativo": "Reunimos los puntos esenciales para que decidas con criterio.",
    "Persuasivo": "Tomar buenas decisiones aquí marca la diferencia.",
    "Creativo": "Te proponemos mirarlo desde un ángulo distinto.",
}


def _seccion_costes() -> str:
    return f"## Costes y plazos\n{TXT_COSTES}"


def _secciones(tema: str, coche: bool, n: int) -> list[str]:
    t = tema.lower()
    if coche:
        pool = [
            "## ¿Qué documentos necesitas?\nAntes de empezar, reúne la documentación necesaria. "
            "La lista exacta debe confirmarse con tus datos fijos:\n"
            "- Documento de identidad de las personas implicadas.\n"
            "- Documento que acredite la titularidad del vehículo.\n"
            "- Cualquier otro documento que indiquen tus datos fijos.",
            "## Paso a paso del trámite\nUn orden claro evita errores:\n"
            "1. Reúne y revisa la documentación.\n"
            "2. Comprueba que los datos coinciden en todos los documentos.\n"
            "3. Realiza el trámite por el canal que corresponda.\n"
            "4. Guarda el justificante.",
            _seccion_costes(),
            "## Errores habituales\nLos fallos más comunes suelen ser documentación incompleta o datos "
            "que no coinciden. Revísalo todo antes de iniciar el trámite.",
        ]
    else:
        pool = [
            f"## Qué debes saber antes de empezar\nAntes de entrar en detalle sobre {t}, conviene "
            "tener claro el objetivo y reunir la información de partida.",
            f"## Pasos para empezar\nUn proceso ordenado ayuda a avanzar con seguridad:\n"
            "1. Define el objetivo.\n2. Reúne la información necesaria.\n"
            "3. Ejecuta los pasos uno a uno.\n4. Revisa el resultado.",
            "## Consejos para que destaque\nCuida los detalles, usa un lenguaje claro y apóyate en "
            "ejemplos propios de tu actividad.",
            "## Errores habituales que conviene evitar\nSuele fallar la falta de planificación y no "
            "revisar el resultado final antes de publicarlo.",
            "## Próximos pasos\nCuando tengas lo básico, mejora de forma gradual midiendo qué funciona.",
        ]
    return pool[: max(1, n)]


def _faq_por_defecto() -> list[dict]:
    return [
        {"q": "¿Por dónde empiezo?",
         "a": "Empieza por definir el objetivo y reunir la información que ya tienes. Después sigue los pasos del artículo."},
        {"q": "¿Cuánto tiempo necesito?",
         "a": TXT_FAQ_PENDIENTE},
        {"q": "¿Puedo hacerlo yo mismo?",
         "a": "En general sí, siguiendo los pasos con calma. Si tienes dudas, consulta antes con un profesional."},
    ]


def generar_borrador(peticion: str, tono: str = "Profesional", longitud: str = "medio",
                     palabras_clave: str = "", fichas: list[dict] | None = None,
                     categoria: str = "Guía") -> dict:
    tema = _limpiar_tema(peticion) or "tu tema"
    coche = _es_coche(peticion)
    kws = [k.strip() for k in (palabras_clave or "").split(",") if k.strip()]
    clave = kws[0] if kws else tema.lower()
    n = next((x[3] for x in ds.LONGITUDES if x[0] == longitud), 3)
    titulo = _titulo(tema)

    intro = (
        f"Si buscas información sobre **{clave}**, este artículo te lo explica de forma clara y sin "
        f"rodeos. {_TONO_FRASE.get(tono, '')}"
    )
    conclusion = (
        f"## Conclusión\nAhora tienes una visión ordenada de {tema.lower()}. "
        "Revisa los datos concretos antes de actuar y, si lo necesitas, contacta con nosotros."
    )
    cuerpo = "\n\n".join([intro, *_secciones(tema, coche, n), conclusion])
    d = ahora()
    b = {
        "titulo": titulo,
        "slug": "",
        "meta_titulo": "",
        "meta_descripcion": f"Descubre todo sobre {tema.lower()}. Una guía clara y práctica, redactada con tono {tono.lower()}."[:160],
        "palabra_clave": clave,
        "palabras": 0,
        "cuerpo": cuerpo,
        "cuerpo_html": "",
        "faq": _faq_por_defecto(),
        "imagen_busqueda": tema.lower(),
        "imagen_alt": f"Imagen ilustrativa sobre {tema.lower()}",
        "avisos": [],
        "categoria": categoria or "Guía",
        "fecha": d,
        "lectura": 1,
        "enviado": False,
        "hist_id": None,
        "v": 0,
        # extras de la demo
        "tema": tema,
        "tono": tono,
        "palabras_clave": kws or [clave],
        "fichas_usadas": [f["nombre"] for f in (fichas or [])],
    }
    return recalcular(b)


# ------------------------------------------------------------ refinamiento
def refinar_borrador(b: dict, instruccion: str) -> tuple[dict, str]:
    """Aplica uno de los cambios limitados de la demo. Devuelve (borrador, respuesta)."""
    n = dict(b)
    n["faq"] = [dict(x) for x in b["faq"]]
    ins = _norm(instruccion)

    if re.search(r"\b(coste|costes|plazo|plazos|precio|precios)\b", ins):
        if "## Costes y plazos" in n["cuerpo"]:
            return b, "La sección «Costes y plazos» ya existe en el borrador."
        partes = n["cuerpo"].split("\n\n## Conclusión")
        n["cuerpo"] = partes[0] + "\n\n" + _seccion_costes() + "\n\n## Conclusión" + "".join(partes[1:])
        return recalcular(n), (
            "He añadido la sección «Costes y plazos» con un marcador [PENDIENTE]: los importes y "
            "plazos deben salir de tus datos fijos; no los invento."
        )

    if re.search(r"\b(acorta|acortar|corto|reduce|reducir|resume|resumir)\b", ins):
        bloques = n["cuerpo"].split("\n\n")
        intermedios = bloques[1:-1]
        if len(intermedios) <= 1:
            return b, "El artículo ya es corto; no hay secciones que quitar."
        n["cuerpo"] = "\n\n".join([bloques[0], intermedios[0], bloques[-1]])
        return recalcular(n), "He acortado el artículo dejando la introducción, una sección y la conclusión."

    if re.search(r"\b(titulo|titulos)\b", ins):
        n["v"] = b["v"] + 1
        t = _cap(b.get("tema", b["titulo"]))
        opciones = [
            f"Todo lo que necesitas saber sobre {t.lower()}",
            f"{t}: claves para hacerlo bien",
            f"{t}: guía práctica y sin complicaciones",
        ]
        n["titulo"] = opciones[(n["v"] - 1) % len(opciones)]
        return recalcular(n), f"Te propongo otro título: «{n['titulo']}»."

    if re.search(r"\b(pregunta|preguntas|faq)\b", ins):
        n["faq"].append({"q": "¿Dónde puedo resolver más dudas?", "a": TXT_FAQ_PENDIENTE})
        return recalcular(n), "He añadido una pregunta frecuente con la respuesta pendiente de tus datos fijos."

    if re.search(r"\b(introduccion|intro)\b", ins):
        bloques = n["cuerpo"].split("\n\n")
        bloques[0] = (f"¿Buscas información sobre **{b['palabra_clave']}**? "
                      "Aquí tienes una guía directa, ordenada y fácil de seguir.")
        n["cuerpo"] = "\n\n".join(bloques)
        return recalcular(n), "He reescrito la introducción: es más directa y mantiene la palabra clave en el primer párrafo."

    if re.search(r"\b(meta|descripcion)\b", ins):
        n["meta_descripcion"] = (
            f"Guía clara sobre {b.get('tema', b['titulo']).lower()}: pasos, documentación y consejos "
            "prácticos para hacerlo bien a la primera.")[:160]
        return recalcular(n), "He reescrito la meta descripción (dentro del límite de 160 caracteres)."

    # Demo: cualquier otra instrucción produce siempre el mismo cambio.
    if "## Resumen rápido" in n["cuerpo"]:
        return b, "Ya apliqué ese ajuste en esta demo: no hay cambios adicionales."
    partes = n["cuerpo"].split("\n\n", 1)
    resumen = ("## Resumen rápido\n- Reúne la documentación.\n- Sigue los pasos en orden.\n"
               "- Revisa los datos antes de publicar.")
    n["cuerpo"] = partes[0] + "\n\n" + resumen + ("\n\n" + partes[1] if len(partes) > 1 else "")
    return recalcular(n), ("He aplicado tu instrucción: añadí un bloque «Resumen rápido» tras la introducción. "
                           "(Demo: ante instrucciones libres siempre hago este mismo cambio.)")


def _chat_general(mensaje: str, n_fichas: int) -> str:
    m = _norm(mensaje)
    if n_fichas == 0:
        ctx = "Ahora mismo no hay fichas activas, así que respondería sin contexto de empresa."
    else:
        ctx = f"Tengo en cuenta tus {n_fichas} fichas activas."
    if re.search(r"\b(hola|buenas|hey)\b", m):
        return f"¡Hola! Soy QuickSite (modo demostración). {ctx} ¿Sobre qué quieres escribir?"
    if re.search(r"\b(articulo|entrada|post|redacta|escribe)\b", m):
        return (f"{ctx} Para generar un borrador completo, ve a «Construcción» y describe el tema. "
                "En esta demo el chat no llama a ningún modelo real.")
    if re.search(r"\b(ficha|fichas)\b", m):
        return f"{ctx} Puedes activarlas, editarlas o crear nuevas en la sección «Fichas» (máximo {ds.LIMITE_FICHAS_ACTIVAS} activas)."
    return (f"{ctx} Esto es una respuesta simulada: aún no hay Ollama conectado. "
            "Cuando lo esté, responderé usando las fichas activas.")


def entrada_historial(b: dict) -> dict:
    primer = _texto_plano(texto_a_html(b["cuerpo"].split("\n\n")[0]))
    return {
        "id": "h" + uuid.uuid4().hex[:8],
        "fecha": b["fecha"],
        "titulo": b["titulo"],
        "palabras_clave": list(b.get("palabras_clave") or [b["palabra_clave"]]),
        "estado": "Enviada como borrador" if b["enviado"] else "Generada",
        "lectura": b["lectura"],
        "resumen": primer,
    }


# ------------------------------------------------------------ SEO (demo)
def puntuacion_seo(b: dict) -> tuple[int, list[tuple[bool, str]]]:
    """Puntuación 0-100 con 6 criterios deterministas. Devuelve (nota, [(ok, criterio)])."""
    kw = _norm(b["palabra_clave"])
    tema = _norm(b.get("tema", b["palabra_clave"]))
    titulo = _norm(b["titulo"])
    primer = _norm(b["cuerpo"].split("\n\n")[0])
    meta = len(b["meta_descripcion"])
    h2 = len(re.findall(r"^## ", b["cuerpo"], re.M))
    checks = [
        (kw in titulo or tema in titulo, "Palabra clave (o tema) en el título"),
        (kw in primer, "Palabra clave en el primer párrafo"),
        (70 <= meta <= 160, "Meta descripción entre 70 y 160 caracteres"),
        (h2 >= 3, "Al menos 3 subtítulos H2"),
        (len(b["faq"]) >= 3, "Al menos 3 preguntas frecuentes"),
        (MARCA_PENDIENTE not in b["cuerpo"] and not any(MARCA_PENDIENTE in f["a"] for f in b["faq"]),
         "Sin marcadores [PENDIENTE]"),
    ]
    return round(100 * sum(ok for ok, _ in checks) / len(checks)), checks


_NEUTRO = "Consulta siempre la información oficial actualizada."
_PAT_PEND = re.compile(r"\[PENDIENTE:[^\]]*\]")


def completar_pendientes(b: dict) -> dict:
    """DEMO: sustituye los marcadores por un texto neutro (sin cifras)."""
    b["cuerpo"] = _PAT_PEND.sub(_NEUTRO, b["cuerpo"])
    b["faq"] = [{**f, "a": _PAT_PEND.sub(_NEUTRO, f["a"])} for f in b["faq"]]
    return recalcular(b)


def tiene_pendientes(b: dict) -> bool:
    return MARCA_PENDIENTE in b["cuerpo"] or any(MARCA_PENDIENTE in f["a"] for f in b["faq"])


# --------------------------------------------------------------- en masa
def generar_masivo(plantilla: dict, ciudades: list[str], tono: str = "Profesional",
                   longitud: str = "corto", fichas: list[dict] | None = None) -> list[dict]:
    """Un borrador por variable, con la misma estructura. Los datos locales quedan [PENDIENTE]."""
    out = []
    for ciudad in ciudades:
        tema = plantilla["tema"].replace("{ciudad}", ciudad)
        kw = plantilla["kw"].replace("{ciudad}", ciudad).lower()
        b = generar_borrador(tema, tono, longitud, kw, fichas, categoria="Servicios")
        b["cuerpo"] = b["cuerpo"].replace(
            "\n\n## Conclusión",
            f"\n\n## Particularidades en {ciudad}\n[PENDIENTE: datos locales de {ciudad} "
            "(organismo, sede y horarios) tomados de tus datos fijos.]\n\n## Conclusión", 1)
        b["ciudad"] = ciudad
        out.append(recalcular(b))
    return out


# ---------------------------------------------------------------- consulta
TXT_ANALITICA = (
    "Con los datos de DEMOSTRACIÓN de Search Console veo tres oportunidades: "
    "1) «cambio de titularidad vehículo» suma 41.500 impresiones en posición 11,3; una página específica podría "
    "llevarla a la primera página. "
    "2) «cambiar nombre coche» está en posición 9,6 con CTR bajo: conviene mejorar título y meta descripción. "
    "3) Las páginas «Bajas de vehículos en …» concentran la mayoría de clics: replícalas con la generación en masa "
    "para más ciudades. Son datos de ejemplo, no reales."
)
_RE_MODIF = re.compile(
    r"\b(cambia|cambiar|modifica|modificar|anade|anadir|quita|quitar|acorta|acortar|reescribe|reescribir|"
    r"elimina|eliminar|mejora|mejorar|corrige|corregir|propon|propone)\b")


def consulta(mensaje: str, n_fichas: int, b: dict | None = None) -> tuple[str, str | None]:
    """Respuesta del modo Chat (solo consulta). Devuelve (texto, etiqueta)."""
    m = _norm(mensaje)
    if re.search(r"\b(search console|analitica|clics|ctr|impresiones|oportunidades|consultas)\b", m) \
            or "posicion media" in m:
        return TXT_ANALITICA, "consulta"
    if b is None:
        return _chat_general(mensaje, n_fichas), "consulta"
    if _RE_MODIF.search(m):
        return ("Estás en modo Chat: aquí solo respondo y no modifico la previsualización. "
                "Cambia a «Construcción» (arriba) y repite la instrucción para que la aplique."), "aviso"
    nota, checks = puntuacion_seo(b)
    if re.search(r"\b(seo|puntuacion|nota)\b", m):
        fallos = [lbl for ok, lbl in checks if not ok]
        extra = (" Criterios sin cumplir: " + "; ".join(fallos) + ".") if fallos else " Cumple todos los criterios."
        return f"La preview tiene {nota}/100 de puntuación SEO.{extra}", "consulta"
    if re.search(r"\b(palabras|extension|largo|lectura|longitud)\b", m):
        return f"La preview tiene {b['palabras']} palabras (≈ {b['lectura']} min de lectura).", "consulta"
    if re.search(r"\b(resume|resumen|resumir)\b", m):
        return f"«{b['titulo']}»: {_texto_plano(texto_a_html(b['cuerpo'].split(chr(10) * 2)[0]))}", "consulta"
    return (f"Sobre la preview «{b['titulo']}»: {b['palabras']} palabras, palabra clave «{b['palabra_clave']}» "
            f"y {nota}/100 de SEO. (Respuesta simulada: no hay modelo conectado.)"), "consulta"


def respuesta_chat(mensaje: str, n_fichas: int, b: dict | None = None) -> str:
    return consulta(mensaje, n_fichas, b)[0]
