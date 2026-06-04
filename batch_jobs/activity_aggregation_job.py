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


def compute_yearly_activity_summaries():
    latest_records = list(
        time_series_collection.aggregate(build_latest_records_pipeline())
    )

    grouped = defaultdict(list)

    for record in latest_records:
        values = record.get("values", {})

        # This job is specifically for Nasdaq RTAT10 activity data.
        if "activity" not in values:
            continue

        asset_id = record["assetId"]
        data_source_id = record["dataSourceId"]
        business_year = record.get("businessYear")

        key = (asset_id, data_source_id, business_year)
        grouped[key].append(record)

    results = []

    for (asset_id, data_source_id, business_year), records in grouped.items():
        activities = [record["values"]["activity"] for record in records]

        # Sort chronologically for first/last activity.
        chronological_records = sorted(
            records,
            key=lambda item: item["businessDate"]
        )

        first_activity = chronological_records[0]["values"]["activity"]
        last_activity = chronological_records[-1]["values"]["activity"]

        absolute_change = last_activity - first_activity
        percentage_change = (
            (absolute_change / first_activity) * 100
            if first_activity != 0
            else None
        )

        if percentage_change is None:
            trend = "unknown"
        elif percentage_change > 5:
            trend = "increasing"
        elif percentage_change < -5:
            trend = "decreasing"
        else:
            trend = "stable"

        summary = {
            "assetId": asset_id,
            "dataSourceId": data_source_id,
            "businessYear": business_year,
            "recordCount": len(records),
            "minActivity": min(activities),
            "maxActivity": max(activities),
            "avgActivity": round(sum(activities) / len(activities), 6),
            "firstActivity": first_activity,
            "lastActivity": last_activity,
            "absoluteChange": round(absolute_change, 6),
            "percentageChange": round(percentage_change, 2) if percentage_change is not None else None,
            "trend": trend,
            "computedAt": datetime.now(timezone.utc),
            "computedBy": "batch_activity_aggregation_job",
            "resultType": "yearly_activity_summary",
        }

        analytics_summaries_collection.insert_one(summary)
        summary["_id"] = str(summary["_id"])
        results.append(summary)

    return {
        "jobType": "yearly_activity_aggregation",
        "sourceCollection": "time_series",
        "targetCollection": "analytics_summaries",
        "groupsComputed": len(results),
        "results": results,
    }


if __name__ == "__main__":
    result = compute_yearly_activity_summaries()
    print(result)