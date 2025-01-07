from pydantic import BaseModel


class YandexAuthRequest(BaseModel):
    code: str


class YandexRevokeTokenRequest(BaseModel):
    access_token: str
