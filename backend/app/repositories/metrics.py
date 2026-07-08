from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import HostDetail, ModDetail, TsarDetail


class MetricsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def overview(self) -> dict[str, int]:
        return {
            "host_count": self.db.scalar(select(func.count()).select_from(HostDetail)) or 0,
            "metric_count": self.db.scalar(select(func.count()).select_from(ModDetail)) or 0,
            "point_count": self.db.scalar(select(func.count()).select_from(TsarDetail)) or 0,
        }

    def series(self, hostid: str, mod: str, limit: int = 200) -> list[TsarDetail]:
        stmt = (
            select(TsarDetail)
            .where(TsarDetail.hostid == hostid, TsarDetail.mod == mod)
            .order_by(TsarDetail.collect_time.desc())
            .limit(limit)
        )
        rows = list(self.db.scalars(stmt))
        return list(reversed(rows))
