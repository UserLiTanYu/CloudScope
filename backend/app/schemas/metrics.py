from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OverviewResponse(BaseModel):
    host_count: int
    metric_count: int
    point_count: int


class MetricPoint(BaseModel):
    collect_time: datetime
    value: Decimal


class MetricSeriesResponse(BaseModel):
    hostid: str
    mod: str
    points: list[MetricPoint]
