from sqlalchemy.orm import Session

from app.repositories.metrics import MetricsRepository
from app.schemas.metrics import MetricPoint, MetricSeriesResponse, OverviewResponse


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
