from sqlalchemy import UUID, Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func

from db.db import Base


class LoginHistory(Base):
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    login_time = Column(DateTime, default=func.now())
