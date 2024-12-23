from pydantic import BaseModel


class JwtTokenPayload(BaseModel):
    user: str
    session_version: int
    iat: int
    exp: int
    role: str
    type: str
