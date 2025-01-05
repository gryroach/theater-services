import uuid

from db.db import Base
from sqlalchemy import UUID, Column, Date, DateTime, ForeignKey, String
from sqlalchemy.sql import func


class LoginHistory(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    login_time = Column(DateTime, default=func.now())
    partition_date = Column(
        Date, default=func.date_trunc("month", func.now()), nullable=False
    )
