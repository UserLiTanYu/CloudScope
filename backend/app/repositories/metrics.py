from datetime import timedelta
from decimal import Decimal

from sqlalchemy import Row, case, func, or_, select
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

    def time_range(self) -> Row[tuple] | None:
        stmt = select(func.min(TsarDetail.collect_time), func.max(TsarDetail.collect_time))
        return self.db.execute(stmt).one_or_none()

    def trend_rows(self, mods: list[str], hours: int = 24) -> list[Row[tuple]]:
        latest_time = self.db.scalar(
            select(func.max(TsarDetail.collect_time)).where(TsarDetail.mod.in_(mods))
        )
        if latest_time is None:
            return []

        start_time = latest_time - timedelta(hours=hours)
        stmt = (
            select(
                TsarDetail.collect_time,
                TsarDetail.mod,
                func.avg(TsarDetail.value).label("avg_value"),
            )
            .where(TsarDetail.mod.in_(mods), TsarDetail.collect_time >= start_time)
            .group_by(TsarDetail.collect_time, TsarDetail.mod)
            .order_by(TsarDetail.collect_time.asc(), TsarDetail.mod.asc())
        )
        return list(self.db.execute(stmt))

    def disk_top(self, limit: int = 8) -> list[Row[tuple]]:
        latest_time = self.db.scalar(
            select(func.max(TsarDetail.collect_time)).where(TsarDetail.tag == "disk_util_percent")
        )
        if latest_time is None:
            return []

        start_time = latest_time - timedelta(hours=24)
        stmt = (
            select(
                TsarDetail.hostid,
                HostDetail.hostname,
                TsarDetail.mod,
                func.max(TsarDetail.value).label("value"),
                ModDetail.unit,
            )
            .join(HostDetail, HostDetail.hostid == TsarDetail.hostid)
            .join(ModDetail, ModDetail.mod == TsarDetail.mod)
            .where(TsarDetail.tag == "disk_util_percent", TsarDetail.collect_time >= start_time)
            .group_by(TsarDetail.hostid, HostDetail.hostname, TsarDetail.mod, ModDetail.unit)
            .order_by(func.max(TsarDetail.value).desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt))

    def metric_top(self, mod: str, limit: int = 8) -> list[Row[tuple]]:
        latest_time = self.db.scalar(
            select(func.max(TsarDetail.collect_time)).where(TsarDetail.mod == mod)
        )
        if latest_time is None:
            return []

        start_time = latest_time - timedelta(hours=24)
        stmt = (
            select(
                TsarDetail.hostid,
                HostDetail.hostname,
                TsarDetail.mod,
                func.avg(TsarDetail.value).label("value"),
                ModDetail.unit,
            )
            .join(HostDetail, HostDetail.hostid == TsarDetail.hostid)
            .join(ModDetail, ModDetail.mod == TsarDetail.mod)
            .where(TsarDetail.mod == mod, TsarDetail.collect_time >= start_time)
            .group_by(TsarDetail.hostid, HostDetail.hostname, TsarDetail.mod, ModDetail.unit)
            .order_by(func.avg(TsarDetail.value).desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt))

    def network_top(self, limit: int = 8) -> list[Row[tuple]]:
        latest_time = self.db.scalar(
            select(func.max(TsarDetail.collect_time)).where(
                TsarDetail.mod.in_(["net_in", "net_out"])
            )
        )
        if latest_time is None:
            return []

        start_time = latest_time - timedelta(hours=24)
        stmt = (
            select(
                TsarDetail.hostid,
                HostDetail.hostname,
                func.sum(TsarDetail.value).label("value"),
            )
            .join(HostDetail, HostDetail.hostid == TsarDetail.hostid)
            .where(
                TsarDetail.mod.in_(["net_in", "net_out"]),
                TsarDetail.collect_time >= start_time,
            )
            .group_by(TsarDetail.hostid, HostDetail.hostname)
            .order_by(func.sum(TsarDetail.value).desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt))

    def location_distribution(self) -> list[Row[tuple]]:
        stmt = (
            select(HostDetail.location1, func.count().label("value"))
            .group_by(HostDetail.location1)
            .order_by(HostDetail.location1.asc())
        )
        return list(self.db.execute(stmt))

    def host_health(self) -> list[Row[tuple]]:
        latest_pref_time = self.db.scalar(
            select(func.max(TsarDetail.collect_time)).where(TsarDetail.type == "pref")
        )
        latest_disk_time = self.db.scalar(
            select(func.max(TsarDetail.collect_time)).where(TsarDetail.tag == "disk_util_percent")
        )
        if latest_pref_time is None and latest_disk_time is None:
            return []

        pref_start = latest_pref_time - timedelta(hours=24) if latest_pref_time else None
        disk_start = latest_disk_time - timedelta(hours=24) if latest_disk_time else None
        time_filters = []
        if pref_start:
            time_filters.append(
                (TsarDetail.type == "pref") & (TsarDetail.collect_time >= pref_start)
            )
        if disk_start:
            time_filters.append(
                (TsarDetail.tag == "disk_util_percent") & (TsarDetail.collect_time >= disk_start)
            )

        metric_avg = (
            select(
                TsarDetail.hostid.label("hostid"),
                func.avg(case((TsarDetail.mod == "cpu_usage", TsarDetail.value))).label(
                    "cpu_usage"
                ),
                func.avg(case((TsarDetail.mod == "mem_used", TsarDetail.value))).label("mem_used"),
                func.max(case((TsarDetail.tag == "disk_util_percent", TsarDetail.value))).label(
                    "disk_util"
                ),
            )
            .where(or_(*time_filters))
            .group_by(TsarDetail.hostid)
            .subquery()
        )

        stmt = (
            select(
                HostDetail.hostid,
                HostDetail.hostname,
                HostDetail.owner,
                HostDetail.model,
                HostDetail.location1,
                HostDetail.location2,
                metric_avg.c.cpu_usage,
                metric_avg.c.mem_used,
                metric_avg.c.disk_util,
            )
            .outerjoin(metric_avg, metric_avg.c.hostid == HostDetail.hostid)
            .order_by(HostDetail.hostid.asc())
        )
        return list(self.db.execute(stmt))

    def average_metric(self, mod: str, hours: int = 24) -> Decimal | None:
        latest_time = self.db.scalar(
            select(func.max(TsarDetail.collect_time)).where(TsarDetail.mod == mod)
        )
        if latest_time is None:
            return None

        start_time = latest_time - timedelta(hours=hours)
        return self.db.scalar(
            select(func.avg(TsarDetail.value)).where(
                TsarDetail.mod == mod,
                TsarDetail.collect_time >= start_time,
            )
        )
