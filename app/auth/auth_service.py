"""Servicios de autenticación: registro y validación de credenciales.

Las contraseñas nunca se manipulan en texto plano más allá de la petición:
siempre se transforman con `get_password_hash` antes de persistirse.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import get_password_hash, verify_password
from app.models.user_model import User
from app.schemas.auth_schema import UserRegister

DEFAULT_ROLE = "user"


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def register_user(db: Session, user_data: UserRegister) -> User:
    """Crea una cuenta activa con rol `user` y contraseña hasheada."""
    user = User(
        name=user_data.name,
        email=str(user_data.email),
        hashed_password=get_password_hash(user_data.password),
        role=DEFAULT_ROLE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Devuelve el usuario cuando el email y la contraseña son válidos."""
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def user_exists(db: Session, email: str) -> bool:
    """Indica si el email ya está registrado en la base de datos."""
    return db.scalar(select(User).where(User.email == email)) is not None
