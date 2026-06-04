from collections import defaultdict
from datetime import datetime, timezone

from app.database import time_series_collection, analytics_summaries_collection


def build_latest_records_pipeline():
    """
    Returns only the latest temporal version for each:
    assetId + dataSourceId + businessDate.
    """
    return [
        {
            "$sort": {
                "assetId": 1,
                "dataSourceId": 1,
                "businessDate": 1,
                "systemTime": -1,
            }
        },
        {
            "$group": {
                "_id": {
                    "assetId": "$assetId",
                    "dataSourceId": "$dataSourceId",
                    "businessDate": "$businessDate",
                },
                "latest": {"$first": "$$ROOT"},
            }
        },
        {"$replaceRoot": {"newRoot": "$latest"}},
        {"$match": {"deleted": False}},
    ]


def compute_yearly_close_summaries():
    latest_records = list(
        time_series_collection.aggregate(build_latest_records_pipeline())
    )

    grouped = defaultdict(list)

    for record in latest_records:
        values = record.get("values", {})

        # This job is specifically for OHLCV close-price data.
        # Nasdaq RTAT10 activity records are handled by the activity summary endpoint.
        if "close" not in values:
            continue

        asset_id = record["assetId"]
        data_source_id = record["dataSourceId"]
        business_year = record.get("businessYear")

        key = (asset_id, data_source_id, business_year)
        grouped[key].append(record)

    results = []

    for (asset_id, data_source_id, business_year), records in grouped.items():
        closes = [record["values"]["close"] for record in records]
        volumes = [
            record["values"]["volume"]
            for record in records
            if "volume" in record.get("values", {})
        ]

        summary = {
            "assetId": asset_id,
            "dataSourceId": data_source_id,
            "businessYear": business_year,
            "recordCount": len(records),
            "minClose": min(closes),
            "maxClose": max(closes),
            "avgClose": round(sum(closes) / len(closes), 2),
            "minVolume": min(volumes) if volumes else None,
            "maxVolume": max(volumes) if volumes else None,
            "avgVolume": round(sum(volumes) / len(volumes), 2) if volumes else None,
            "computedAt": datetime.now(timezone.utc),
            "computedBy": "batch_yearly_aggregation_job",
            "resultType": "yearly_close_summary",
        }

        analytics_summaries_collection.insert_one(summary)
        summary["_id"] = str(summary["_id"])
        results.append(summary)

    return {
        "jobType": "yearly_close_aggregation",
        "sourceCollection": "time_series",
        "targetCollection": "analytics_summaries",
        "groupsComputed": len(results),
        "results": results,
    }


if __name__ == "__main__":
    result = compute_yearly_close_summaries()
    print(result)