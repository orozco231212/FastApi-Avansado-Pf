from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.schemas.user_schema import Role, UserCreate, UserPatch, UserResponse, UserUpdate
from app.schemas.loan_schema import LoanDetailResponse
from app.services import loan_service, user_service

router = APIRouter(prefix="/users", tags=["Users"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Crear usuario")
def create_user(user_data: UserCreate, db: DbSession) -> UserResponse:
    try:
        return user_service.create_user(db, user_data)
    except (ValueError, IntegrityError) as error:
        db.rollback()
        if isinstance(error, ValueError):
            raise HTTPException(status_code=400, detail=str(error)) from error
        raise HTTPException(status_code=400, detail="El email ya está registrado") from error


@router.get("", response_model=list[UserResponse], summary="Listar y filtrar usuarios")
def list_users(
    db: DbSession,
    role: Role | None = Query(default=None, description="Filtra por rol"),
    is_active: bool | None = Query(default=None, description="Filtra por estado"),
    order_by: str = Query(default="name", pattern="^(name|created_at)$"),
) -> list[UserResponse]:
    return user_service.get_users(db, role=role, is_active=is_active, order_by=order_by)


@router.get("/{user_id}", response_model=UserResponse, summary="Buscar usuario por ID")
def get_user(user_id: int, db: DbSession) -> UserResponse:
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.get("/{user_id}/loans", response_model=list[LoanDetailResponse], summary="Consultar préstamos de un usuario")
def user_loans(user_id: int, db: DbSession) -> list[LoanDetailResponse]:
    if not user_service.get_user(db, user_id):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return loan_service.get_loans(db, user_id=user_id)


@router.put("/{user_id}", response_model=UserResponse, summary="Actualizar usuario completo")
def update_user(user_id: int, user_data: UserUpdate, db: DbSession) -> UserResponse:
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    try:
        return user_service.update_user(db, user, user_data)
    except (ValueError, IntegrityError) as error:
        db.rollback()
        raise HTTPException(status_code=400, detail="El email ya está registrado") from error


@router.patch("/{user_id}", response_model=UserResponse, summary="Actualizar usuario parcialmente")
def patch_user(user_id: int, user_data: UserPatch, db: DbSession) -> UserResponse:
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    try:
        return user_service.patch_user(db, user, user_data)
    except (ValueError, IntegrityError) as error:
        db.rollback()
        raise HTTPException(status_code=400, detail="El email ya está registrado") from error


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar usuario")
def delete_user(user_id: int, db: DbSession) -> Response:
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_service.delete_user(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)