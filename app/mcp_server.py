import os
from typing import Any, Dict

import requests
from mcp.server.fastmcp import FastMCP


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")

mcp = FastMCP("financial-dwh-assistant")


def api_get(path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    url = f"{API_BASE_URL}{path}"

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as error:
        return {
            "error": "http_error",
            "statusCode": response.status_code,
            "details": response.text,
            "url": url,
            "params": params,
        }
    except requests.RequestException as error:
        return {
            "error": "request_failed",
            "details": str(error),
            "url": url,
            "params": params,
        }


@mcp.tool()
def list_assets(offset: int = 0, limit: int = 20) -> Dict[str, Any]:
    """
    List financial assets available in the warehouse.

    Returns a paginated list of latest non-deleted asset versions.
    """
    return api_get(
        "/assets",
        params={
            "offset": offset,
            "limit": limit,
        },
    )


@mcp.tool()
def get_asset_details(assetId: str) -> Dict[str, Any]:
    """
    Get the latest visible details for one financial asset.

    Use this when the user asks about a specific asset identifier such as BTCUSD or ETHUSD.
    """
    return api_get(f"/assets/{assetId}")


@mcp.tool()
def list_data_sources(offset: int = 0, limit: int = 20) -> Dict[str, Any]:
    """
    List financial data sources available in the warehouse.

    Returns a paginated list of latest non-deleted data source versions.
    """
    return api_get(
        "/data-sources",
        params={
            "offset": offset,
            "limit": limit,
        },
    )


@mcp.tool()
def get_data_source_details(dataSourceId: str) -> Dict[str, Any]:
    """
    Get details for a data source, including provider, dataset, and supported attributes.
    """
    return api_get(f"/data-sources/{dataSourceId}")


@mcp.tool()
def get_time_series_data(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: str,
    endBusinessDate: str,
    includeAttributes: bool = True,
    asOfSystemTime: str | None = None,
) -> Dict[str, Any]:
    """
    Retrieve time-series data for one asset and one data source.

    Dates must use YYYY-MM-DD format.
    The interval is start-inclusive and end-exclusive.
    Results use the latest temporal version per business date.

    Optional asOfSystemTime lets the assistant ask what the warehouse knew
    at a specific historical system time, for example:
    2026-05-30T17:10:00
    """
    params = {
        "assetId": assetId,
        "dataSourceId": dataSourceId,
        "startBusinessDate": startBusinessDate,
        "endBusinessDate": endBusinessDate,
        "includeAttributes": includeAttributes,
    }

    if asOfSystemTime:
        params["asOfSystemTime"] = asOfSystemTime

    return api_get(
        "/data",
        params=params,
    )


@mcp.tool()
def summarize_asset(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: str,
    endBusinessDate: str,
) -> Dict[str, Any]:
    """
    Compute a summary for one asset over a bounded date interval.

    Returns record count, min/max/average close, first/last close, percentage change,
    volume statistics, and trend.
    """
    return api_get(
        "/analytics/summary",
        params={
            "assetId": assetId,
            "dataSourceId": dataSourceId,
            "startBusinessDate": startBusinessDate,
            "endBusinessDate": endBusinessDate,
        },
    )


@mcp.tool()
def compare_assets(
    assetId1: str,
    assetId2: str,
    dataSourceId: str,
    startBusinessDate: str,
    endBusinessDate: str,
) -> Dict[str, Any]:
    """
    Compare two assets over the same bounded date interval.

    Returns both summaries and identifies the stronger performer by percentage change.
    """
    return api_get(
        "/analytics/compare",
        params={
            "assetId1": assetId1,
            "assetId2": assetId2,
            "dataSourceId": dataSourceId,
            "startBusinessDate": startBusinessDate,
            "endBusinessDate": endBusinessDate,
        },
    )


@mcp.tool()
def predict_next_close(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: str,
    endBusinessDate: str,
) -> Dict[str, Any]:
    """
    Predict the next close price using the average daily close-price change.

    This is a simple warehouse-grounded forecast based only on stored time-series records.
    """
    return api_get(
        "/analytics/predict-next",
        params={
            "assetId": assetId,
            "dataSourceId": dataSourceId,
            "startBusinessDate": startBusinessDate,
            "endBusinessDate": endBusinessDate,
        },
    )

@mcp.tool()
def summarize_activity(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: str,
    endBusinessDate: str,
) -> Dict[str, Any]:
    """
    Compute an activity summary for Nasdaq RTAT10 activity data.

    Use this for assets such as AAPL_NASDAQ, MSFT_NASDAQ, TSLA_NASDAQ,
    and GOOGL_NASDAQ with dataSourceId NASDAQ_DATA_LINK_RTAT10.
    Dates must use YYYY-MM-DD format.
    """
    return api_get(
        "/analytics/activity-summary",
        params={
            "assetId": assetId,
            "dataSourceId": dataSourceId,
            "startBusinessDate": startBusinessDate,
            "endBusinessDate": endBusinessDate,
        },
    )

@mcp.tool()
def list_persisted_summaries(
    assetId: str | None = None,
    dataSourceId: str | None = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    List persisted analytics summaries.

    This includes on-demand persisted summaries and batch analytics results,
    such as yearly_close_summary and yearly_activity_summary.
    """
    params = {
        "limit": limit,
    }

    if assetId:
        params["assetId"] = assetId

    if dataSourceId:
        params["dataSourceId"] = dataSourceId

    return api_get(
        "/analytics/summary/results",
        params=params,
    )

@mcp.tool()
def list_persisted_predictions(
    assetId: str | None = None,
    dataSourceId: str | None = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    List persisted prediction results.

    This returns predictions saved into MongoDB by the prediction persistence endpoint.
    """
    params = {
        "limit": limit,
    }

    if assetId:
        params["assetId"] = assetId

    if dataSourceId:
        params["dataSourceId"] = dataSourceId

    return api_get(
        "/analytics/prediction/results",
        params=params,
    )


if __name__ == "__main__":
    mcp.run()