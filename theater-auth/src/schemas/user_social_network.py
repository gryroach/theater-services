from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserSocialNetworkCreate(BaseModel):
    user_id: UUID
    google_id: str | None = None
    yandex_id: str | None = None


class UserSocialNetworkInDB(BaseModel):
    id: UUID
    user_id: UUID
    google_id: str | None = None
    yandex_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
