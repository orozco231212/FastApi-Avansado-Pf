from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.dependencies.database_dependency import get_db
from app.models.user_model import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]
SIN_TOKEN = "No autenticado: envía el token en la cabecera 'Authorization: Bearer <token>'"


def get_current_user(token: Annotated[str | None, Depends(oauth2_scheme)], db: DbSession) -> User:
    """Obtiene el usuario dueño del token JWT o responde 401 en español."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=SIN_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    subject = payload.get("sub") if payload else None
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: no contiene un usuario válido",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario del token ya no existe",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user



def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    return current_user


def require_roles(*roles: str):
    """Fábrica de dependencias que exige que el usuario tenga uno de los roles."""

    def role_dependency(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes: se requiere uno de los roles {', '.join(roles)}",
            )
        return current_user

    return role_dependency


def require_admin(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """Permite el acceso solo al rol `admin`."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes: se requiere rol admin")
    return current_user


def require_staff(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """Permite el acceso a los roles `admin` y `support`."""
    if current_user.role not in {"admin", "support"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes: se requiere rol admin o support",
        )
    return current_user