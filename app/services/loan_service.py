from datetime import UTC, datetime

from sqlalchemy import Select, and_, select
from sqlalchemy.orm import Session, joinedload

from app.models.device_model import Device
from app.models.loan_model import Loan
from app.models.user_model import User
from app.schemas.loan_schema import LoanCreate


def get_loan(db: Session, loan_id: int) -> Loan | None:
    return db.scalar(select(Loan).options(joinedload(Loan.user), joinedload(Loan.device)).where(Loan.id == loan_id))


def create_loan(db: Session, data: LoanCreate) -> Loan:
    user = db.get(User, data.user_id)
    if not user:
        raise LookupError("Usuario no encontrado")
    device = db.get(Device, data.device_id)
    if not device:
        raise LookupError("Dispositivo no encontrado")
    if not device.is_available:
        raise RuntimeError("El dispositivo no está disponible")
    loan = Loan(user=user, device=device, status="active")
    device.is_available = False
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return get_loan(db, loan.id)


def return_loan(db: Session, loan: Loan) -> Loan:
    if loan.status == "returned":
        raise RuntimeError("El préstamo ya fue devuelto")
    loan.status = "returned"
    loan.return_date = datetime.now(UTC)
    loan.device.is_available = True
    db.commit()
    db.refresh(loan)
    return get_loan(db, loan.id)


def get_loans(db: Session, status: str | None = None, user_email: str | None = None, device_type: str | None = None, user_id: int | None = None, device_id: int | None = None) -> list[Loan]:
    query: Select[tuple[Loan]] = select(Loan).join(User).join(Device).options(joinedload(Loan.user), joinedload(Loan.device))
    filters = []
    if status:
        filters.append(Loan.status == status)
    if user_email:
        filters.append(User.email.ilike(f"%{user_email}%"))
    if device_type:
        filters.append(Device.device_type.ilike(device_type))
    if user_id is not None:
        filters.append(Loan.user_id == user_id)
    if device_id is not None:
        filters.append(Loan.device_id == device_id)
    if filters:
        query = query.where(and_(*filters))
    return list(db.scalars(query.order_by(Loan.loan_date.desc())).unique().all())