from datetime import datetime, timezone
from typing import List

from app.database import analytics_summaries_collection, prediction_results_collection


class AnalyticsRepository:
    def save_summary(self, summary: dict) -> dict:
        document = dict(summary)
        document["computedAt"] = datetime.now(timezone.utc)
        document["resultType"] = "summary"

        analytics_summaries_collection.insert_one(document)

        document["_id"] = str(document["_id"])
        return document

    def save_prediction(self, prediction: dict) -> dict:
        document = dict(prediction)
        document["computedAt"] = datetime.now(timezone.utc)
        document["resultType"] = "prediction"

        prediction_results_collection.insert_one(document)

        document["_id"] = str(document["_id"])
        return document

    def find_latest_summaries(
        self,
        asset_id: str | None = None,
        data_source_id: str | None = None,
        limit: int = 20,
    ) -> List[dict]:
        query = {}

        if asset_id:
            query["assetId"] = asset_id

        if data_source_id:
            query["dataSourceId"] = data_source_id

        results = list(
            analytics_summaries_collection
            .find(query)
            .sort("computedAt", -1)
            .limit(limit)
        )

        for item in results:
            item["_id"] = str(item["_id"])

        return results

    def find_latest_predictions(
        self,
        asset_id: str | None = None,
        data_source_id: str | None = None,
        limit: int = 20,
    ) -> List[dict]:
        query = {}

        if asset_id:
            query["assetId"] = asset_id

        if data_source_id:
            query["dataSourceId"] = data_source_id

        results = list(
            prediction_results_collection
            .find(query)
            .sort("computedAt", -1)
            .limit(limit)
        )

        for item in results:
            item["_id"] = str(item["_id"])

        return results