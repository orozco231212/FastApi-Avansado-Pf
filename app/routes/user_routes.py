from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import get_current_active_user, require_admin, require_staff
from app.dependencies.database_dependency import get_db
from app.middlewares.rate_limiter import USERS_LIST_LIMIT, limiter
from app.models.user_model import User
from app.schemas.loan_schema import LoanDetailResponse
from app.schemas.user_schema import Role, UserCreate, UserPatch, UserResponse, UserUpdate
from app.services import loan_service, user_service

router = APIRouter(prefix="/users", tags=["Users"])
DbSession = Annotated[Session, Depends(get_db)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
StaffUser = Annotated[User, Depends(require_staff)]
AdminUser = Annotated[User, Depends(require_admin)]


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description="Crea un usuario con rol explícito y contraseña hasheada. Requiere rol `admin` o `support`.",
    response_description="Usuario creado sin `hashed_password`.",
    responses={
        201: {"description": "Usuario creado"},
        400: {"description": "Email duplicado o contraseña débil"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "El usuario autenticado no tiene rol admin/support"},
        422: {"description": "Datos inválidos"},
    },
)
def create_user(user_data: UserCreate, db: DbSession, _current_user: StaffUser) -> UserResponse:
    try:
        return user_service.create_user(db, user_data)
    except (ValueError, IntegrityError) as error:
        db.rollback()
        if isinstance(error, ValueError):
            raise HTTPException(status_code=400, detail=str(error)) from error
        raise HTTPException(status_code=400, detail="El email ya está registrado") from error


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar y filtrar usuarios",
    description=f"Lista usuarios autenticados con filtros opcionales. Límite de peticiones: {USERS_LIST_LIMIT}.",
    response_description="Colección de usuarios sin datos sensibles.",
    responses={
        200: {"description": "Listado obtenido"},
        401: {"description": "Token ausente o inválido"},
        429: {"description": "Demasiadas solicitudes (rate limiting)"},
    },
)
@limiter.limit(USERS_LIST_LIMIT)
def list_users(
    request: Request,
    response: Response,
    db: DbSession,
    _current_user: ActiveUser,
    role: Role | None = Query(default=None, description="Filtra por rol"),
    is_active: bool | None = Query(default=None, description="Filtra por estado"),
    order_by: str = Query(default="name", pattern="^(name|created_at)$"),
) -> list[UserResponse]:
    return user_service.get_users(db, role=role, is_active=is_active, order_by=order_by)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Buscar usuario por ID",
    description="Devuelve un usuario autenticado. Cualquier usuario con token válido puede consultarlo.",
    response_description="Datos del usuario solicitado.",
    responses={
        200: {"description": "Usuario encontrado"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Usuario no encontrado"},
    },
)
def get_user(user_id: int, db: DbSession, _current_user: ActiveUser) -> UserResponse:
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.get(
    "/{user_id}/loans",
    response_model=list[LoanDetailResponse],
    summary="Consultar préstamos de un usuario",
    description=(
        "Consulta con join entre `loans`, `users` y `devices`. El rol `user` solo puede consultar su propio historial."
    ),
    response_description="Préstamos del usuario con datos relacionados.",
    responses={
        200: {"description": "Historial obtenido"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Un rol user intentó consultar otro historial"},
        404: {"description": "Usuario no encontrado"},
    },
)
def user_loans(user_id: int, db: DbSession, current_user: ActiveUser) -> list[LoanDetailResponse]:
    if current_user.role == "user" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para consultar este historial")
    if not user_service.get_user(db, user_id):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return loan_service.get_loans(db, user_id=user_id)



@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario completo",
    description="Reemplaza los campos editables del usuario. Requiere rol `admin` o `support`.",
    response_description="Usuario actualizado.",
    responses={
        200: {"description": "Usuario actualizado"},
        400: {"description": "Email duplicado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol no autorizado"},
        404: {"description": "Usuario no encontrado"},
        422: {"description": "Datos inválidos"},
    },
)
def update_user(user_id: int, user_data: UserUpdate, db: DbSession, _current_user: StaffUser) -> UserResponse:
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    try:
        return user_service.update_user(db, user, user_data)
    except (ValueError, IntegrityError) as error:
        db.rollback()
        raise HTTPException(status_code=400, detail="El email ya está registrado") from error


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario parcialmente",
    description="Actualiza solo los campos enviados. Requiere rol `admin` o `support`.",
    response_description="Usuario actualizado.",
    responses={
        200: {"description": "Usuario actualizado"},
        400: {"description": "Email duplicado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol no autorizado"},
        404: {"description": "Usuario no encontrado"},
        422: {"description": "Datos inválidos"},
    },
)
def patch_user(user_id: int, user_data: UserPatch, db: DbSession, _current_user: StaffUser) -> UserResponse:
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    try:
        return user_service.patch_user(db, user, user_data)
    except (ValueError, IntegrityError) as error:
        db.rollback()
        raise HTTPException(status_code=400, detail="El email ya está registrado") from error


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    description="Elimina un usuario existente. Solo el rol `admin` puede ejecutar esta operación.",
    responses={
        204: {"description": "Usuario eliminado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol distinto de admin"},
        404: {"description": "Usuario no encontrado"},
    },
)
def delete_user(user_id: int, db: DbSession, _current_user: AdminUser) -> Response:
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_service.delete_user(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
