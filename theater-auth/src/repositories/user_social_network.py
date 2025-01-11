from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserSocialNetwork
from repositories.base import RepositoryDB
from schemas.user_social_network import (
    UserSocialNetworkCreate,
    UserSocialNetworkInDB,
)


class UserSocialNetworkRepository(
    RepositoryDB[UserSocialNetwork, UserSocialNetworkCreate, UserSocialNetworkInDB]
):
    def __init__(self):
        super().__init__(UserSocialNetwork)

    async def create_or_update_provider(
        self, db: AsyncSession, *, obj_in: UserSocialNetworkCreate, provider_field: str
    ) -> UserSocialNetwork:
        db_obj = await self.get_by_field(db, "user_id", obj_in.user_id)
        if db_obj:
            db_obj_data = jsonable_encoder(db_obj)
            new_obj_in = UserSocialNetworkCreate(**db_obj_data)
            setattr(new_obj_in, provider_field, getattr(obj_in, provider_field))
            return await self.update(db=db, db_obj=db_obj, obj_in=new_obj_in)
        else:
            return await self.create(db=db, obj_in=obj_in)
