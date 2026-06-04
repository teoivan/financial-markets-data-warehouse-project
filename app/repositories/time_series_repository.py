from datetime import datetime, timezone
from typing import List

from app.database import time_series_collection
from app.models.time_series import TimeSeriesCreate


class TimeSeriesRepository:
    def save(self, record: TimeSeriesCreate) -> dict:
        document = record.model_dump()
        document["businessDate"] = str(document["businessDate"])
        document["businessYear"] = int(document["businessDate"][:4])
        document["systemTime"] = datetime.now(timezone.utc)
        document["deleted"] = False

        time_series_collection.insert_one(document)

        document["_id"] = str(document["_id"])
        return document

    def find_latest_range(
        self,
        asset_id: str,
        data_source_id: str,
        start_business_date,
        end_business_date,
        as_of_system_time=None,
    ) -> List[dict]:
        start_business_date = str(start_business_date)
        end_business_date = str(end_business_date)

        match_stage = {
            "assetId": asset_id,
            "dataSourceId": data_source_id,
            "businessDate": {
                "$gte": start_business_date,
                "$lt": end_business_date,
            },
        }

        if as_of_system_time is not None:
            match_stage["systemTime"] = {
                "$lte": as_of_system_time,
            }

        pipeline = [
            {"$match": match_stage},
            {
                "$sort": {
                    "businessDate": -1,
                    "systemTime": -1,
                }
            },
            {
                "$group": {
                    "_id": "$businessDate",
                    "latest": {"$first": "$$ROOT"},
                }
            },
            {"$replaceRoot": {"newRoot": "$latest"}},
            {"$match": {"deleted": False}},
            {"$sort": {"businessDate": -1}},
        ]

        results = list(time_series_collection.aggregate(pipeline))

        for item in results:
            item["_id"] = str(item["_id"])

        return results

    def find_all_latest(self, offset: int = 0, limit: int = 20) -> List[dict]:
        pipeline = [
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
            {"$sort": {"assetId": 1, "dataSourceId": 1, "businessDate": -1}},
            {"$skip": offset},
            {"$limit": limit},
        ]

        results = list(time_series_collection.aggregate(pipeline))

        for item in results:
            item["_id"] = str(item["_id"])

        return results