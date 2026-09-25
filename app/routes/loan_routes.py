from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import get_current_active_user, require_staff
from app.dependencies.database_dependency import get_db
from app.middlewares.rate_limiter import LOANS_CREATE_LIMIT, limiter
from app.models.user_model import User
from app.schemas.loan_schema import LoanCreate, LoanDetailResponse, LoanStatus
from app.services import loan_service

router = APIRouter(prefix="/loans", tags=["Loans"])
DbSession = Annotated[Session, Depends(get_db)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
StaffUser = Annotated[User, Depends(require_staff)]


@router.post(
    "",
    response_model=LoanDetailResponse,
    status_code=201,
    summary="Crear préstamo",
    description=(
        "Valida usuario y dispositivo, verifica disponibilidad, registra el préstamo y marca "
        f"el dispositivo como no disponible. Límite de peticiones: {LOANS_CREATE_LIMIT}. "
        "Un usuario con rol `user` solo puede prestar para sí mismo."
    ),
    response_description="Préstamo creado con datos relacionados del usuario y del dispositivo.",
    responses={
        201: {"description": "Préstamo registrado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Intento de crear un préstamo para otro usuario"},
        404: {"description": "Usuario o dispositivo no encontrado"},
        409: {"description": "El dispositivo no está disponible"},
        429: {"description": "Demasiadas solicitudes (rate limiting)"},
    },
)
@limiter.limit(LOANS_CREATE_LIMIT)
def create_loan(
    request: Request,
    response: Response,
    data: LoanCreate,
    db: DbSession,
    current_user: ActiveUser,
) -> LoanDetailResponse:
    if current_user.role == "user" and current_user.id != data.user_id:
        raise HTTPException(status_code=403, detail="No puedes crear préstamos para otro usuario")
    try:
        return loan_service.create_loan(db, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get(
    "",
    response_model=list[LoanDetailResponse],
    summary="Listar préstamos",
    description="Requiere rol `admin` o `support`. Filtros opcionales por estado, correo y tipo de dispositivo.",
    response_description="Préstamos con información relacionada (joins).",
    responses={
        200: {"description": "Listado obtenido"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol no autorizado"},
        422: {"description": "Filtro de estado inválido"},
    },
)
def list_loans(
    db: DbSession,
    _current_user: StaffUser,
    status: LoanStatus | None = Query(default=None, description="Estado del préstamo"),
    user_email: str | None = Query(default=None, description="Filtro parcial por correo del usuario"),
    device_type: str | None = Query(default=None, description="Tipo de dispositivo"),
) -> list[LoanDetailResponse]:
    return loan_service.get_loans(db, status, user_email, device_type)



@router.get(
    "/details",
    response_model=list[LoanDetailResponse],
    summary="Listar préstamos con detalles (join)",
    description=(
        "Consulta con `join` y `joinedload` que devuelve el préstamo junto con los datos del usuario "
        "y del dispositivo. Requiere rol `admin` o `support`."
    ),
    response_description="Detalle de préstamos con objetos `user` y `device` anidados.",
    responses={
        200: {"description": "Detalle obtenido"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol no autorizado"},
    },
)
def list_loan_details(
    db: DbSession,
    _current_user: StaffUser,
    status: LoanStatus | None = Query(default=None, description="Estado del préstamo"),
    user_email: str | None = Query(default=None, description="Filtro parcial por correo del usuario"),
    device_type: str | None = Query(default=None, description="Tipo de dispositivo"),
) -> list[LoanDetailResponse]:
    return loan_service.get_loans(db, status, user_email, device_type)


@router.get(
    "/{loan_id}",
    response_model=LoanDetailResponse,
    summary="Buscar préstamo por ID",
    description="Un usuario con rol `user` solo puede consultar préstamos propios.",
    response_description="Préstamo con datos relacionados.",
    responses={
        200: {"description": "Préstamo encontrado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol user consultando un préstamo ajeno"},
        404: {"description": "Préstamo no encontrado"},
    },
)
def get_loan(loan_id: int, db: DbSession, current_user: ActiveUser) -> LoanDetailResponse:
    loan = loan_service.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    if current_user.role == "user" and current_user.id != loan.user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para consultar este préstamo")
    return loan


@router.patch(
    "/{loan_id}/return",
    response_model=LoanDetailResponse,
    summary="Registrar devolución",
    description=(
        "Marca el préstamo como `returned`, asigna la fecha de devolución y vuelve a marcar el "
        "dispositivo como disponible. Requiere rol `admin` o `support`."
    ),
    response_description="Préstamo devuelto.",
    responses={
        200: {"description": "Devolución registrada"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Rol no autorizado"},
        404: {"description": "Préstamo no encontrado"},
        409: {"description": "El préstamo ya fue devuelto"},
    },
)
def return_loan(loan_id: int, db: DbSession, _current_user: StaffUser) -> LoanDetailResponse:
    loan = loan_service.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    try:
        return loan_service.return_loan(db, loan)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
