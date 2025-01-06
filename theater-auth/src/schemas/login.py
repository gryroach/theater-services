from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LoginHistoryCreate(BaseModel):
    id: UUID | None = None
    user_id: UUID
    ip_address: str | None
    user_agent: str | None


class LoginHistoryInDB(LoginHistoryCreate):
    login_time: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    login: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)
