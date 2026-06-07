from datetime import date
from unittest.mock import Mock

from app.database import (
    assets_collection,
    data_sources_collection,
    time_series_collection,
)
from app.repositories.asset_repository import AssetRepository
from app.repositories.data_source_repository import DataSourceRepository
from app.repositories.time_series_repository import TimeSeriesRepository
from app.services.ingestion_service import CsvIngestionService
from app.services.nasdaq_ingestion_service import NasdaqDataLinkIngestionService


def cleanup_csv_ingestion_test_data():
    assets_collection.delete_many({
        "assetId": {
            "$in": [
                "BTCUSD",
                "ETHUSD",
            ]
        }
    })

    data_sources_collection.delete_many({
        "dataSourceId": "NASDAQ_DATA_LINK_BITFINEX"
    })

    time_series_collection.delete_many({
        "assetId": {
            "$in": [
                "BTCUSD",
                "ETHUSD",
            ]
        },
        "dataSourceId": "NASDAQ_DATA_LINK_BITFINEX",
    })


def cleanup_nasdaq_ingestion_test_data():
    assets_collection.delete_many({
        "assetId": {
            "$in": [
                "AAPL_NASDAQ",
                "MSFT_NASDAQ",
                "TSLA_NASDAQ",
                "GOOGL_NASDAQ",
            ]
        }
    })

    data_sources_collection.delete_many({
        "dataSourceId": "NASDAQ_DATA_LINK_RTAT10"
    })

    time_series_collection.delete_many({
        "assetId": {
            "$in": [
                "AAPL_NASDAQ",
                "MSFT_NASDAQ",
                "TSLA_NASDAQ",
                "GOOGL_NASDAQ",
            ]
        },
        "dataSourceId": "NASDAQ_DATA_LINK_RTAT10",
    })


def test_csv_ingestion_creates_assets_sources_and_time_series_records():
    cleanup_csv_ingestion_test_data()

    service = CsvIngestionService()
    result = service.ingest("data/sample_market_data.csv")

    assert result["jobType"] == "csv_market_data_ingestion"
    assert result["totalStoredRecords"] > 0
    assert result["totalFailedRecords"] == 0

    btc_asset = AssetRepository().find_latest("BTCUSD")
    eth_asset = AssetRepository().find_latest("ETHUSD")
    data_source = DataSourceRepository().find_latest("NASDAQ_DATA_LINK_BITFINEX")

    assert btc_asset is not None
    assert btc_asset["assetId"] == "BTCUSD"
    assert btc_asset["attributes"]["source"] == "csv_ingestion"

    assert eth_asset is not None
    assert eth_asset["assetId"] == "ETHUSD"
    assert eth_asset["attributes"]["source"] == "csv_ingestion"

    assert data_source is not None
    assert data_source["dataSourceId"] == "NASDAQ_DATA_LINK_BITFINEX"
    assert "close" in data_source["supportedAttributes"]
    assert "volume" in data_source["supportedAttributes"]

    btc_records = TimeSeriesRepository().find_latest_range(
        asset_id="BTCUSD",
        data_source_id="NASDAQ_DATA_LINK_BITFINEX",
        start_business_date=date(2024, 1, 1),
        end_business_date=date(2024, 1, 6),
    )

    eth_records = TimeSeriesRepository().find_latest_range(
        asset_id="ETHUSD",
        data_source_id="NASDAQ_DATA_LINK_BITFINEX",
        start_business_date=date(2024, 1, 1),
        end_business_date=date(2024, 1, 6),
    )

    assert len(btc_records) == 5
    assert len(eth_records) == 5

    sample_record = btc_records[0]

    assert "close" in sample_record["values"]
    assert "volume" in sample_record["values"]
    assert sample_record["provenance"]["provider"] == "Nasdaq Data Link"
    assert sample_record["provenance"]["dataset"] == "BITFINEX"
    assert sample_record["provenance"]["ingestionMode"] == "csv_batch"

    cleanup_csv_ingestion_test_data()


def test_nasdaq_ingestion_creates_activity_assets_source_and_records(monkeypatch):
    cleanup_nasdaq_ingestion_test_data()

    monkeypatch.setenv("NASDAQ_DATA_LINK_API_KEY", "test-api-key")

    def mocked_get(url, timeout=30, headers=None):
        response = Mock()
        response.status_code = 200

        if "ticker=AAPL" in url:
            response.text = (
                "date,ticker,activity\n"
                "2024-03-25,AAPL,0.0198\n"
                "2024-03-26,AAPL,0.0188\n"
            )
        elif "ticker=MSFT" in url:
            response.text = (
                "date,ticker,activity\n"
                "2024-03-25,MSFT,0.0137\n"
                "2024-03-26,MSFT,0.0121\n"
            )
        elif "ticker=TSLA" in url:
            response.text = (
                "date,ticker,activity\n"
                "2024-03-25,TSLA,0.0949\n"
                "2024-03-26,TSLA,0.0881\n"
            )
        elif "ticker=GOOGL" in url:
            response.text = (
                "date,ticker,activity\n"
                "2024-03-25,GOOGL,0.0163\n"
                "2024-03-26,GOOGL,0.0101\n"
            )
        else:
            response.text = "date,ticker,activity\n"

        return response

    monkeypatch.setattr("requests.get", mocked_get)

    service = NasdaqDataLinkIngestionService()
    result = service.ingest_demo()

    assert result["jobType"] == "nasdaq_data_link_external_ingestion"
    assert result["provider"] == "Nasdaq Data Link"
    assert result["dataSourceId"] == "NASDAQ_DATA_LINK_RTAT10"
    assert result["totalFetchedRecords"] == 8
    assert result["totalStoredRecords"] == 8
    assert result["totalFailedRecords"] == 0

    data_source = DataSourceRepository().find_latest("NASDAQ_DATA_LINK_RTAT10")

    assert data_source is not None
    assert data_source["dataSourceId"] == "NASDAQ_DATA_LINK_RTAT10"
    assert data_source["provider"] == "Nasdaq Data Link"
    assert "activity" in data_source["supportedAttributes"]

    aapl_asset = AssetRepository().find_latest("AAPL_NASDAQ")

    assert aapl_asset is not None
    assert aapl_asset["assetId"] == "AAPL_NASDAQ"
    assert aapl_asset["attributes"]["source"] == "nasdaq_data_link_live_ingestion"
    assert aapl_asset["attributes"]["dataset"] == "NDAQ/RTAT10"

    aapl_records = TimeSeriesRepository().find_latest_range(
        asset_id="AAPL_NASDAQ",
        data_source_id="NASDAQ_DATA_LINK_RTAT10",
        start_business_date=date(2024, 3, 25),
        end_business_date=date(2024, 3, 27),
    )

    assert len(aapl_records) == 2

    sample_record = aapl_records[0]

    assert "activity" in sample_record["values"]
    assert sample_record["provenance"]["provider"] == "Nasdaq Data Link"
    assert sample_record["provenance"]["providerSymbol"] == "AAPL"
    assert sample_record["provenance"]["ingestionMode"] == "external_provider_csv"

    cleanup_nasdaq_ingestion_test_data()