from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from werkzeug.security import generate_password_hash

from services.roles import Roles


class UserCredentials(BaseModel):
    login: str
    password: str


class UserRegister(UserCredentials):
    first_name: str
    last_name: str
    email: EmailStr | None = None


class UserCreate(UserRegister):
    role: str = Roles.regular_user.name


class UserInDB(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr | None = None

    model_config = ConfigDict(from_attributes=True)


class UserData(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCredentialsUpdate(BaseModel):
    login: str
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def replace_hyphen(cls, v: str) -> str:
        return generate_password_hash(v)


class UserEmailRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
