from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.auth.security import create_access_token
from app.dependencies.auth_dependency import get_current_active_user
from app.dependencies.database_dependency import get_db
from app.middlewares.rate_limiter import LOGIN_LIMIT, REGISTER_LIMIT, limiter
from app.models.user_model import User
from app.schemas.auth_schema import Token, UserRegister
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
DbSession = Annotated[Session, Depends(get_db)]
FORM_DESCRIPTION = "Formulario OAuth2 (`username` = email del usuario, `password` = contraseña)"


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description=(
        "Crea una cuenta activa con rol `user` y almacena la contraseña como hash "
        "`bcrypt_sha256`. El rol no se toma del cliente para evitar escalamiento de privilegios. "
        f"Límite de peticiones: {REGISTER_LIMIT}."
    ),
    response_description="Usuario creado sin exponer `hashed_password`.",
    responses={
        201: {"description": "Usuario registrado correctamente"},
        400: {"description": "El email ya está registrado"},
        422: {"description": "Datos inválidos o contraseña débil"},
        429: {"description": "Demasiadas solicitudes (rate limiting)"},
    },
)
@limiter.limit(REGISTER_LIMIT)
def register(
    request: Request,
    response: Response,
    data: UserRegister,
    db: DbSession,
) -> UserResponse:
    if auth_service.user_exists(db, str(data.email)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")
    try:
        return auth_service.register_user(db, data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado") from error


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
    description=(
        "Autentica con el formulario OAuth2 (email y contraseña), verifica el hash almacenado "
        f"y devuelve un token JWT firmado con HS256. Límite de peticiones: {LOGIN_LIMIT}. "
        f"{FORM_DESCRIPTION}."
    ),
    response_description="Token de acceso y tipo de token.",
    responses={
        200: {"description": "Credenciales válidas: token JWT generado"},
        401: {"description": "Email o contraseña incorrectos, o usuario inactivo"},
        429: {"description": "Demasiadas solicitudes (rate limiting)"},
    },
)
@limiter.limit(LOGIN_LIMIT)
def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token({"sub": str(user.id), "role": user.role}))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Consultar usuario autenticado",
    description="Devuelve los datos del usuario dueño del token enviado en `Authorization: Bearer <token>`.",
    response_description="Perfil del usuario autenticado, siempre sin `hashed_password`.",
    responses={
        200: {"description": "Datos del usuario autenticado"},
        401: {"description": "Token ausente, inválido o expirado"},
        403: {"description": "Usuario inactivo"},
    },
)
def read_current_user(current_user: Annotated[User, Depends(get_current_active_user)]) -> UserResponse:
    return current_user
