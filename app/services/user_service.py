from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserPatch, UserUpdate


def create_user(db: Session, user_data: UserCreate) -> User:
    existing_user = get_user_by_email(db, str(user_data.email))
    if existing_user:
        raise ValueError("El email ya está registrado")

    user = User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_users(
    db: Session,
    role: str | None = None,
    is_active: bool | None = None,
    order_by: str = "name",
) -> list[User]:
    query: Select[tuple[User]] = select(User)
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    if order_by == "created_at":
        query = query.order_by(User.created_at.desc())
    else:
        query = query.order_by(User.name.asc())
    return list(db.scalars(query).all())


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    if user_data.email != user.email and get_user_by_email(db, str(user_data.email)):
        raise ValueError("El email ya está registrado")

    for field, value in user_data.model_dump().items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def patch_user(db: Session, user: User, user_data: UserPatch) -> User:
    values = user_data.model_dump(exclude_unset=True)
    if "email" in values and values["email"] != user.email:
        if get_user_by_email(db, str(values["email"])):
            raise ValueError("El email ya está registrado")

    for field, value in values.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()