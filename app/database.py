from pymongo import MongoClient, ASCENDING, DESCENDING
from app.config import MONGO_URI, DATABASE_NAME

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

assets_collection = db["assets"]
data_sources_collection = db["data_sources"]
time_series_collection = db["time_series"]
analytics_summaries_collection = db["analytics_summaries"]
prediction_results_collection = db["prediction_results"]


def create_indexes():
    assets_collection.create_index(
        [("assetId", ASCENDING), ("systemTime", DESCENDING)]
    )

    data_sources_collection.create_index(
        [("dataSourceId", ASCENDING), ("systemTime", DESCENDING)]
    )

    time_series_collection.create_index(
        [
            ("assetId", ASCENDING),
            ("dataSourceId", ASCENDING),
            ("businessDate", DESCENDING),
            ("systemTime", DESCENDING),
        ]
    )

    analytics_summaries_collection.create_index(
        [
            ("assetId", ASCENDING),
            ("dataSourceId", ASCENDING),
            ("computedAt", DESCENDING),
        ]
    )

    prediction_results_collection.create_index(
        [
            ("assetId", ASCENDING),
            ("dataSourceId", ASCENDING),
            ("computedAt", DESCENDING),
        ]
    )