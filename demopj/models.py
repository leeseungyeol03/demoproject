# models.py
from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from demopj.database import Base

class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    tag: Mapped[str] = mapped_column(String(30), default="general")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
