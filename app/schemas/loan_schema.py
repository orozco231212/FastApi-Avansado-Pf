from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

LoanStatus = Literal["active", "returned", "overdue"]


class LoanCreate(BaseModel):
    user_id: int
    device_id: int


class LoanUpdate(BaseModel):
    status: LoanStatus | None = None


class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    device_id: int
    loan_date: datetime
    return_date: datetime | None
    status: LoanStatus


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class DeviceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    serial_number: str
    device_type: str


class LoanDetailResponse(LoanResponse):
    user: UserSummary
    device: DeviceSummary