import csv
from datetime import datetime, timezone
from pathlib import Path

from app.models.asset import AssetCreate
from app.models.data_source import DataSourceCreate
from app.models.time_series import TimeSeriesCreate

from app.repositories.asset_repository import AssetRepository
from app.repositories.data_source_repository import DataSourceRepository
from app.repositories.time_series_repository import TimeSeriesRepository


class CsvIngestionService:
    def __init__(self):
        self.asset_repository = AssetRepository()
        self.data_source_repository = DataSourceRepository()
        self.time_series_repository = TimeSeriesRepository()

    def ingest(self, csv_path: str) -> dict:
        path = Path(csv_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        fetched_records = 0
        stored_records = 0
        skipped_records = 0
        failed_records = 0

        seen_assets = set()
        seen_sources = set()

        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                fetched_records += 1

                try:
                    asset_id = row["assetId"]
                    data_source_id = row["dataSourceId"]

                    if asset_id not in seen_assets:
                        asset = AssetCreate(
                            assetId=asset_id,
                            symbol=row["symbol"],
                            name=row["name"],
                            assetClass=row["assetClass"],
                            region=row["region"],
                            description=f"{row['name']} market data",
                            attributes={
                                "currency": "USD",
                                "source": "csv_ingestion"
                            }
                        )
                        self.asset_repository.save(asset)
                        seen_assets.add(asset_id)

                    if data_source_id not in seen_sources:
                        data_source = DataSourceCreate(
                            dataSourceId=data_source_id,
                            provider=row["provider"],
                            dataset=row["dataset"],
                            description="Historical crypto exchange rates loaded from CSV sample",
                            apiEndpoint="https://data.nasdaq.com/databases/BITFINEX",
                            supportedAttributes=["open", "high", "low", "close", "volume"],
                            attributes={
                                "ingestionType": "csv",
                                "sourceFile": str(path)
                            }
                        )
                        self.data_source_repository.save(data_source)
                        seen_sources.add(data_source_id)

                    record = TimeSeriesCreate(
                        assetId=asset_id,
                        dataSourceId=data_source_id,
                        businessDate=datetime.strptime(row["businessDate"], "%Y-%m-%d").date(),
                        values={
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"]),
                        },
                        provenance={
                            "provider": row["provider"],
                            "dataset": row["dataset"],
                            "sourceFile": str(path),
                            "ingestionMode": "csv_batch",
                            "ingestedAt": datetime.now(timezone.utc).isoformat()
                        }
                    )

                    self.time_series_repository.save(record)
                    stored_records += 1

                except Exception as error:
                    failed_records += 1
                    print(f"Failed to ingest row {fetched_records}: {error}")

        return {
            "jobType": "csv_ingestion",
            "csvPath": str(path),
            "fetchedRecords": fetched_records,
            "storedRecords": stored_records,
            "skippedRecords": skipped_records,
            "failedRecords": failed_records,
            "assetsCreatedOrVersioned": len(seen_assets),
            "dataSourcesCreatedOrVersioned": len(seen_sources)
        }


if __name__ == "__main__":
    service = CsvIngestionService()
    result = service.ingest("data/sample_market_data.csv")
    print(result)