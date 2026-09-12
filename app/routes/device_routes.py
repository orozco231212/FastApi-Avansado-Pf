from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.schemas.device_schema import DeviceCreate, DeviceResponse, DeviceUpdate
from app.services import device_service, loan_service
from app.schemas.loan_schema import LoanDetailResponse

router = APIRouter(prefix="/devices", tags=["Devices"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(data: DeviceCreate, db: DbSession) -> DeviceResponse:
    try:
        return device_service.create_device(db, data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=list[DeviceResponse])
def list_devices(db: DbSession, device_type: str | None = None, is_available: bool | None = None, brand: str | None = None, search: str | None = None) -> list[DeviceResponse]:
    return device_service.get_devices(db, device_type, is_available, brand, search)


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: DbSession) -> DeviceResponse:
    device = device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
@router.patch("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: int, data: DeviceUpdate, db: DbSession) -> DeviceResponse:
    device = device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    try:
        return device_service.update_device(db, device, data)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, db: DbSession) -> Response:
    device = device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    try:
        device_service.delete_device(db, device)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{device_id}/loans", response_model=list[LoanDetailResponse])
def device_loans(device_id: int, db: DbSession) -> list[LoanDetailResponse]:
    if not device_service.get_device(db, device_id):
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return loan_service.get_loans(db, device_id=device_id)