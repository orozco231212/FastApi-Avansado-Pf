from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    serial_number: str = Field(..., min_length=2, max_length=100)
    device_type: str = Field(..., min_length=2, max_length=50)
    brand: str | None = Field(default=None, max_length=100)


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    serial_number: str | None = Field(default=None, min_length=2, max_length=100)
    device_type: str | None = Field(default=None, min_length=2, max_length=50)
    brand: str | None = Field(default=None, max_length=100)
    is_available: bool | None = None


class DeviceResponse(DeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_available: bool
    created_at: datetime