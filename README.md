# QuickSite

> **Del brief al borrador de WordPress, con IA local y tus propias fichas de contexto.**

**Estado:** en desarrollo — Fase 0 (preparación)
**Equipo:** Ángel e Ismael
**Objetivo de la primera versión:** antes de diciembre de 2026

---

## Índice

1. [¿Qué es QuickSite?](#1-qué-es-quicksite)
2. [Cómo funciona](#2-cómo-funciona)
3. [Fichas de contexto](#3-fichas-de-contexto)
4. [Interfaz](#4-interfaz)
5. [Tecnologías](#5-tecnologías)
6. [Estructura del repositorio](#6-estructura-del-repositorio)
7. [Requisitos](#7-requisitos)
8. [Instalación y arranque](#8-instalación-y-arranque)
9. [Configuración](#9-configuración)
10. [Trabajo en equipo (Git)](#10-trabajo-en-equipo-git)
11. [Hoja de ruta y tareas](#11-hoja-de-ruta-y-tareas)
12. [Más adelante](#12-más-adelante)
13. [Decisiones pendientes](#13-decisiones-pendientes)
14. [Seguridad y revisión humana](#14-seguridad-y-revisión-humana)
15. [Licencia](#15-licencia)

---

## 1. ¿Qué es QuickSite?

QuickSite es una aplicación interna que genera **entradas de blog para WordPress** a partir de una petición escrita en lenguaje natural (palabras clave, tema, tono, extras) y las deja en WordPress como **borrador**, listas para revisión humana.

Puntos clave:

- **IA local y gratuita.** Usa [Ollama](https://ollama.com) en un equipo propio. No hay coste por uso ni salen datos a servicios externos.
- **Basada en fichas de contexto intercambiables.** El conocimiento sobre la empresa, el estilo y las reglas vive en fichas editables, no en el modelo. Cambiando de fichas, la misma herramienta sirve para otro tema o negocio.
- **Interfaz de chat con dos modos.** Un modo de *construcción* para generar entradas y un modo de *chat* para preguntar, comentar y pedir ajustes.
- **Revisión humana siempre.** QuickSite nunca publica: solo crea borradores.
- **Sin entrenar modelos.** Se consigue el resultado con contexto bien preparado (fichas + ejemplos), no con *fine-tuning*.

**Alcance de la versión 1:** solo entradas de blog, en castellano, para WordPress con Elementor y Rank Math SEO. Uso interno, máximo 3 personas.

---

## 2. Cómo funciona

```
Petición del usuario (palabras clave, tema, extras)
        ↓
Fichas de contexto activas (datos fijos + estilo + reglas)
        ↓
Ensamblado del prompt
        ↓
Ollama genera la entrada (JSON estructurado)
        ↓
Validación (estructura, longitud, datos fijos)
        ↓
Previsualización y edición en la app
        ↓
Imagen de stock + crédito
        ↓
API REST de WordPress → BORRADOR (con campos de Rank Math)
        ↓
Revisión humana en WordPress (Editar con Elementor) → publicación
```

### Formato de salida del modelo (JSON)

Cada generación devuelve una estructura fija:

| Campo | Descripción |
|---|---|
| `titulo` | Título de la entrada |
| `slug` | URL propuesta |
| `meta_titulo` | Título SEO |
| `meta_descripcion` | Descripción SEO |
| `palabra_clave` | Palabra clave principal |
| `cuerpo_html` | Contenido con encabezados H2/H3 |
| `faq` | Preguntas frecuentes |
| `imagen_busqueda` | Términos en inglés para buscar la foto de stock |
| `imagen_alt` | Texto alternativo de la imagen |
| `avisos` | Cosas que el revisor debe comprobar |

> **TODO:** cerrar este formato en la Fase 0 y guardarlo en `docs/formato-salida.md`.

---

## 3. Fichas de contexto

Una **ficha** es un archivo editable que le da contexto al modelo. Se pueden activar varias a la vez y combinarlas.

Tipos previstos:

| Tipo | Contenido | Ejemplo |
|---|---|---|
| **Datos fijos** | Información que el modelo no puede cambiar: precios, plazos, horarios, documentación, contacto | Tasas y plazos de cada trámite |
| **Estilo** | Tono, vocabulario, ejemplos de textos propios | "Cercano y claro, sin tecnicismos" |
| **Reglas** | Lo que nunca debe hacer | "No citar leyes ni importes que no estén en los datos fijos" |
| **Tema** | Contexto de un área concreta | Una familia de trámites |

Desde la app se pueden **crear, editar, duplicar, activar/desactivar y borrar** fichas.

> **TODO:** decidir el formato de archivo (YAML o Markdown con cabecera) y si las fichas reales se versionan en Git o quedan fuera del repositorio.

---

## 4. Interfaz

La parte gráfica es lo primero que se desarrolla. Se construye con **datos simulados** y después se conecta al generador real.

### Modos

- **Construcción:** se escribe la petición, la app genera la entrada y la muestra en la previsualización. Se puede editar y enviar a WordPress.
- **Chat:** conversación libre con la IA para preguntar, comentar el borrador, pedir ideas o ajustes. Usa las fichas activas como contexto.

### Pantallas y componentes

1. **Chat / generador:** historial de mensajes, caja de texto y botón **Enviar**.
2. **Selector de modo:** Construcción / Chat.
3. **Previsualización:** título, meta descripción, cuerpo e imagen, con edición básica.
4. **Botón "Enviar a WordPress (borrador)"**, conectado a la API de WordPress.
5. **Gestor de fichas:** crear, editar, administrar y activar fichas.
6. **Historial de generaciones:** consultar, reabrir y reenviar generaciones anteriores.

### Diseño visual

- **Solo modo oscuro** por ahora.
- **Color de acento:** naranja de la empresa.
- Estilo limpio, con mucho espacio y una sola columna principal más un panel de previsualización.
- Los bocetos de pantalla estarán en `docs/bocetos/`.

> **TODO:** fijar el código hexadecimal exacto del naranja corporativo.

---

## 5. Tecnologías

| Pieza | Tecnología | Notas |
|---|---|---|
| Lenguaje | Python 3.14.7 | Si alguna librería no es compatible, usar 3.13 en un entorno virtual |
| Interfaz | Streamlit (previsto) | Tema oscuro con acento naranja; la lógica va separada de la interfaz para poder cambiarla más adelante |
| Modelo de IA | Ollama (local) | Modelo temporal pequeño; modelo definitivo **por definir** tras comparar |
| Persistencia | Archivos para fichas y SQLite para el historial (previsto) | |
| CMS | WordPress + Elementor (versión base) + Rank Math SEO | API REST con contraseña de aplicación |
| Imágenes | Banco gratuito (Pexels, previsto) | Siempre con crédito del autor |
| Control de versiones | Git + GitHub (repositorio privado) | |
| Sistema | Windows | |

> **TODO:** confirmar que Streamlit y el resto de dependencias instalan correctamente con Python 3.14.7.

---

## 6. Estructura del repositorio

Estructura prevista (se irá creando por fases):

```
quicksite/
├── README.md
├── .gitignore
├── .env.example              # plantilla de variables, sin valores reales
├── requirements.txt          # pendiente
├── .streamlit/
│   └── config.toml           # tema oscuro + naranja
├── fichas/                   # fichas de contexto
├── prompts/                  # plantillas de prompts versionadas
├── src/
│   └── quicksite/
│       ├── app.py            # punto de entrada de la interfaz
│       ├── ui/               # pantallas y componentes
│       ├── core/             # generación, fichas, historial
│       ├── wordpress/        # cliente de la API REST
│       ├── imagenes/         # bancos de fotos
│       └── validador/        # comprobaciones de calidad
├── data/                     # historial local (no se sube a Git)
├── tests/
│   └── peticiones_prueba/
└── docs/
    ├── bocetos/
    ├── decisiones.md         # qué se decidió y por qué
    └── formato-salida.md
```

**Principio de diseño:** la interfaz (`ui/`) no contiene lógica de negocio. Todo lo que genera, valida o envía vive en `core/`, `wordpress/`, etc., para poder cambiar la interfaz sin reescribir nada.

---

## 7. Requisitos

- Windows
- [Git](https://git-scm.com)
- [Python 3.14.7](https://www.python.org/downloads/) (con "Add python.exe to PATH" marcado)
- [VS Code](https://code.visualstudio.com) con la extensión de Python de Microsoft
- [Ollama](https://ollama.com)
- Un WordPress con permisos de administrador y:
  - **Contraseña de aplicación** (Usuarios → Perfil)
  - **Rank Math SEO**
- Equipo del servidor de IA: RTX 5080 (16 GB de VRAM), Ryzen 7 9800X3D, 64 GB de RAM

---

## 8. Instalación y arranque

> **Provisional:** estos pasos se confirmarán cuando exista la primera versión de la app.

En PowerShell:

```powershell
git clone https://github.com/<ORGANIZACION_O_USUARIO>/quicksite.git
cd quicksite

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt      # pendiente de crear

copy .env.example .env               # y rellenar con tus datos
ollama pull <MODELO_TEMPORAL>        # por definir

streamlit run src/quicksite/app.py   # provisional
```

Si PowerShell bloquea la activación del entorno virtual, ejecuta una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## 9. Configuración

Las claves y datos privados van en un archivo `.env` local que **nunca se sube a Git**. El archivo `.env.example` indica qué variables existen.

| Variable | Descripción |
|---|---|
| `OLLAMA_URL` | Dirección de Ollama (por defecto, la local) |
| `OLLAMA_MODELO` | Modelo a usar |
| `WP_URL` | Dirección de la web, sin barra final |
| `WP_USUARIO` | Usuario de WordPress |
| `WP_APP_PASSWORD` | Contraseña de aplicación |
| `PEXELS_API_KEY` | Clave de la API de fotos |

> Estos nombres son provisionales y pueden cambiar al implementarlos.

---

## 10. Trabajo en equipo (Git)

### Flujo

1. `git switch main` y `git pull` para partir de lo último.
2. `git switch -c area/descripcion` (por ejemplo `ui/modo-chat`, `wp/borrador-api`).
3. Hacer commits pequeños, con mensaje claro en castellano que empiece por un verbo ("Añade…", "Corrige…").
4. `git push -u origin area/descripcion` y abrir un **Pull Request**.
5. El otro miembro revisa y aprueba. Se fusiona con **Squash and merge**.
6. Borrar la rama y volver a `main`.

### Normas

1. **Nadie trabaja directamente en `main`.**
2. **Nunca usar `git push --force`.**
3. **Los secretos solo en `.env`.** Si una clave se sube por error, se revoca, no basta con borrarla.
4. **No subir modelos de Ollama ni archivos pesados.**
5. **Commits pequeños y entendibles.**
6. **Toda decisión importante se anota** en `docs/decisiones.md`.

### Rutina

- Reunión de 10-15 minutos al empezar cada jornada de trabajo: qué hice, qué toca, qué me bloquea.
- Programación en pareja (conductor y navegador) para las tareas más nuevas.
- Tablero de tareas con GitHub Issues o Projects.

---

## 11. Hoja de ruta y tareas

**Responsables:** Ángel · Ismael · Ambos. *El reparto es provisional y se puede intercambiar.*

### Fase 0 — Preparación (Semana 1 · hasta el 30 de octubre)

- [X] Crear el repositorio privado en GitHub e invitar a Ismael — **Ángel**
- [X] Instalar Git, VS Code y Python 3.14.7 en ambos equipos — **Ambos**
- [X] Configurar la identidad de Git (`user.name`, `user.email`) — **Ambos**
- [ ] Primer ciclo completo de Git: rama → commit → PR → revisión → merge — **Ambos**
- [ ] Subir `.gitignore` (con `.env`, `.venv/`, `data/`), `.env.example` y este README — **Ángel**
- [ ] Comprobar que Streamlit y las librerías previstas instalan bien con Python 3.14.7 (si no, usar 3.13) — **Ismael**
- [ ] Instalar Ollama y descargar un modelo pequeño temporal — **Ismael**
- [ ] Script mínimo: enviar una pregunta a Ollama y mostrar la respuesta — **Ambos**
- [ ] Cerrar el formato de salida (JSON) de la entrada de blog — **Ambos**
- [ ] Decidir el formato de las fichas (YAML o Markdown) — **Ambos**
- [ ] Generar y validar los bocetos de pantalla — **Ángel**
- [ ] Corregir incoherencias de la web (horarios, teléfonos, post con URL `/__trashed/`) — **Ismael**
- [ ] Acordar con la dirección la propiedad del proyecto y dejarlo por escrito — **Ambos**

**Hecho cuando:** los dos tenéis el repo clonado, habéis hecho un PR, Ollama responde y los bocetos están aprobados.

### Fase 1 — Interfaz con datos simulados (Semana 2 · hasta el 6 de noviembre)

- [ ] Arrancar el proyecto Streamlit con tema oscuro y acento naranja (`.streamlit/config.toml`) — **Ángel**
- [ ] Layout base: barra lateral (navegación y fichas activas) y zona principal — **Ángel**
- [ ] Selector de modo Construcción / Chat — **Ángel**
- [ ] Interfaz de chat: historial de mensajes, caja de texto y botón Enviar — **Ángel**
- [ ] Respuesta simulada para probar el flujo sin modelo — **Ismael**
- [ ] Panel de previsualización (título, meta, cuerpo, imagen) — **Ángel**
- [ ] Edición básica del resultado antes de enviar — **Ismael**
- [ ] Botón "Enviar a WordPress (borrador)", todavía simulado — **Ismael**
- [ ] Gestor de fichas: listar, crear, editar, duplicar, activar y borrar — **Ismael**
- [ ] Revisión cruzada del código y demostración interna — **Ambos**

**Hecho cuando:** se puede recorrer todo el flujo en la app con datos simulados.

### Fase 2 — Generación con Ollama (Semana 3 · hasta el 13 de noviembre)

- [ ] Conectar la app con Ollama usando el modelo temporal — **Ismael**
- [ ] Ensamblar el prompt: fichas activas + petición del usuario — **Ángel**
- [ ] Pedir y validar la salida en JSON, con gestión de errores — **Ismael**
- [ ] Modo chat con contexto de las fichas y del borrador actual — **Ángel**
- [ ] Mostrar la respuesta de forma progresiva (*streaming*) — **Ismael**
- [ ] Historial de generaciones persistente — **Ángel**
- [ ] Primera ficha real de datos fijos y primera de estilo — **Ambos**

**Hecho cuando:** la app genera una entrada real con el modelo temporal y la guarda en el historial.

### Fase 3 — Conexión con WordPress (Semana 4 · hasta el 20 de noviembre)

- [ ] Preparar un entorno de pruebas de WordPress — **Ismael**
- [ ] Crear la contraseña de aplicación y probar un borrador de texto fijo — **Ismael**
- [ ] Exponer en la API los campos de Rank Math (título SEO, descripción, palabra clave) — **Ismael**
- [ ] Buscar foto de stock, subirla como imagen destacada y añadir el crédito — **Ángel**
- [ ] Conectar el botón "Enviar a WordPress" con la API real — **Ambos**
- [ ] Mostrar en la app confirmación y enlace al borrador, o el error — **Ángel**
- [ ] Probar y documentar el flujo con Elementor (abrir borrador → "Editar con Elementor") — **Ambos**

**Hecho cuando:** un clic en la app deja en WordPress un borrador completo con SEO e imagen.

### Fase 4 — Calidad y modelo definitivo (Semana 5 · hasta el 27 de noviembre)

- [ ] Definir 5 peticiones de prueba variadas — **Ambos**
- [ ] Comparar modelos candidatos a ciegas con una rúbrica (castellano, exactitud, SEO, tono, ausencia de relleno) — **Ambos**
- [ ] Elegir el modelo y registrar la decisión en `docs/decisiones.md` — **Ambos**
- [ ] Validador de datos fijos (importes, plazos y horarios del texto frente a las fichas) — **Ismael**
- [ ] Checklist de revisión humana antes de publicar — **Ángel**
- [ ] Generar 3 entradas reales de principio a fin y revisarlas como si fueran a publicarse — **Ambos**

**Hecho cuando:** hay un modelo elegido y tres entradas reales que pasarían la revisión.

### Margen y pulido (hasta el 4 de diciembre)

- [ ] Corregir fallos detectados y ajustar prompts y fichas — **Ambos**
- [ ] Pulir la interfaz y los mensajes de error — **Ángel**
- [ ] Completar la documentación y la instalación definitiva — **Ismael**
- [ ] Demostración a la dirección — **Ambos**

---

## 12. Más adelante

Ideas fuera de la versión 1:

- [ ] Páginas locales (landings) con plantilla de Elementor y contenido realmente distinto por zona
- [ ] Plantilla de Elementor con marcadores que la herramienta rellene directamente
- [ ] Acceso remoto seguro al servidor (VPN privada) y control de usuarios
- [ ] Integración con Google Search Console para proponer temas según búsquedas reales
- [ ] Integración con Google Ads
- [ ] Soporte para otros plugins SEO además de Rank Math
- [ ] Generación de imágenes con IA como alternativa a las de stock
- [ ] Comprobación de canibalización de palabras clave contra las entradas ya publicadas
- [ ] Migrar la interfaz a una web a medida (FastAPI + frontend) si Streamlit se queda corto
- [ ] Pruebas automáticas
- [ ] Preparar el proyecto para abrirlo o monetizarlo (licencia, limpieza de datos, documentación pública)

---

## 13. Decisiones pendientes

- [ ] Código hexadecimal exacto del naranja corporativo
- [ ] Formato de las fichas y si las reales se guardan en Git
- [ ] Modelo definitivo de Ollama
- [ ] Titular de los derechos del proyecto (ver licencia)
- [ ] Dónde y cómo se despliega para uso remoto
- [ ] Confirmar la compatibilidad de las dependencias con Python 3.14.7

---

## 14. Seguridad y revisión humana

- **QuickSite nunca publica.** Solo crea borradores; una persona revisa y publica.
- **Datos fijos protegidos.** El modelo recibe instrucciones de no inventar ni modificar precios, plazos o datos legales, y el validador comprueba el resultado.
- **Sin secretos en el repositorio.** Las claves van en `.env`.
- **Ollama no se expone a internet.** Si se necesita acceso remoto, se hace por VPN o detrás de un inicio de sesión.
- **Fotos con licencia clara.** Se guarda siempre la fuente y el crédito.
- **Revisar antes de publicar:** cifras, plazos, nombres, imagen y enlaces.

---

## 15. Licencia

Copyright © 2026 — **TODO: titular por confirmar**. Todos los derechos reservados.

Este software es de uso interno y no puede copiarse, distribuirse ni modificarse sin autorización expresa de sus titulares.
