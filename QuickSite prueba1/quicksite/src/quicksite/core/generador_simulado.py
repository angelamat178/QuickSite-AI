"""Generador FALSO: devuelve una entrada de ejemplo con el formato JSON del README.

Cuando conectéis Ollama (Fase 2), sustituid el contenido de `generar_borrador`
y `responder_chat` manteniendo la misma firma y los mismos campos.
"""
import re
import unicodedata
import uuid
from datetime import datetime


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def generar_borrador(peticion: str, titulo: str | None = None, palabra_clave: str | None = None) -> dict:
    tema = re.sub(r"^(entrada|artículo|articulo|post)\s+(sobre|de)\s+", "", peticion.strip(), flags=re.I)
    tema = tema.rstrip(".") or "tu tema"
    titulo = titulo or f"{tema[0].upper() + tema[1:]} paso a paso"
    palabra_clave = palabra_clave or tema.lower()

    cuerpo = (
        f"<p><strong>{tema[0].upper() + tema[1:]}</strong> es un tema que preocupa a muchas "
        "personas. En esta guía te lo explicamos de forma clara y sencilla.</p>"
        "<h2>¿Qué necesitas saber antes de empezar?</h2>"
        "<p>Reúne la documentación básica y comprueba los requisitos. "
        "Este texto es simulado: aquí irá el contenido real generado por el modelo.</p>"
        "<h2>Pasos a seguir</h2>"
        "<p>1. Prepara los documentos. 2. Realiza el trámite. 3. Guarda el justificante.</p>"
        "<h2>Conclusión</h2>"
        "<p>Con los pasos adecuados es más fácil de lo que parece. ¡Contacta con nosotros si tienes dudas!</p>"
    )
    return {
        "id": uuid.uuid4().hex[:8],
        "fecha": datetime.now(),
        "titulo": titulo,
        "slug": _slug(titulo),
        "meta_titulo": titulo[:60],
        "meta_descripcion": f"Descubre todo sobre {tema.lower()}: pasos, requisitos y consejos. Guía completa y actualizada.",
        "palabra_clave": palabra_clave,
        "cuerpo_html": cuerpo,
        "faq": [
            {"pregunta": "¿Cuánto tiempo se tarda?", "respuesta": "Depende de cada caso (dato simulado)."},
            {"pregunta": "¿Puedo hacerlo online?", "respuesta": "En muchos casos sí (dato simulado)."},
        ],
        "imagen_busqueda": "documents desk paperwork",
        "imagen_alt": f"Imagen ilustrativa sobre {tema.lower()}",
        "categoria": "Guías",
        "minutos_lectura": 5,
        "avisos": [
            "Comprueba cifras y plazos con las fichas de datos fijos.",
            "Revisa la imagen y el crédito antes de publicar.",
        ],
    }


def responder_chat(mensaje: str, nombres_fichas: list[str]) -> str:
    contexto = ", ".join(nombres_fichas) if nombres_fichas else "ninguna ficha"
    return (
        f"Respuesta simulada a: «{mensaje}».\n\n"
        f"(Fichas de contexto activas: {contexto}). "
        "Cuando conectemos Ollama, aquí aparecerá la respuesta real del modelo."
    )
