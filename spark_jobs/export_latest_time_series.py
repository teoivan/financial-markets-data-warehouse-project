import json
from pathlib import Path

from app.repositories.time_series_repository import TimeSeriesRepository


EXPORT_DIR = Path("data/exports")
EXPORT_FILE = EXPORT_DIR / "latest_time_series.json"


def export_latest_time_series(offset: int = 0, limit: int = 10000) -> dict:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    repository = TimeSeriesRepository()
    records = repository.find_all_latest(offset=offset, limit=limit)

    with EXPORT_FILE.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, default=str) + "\n")

    return {
        "jobType": "export_latest_time_series_for_spark",
        "targetFile": str(EXPORT_FILE),
        "recordCount": len(records),
    }


if __name__ == "__main__":
    result = export_latest_time_series()
    print(result)