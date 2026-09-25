"""Endpoints del tag Security: salud y política de seguridad aplicada."""

import os

from fastapi import APIRouter

from app.auth.security import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, PASSWORD_SCHEME
from app.middlewares.rate_limiter import RATE_LIMITS
from app.schemas.security_schema import JwtPolicy, PasswordPolicy, SecurityPolicyResponse

router = APIRouter(prefix="/security", tags=["Security"])

MIDDLEWARE_HEADERS = [
    "X-App-Name: device_systems",
    "X-Process-Time: <segundos>",
    "X-Request-ID: <uuid o valor propagado>",
    "X-Content-Type-Options: nosniff",
    "X-Frame-Options: DENY",
    "Referrer-Policy: no-referrer",
]

PROTECTED_ROUTES = {
    "GET /users": "Usuario autenticado",
    "GET /users/{user_id}": "Usuario autenticado",
    "POST /devices": "admin o support",
    "PUT|PATCH /devices/{device_id}": "admin o support",
    "DELETE /devices/{device_id}": "admin",
    "POST /loans": "Usuario autenticado (solo para sí mismo si el rol es user)",
    "PATCH /loans/{loan_id}/return": "admin o support",
    "GET /loans/details": "admin o support",
}


@router.get(
    "/policy",
    response_model=SecurityPolicyResponse,
    summary="Consultar política de seguridad",
    description=(
        "Devuelve la configuración de seguridad vigente: orígenes CORS permitidos, "
        "límites de peticiones, cabeceras del middleware, matriz de rutas protegidas "
        "y política de contraseñas y tokens. No expone ningún secreto."
    ),
    response_description="Política de seguridad activa de device_systems.",
)
def read_security_policy() -> SecurityPolicyResponse:
    allowed_origins = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if origin.strip()
    ]
    return SecurityPolicyResponse(
        app_name="device_systems",
        version="3.0.0",
        cors_allowed_origins=allowed_origins,
        cors_allow_credentials=True,
        cors_note=(
            "Con allow_credentials=True no se debe usar '*' en allow_origins: el navegador "
            "rechaza el comodín cuando la petición envía cookies o cabecera Authorization."
        ),
        rate_limits=RATE_LIMITS,
        middleware_headers=MIDDLEWARE_HEADERS,
        protected_routes=PROTECTED_ROUTES,
        password_policy=PasswordPolicy(
            min_length=8,
            requires_uppercase=True,
            requires_lowercase=True,
            requires_digit=True,
            allows_whitespace=False,
            hash_algorithm=PASSWORD_SCHEME,
        ),
        jwt_policy=JwtPolicy(
            algorithm=ALGORITHM,
            access_token_expire_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
            token_type="bearer",
            header="Authorization: Bearer <token>",
        ),
    )

