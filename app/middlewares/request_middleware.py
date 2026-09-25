"""Middleware HTTP global: trazabilidad, tiempos de respuesta y cabeceras de seguridad."""

import logging
import re
import time
from uuid import uuid4

from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("device_systems.requests")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


async def request_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """Mide el tiempo, propaga el `X-Request-ID`, registra la petición y agrega cabeceras."""
    started_at = time.perf_counter()
    incoming_request_id = request.headers.get("X-Request-ID", "")
    request_id = incoming_request_id if REQUEST_ID_PATTERN.fullmatch(incoming_request_id) else str(uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    process_time = time.perf_counter() - started_at

    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-Request-ID"] = request_id
    # Cabeceras de endurecimiento básicas para clientes y proxies.
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    logger.info(
        "peticion metodo=%s ruta=%s estado=%s duracion=%.4fs id_peticion=%s cliente=%s",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
        request_id,
        request.client.host if request.client else "desconocido",
    )
    return response
