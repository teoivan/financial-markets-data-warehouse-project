import csv
import io
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

from app.models.asset import AssetCreate
from app.models.data_source import DataSourceCreate
from app.models.time_series import TimeSeriesCreate

from app.repositories.asset_repository import AssetRepository
from app.repositories.data_source_repository import DataSourceRepository
from app.repositories.time_series_repository import TimeSeriesRepository


load_dotenv()

NASDAQ_DATA_SOURCE_ID = "NASDAQ_DATA_LINK_RTAT10"
NASDAQ_DATASET_CODE = "NDAQ/RTAT10"


class NasdaqDataLinkIngestionService:
    """
    Ingests real external financial data from Nasdaq Data Link.

    The assignment mentions Nasdaq Data Link and BITFINEX as example financial
    data providers/datasets. This implemented live provider demo uses the
    accessible Nasdaq Data Link table NDAQ/RTAT10.

    The warehouse supports heterogeneous data, so the Nasdaq records store
    an 'activity' indicator while the CSV fallback stores OHLCV crypto data.
    """

    def __init__(self):
        self.api_key = os.getenv("NASDAQ_DATA_LINK_API_KEY")

        self.asset_repository = AssetRepository()
        self.data_source_repository = DataSourceRepository()
        self.time_series_repository = TimeSeriesRepository()

    def require_api_key(self) -> None:
        if not self.api_key:
            raise ValueError(
                "NASDAQ_DATA_LINK_API_KEY is missing. "
                "Add it to C:\\Users\\teodo\\financial_project\\.env"
            )

    def create_data_source(self) -> None:
        data_source = DataSourceCreate(
            dataSourceId=NASDAQ_DATA_SOURCE_ID,
            provider="Nasdaq Data Link",
            dataset=NASDAQ_DATASET_CODE,
            description="Retail Trading Activity Tracker data downloaded from Nasdaq Data Link",
            apiEndpoint="https://data.nasdaq.com/api/v3/datatables/NDAQ/RTAT10.csv",
            supportedAttributes=["activity"],
            attributes={
                "format": "csv",
                "externalProvider": True,
                "requiresApiKey": True,
                "frequency": "daily",
                "dataType": "retail_trading_activity",
            },
        )

        self.data_source_repository.save(data_source)

    def create_asset(self, metadata: Dict[str, str], provider_symbol: str) -> None:
        asset = AssetCreate(
            assetId=metadata["assetId"],
            symbol=metadata["symbol"],
            name=metadata["name"],
            assetClass=metadata["assetClass"],
            region=metadata["region"],
            description=f"{metadata['name']} retail trading activity from Nasdaq Data Link",
            attributes={
                "providerSymbol": provider_symbol,
                "currency": "USD",
                "source": "nasdaq_data_link_live_ingestion",
                "dataset": NASDAQ_DATASET_CODE,
            },
        )

        self.asset_repository.save(asset)

    def build_table_csv_url(
        self,
        database_code: str,
        table_code: str,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> str:
        base_url = (
            f"https://data.nasdaq.com/api/v3/datatables/"
            f"{database_code}/{table_code}.csv"
        )

        params = {
            "api_key": self.api_key,
        }

        if extra_params:
            params.update(extra_params)

        query = "&".join(f"{key}={value}" for key, value in params.items())
        return f"{base_url}?{query}"

    def fetch_csv(self, url: str) -> str:
        response = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": "financial-dwh-student-project/1.0"
            },
        )

        text = response.text.strip()

        if response.status_code != 200:
            raise ValueError(
                f"Nasdaq Data Link request failed with status {response.status_code}. "
                f"Response: {text[:500]}"
            )

        if not text:
            raise ValueError("Nasdaq Data Link returned an empty response.")

        if "error" in text.lower() and "quandl_error" in text.lower():
            raise ValueError(f"Nasdaq Data Link error response: {text[:500]}")

        return text

    def normalize_row(self, row: dict) -> dict:
        return {
            str(key).strip().lower(): str(value).strip()
            for key, value in row.items()
            if key is not None and value is not None
        }

    def get_value(self, row: dict, *possible_names: str) -> str:
        for name in possible_names:
            value = row.get(name.lower())
            if value not in (None, ""):
                return value

        raise KeyError(
            f"Missing one of columns: {possible_names}. "
            f"Available columns: {list(row.keys())}"
        )

    def parse_date(self, value: str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass

        raise ValueError(f"Unsupported date format: {value}")

    def parse_float_optional(self, value: str) -> Optional[float]:
        if value in (None, "", "None", "null", "NULL"):
            return None

        return float(value)

    def row_to_time_series(
        self,
        row: dict,
        metadata: Dict[str, str],
        provider_symbol: str,
        source_url: str,
    ) -> TimeSeriesCreate:
        normalized = self.normalize_row(row)

        business_date_raw = self.get_value(
            normalized,
            "date",
            "business_date",
            "time",
            "timestamp",
        )

        business_date = self.parse_date(business_date_raw[:10])

        values = {}

        field_mapping = {
            "open": ("open", "open_price"),
            "high": ("high", "high_price"),
            "low": ("low", "low_price"),
            "close": ("close", "last", "last_price", "mid", "price"),
            "volume": ("volume", "volume_usd", "vol"),
            "bid": ("bid",),
            "ask": ("ask",),
            "activity": ("activity", "retail_activity"),
        }

        for canonical_name, possible_names in field_mapping.items():
            try:
                raw_value = self.get_value(normalized, *possible_names)
                parsed = self.parse_float_optional(raw_value)
                if parsed is not None:
                    values[canonical_name] = parsed
            except KeyError:
                continue

        if not values:
            raise ValueError(
                f"No numeric market values could be parsed from row. "
                f"Available columns: {list(normalized.keys())}"
            )

        return TimeSeriesCreate(
            assetId=metadata["assetId"],
            dataSourceId=NASDAQ_DATA_SOURCE_ID,
            businessDate=business_date,
            values=values,
            provenance={
                "provider": "Nasdaq Data Link",
                "dataset": NASDAQ_DATASET_CODE,
                "providerSymbol": provider_symbol,
                "url": source_url.replace(self.api_key or "", "***"),
                "ingestionMode": "external_provider_csv",
                "ingestedAt": datetime.now(timezone.utc).isoformat(),
            },
        )

    def ingest_table(
        self,
        database_code: str,
        table_code: str,
        provider_symbol: str,
        metadata: Dict[str, str],
        extra_params: Optional[Dict[str, str]] = None,
        max_rows: int = 100,
    ) -> dict:
        self.require_api_key()

        self.create_data_source()
        self.create_asset(metadata, provider_symbol)

        url = self.build_table_csv_url(
            database_code=database_code,
            table_code=table_code,
            extra_params=extra_params,
        )

        csv_text = self.fetch_csv(url)
        reader = csv.DictReader(io.StringIO(csv_text))

        print(f"Nasdaq columns for {database_code}/{table_code}:", reader.fieldnames)

        fetched_records = 0
        stored_records = 0
        failed_records = 0

        for row in reader:
            if fetched_records >= max_rows:
                break

            fetched_records += 1

            try:
                record = self.row_to_time_series(
                    row=row,
                    metadata=metadata,
                    provider_symbol=provider_symbol,
                    source_url=url,
                )

                self.time_series_repository.save(record)
                stored_records += 1

            except Exception as error:
                failed_records += 1
                print(f"Failed Nasdaq row for {provider_symbol}: {error}")
                print(f"Raw row was: {row}")

        return {
            "databaseCode": database_code,
            "tableCode": table_code,
            "providerSymbol": provider_symbol,
            "assetId": metadata["assetId"],
            "fetchedRecords": fetched_records,
            "storedRecords": stored_records,
            "failedRecords": failed_records,
        }

    def ingest_demo(self) -> dict:
        stock_assets = {
            "AAPL": {
                "assetId": "AAPL_NASDAQ",
                "symbol": "AAPL",
                "name": "Apple Inc. from Nasdaq Data Link",
                "assetClass": "stock",
                "region": "US",
            },
            "MSFT": {
                "assetId": "MSFT_NASDAQ",
                "symbol": "MSFT",
                "name": "Microsoft Corporation from Nasdaq Data Link",
                "assetClass": "stock",
                "region": "US",
            },
            "TSLA": {
                "assetId": "TSLA_NASDAQ",
                "symbol": "TSLA",
                "name": "Tesla Inc. from Nasdaq Data Link",
                "assetClass": "stock",
                "region": "US",
            },
            "GOOGL": {
                "assetId": "GOOGL_NASDAQ",
                "symbol": "GOOGL",
                "name": "Alphabet Inc. from Nasdaq Data Link",
                "assetClass": "stock",
                "region": "US",
            },
        }

        results = []

        total_fetched = 0
        total_stored = 0
        total_failed = 0

        for ticker, metadata in stock_assets.items():
            try:
                result = self.ingest_table(
                    database_code="NDAQ",
                    table_code="RTAT10",
                    provider_symbol=ticker,
                    metadata=metadata,
                    extra_params={
                        "date.gte": "2024-01-01",
                        "date.lte": "2024-03-31",
                        "ticker": ticker,
                        "qopts.columns": "date,ticker,activity",
                    },
                    max_rows=100,
                )

                total_fetched += result["fetchedRecords"]
                total_stored += result["storedRecords"]
                total_failed += result["failedRecords"]
                results.append(result)

            except Exception as error:
                total_failed += 1
                results.append({
                    "providerSymbol": ticker,
                    "error": str(error),
                })

        return {
            "jobType": "nasdaq_data_link_external_ingestion",
            "provider": "Nasdaq Data Link",
            "dataSourceId": NASDAQ_DATA_SOURCE_ID,
            "table": NASDAQ_DATASET_CODE,
            "totalFetchedRecords": total_fetched,
            "totalStoredRecords": total_stored,
            "totalFailedRecords": total_failed,
            "details": results,
        }


if __name__ == "__main__":
    service = NasdaqDataLinkIngestionService()
    result = service.ingest_demo()
    print(result)