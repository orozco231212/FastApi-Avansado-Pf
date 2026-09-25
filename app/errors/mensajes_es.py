"""Diccionarios de traducción al español de los mensajes generados por FastAPI, Pydantic y slowapi."""

from typing import Final

# Mensajes exactos que devuelve Pydantic v2 en inglés.
MENSAJES_PYDANTIC: Final[dict[str, str]] = {
    "Field required": "Este campo es obligatorio",
    "Input should be a valid string": "Debe ser un texto",
    "Input should be a valid integer": "Debe ser un número entero",
    "Input should be a valid integer, unable to parse string as an integer": "Debe ser un número entero",
    "Input should be a valid number": "Debe ser un número",
    "Input should be a valid boolean, unable to interpret input": "Debe ser verdadero o falso",
    "Input should be a valid list": "Debe ser una lista",
    "Input should be a valid dictionary or object to extract fields from": "Debe ser un objeto con campos",
    "Input should be a valid date": "Debe ser una fecha válida",
    "Invalid input": "Entrada inválida",
    "Extra inputs are not permitted": "Este campo no está permitido",
    "JSON decode error": "El cuerpo enviado no es un JSON válido",
}

# Reemplazos parciales para mensajes con valores dinámicos.
REEMPLAZOS_PARCIALES: Final[dict[str, str]] = {
    "Value error, ": "",
    "Assertion failed, ": "",
    "value is not a valid email address": "No es un correo electrónico válido",
    "An email address must have an @-sign.": "falta el signo @",
    "The part after the @-sign is not valid.": "la parte después de la @ no es válida",
    "It should have a period.": "debe incluir un punto",
    "The email address is not valid.": "el correo electrónico no es válido",
    "String should have at least ": "Debe tener al menos ",
    "String should have at most ": "Debe tener como máximo ",
    " characters": " caracteres",
    "Input should be a valid email address": "Debe ser un correo electrónico válido",
    "Input should be a valid integer": "Debe ser un número entero",
    "Input should be 'admin', 'support' or 'user'": "Debe ser uno de estos roles: admin, support, user",
    "Input should be 'active', 'returned' or 'overdue'": "Debe ser uno de estos estados: active, returned, overdue",
    "Input should be greater than or equal to ": "Debe ser mayor o igual a ",
    "Input should be less than or equal to ": "Debe ser menor o igual a ",
    "Input should be greater than ": "Debe ser mayor que ",
    "Input should be less than ": "Debe ser menor que ",
    "unable to parse input as a date": "",
}

# Plantillas por tipo de error de Pydantic (permiten mensajes claros y en español).
PLANTILLAS_ERROR: Final[dict[str, str]] = {
    "missing": "El campo es obligatorio",
    "extra_forbidden": "El campo no está permitido",
    "string_type": "Debe ser un texto",
    "string_too_short": "Debe tener al menos {min_length} caracteres",
    "string_too_long": "Debe tener como máximo {max_length} caracteres",
    "string_pattern_mismatch": "El formato no es válido",
    "int_type": "Debe ser un número entero",
    "int_parsing": "Debe ser un número entero",
    "float_parsing": "Debe ser un número decimal",
    "bool_type": "Debe ser verdadero o falso",
    "bool_parsing": "Debe ser verdadero o falso",
    "json_invalid": "El cuerpo enviado no es un JSON válido",
    "list_type": "Debe ser una lista",
    "literal_error": "El valor no está permitido",
    "value_error": "{mensaje}",
}

# Frases por defecto de Starlette que se muestran al cliente.
FRASES_HTTP: Final[dict[int, str]] = {
    400: "Solicitud incorrecta",
    401: "No autenticado",
    403: "Acceso denegado",
    404: "Recurso no encontrado",
    405: "Método no permitido",
    409: "Conflicto con el estado del recurso",
    413: "El contenido enviado es demasiado grande",
    415: "Tipo de contenido no soportado",
    422: "Error de validación",
    429: "Demasiadas solicitudes",
    500: "Error interno del servidor",
}

# Traducción de las unidades de tiempo que usa slowapi en los límites.
UNIDADES_TIEMPO: Final[dict[str, str]] = {
    " per ": " por ",
    "second": "segundo",
    "minute": "minuto",
    "hour": "hora",
    "day": "día",
}


def traducir_mensaje(mensaje: str) -> str:
    """Traduce un mensaje de Pydantic aplicando coincidencias exactas y parciales."""
    if mensaje in MENSAJES_PYDANTIC:
        return MENSAJES_PYDANTIC[mensaje]

    traducido = mensaje
    for original, reemplazo in REEMPLAZOS_PARCIALES.items():
        traducido = traducido.replace(original, reemplazo)
    return traducido.strip()


def traducir_limite(detalle: str) -> str:
    """Convierte, por ejemplo, '3 per 1 minute' en '3 por 1 minuto'."""
    traducido = detalle
    for original, reemplazo in UNIDADES_TIEMPO.items():
        traducido = traducido.replace(original, reemplazo)
    return traducido


def mensaje_de_error(error: dict[str, object]) -> str:
    """Construye el mensaje en español de un error de validación de Pydantic."""
    tipo = str(error.get("type", ""))
    mensaje = str(error.get("msg", "Entrada inválida"))
    plantilla = PLANTILLAS_ERROR.get(tipo)

    if plantilla is None:
        return traducir_mensaje(mensaje)

    valores: dict[str, object] = {
        "mensaje": traducir_mensaje(mensaje),
        "min_length": "",
        "max_length": "",
    }
    contexto = error.get("ctx")
    if isinstance(contexto, dict):
        valores.update({clave: valor for clave, valor in contexto.items() if isinstance(valor, (str, int, float))})
    return plantilla.format(**valores).strip()
