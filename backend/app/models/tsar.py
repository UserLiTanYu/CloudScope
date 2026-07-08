from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TsarDetail(Base):
    __tablename__ = "tsar_detail"
    __table_args__ = (
        UniqueConstraint("ts", "hostid", "type", "mod", name="uq_tsar_point"),
        Index("idx_tsar_host_time", "hostid", "collect_time"),
        Index("idx_tsar_mod_time", "mod", "collect_time"),
        Index("idx_tsar_type_tag_time", "type", "tag", "collect_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[int] = mapped_column(nullable=False)
    collect_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hostid: Mapped[str] = mapped_column(ForeignKey("host_detail.hostid"), nullable=False)
    type: Mapped[str] = mapped_column("type", String(16), nullable=False, quote=True)
    mod: Mapped[str] = mapped_column(
        "mod",
        ForeignKey("mod_detail.mod"),
        nullable=False,
        quote=True,
    )
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    tag: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    host = relationship("HostDetail", back_populates="tsar_points")
    metric = relationship("ModDetail", back_populates="tsar_points")
