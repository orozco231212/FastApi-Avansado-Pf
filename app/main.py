"""Aplicación FastAPI de device_systems (versión 3.0.0 con capa de seguridad)."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.auth.auth_routes import router as auth_router
from app.middlewares.rate_limiter import limiter
from app.middlewares.request_middleware import request_middleware
from app.routes.device_routes import router as device_router
from app.routes.loan_routes import router as loan_router
from app.routes.security_routes import router as security_router
from app.routes.user_routes import router as user_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

TAGS_METADATA = [
    {"name": "Auth", "description": "Registro, login OAuth2 y consulta del usuario autenticado."},
    {"name": "Users", "description": "Gestión de usuarios. Requiere token JWT; el rol se valida por endpoint."},
    {"name": "Devices", "description": "Gestión de dispositivos. Escritura solo para `admin` y `support`."},
    {"name": "Loans", "description": "Préstamos y devoluciones con información relacionada (joins)."},
    {"name": "Security", "description": "Estado de salud y política de seguridad aplicada a la API."},
]

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST segura para gestión de usuarios, dispositivos y préstamos. "
        "Incluye autenticación OAuth2 con JWT, hash de contraseñas con passlib, "
        "autorización por roles, middleware de trazabilidad, CORS y rate limiting."
    ),
    version="3.0.0",
    openapi_tags=TAGS_METADATA,
    contact={"name": "device_systems - SENA", "url": "https://github.com/orozco231212/FastApi-Avansado-Pf"},
    license_info={"name": "MIT"},
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.middleware("http")(request_middleware)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(device_router)
app.include_router(loan_router)
app.include_router(security_router)


@app.get(
    "/",
    tags=["Security"],
    summary="Estado de la API",
    description="Endpoint público de verificación de disponibilidad del servicio.",
    response_description="Mensaje de confirmación.",
)
def read_root() -> dict[str, str]:
    return {"message": "device_systems API activa"}
