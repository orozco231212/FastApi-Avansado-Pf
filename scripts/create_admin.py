"""Crea un usuario administrador inicial para pruebas, capturas y demostración.

Uso (desde la raíz del proyecto, con el entorno virtual activado):

    python -m scripts.create_admin
    python -m scripts.create_admin admin@sena.edu.co MiClaveSegura123 "Admin SENA"

Es idempotente: si el correo ya existe, informa y no modifica la base de datos.
"""

import os
import sys

from sqlalchemy import select

from app.auth.security import get_password_hash
from app.database.connection import SessionLocal
from app.models.device_model import Device  # noqa: F401 - registra el modelo relacionado
from app.models.loan_model import Loan  # noqa: F401 - registra el modelo relacionado
from app.models.user_model import User

DEFAULT_NAME = "Admin SENA"
DEFAULT_EMAIL = "admin@sena.edu.co"
DEFAULT_PASSWORD = "AdminSeguro123"


def create_admin(
    email: str = DEFAULT_EMAIL,
    password: str = DEFAULT_PASSWORD,
    name: str = DEFAULT_NAME,
) -> str:
    """Registra el usuario admin si no existe y devuelve un mensaje descriptivo."""
    session = SessionLocal()
    try:
        existing_user = session.scalar(select(User).where(User.email == email))
        if existing_user is not None:
            return f"El usuario {email} ya existe con rol '{existing_user.role}'. No se creó nada."

        session.add(
            User(
                name=name,
                email=email,
                hashed_password=get_password_hash(password),
                role="admin",
                is_active=True,
            )
        )
        session.commit()
        return f"Usuario admin creado correctamente.\n  email: {email}\n  password: {password}\n  rol: admin"
    finally:
        session.close()


if __name__ == "__main__":
    arguments = sys.argv[1:]
    admin_email = arguments[0] if arguments else os.getenv("ADMIN_EMAIL", DEFAULT_EMAIL)
    admin_password = arguments[1] if len(arguments) > 1 else os.getenv("ADMIN_PASSWORD", DEFAULT_PASSWORD)
    admin_name = arguments[2] if len(arguments) > 2 else os.getenv("ADMIN_NAME", DEFAULT_NAME)
    print(create_admin(admin_email, admin_password, admin_name))
