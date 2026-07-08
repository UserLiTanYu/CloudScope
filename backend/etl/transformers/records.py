from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class HostRecord:
    hostid: str
    hostname: str
    owner: str
    model: str
    location1: str
    location2: str


@dataclass(frozen=True)
class MetricRecord:
    mod: str
    type: str
    description: str
    unit: str
    tag: str


@dataclass(frozen=True)
class TsarRecord:
    ts: int
    collect_time: datetime
    hostid: str
    type: str
    mod: str
    value: Decimal
    tag: str


def transform_host(row: dict[str, str]) -> HostRecord:
    return HostRecord(
        hostid=_required(row, "hostid"),
        hostname=_required(row, "hostname"),
        owner=_required(row, "owner"),
        model=_required(row, "model"),
        location1=_required(row, "location1"),
        location2=_required(row, "location2"),
    )


def transform_metric(row: dict[str, str]) -> MetricRecord:
    return MetricRecord(
        mod=_required(row, "mod"),
        type=_required(row, "type"),
        description=_required(row, "desc"),
        unit=row.get("unit", ""),
        tag=_required(row, "tag"),
    )


def transform_tsar(row: dict[str, str]) -> TsarRecord:
    ts = int(_required(row, "ts"))
    try:
        value = Decimal(_required(row, "value"))
    except InvalidOperation as exc:
        line_number = row.get("_line_number")
        raise ValueError(f"Invalid value at line {line_number}: {row.get('value')}") from exc

    return TsarRecord(
        ts=ts,
        collect_time=datetime.fromtimestamp(ts / 1000, tz=UTC).replace(tzinfo=None),
        hostid=_required(row, "hostid"),
        type=_required(row, "type"),
        mod=_required(row, "mod"),
        value=value,
        tag=_required(row, "tag"),
    )


def _required(row: dict[str, str], field: str) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise ValueError(f"Missing required field '{field}' at line {row.get('_line_number')}")
    return value
