from sqlalchemy import UUID, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship, validates
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

    social_network = relationship("UserSocialNetwork", uselist=False, back_populates="user")

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


class UserSocialNetwork(Base):
    user_id = Column(UUID, ForeignKey('user.id'), nullable=False, unique=True)
    google_id = Column(String(255), unique=True)
    yandex_id = Column(String(255), unique=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="social_network", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User social network {self.user_id}>"
