import csv
from collections.abc import Iterator
from pathlib import Path


def read_tsv(path: Path) -> Iterator[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        for line_number, row in enumerate(reader, start=2):
            cleaned = {key.strip(): (value or "").strip() for key, value in row.items() if key}
            cleaned["_line_number"] = str(line_number)
            yield cleaned
