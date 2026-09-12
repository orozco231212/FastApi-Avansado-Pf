from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.device_model import Device
from app.schemas.device_schema import DeviceCreate, DeviceUpdate


def get_device(db: Session, device_id: int) -> Device | None:
    return db.get(Device, device_id)


def get_device_by_serial(db: Session, serial_number: str) -> Device | None:
    return db.scalar(select(Device).where(Device.serial_number == serial_number))


def create_device(db: Session, data: DeviceCreate) -> Device:
    if get_device_by_serial(db, data.serial_number):
        raise ValueError("El número de serie ya está registrado")
    device = Device(**data.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def get_devices(db: Session, device_type: str | None = None, is_available: bool | None = None, brand: str | None = None, search: str | None = None) -> list[Device]:
    query: Select[tuple[Device]] = select(Device)
    if device_type:
        query = query.where(Device.device_type.ilike(device_type))
    if is_available is not None:
        query = query.where(Device.is_available == is_available)
    if brand:
        query = query.where(Device.brand.ilike(f"%{brand}%"))
    if search:
        query = query.where(Device.name.ilike(f"%{search}%"))
    return list(db.scalars(query.order_by(Device.name)).all())


def update_device(db: Session, device: Device, data: DeviceUpdate) -> Device:
    values = data.model_dump(exclude_unset=True)
    if "serial_number" in values and values["serial_number"] != device.serial_number and get_device_by_serial(db, values["serial_number"]):
        raise ValueError("El número de serie ya está registrado")
    for field, value in values.items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return device


def delete_device(db: Session, device: Device) -> None:
    if device.loans:
        raise ValueError("No se puede eliminar un dispositivo con historial de préstamos")
    db.delete(device)
    db.commit()