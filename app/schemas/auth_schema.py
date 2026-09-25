from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.auth.security import validate_password


class UserRegister(BaseModel):
    """Datos de entrada para `POST /auth/register`.

    El rol no se acepta desde el cliente: toda cuenta nueva se crea con rol `user`
    para evitar escalamiento de privilegios.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"name": "Ana Torres", "email": "ana@sena.edu.co", "password": "ClaveSegura123"}
            ]
        },
    )

    name: str = Field(min_length=3, max_length=100, description="Nombre completo", examples=["Ana Torres"])
    email: EmailStr = Field(description="Correo único del usuario", examples=["ana@sena.edu.co"])
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Mínimo 8 caracteres con mayúscula, minúscula y número, sin espacios",
        examples=["ClaveSegura123"],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        cleaned_name = " ".join(name.split())
        if len(cleaned_name) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        return cleaned_name

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, password: str) -> str:
        return validate_password(password)

    @model_validator(mode="after")
    def validate_password_is_not_personal_data(self) -> "UserRegister":
        """Evita contraseñas construidas con el correo o el nombre del usuario."""
        local_part = str(self.email).split("@")[0].lower()
        password_lower = self.password.lower()
        if local_part and local_part in password_lower:
            raise ValueError("La contraseña no puede contener la parte local del correo")
        name_tokens = [token for token in self.name.lower().split() if len(token) > 3]
        if any(token in password_lower for token in name_tokens):
            raise ValueError("La contraseña no puede contener el nombre del usuario")
        return self


class UserLogin(BaseModel):
    """Credenciales enviadas por un cliente JSON (complementa el formulario OAuth2)."""

    email: EmailStr = Field(examples=["ana@sena.edu.co"])
    password: str = Field(examples=["ClaveSegura123"])


class Token(BaseModel):
    """Token de acceso emitido por `POST /auth/login`."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}]
        }
    )

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Contenido útil decodificado desde el JWT."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int | None = None
    role: str | None = None
