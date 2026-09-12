from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.schemas.loan_schema import LoanCreate, LoanDetailResponse, LoanResponse
from app.services import loan_service

router = APIRouter(prefix="/loans", tags=["Loans"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=LoanDetailResponse, status_code=201)
def create_loan(data: LoanCreate, db: DbSession) -> LoanDetailResponse:
    try:
        return loan_service.create_loan(db, data)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("", response_model=list[LoanDetailResponse])
@router.get("/details", response_model=list[LoanDetailResponse], include_in_schema=False)
def list_loans(db: DbSession, status: str | None = None, user_email: str | None = None, device_type: str | None = None) -> list[LoanDetailResponse]:
    if status is not None and status not in {"active", "returned", "overdue"}:
        raise HTTPException(status_code=422, detail="Estado de préstamo inválido")
    return loan_service.get_loans(db, status, user_email, device_type)


@router.get("/{loan_id}", response_model=LoanDetailResponse)
def get_loan(loan_id: int, db: DbSession) -> LoanDetailResponse:
    loan = loan_service.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return loan


@router.patch("/{loan_id}/return", response_model=LoanDetailResponse)
def return_loan(loan_id: int, db: DbSession) -> LoanDetailResponse:
    loan = loan_service.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    try:
        return loan_service.return_loan(db, loan)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error