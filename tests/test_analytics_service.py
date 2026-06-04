from datetime import date

from app.models.asset import AssetCreate
from app.models.data_source import DataSourceCreate
from app.models.time_series import TimeSeriesCreate

from app.repositories.asset_repository import AssetRepository
from app.repositories.data_source_repository import DataSourceRepository
from app.repositories.time_series_repository import TimeSeriesRepository

from app.services.analytics_service import AnalyticsService

from app.database import (
    assets_collection,
    data_sources_collection,
    time_series_collection,
    analytics_summaries_collection,
)

from batch_jobs.yearly_aggregation_job import compute_yearly_close_summaries
from batch_jobs.activity_aggregation_job import compute_yearly_activity_summaries


def clear_test_data():
    assets_collection.delete_many({
        "assetId": {
            "$in": [
                "TESTBTC",
                "TESTETH",
                "TESTACT",
                "TEST_DELETE_ASSET",
            ]
        }
    })

    data_sources_collection.delete_many({
        "dataSourceId": {
            "$in": [
                "TEST_SOURCE",
                "TEST_ACTIVITY_SOURCE",
                "TEST_DELETE_SOURCE",
            ]
        }
    })

    time_series_collection.delete_many({
        "assetId": {
            "$in": [
                "TESTBTC",
                "TESTETH",
                "TESTACT",
                "TEST_DELETE_ASSET",
            ]
        },
        "dataSourceId": {
            "$in": [
                "TEST_SOURCE",
                "TEST_ACTIVITY_SOURCE",
                "TEST_DELETE_SOURCE",
            ]
        }
    })

    analytics_summaries_collection.delete_many({
        "assetId": {
            "$in": [
                "TESTBTC",
                "TESTETH",
                "TESTACT",
                "TEST_DELETE_ASSET",
            ]
        },
        "dataSourceId": {
            "$in": [
                "TEST_SOURCE",
                "TEST_ACTIVITY_SOURCE",
                "TEST_DELETE_SOURCE",
            ]
        }
    })


def setup_test_data():
    clear_test_data()

    asset_repository = AssetRepository()
    data_source_repository = DataSourceRepository()
    time_series_repository = TimeSeriesRepository()

    asset_repository.save(
        AssetCreate(
            assetId="TESTBTC",
            symbol="TBTC",
            name="Test Bitcoin",
            assetClass="crypto",
            region="Global",
            description="Test BTC asset",
            attributes={"test": True},
        )
    )

    asset_repository.save(
        AssetCreate(
            assetId="TESTETH",
            symbol="TETH",
            name="Test Ethereum",
            assetClass="crypto",
            region="Global",
            description="Test ETH asset",
            attributes={"test": True},
        )
    )

    data_source_repository.save(
        DataSourceCreate(
            dataSourceId="TEST_SOURCE",
            provider="Test Provider",
            dataset="TEST",
            description="Test source",
            apiEndpoint="http://example.com",
            supportedAttributes=["open", "high", "low", "close", "volume"],
            attributes={"test": True},
        )
    )

    btc_records = [
        ("2024-01-01", 100),
        ("2024-01-02", 110),
        ("2024-01-03", 120),
    ]

    eth_records = [
        ("2024-01-01", 200),
        ("2024-01-02", 210),
        ("2024-01-03", 220),
    ]

    for business_date, close in btc_records:
        time_series_repository.save(
            TimeSeriesCreate(
                assetId="TESTBTC",
                dataSourceId="TEST_SOURCE",
                businessDate=date.fromisoformat(business_date),
                values={
                    "open": close - 1,
                    "high": close + 2,
                    "low": close - 3,
                    "close": close,
                    "volume": 1000,
                },
                provenance={"test": True},
            )
        )

    for business_date, close in eth_records:
        time_series_repository.save(
            TimeSeriesCreate(
                assetId="TESTETH",
                dataSourceId="TEST_SOURCE",
                businessDate=date.fromisoformat(business_date),
                values={
                    "open": close - 1,
                    "high": close + 2,
                    "low": close - 3,
                    "close": close,
                    "volume": 2000,
                },
                provenance={"test": True},
            )
        )


def setup_activity_test_data():
    clear_test_data()

    asset_repository = AssetRepository()
    data_source_repository = DataSourceRepository()
    time_series_repository = TimeSeriesRepository()

    asset_repository.save(
        AssetCreate(
            assetId="TESTACT",
            symbol="TACT",
            name="Test Activity Asset",
            assetClass="stock",
            region="US",
            description="Test activity asset",
            attributes={"test": True},
        )
    )

    data_source_repository.save(
        DataSourceCreate(
            dataSourceId="TEST_ACTIVITY_SOURCE",
            provider="Test Activity Provider",
            dataset="TEST_ACTIVITY",
            description="Test activity source",
            apiEndpoint="http://example.com/activity",
            supportedAttributes=["activity"],
            attributes={"test": True},
        )
    )

    activity_records = [
        ("2024-01-01", 0.10),
        ("2024-01-02", 0.12),
        ("2024-01-03", 0.15),
    ]

    for business_date, activity in activity_records:
        time_series_repository.save(
            TimeSeriesCreate(
                assetId="TESTACT",
                dataSourceId="TEST_ACTIVITY_SOURCE",
                businessDate=date.fromisoformat(business_date),
                values={"activity": activity},
                provenance={"test": True},
            )
        )


def test_summary_calculation():
    setup_test_data()

    service = AnalyticsService()

    result = service.summarize_asset(
        asset_id="TESTBTC",
        data_source_id="TEST_SOURCE",
        start_business_date=date(2024, 1, 1),
        end_business_date=date(2024, 1, 4),
    )

    assert result["recordCount"] == 3
    assert result["minClose"] == 100
    assert result["maxClose"] == 120
    assert result["avgClose"] == 110
    assert result["firstClose"] == 100
    assert result["lastClose"] == 120
    assert result["absoluteChange"] == 20
    assert result["trend"] == "upward"

    clear_test_data()


def test_prediction_calculation():
    setup_test_data()

    service = AnalyticsService()

    result = service.predict_next_close(
        asset_id="TESTBTC",
        data_source_id="TEST_SOURCE",
        start_business_date=date(2024, 1, 1),
        end_business_date=date(2024, 1, 4),
    )

    assert result["model"] == "average_daily_close_change"
    assert result["lastClose"] == 120
    assert result["averageDailyChange"] == 10
    assert result["predictedNextClose"] == 130
    assert result["signal"] == "positive"

    clear_test_data()


def test_compare_assets():
    setup_test_data()

    service = AnalyticsService()

    result = service.compare_assets(
        asset_id_1="TESTBTC",
        asset_id_2="TESTETH",
        data_source_id="TEST_SOURCE",
        start_business_date=date(2024, 1, 1),
        end_business_date=date(2024, 1, 4),
    )

    assert result["assetId1"] == "TESTBTC"
    assert result["assetId2"] == "TESTETH"
    assert "asset1Summary" in result
    assert "asset2Summary" in result
    assert result["strongerPerformer"] == "TESTBTC"

    clear_test_data()


def test_temporal_latest_version_for_same_business_date():
    clear_test_data()

    repository = TimeSeriesRepository()

    repository.save(
        TimeSeriesCreate(
            assetId="TESTBTC",
            dataSourceId="TEST_SOURCE",
            businessDate=date(2024, 1, 1),
            values={"close": 100},
            provenance={"version": "old"},
        )
    )

    repository.save(
        TimeSeriesCreate(
            assetId="TESTBTC",
            dataSourceId="TEST_SOURCE",
            businessDate=date(2024, 1, 1),
            values={"close": 150},
            provenance={"version": "corrected"},
        )
    )

    records = repository.find_latest_range(
        asset_id="TESTBTC",
        data_source_id="TEST_SOURCE",
        start_business_date=date(2024, 1, 1),
        end_business_date=date(2024, 1, 2),
    )

    assert len(records) == 1
    assert records[0]["values"]["close"] == 150
    assert records[0]["provenance"]["version"] == "corrected"

    clear_test_data()


def test_activity_summary_calculation():
    setup_activity_test_data()

    service = AnalyticsService()

    result = service.summarize_activity(
        asset_id="TESTACT",
        data_source_id="TEST_ACTIVITY_SOURCE",
        start_business_date=date(2024, 1, 1),
        end_business_date=date(2024, 1, 4),
    )

    assert result["metric"] == "activity"
    assert result["recordCount"] == 3
    assert result["minActivity"] == 0.10
    assert result["maxActivity"] == 0.15
    assert result["avgActivity"] == 0.123333
    assert result["firstActivity"] == 0.10
    assert result["lastActivity"] == 0.15
    assert result["trend"] == "increasing"

    clear_test_data()


def test_batch_yearly_close_aggregation_job():
    setup_test_data()

    result = compute_yearly_close_summaries()

    assert result["jobType"] == "yearly_close_aggregation"
    assert result["groupsComputed"] >= 2

    test_results = [
        item for item in result["results"]
        if item["assetId"] == "TESTBTC"
        and item["dataSourceId"] == "TEST_SOURCE"
    ]

    assert len(test_results) == 1

    summary = test_results[0]
    assert summary["businessYear"] == 2024
    assert summary["recordCount"] == 3
    assert summary["minClose"] == 100
    assert summary["maxClose"] == 120
    assert summary["avgClose"] == 110
    assert summary["computedBy"] == "batch_yearly_aggregation_job"
    assert summary["resultType"] == "yearly_close_summary"

    clear_test_data()


def test_batch_yearly_activity_aggregation_job():
    setup_activity_test_data()

    result = compute_yearly_activity_summaries()

    assert result["jobType"] == "yearly_activity_aggregation"
    assert result["groupsComputed"] >= 1

    test_results = [
        item for item in result["results"]
        if item["assetId"] == "TESTACT"
        and item["dataSourceId"] == "TEST_ACTIVITY_SOURCE"
    ]

    assert len(test_results) == 1

    summary = test_results[0]
    assert summary["businessYear"] == 2024
    assert summary["recordCount"] == 3
    assert summary["minActivity"] == 0.10
    assert summary["maxActivity"] == 0.15
    assert summary["avgActivity"] == 0.123333
    assert summary["computedBy"] == "batch_activity_aggregation_job"
    assert summary["resultType"] == "yearly_activity_summary"

    clear_test_data()


def test_asset_temporal_deactivation_marker():
    clear_test_data()

    repository = AssetRepository()

    repository.save(
        AssetCreate(
            assetId="TEST_DELETE_ASSET",
            symbol="TDEL",
            name="Temporary Delete Test Asset",
            assetClass="test",
            region="Test",
            description="Asset used to test temporal deactivation",
            attributes={"test": True},
        )
    )

    deactivated = repository.deactivate(
        asset_id="TEST_DELETE_ASSET",
        reason="Testing temporal delete marker",
    )

    assert deactivated is not None
    assert deactivated["assetId"] == "TEST_DELETE_ASSET"
    assert deactivated["deleted"] is True
    assert deactivated["deletionReason"] == "Testing temporal delete marker"
    assert deactivated["attributes"]["deactivationType"] == "temporal_marker"

    latest_visible = repository.find_latest("TEST_DELETE_ASSET")
    assert latest_visible is None

    stored_versions = list(assets_collection.find({
        "assetId": "TEST_DELETE_ASSET"
    }))

    assert len(stored_versions) == 2

    clear_test_data()


def test_data_source_temporal_deactivation_marker():
    clear_test_data()

    repository = DataSourceRepository()

    repository.save(
        DataSourceCreate(
            dataSourceId="TEST_DELETE_SOURCE",
            provider="Temporary Provider",
            dataset="TEMP_DATASET",
            description="Temporary source used to test temporal deactivation",
            apiEndpoint="http://example.com/temp",
            supportedAttributes=["test"],
            attributes={"test": True},
        )
    )

    deactivated = repository.deactivate(
        data_source_id="TEST_DELETE_SOURCE",
        reason="Testing temporal source delete marker",
    )

    assert deactivated is not None
    assert deactivated["dataSourceId"] == "TEST_DELETE_SOURCE"
    assert deactivated["deleted"] is True
    assert deactivated["deletionReason"] == "Testing temporal source delete marker"
    assert deactivated["attributes"]["deactivationType"] == "temporal_marker"

    latest_visible = repository.find_latest("TEST_DELETE_SOURCE")
    assert latest_visible is None

    stored_versions = list(data_sources_collection.find({
        "dataSourceId": "TEST_DELETE_SOURCE"
    }))

    assert len(stored_versions) == 2

    clear_test_data()

def test_time_series_as_of_system_time_query():
    clear_test_data()

    repository = TimeSeriesRepository()

    old_version = repository.save(
        TimeSeriesCreate(
            assetId="TESTBTC",
            dataSourceId="TEST_SOURCE",
            businessDate=date(2024, 1, 1),
            values={"close": 100},
            provenance={"version": "old"},
        )
    )

    corrected_version = repository.save(
        TimeSeriesCreate(
            assetId="TESTBTC",
            dataSourceId="TEST_SOURCE",
            businessDate=date(2024, 1, 1),
            values={"close": 150},
            provenance={"version": "corrected"},
        )
    )

    old_system_time = old_version["systemTime"]
    corrected_system_time = corrected_version["systemTime"]

    records_as_of_old = repository.find_latest_range(
        asset_id="TESTBTC",
        data_source_id="TEST_SOURCE",
        start_business_date=date(2024, 1, 1),
        end_business_date=date(2024, 1, 2),
        as_of_system_time=old_system_time,
    )

    assert len(records_as_of_old) == 1
    assert records_as_of_old[0]["values"]["close"] == 100
    assert records_as_of_old[0]["provenance"]["version"] == "old"

    records_as_of_corrected = repository.find_latest_range(
        asset_id="TESTBTC",
        data_source_id="TEST_SOURCE",
        start_business_date=date(2024, 1, 1),
        end_business_date=date(2024, 1, 2),
        as_of_system_time=corrected_system_time,
    )

    assert len(records_as_of_corrected) == 1
    assert records_as_of_corrected[0]["values"]["close"] == 150
    assert records_as_of_corrected[0]["provenance"]["version"] == "corrected"

    clear_test_data()