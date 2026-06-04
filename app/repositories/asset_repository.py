from datetime import datetime, timezone
from typing import List, Optional

from app.database import assets_collection
from app.models.asset import AssetCreate


class AssetRepository:
    def save(self, asset: AssetCreate) -> dict:
        document = asset.model_dump()
        document["systemTime"] = datetime.now(timezone.utc)
        document["deleted"] = False

        assets_collection.insert_one(document)

        document["_id"] = str(document["_id"])
        return document

    def find_latest(self, asset_id: str) -> Optional[dict]:
        document = assets_collection.find_one(
            {"assetId": asset_id},
            sort=[("systemTime", -1)]
        )

        if not document or document.get("deleted") is True:
            return None

        document["_id"] = str(document["_id"])
        return document

    def find_all_latest(self, offset: int = 0, limit: int = 20) -> List[dict]:
        pipeline = [
            {"$sort": {"assetId": 1, "systemTime": -1}},
            {
                "$group": {
                    "_id": "$assetId",
                    "latest": {"$first": "$$ROOT"}
                }
            },
            {"$replaceRoot": {"newRoot": "$latest"}},
            {"$match": {"deleted": False}},
            {"$sort": {"assetId": 1}},
            {"$skip": offset},
            {"$limit": limit}
        ]

        results = list(assets_collection.aggregate(pipeline))

        for item in results:
            item["_id"] = str(item["_id"])

        return results

    def mark_deleted(self, asset_id: str) -> Optional[dict]:
        return self.deactivate(
            asset_id=asset_id,
            reason="Asset marked as deleted"
        )

    def deactivate(self, asset_id: str, reason: str | None = None) -> Optional[dict]:
        latest_asset = self.find_latest(asset_id)

        if latest_asset is None:
            return None

        latest_asset.pop("_id", None)

        latest_asset["systemTime"] = datetime.now(timezone.utc)
        latest_asset["deleted"] = True
        latest_asset["deletionReason"] = reason or "Asset deactivated"

        latest_asset["attributes"] = latest_asset.get("attributes", {})
        latest_asset["attributes"]["deactivationType"] = "temporal_marker"

        result = assets_collection.insert_one(latest_asset)

        latest_asset["_id"] = str(result.inserted_id)
        return latest_asset