from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import get_current_active_user, require_admin, require_staff
from app.dependencies.database_dependency import get_db
from app.models.user_model import User
from app.schemas.device_schema import DeviceCreate, DeviceResponse, DeviceUpdate
from app.schemas.loan_schema import LoanDetailResponse
from app.services import device_service, loan_service

router = APIRouter(prefix="/devices", tags=["Devices"])
DbSession = Annotated[Session, Depends(get_db)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
StaffUser = Annotated[User, Depends(require_staff)]
AdminUser = Annotated[User, Depends(require_admin)]


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear dispositivo",
    description="Registra un dispositivo tecnológico. Requiere rol `admin` o `support`.",
    response_description="Dispositivo creado.",
    responses={
        201: {"description": "Dispositivo creado"},
        400: {"description": "Número de serie duplicado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol no autorizado"},
        422: {"description": "Datos inválidos"},
    },
)
def create_device(data: DeviceCreate, db: DbSession, _current_user: StaffUser) -> DeviceResponse:
    try:
        return device_service.create_device(db, data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get(
    "",
    response_model=list[DeviceResponse],
    summary="Listar y filtrar dispositivos",
    description=(
        "Requiere usuario autenticado. Filtros opcionales por `device_type`, `is_available`, "
        "`brand` y búsqueda parcial por nombre con `search`."
    ),
    response_description="Colección de dispositivos.",
    responses={
        200: {"description": "Listado obtenido"},
        401: {"description": "Token ausente o inválido"},
    },
)
def list_devices(
    db: DbSession,
    _current_user: ActiveUser,
    device_type: str | None = None,
    is_available: bool | None = None,
    brand: str | None = None,
    search: str | None = None,
) -> list[DeviceResponse]:
    return device_service.get_devices(db, device_type, is_available, brand, search)


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Buscar dispositivo por ID",
    description="Consulta un dispositivo autenticado. Responde 404 si no existe.",
    response_description="Dispositivo encontrado.",
    responses={
        200: {"description": "Dispositivo encontrado"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Dispositivo no encontrado"},
    },
)
def get_device(device_id: int, db: DbSession, _current_user: ActiveUser) -> DeviceResponse:
    device = device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return device



@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Actualizar dispositivo completo",
    description="Actualiza los datos del dispositivo. Requiere rol `admin` o `support`.",
    response_description="Dispositivo actualizado.",
    responses={
        200: {"description": "Dispositivo actualizado"},
        400: {"description": "Número de serie duplicado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol no autorizado"},
        404: {"description": "Dispositivo no encontrado"},
        422: {"description": "Datos inválidos"},
    },
)
@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Actualizar dispositivo parcialmente",
    description="Actualiza solo los campos enviados. Requiere rol `admin` o `support`.",
    response_description="Dispositivo actualizado.",
    responses={
        200: {"description": "Dispositivo actualizado"},
        400: {"description": "Número de serie duplicado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol no autorizado"},
        404: {"description": "Dispositivo no encontrado"},
        422: {"description": "Datos inválidos"},
    },
)
def update_device(device_id: int, data: DeviceUpdate, db: DbSession, _current_user: StaffUser) -> DeviceResponse:
    device = device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    try:
        return device_service.update_device(db, device, data)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar dispositivo",
    description="Elimina un dispositivo sin historial de préstamos. Solo el rol `admin` puede hacerlo.",
    responses={
        204: {"description": "Dispositivo eliminado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol distinto de admin"},
        404: {"description": "Dispositivo no encontrado"},
        409: {"description": "El dispositivo tiene historial de préstamos"},
    },
)
def delete_device(device_id: int, db: DbSession, _current_user: AdminUser) -> Response:
    device = device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    try:
        device_service.delete_device(db, device)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{device_id}/loans",
    response_model=list[LoanDetailResponse],
    summary="Consultar historial de préstamos del dispositivo",
    description="Consulta con join del historial completo de préstamos asociados al dispositivo.",
    response_description="Préstamos del dispositivo con datos de usuario y dispositivo.",
    responses={
        200: {"description": "Historial obtenido"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Dispositivo no encontrado"},
    },
)
def device_loans(device_id: int, db: DbSession, _current_user: ActiveUser) -> list[LoanDetailResponse]:
    if not device_service.get_device(db, device_id):
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return loan_service.get_loans(db, device_id=device_id)
