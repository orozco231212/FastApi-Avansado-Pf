"""Schemas de la política de seguridad expuesta por `GET /security/policy`."""

from pydantic import BaseModel, ConfigDict, Field


class PasswordPolicy(BaseModel):
    """Reglas aplicadas a las contraseñas aceptadas por la API."""

    min_length: int = Field(description="Longitud mínima exigida")
    requires_uppercase: bool
    requires_lowercase: bool
    requires_digit: bool
    allows_whitespace: bool
    hash_algorithm: str = Field(description="Esquema de hash usado por passlib")


class JwtPolicy(BaseModel):
    """Configuración del token JWT emitido por el login."""

    algorithm: str
    access_token_expire_minutes: int
    token_type: str
    header: str = Field(description="Encabezado HTTP esperado en rutas protegidas")


class SecurityPolicyResponse(BaseModel):
    """Resumen de la configuración de seguridad activa (sin exponer secretos)."""

    model_config = ConfigDict(from_attributes=True)

    app_name: str
    version: str
    cors_allowed_origins: list[str]
    cors_allow_credentials: bool
    cors_note: str
    rate_limits: dict[str, str]
    middleware_headers: list[str]
    protected_routes: dict[str, str]
    password_policy: PasswordPolicy
    jwt_policy: JwtPolicy
