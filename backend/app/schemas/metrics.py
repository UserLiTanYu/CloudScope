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


class SummaryMetric(BaseModel):
    key: str
    label: str
    value: int | float | str
    unit: str = ""


class TrendSeries(BaseModel):
    name: str
    unit: str
    points: list[MetricPoint]


class TopMetricItem(BaseModel):
    hostid: str
    hostname: str
    mod: str
    value: Decimal
    unit: str


class HostHealthRow(BaseModel):
    hostid: str
    hostname: str
    owner: str
    model: str
    location: str
    cpu_usage: Decimal | None
    mem_used: Decimal | None
    disk_util: Decimal | None


class DashboardResponse(BaseModel):
    summary: list[SummaryMetric]
    trends: list[TrendSeries]
    disk_top: list[TopMetricItem]
    host_health: list[HostHealthRow]
