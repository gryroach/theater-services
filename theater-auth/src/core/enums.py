from enum import Enum


class PayloadKeys(str, Enum):
    USER = "user"
    SESSION_VERSION = "session_version"
    TYPE = "type"
    IAT = "iat"
    EXP = "exp"
    ROLE = "role"


class TokenTypes(str, Enum):
    REFRESH = "refresh"
    ACCESS = "access"
