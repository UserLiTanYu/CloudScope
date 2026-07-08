from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ModDetail(Base):
    __tablename__ = "mod_detail"

    mod: Mapped[str] = mapped_column("mod", String(64), primary_key=True, quote=True)
    type: Mapped[str] = mapped_column("type", String(16), nullable=False, index=True, quote=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    tag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    tsar_points = relationship("TsarDetail", back_populates="metric")
