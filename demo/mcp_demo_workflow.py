from pprint import pprint

from app.mcp_server import (
    list_assets,
    get_asset_details,
    get_time_series_data,
    summarize_asset,
    compare_assets,
    predict_next_close,
    summarize_activity,
    list_persisted_summaries,
    list_persisted_predictions,
)


def print_section(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def run_demo_workflow():
    print_section("1. List available assets")
    assets = list_assets()
    pprint(assets)

    print_section("2. Get BTCUSD asset details")
    btc_asset = get_asset_details("BTCUSD")
    pprint(btc_asset)

    print_section("3. Fetch latest BTCUSD time-series data")
    btc_latest = get_time_series_data(
        assetId="BTCUSD",
        dataSourceId="NASDAQ_DATA_LINK_BITFINEX",
        startBusinessDate="2024-01-01",
        endBusinessDate="2024-01-03",
        includeAttributes=True,
    )
    pprint(btc_latest)

    print_section("4. Fetch BTCUSD historical view before correction")
    btc_before_correction = get_time_series_data(
        assetId="BTCUSD",
        dataSourceId="NASDAQ_DATA_LINK_BITFINEX",
        startBusinessDate="2024-01-01",
        endBusinessDate="2024-01-03",
        includeAttributes=True,
        asOfSystemTime="2026-05-30T17:10:00",
    )
    pprint(btc_before_correction)

    print_section("5. Fetch BTCUSD historical view after correction")
    btc_after_correction = get_time_series_data(
        assetId="BTCUSD",
        dataSourceId="NASDAQ_DATA_LINK_BITFINEX",
        startBusinessDate="2024-01-01",
        endBusinessDate="2024-01-03",
        includeAttributes=True,
        asOfSystemTime="2026-05-30T17:12:00",
    )
    pprint(btc_after_correction)

    print_section("6. Summarize BTCUSD trend")
    btc_summary = summarize_asset(
        assetId="BTCUSD",
        dataSourceId="NASDAQ_DATA_LINK_BITFINEX",
        startBusinessDate="2024-01-01",
        endBusinessDate="2024-01-06",
    )
    pprint(btc_summary)

    print_section("7. Compare BTCUSD and ETHUSD")
    comparison = compare_assets(
        assetId1="BTCUSD",
        assetId2="ETHUSD",
        dataSourceId="NASDAQ_DATA_LINK_BITFINEX",
        startBusinessDate="2024-01-01",
        endBusinessDate="2024-01-06",
    )
    pprint(comparison)

    print_section("8. Predict next ETHUSD close")
    prediction = predict_next_close(
        assetId="ETHUSD",
        dataSourceId="NASDAQ_DATA_LINK_BITFINEX",
        startBusinessDate="2024-01-01",
        endBusinessDate="2024-01-06",
    )
    pprint(prediction)

    print_section("9. Summarize Nasdaq Data Link activity for AAPL")
    activity_summary = summarize_activity(
        assetId="AAPL_NASDAQ",
        dataSourceId="NASDAQ_DATA_LINK_RTAT10",
        startBusinessDate="2024-03-25",
        endBusinessDate="2024-03-29",
    )
    pprint(activity_summary)

    print_section("10. List persisted analytics summaries")
    persisted_summaries = list_persisted_summaries(limit=5)
    pprint(persisted_summaries)

    print_section("11. List persisted predictions")
    persisted_predictions = list_persisted_predictions(limit=5)
    pprint(persisted_predictions)


if __name__ == "__main__":
    run_demo_workflow()