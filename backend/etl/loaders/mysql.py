from collections.abc import Iterable
from dataclasses import asdict

from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.models import HostDetail, ModDetail, TsarDetail
from etl.transformers.records import HostRecord, MetricRecord, TsarRecord


def upsert_hosts(db: Session, records: Iterable[HostRecord]) -> int:
    rows = [asdict(record) for record in records]
    if not rows:
        return 0
    stmt = insert(HostDetail).values(rows)
    update_columns = {
        column: stmt.inserted[column]
        for column in ["hostname", "owner", "model", "location1", "location2"]
    }
    db.execute(stmt.on_duplicate_key_update(**update_columns))
    return len(rows)


def upsert_metrics(db: Session, records: Iterable[MetricRecord]) -> int:
    rows = [asdict(record) for record in records]
    if not rows:
        return 0
    stmt = insert(ModDetail).values(rows)
    update_columns = {
        "type": stmt.inserted.type,
        "description": stmt.inserted.description,
        "unit": stmt.inserted.unit,
        "tag": stmt.inserted.tag,
    }
    db.execute(stmt.on_duplicate_key_update(**update_columns))
    return len(rows)


def upsert_tsar_points(db: Session, records: Iterable[TsarRecord], chunk_size: int = 2000) -> int:
    total = 0
    buffer: list[dict] = []
    for record in records:
        buffer.append(asdict(record))
        if len(buffer) >= chunk_size:
            total += _upsert_tsar_chunk(db, buffer)
            buffer.clear()
    if buffer:
        total += _upsert_tsar_chunk(db, buffer)
    return total


def _upsert_tsar_chunk(db: Session, rows: list[dict]) -> int:
    stmt = insert(TsarDetail).values(rows)
    update_columns = {
        "collect_time": stmt.inserted.collect_time,
        "value": stmt.inserted.value,
        "tag": stmt.inserted.tag,
    }
    db.execute(stmt.on_duplicate_key_update(**update_columns))
    return len(rows)
