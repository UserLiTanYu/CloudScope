from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.metrics import MetricSeriesResponse, OverviewResponse
from app.services.metrics import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/overview", response_model=OverviewResponse)
def overview(db: Session = Depends(get_db)) -> OverviewResponse:
    return MetricsService(db).overview()


@router.get("/series", response_model=MetricSeriesResponse)
def series(
    hostid: str,
    mod: str,
    limit: int = Query(default=200, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> MetricSeriesResponse:
    return MetricsService(db).series(hostid=hostid, mod=mod, limit=limit)
