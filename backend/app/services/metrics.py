from sqlalchemy.orm import Session

from app.repositories.metrics import MetricsRepository
from app.schemas.metrics import (
    DashboardResponse,
    HostHealthRow,
    MetricPoint,
    MetricSeriesResponse,
    OverviewResponse,
    SummaryMetric,
    TopMetricItem,
    TrendSeries,
)

TREND_METRICS = {
    "cpu_usage": ("CPU 使用率", "%"),
    "mem_used": ("内存使用", "MB"),
    "net_in": ("入站带宽", "MB/s"),
}


class MetricsService:
    def __init__(self, db: Session) -> None:
        self.repository = MetricsRepository(db)

    def overview(self) -> OverviewResponse:
        return OverviewResponse(**self.repository.overview())

    def series(self, hostid: str, mod: str, limit: int) -> MetricSeriesResponse:
        rows = self.repository.series(hostid=hostid, mod=mod, limit=limit)
        return MetricSeriesResponse(
            hostid=hostid,
            mod=mod,
            points=[MetricPoint(collect_time=row.collect_time, value=row.value) for row in rows],
        )

    def dashboard(self) -> DashboardResponse:
        overview = self.repository.overview()
        time_range = self.repository.time_range()
        avg_cpu = self.repository.average_metric("cpu_usage")
        avg_mem = self.repository.average_metric("mem_used")

        summary = [
            SummaryMetric(key="host_count", label="主机数量", value=overview["host_count"]),
            SummaryMetric(key="metric_count", label="指标数量", value=overview["metric_count"]),
            SummaryMetric(key="point_count", label="采集点数", value=overview["point_count"]),
            SummaryMetric(
                key="avg_cpu",
                label="近 24 小时平均 CPU",
                value=round(float(avg_cpu or 0), 2),
                unit="%",
            ),
            SummaryMetric(
                key="avg_mem",
                label="近 24 小时平均内存",
                value=round(float(avg_mem or 0), 2),
                unit="MB",
            ),
            SummaryMetric(
                key="time_range",
                label="数据时间范围",
                value=self._format_time_range(time_range),
            ),
        ]

        trend_points = {mod: [] for mod in TREND_METRICS}
        for row in self.repository.trend_rows(list(TREND_METRICS)):
            trend_points[row.mod].append(
                MetricPoint(collect_time=row.collect_time, value=row.avg_value)
            )

        trends = [
            TrendSeries(name=name, unit=unit, points=trend_points[mod])
            for mod, (name, unit) in TREND_METRICS.items()
        ]

        disk_top = [
            TopMetricItem(
                hostid=row.hostid,
                hostname=row.hostname,
                mod=row.mod,
                value=row.value,
                unit=row.unit,
            )
            for row in self.repository.disk_top()
        ]

        host_health = [
            HostHealthRow(
                hostid=row.hostid,
                hostname=row.hostname,
                owner=row.owner,
                model=row.model,
                location=f"{row.location1} / {row.location2}",
                cpu_usage=row.cpu_usage,
                mem_used=row.mem_used,
                disk_util=row.disk_util,
            )
            for row in self.repository.host_health()
        ]

        return DashboardResponse(
            summary=summary,
            trends=trends,
            disk_top=disk_top,
            host_health=host_health,
        )

    def _format_time_range(self, time_range: object) -> str:
        if not time_range or not time_range[0] or not time_range[1]:  # type: ignore[index]
            return "-"
        return f"{time_range[0]:%Y-%m-%d %H:%M} 至 {time_range[1]:%Y-%m-%d %H:%M}"  # type: ignore[index]
