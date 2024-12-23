from models.login_history import LoginHistory
from repositories.base import RepositoryDB
from schemas.login import LoginHistoryCreate, LoginHistoryInDB


class LoginHistoryRepository(
    RepositoryDB[LoginHistory, LoginHistoryCreate, LoginHistoryInDB]
):
    def __init__(self):
        super().__init__(model=LoginHistory)
