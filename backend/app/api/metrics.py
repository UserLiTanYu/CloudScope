from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.metrics import DashboardResponse, MetricSeriesResponse, OverviewResponse
from app.services.metrics import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/overview", response_model=OverviewResponse)
def overview(db: DbSession) -> OverviewResponse:
    return MetricsService(db).overview()


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: DbSession) -> DashboardResponse:
    return MetricsService(db).dashboard()


@router.get("/series", response_model=MetricSeriesResponse)
def series(
    hostid: str,
    mod: str,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=2000)] = 200,
) -> MetricSeriesResponse:
    return MetricsService(db).series(hostid=hostid, mod=mod, limit=limit)
