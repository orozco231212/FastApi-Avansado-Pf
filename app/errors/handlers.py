"""Manejadores de excepciones que devuelven todos los mensajes de error en español.

Se encargan de tres casos:

* Errores de validación de Pydantic v2 (requieren el atributo ``exc.errors()``).
* Errores HTTP generados por Starlette/FastAPI (``404``, ``405``, etc.).
* Límite de peticiones superado (slowapi) junto con sus cabeceras ``X-RateLimit-*``.
"""

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors.mensajes_es import FRASES_HTTP, mensaje_de_error, traducir_limite

# Partes de la ubicación del error que no aportan información al cliente.
PARTES_IGNORADAS = {"body", "query", "path", "header", "cookie", "form"}

# 422: se usa el número literal para evitar el aviso de obsolescencia de Starlette.
CODIGO_VALIDACION = 422


def detalle_de_validacion(exc: RequestValidationError) -> list[dict[str, str]]:
    """Convierte los errores de Pydantic en una lista legible en español."""
    errores: list[dict[str, str]] = []
    for error in exc.errors():
        ubicacion = [str(parte) for parte in error.get("loc", ()) if str(parte) not in PARTES_IGNORADAS]
        errores.append(
            {
                "campo": " -> ".join(ubicacion) if ubicacion else "cuerpo",
                "mensaje": mensaje_de_error(error),
            }
        )
    return errores


async def manejador_errores_de_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Responde 422 con los campos inválidos y su explicación en español."""
    return JSONResponse(
        status_code=CODIGO_VALIDACION,
        content={
            "detail": "Los datos enviados no son válidos",
            "errores": detalle_de_validacion(exc),
        },
    )


async def manejador_errores_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Traduce las frases por defecto de Starlette (por ejemplo ``Not Found``)."""
    detalle: Any = exc.detail
    try:
        frase_por_defecto: str = HTTPStatus(exc.status_code).phrase
    except ValueError:
        frase_por_defecto = ""

    if isinstance(detalle, str) and detalle.strip() in {frase_por_defecto, ""}:
        detalle = FRASES_HTTP.get(exc.status_code, detalle)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detalle},
        headers=getattr(exc, "headers", None),
    )


async def manejador_limite_excedido(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Responde 429 en español y conserva las cabeceras del rate limiting."""
    limite = traducir_limite(str(exc.detail))
    respuesta = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Demasiadas solicitudes",
            "mensaje": f"Superaste el límite de {limite}. Espera un momento antes de volver a intentarlo.",
            "limite": limite,
        },
    )
    # `_inject_headers` es el mismo mecanismo que usa slowapi en su manejador por defecto.
    return request.app.state.limiter._inject_headers(respuesta, request.state.view_rate_limit)


def registrar_manejadores_en_espanol(app: FastAPI) -> None:
    """Registra los tres manejadores de excepciones de la API."""
    app.add_exception_handler(RequestValidationError, manejador_errores_de_validacion)
    app.add_exception_handler(StarletteHTTPException, manejador_errores_http)
    app.add_exception_handler(RateLimitExceeded, manejador_limite_excedido)
