"""Traducción al español de la interfaz de Swagger UI que sirve `/docs`.

Swagger UI (la librería de terceros que renderiza `/docs`) no incluye traducciones
oficiales: sus etiquetas —incluido el diálogo *Authorize*— se publican en inglés.
Para que la documentación de la API quede en español, este módulo sirve la página
de `/docs` con un pequeño script que traduce los textos de la interfaz después de
renderizarse. Si Swagger UI cambia alguna etiqueta, simplemente se muestra tal cual.

Nunca se traducen bloques de código ni ejemplos (`<pre>`/`<code>`), para no alterar
los nombres reales de los campos del contrato de la API.
"""

import json
from typing import Any, Final

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

# Etiquetas que se traducen solo cuando el texto completo coincide (evita tocar datos).
TRADUCCIONES_EXACTAS: Final[dict[str, str]] = {
    "Available authorizations": "Autorizaciones disponibles",
    "Authorize": "Autorizar",
    "Authorized": "Autorizado",
    "Close": "Cerrar",
    "Logout": "Cerrar sesión",
    "Try it out": "Probar",
    "Cancel": "Cancelar",
    "Execute": "Ejecutar",
    "Clear": "Limpiar",
    "Parameters": "Parámetros",
    "No parameters": "Sin parámetros",
    "Responses": "Respuestas",
    "Response": "Respuesta",
    "Request body": "Cuerpo de la petición",
    "required": "obligatorio",
    "Items": "Elementos",
    "Parameter content type": "Tipo de contenido del parámetro",
    "Response content type": "Tipo de contenido de la respuesta",
    "Response body": "Cuerpo de la respuesta",
    "Request URL": "URL de la petición",
    "Server response": "Respuesta del servidor",
    "Request headers": "Cabeceras de la petición",
    "Response headers": "Cabeceras de la respuesta",
    "Schemas": "Esquemas",
    "Schema": "Esquema",
    "Example Value": "Valor de ejemplo",
    "Examples": "Ejemplos",
    "Media type": "Tipo de medio",
    "Details": "Detalles",
    "Code": "Código",
    "Links": "Enlaces",
    "No links": "Sin enlaces",
    "Download": "Descargar",
    "Servers": "Servidores",
    "Models": "Modelos",
    "Loading...": "Cargando...",
    "Successful Response": "Respuesta exitosa",
    "Validation Error": "Error de validación",
    "Token URL:": "URL del token:",
    "Flow:": "Flujo:",
    "username:": "usuario (email):",
    "password:": "contraseña:",
    "Client credentials location:": "Ubicación de las credenciales:",
    "Authorization header": "cabecera Authorization",
    "Scopes": "Alcances",
    "Expand operation": "Expandir operación",
    "Collapse operation": "Contraer operación",
    "Deprecated": "Obsoleto",
    "Description": "Descripción",
    "Name": "Nombre",
    "Type": "Tipo",
    "Default": "Por defecto",
    "Enum": "Valores permitidos",
    "Search": "Buscar",
    "Filter by tag": "Filtrar por etiqueta",
    "Select a definition": "Selecciona una definición",
    "No operations defined in spec!": "¡La especificación no define operaciones!",
}

# Frases largas que se traducen por coincidencia parcial.
TRADUCCIONES_PARCIALES: Final[dict[str, str]] = {
    (
        "Scopes are used to grant an application different levels of access to data "
        "on behalf of the end user. Each API may declare one or more scopes."
    ): (
        "Los alcances (scopes) permiten otorgar a una aplicación distintos niveles de acceso "
        "a los datos en nombre del usuario final. Cada API puede declarar uno o más alcances."
    ),
    "API requires the following scopes. Select which ones you want to grant to Swagger UI.": (
        "La API requiere los siguientes alcances. Selecciona cuáles deseas otorgar a Swagger UI."
    ),
    "Controls Accept header.": "Controla la cabecera Accept.",
}

# Parámetros de la interfaz: botones "Probar" activos, duración y token persistente.
PARAMETROS_SWAGGER: Final[dict[str, Any]] = {
    "docExpansion": "list",
    "defaultModelsExpandDepth": 1,
    "displayRequestDuration": True,
    "filter": True,
    "persistAuthorization": True,
    "tryItOutEnabled": True,
}


def _script_de_traduccion() -> str:
    """Devuelve el script que traduce la interfaz en el navegador."""
    exactas = json.dumps(TRADUCCIONES_EXACTAS, ensure_ascii=False)
    parciales = json.dumps(TRADUCCIONES_PARCIALES, ensure_ascii=False)
    return SCRIPT_TRADUCCION.replace("__EXACTAS__", exactas).replace("__PARCIALES__", parciales)


def registrar_docs_en_espanol(app: FastAPI) -> None:
    """Registra la ruta `/docs` con la interfaz de Swagger UI traducida al español."""

    @app.get("/docs", include_in_schema=False)
    async def documentacion_en_espanol() -> HTMLResponse:
        html = get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} - Documentación",
            swagger_ui_parameters=PARAMETROS_SWAGGER,
        ).body.decode("utf-8")
        return HTMLResponse(html.replace("</body>", f"{_script_de_traduccion()}</body>"))


SCRIPT_TRADUCCION = """
<script>
(function () {
  const exactas = __EXACTAS__;
  const parciales = __PARCIALES__;
  const atributos = ["placeholder", "title", "aria-label"];
  let traduciendo = false;

  function traducir(texto) {
    const limpio = texto.trim();
    if (Object.prototype.hasOwnProperty.call(exactas, limpio)) {
      return texto.replace(limpio, exactas[limpio]);
    }
    let resultado = texto;
    for (const original of Object.keys(parciales)) {
      if (resultado.includes(original)) {
        resultado = resultado.split(original).join(parciales[original]);
      }
    }
    return resultado;
  }

  function dentroDeCodigo(nodo) {
    let padre = nodo.parentElement;
    while (padre) {
      if (["PRE", "CODE", "SCRIPT", "STYLE"].indexOf(padre.tagName) !== -1) {
        return true;
      }
      padre = padre.parentElement;
    }
    return false;
  }

  function traducirArbol(raiz) {
    if (!raiz) { return; }
    const recorrido = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT, null);
    const cambios = [];
    let nodo = recorrido.nextNode();
    while (nodo) {
      if (!dentroDeCodigo(nodo)) {
        const nuevo = traducir(nodo.nodeValue);
        if (nuevo !== nodo.nodeValue) { cambios.push([nodo, nuevo]); }
      }
      nodo = recorrido.nextNode();
    }
    cambios.forEach(function (cambio) { cambio[0].nodeValue = cambio[1]; });

    if (raiz.querySelectorAll) {
      raiz.querySelectorAll("[placeholder], [title], [aria-label]").forEach(function (elemento) {
        atributos.forEach(function (atributo) {
          const valor = elemento.getAttribute(atributo);
          if (!valor) { return; }
          const nuevo = traducir(valor);
          if (nuevo !== valor) { elemento.setAttribute(atributo, nuevo); }
        });
      });
    }
  }

  function traducirTodo() {
    if (traduciendo) { return; }
    traduciendo = true;
    try {
      traducirArbol(document.body);
    } finally {
      traduciendo = false;
    }
  }

  function iniciar() {
    traducirTodo();
    let programado = false;
    const observador = new MutationObserver(function () {
      if (programado) { return; }
      programado = true;
      window.setTimeout(function () {
        programado = false;
        traducirTodo();
      }, 40);
    });
    observador.observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
</script>
"""

