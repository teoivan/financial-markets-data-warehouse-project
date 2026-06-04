from datetime import datetime, timezone
from typing import List, Optional

from app.database import data_sources_collection
from app.models.data_source import DataSourceCreate


class DataSourceRepository:
    def save(self, data_source: DataSourceCreate) -> dict:
        document = data_source.model_dump()
        document["systemTime"] = datetime.now(timezone.utc)
        document["deleted"] = False

        data_sources_collection.insert_one(document)

        document["_id"] = str(document["_id"])
        return document

    def find_latest(self, data_source_id: str) -> Optional[dict]:
        document = data_sources_collection.find_one(
            {"dataSourceId": data_source_id},
            sort=[("systemTime", -1)]
        )

        if not document or document.get("deleted") is True:
            return None

        document["_id"] = str(document["_id"])
        return document

    def find_all_latest(self, offset: int = 0, limit: int = 20) -> List[dict]:
        pipeline = [
            {"$sort": {"dataSourceId": 1, "systemTime": -1}},
            {
                "$group": {
                    "_id": "$dataSourceId",
                    "latest": {"$first": "$$ROOT"}
                }
            },
            {"$replaceRoot": {"newRoot": "$latest"}},
            {"$match": {"deleted": False}},
            {"$sort": {"dataSourceId": 1}},
            {"$skip": offset},
            {"$limit": limit}
        ]

        results = list(data_sources_collection.aggregate(pipeline))

        for item in results:
            item["_id"] = str(item["_id"])

        return results

    def mark_deleted(self, data_source_id: str) -> Optional[dict]:
        return self.deactivate(
            data_source_id=data_source_id,
            reason="Data source marked as deleted"
        )

    def deactivate(self, data_source_id: str, reason: str | None = None) -> Optional[dict]:
        latest_data_source = self.find_latest(data_source_id)

        if latest_data_source is None:
            return None

        latest_data_source.pop("_id", None)

        latest_data_source["systemTime"] = datetime.now(timezone.utc)
        latest_data_source["deleted"] = True
        latest_data_source["deletionReason"] = reason or "Data source deactivated"

        latest_data_source["attributes"] = latest_data_source.get("attributes", {})
        latest_data_source["attributes"]["deactivationType"] = "temporal_marker"

        result = data_sources_collection.insert_one(latest_data_source)

        latest_data_source["_id"] = str(result.inserted_id)
        return latest_data_source