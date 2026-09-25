"""Utilidades de seguridad: hash de contraseñas (passlib) y tokens JWT (python-jose).

Ninguna contraseña se persiste ni se devuelve en texto plano: siempre se usa el
hash generado por passlib.

Nota de compatibilidad: se fija `bcrypt<4.1` en `requirements.txt` porque passlib
1.7.4 (última versión publicada) falla al inicializar su backend con bcrypt >= 4.1
al enviar internamente una contraseña de más de 72 bytes durante la detección del
"wrap bug". Con bcrypt 4.0.1 el esquema `bcrypt_sha256` funciona correctamente.
"""

import os
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-this-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
PASSWORD_SCHEME = "bcrypt_sha256"
password_context = CryptContext(schemes=[PASSWORD_SCHEME], deprecated="auto")


def validate_password(password: str) -> str:
    """Valida la política de contraseñas y devuelve el valor si es aceptable.

    Reglas: mínimo 8 caracteres, sin espacios, con mayúscula, minúscula y número.
    Se usa tanto en los schemas Pydantic v2 como en los servicios.
    """
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if any(character.isspace() for character in password):
        raise ValueError("La contraseña no puede contener espacios")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe incluir una mayúscula")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe incluir una minúscula")
    if not re.search(r"\d", password):
        raise ValueError("La contraseña debe incluir un número")
    return password


def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña lista para almacenarse."""
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano contra el hash almacenado."""
    try:
        return password_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Firma un JWT con los datos recibidos y la expiración configurada."""
    payload = data.copy()
    expire_at = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload["exp"] = expire_at
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decodifica y valida el JWT. Devuelve `None` si es inválido o expiró."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
