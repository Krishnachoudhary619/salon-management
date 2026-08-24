from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BaseModel


class Widget(BaseModel):
    __tablename__ = "widgets"

    name: Mapped[str] = mapped_column(nullable=False)
