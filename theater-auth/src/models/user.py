from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import validates
from sqlalchemy.sql import func
from werkzeug.security import check_password_hash, generate_password_hash

from db.db import Base
from services.roles import Roles


class User(Base):
    login = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(String(50), default=Roles.regular_user.name, nullable=False)
    created_at = Column(DateTime, default=func.now())

    def __init__(
        self,
        login: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str | None = None,
    ) -> None:
        self.login = login
        self.password = generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        if role is not None:
            self.role = role

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    @validates("role")
    def validate_role(self, key: str, role: str) -> str:
        if role not in Roles.roles():
            raise ValueError(f"Invalid role: {role}")
        return role

    def __repr__(self) -> str:
        return f"<User {self.login}>"
