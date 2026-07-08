from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class HostDetail(Base):
    __tablename__ = "host_detail"

    hostid: Mapped[str] = mapped_column(String(32), primary_key=True)
    hostname: Mapped[str] = mapped_column(String(128), nullable=False)
    owner: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    location1: Mapped[str] = mapped_column(String(64), nullable=False)
    location2: Mapped[str] = mapped_column(String(64), nullable=False)

    tsar_points = relationship("TsarDetail", back_populates="host")
