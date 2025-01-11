from pydantic import BaseModel


class OAuthCodeRequest(BaseModel):
    code: str


class YandexRevokeTokenRequest(BaseModel):
    access_token: str
