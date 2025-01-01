from enum import Enum

from pydantic import BaseModel, Field


class Status(str, Enum):
    connected = "connected"
    error = "error"


class DatabaseStatus(BaseModel):
    status: Status = Field(Status.connected.value)
    info: str | None = Field(
        title="Info about database",
        description="Database name and version",
    )
    time: float = Field(description="ping time")


class RedisStatus(BaseModel):
    status: str
    info: str
    time: float


class Ping(BaseModel):
    database: DatabaseStatus
    redis: RedisStatus
