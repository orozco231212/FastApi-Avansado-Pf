"""Configuración central de rate limiting con slowapi.

Se limita por dirección IP del cliente (`get_remote_address`) y cada endpoint
declara su propio cupo mediante las constantes de este módulo, de forma que los
límites queden documentados en un solo lugar.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Límites mínimos exigidos por la actividad.
LOGIN_LIMIT = "5/minute"
REGISTER_LIMIT = "3/minute"
USERS_LIST_LIMIT = "30/minute"
LOANS_CREATE_LIMIT = "10/minute"

limiter = Limiter(key_func=get_remote_address, headers_enabled=True)

RATE_LIMITS = {
    "POST /auth/login": LOGIN_LIMIT,
    "POST /auth/register": REGISTER_LIMIT,
    "GET /users": USERS_LIST_LIMIT,
    "POST /loans": LOANS_CREATE_LIMIT,
}
