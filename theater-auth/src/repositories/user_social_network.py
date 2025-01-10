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
