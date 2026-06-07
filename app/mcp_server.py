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
    return api_get(
        "/assets",
        params={
            "offset": offset,
            "limit": limit,
        },
    )


@mcp.tool()
def get_asset_details(assetId: str) -> Dict[str, Any]:
    return api_get(f"/assets/{assetId}")


@mcp.tool()
def list_data_sources(offset: int = 0, limit: int = 20) -> Dict[str, Any]:
    return api_get(
        "/data-sources",
        params={
            "offset": offset,
            "limit": limit,
        },
    )


@mcp.tool()
def get_data_source_details(dataSourceId: str) -> Dict[str, Any]:
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