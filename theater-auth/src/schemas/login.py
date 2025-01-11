from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from core.enums import OauthRequestTypes


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


class LoginPasswordResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    login: str | None = None
    password: str | None = None


class OauthTokenResponse(BaseModel):
    oauth_tokens: dict | None = None


class SocialNetworkAttachedResponse(BaseModel):
    detail: str


class OauthState(BaseModel):
    request_type: OauthRequestTypes
    user_id: str | None = None
