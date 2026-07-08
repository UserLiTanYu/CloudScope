import argparse
import logging
from pathlib import Path

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging import configure_logging
from etl.loaders.mysql import upsert_hosts, upsert_metrics, upsert_tsar_points
from etl.readers.tabular import read_tsv
from etl.transformers.records import transform_host, transform_metric, transform_tsar

logger = logging.getLogger(__name__)


def import_all(data_dir: Path | None = None) -> None:
    settings = get_settings()
    source_dir = data_dir or settings.source_data_dir

    host_file = source_dir / "host_detail.dat"
    metric_file = source_dir / "mod_detail.dat"
    disk_file = source_dir / "disk_tsar.dat"
    pref_file = source_dir / "pref_tsar.dat"

    with SessionLocal() as db:
        host_count = upsert_hosts(db, (transform_host(row) for row in read_tsv(host_file)))
        metric_count = upsert_metrics(db, (transform_metric(row) for row in read_tsv(metric_file)))
        disk_count = upsert_tsar_points(db, (transform_tsar(row) for row in read_tsv(disk_file)))
        pref_count = upsert_tsar_points(db, (transform_tsar(row) for row in read_tsv(pref_file)))
        db.commit()

    logger.info(
        "Import completed: hosts=%s metrics=%s disk_points=%s pref_points=%s",
        host_count,
        metric_count,
        disk_count,
        pref_count,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Import CloudScope .dat files into MySQL.")
    parser.add_argument("--data-dir", type=Path, default=None)
    args = parser.parse_args()

    configure_logging()
    import_all(args.data_dir)


if __name__ == "__main__":
    main()
