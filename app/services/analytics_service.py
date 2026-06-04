from datetime import date
from statistics import mean

from app.repositories.time_series_repository import TimeSeriesRepository


class AnalyticsService:
    def __init__(self):
        self.time_series_repository = TimeSeriesRepository()

    def summarize_asset(
        self,
        asset_id: str,
        data_source_id: str,
        start_business_date: date,
        end_business_date: date,
    ) -> dict:
        records = self.time_series_repository.find_latest_range(
            asset_id=asset_id,
            data_source_id=data_source_id,
            start_business_date=start_business_date,
            end_business_date=end_business_date,
        )

        if not records:
            return {
                "assetId": asset_id,
                "dataSourceId": data_source_id,
                "startBusinessDate": str(start_business_date),
                "endBusinessDate": str(end_business_date),
                "recordCount": 0,
                "message": "No records found for the selected interval."
            }

        # Records are returned newest first, so reverse them for trend calculations.
        chronological_records = list(reversed(records))

        closes = [
            record["values"]["close"]
            for record in chronological_records
            if "close" in record.get("values", {})
        ]

        volumes = [
            record["values"]["volume"]
            for record in chronological_records
            if "volume" in record.get("values", {})
        ]

        if not closes:
            return {
                "assetId": asset_id,
                "dataSourceId": data_source_id,
                "startBusinessDate": str(start_business_date),
                "endBusinessDate": str(end_business_date),
                "recordCount": len(records),
                "message": "Records found, but no close values are available."
            }

        first_close = closes[0]
        last_close = closes[-1]

        absolute_change = last_close - first_close
        percentage_change = (
            (absolute_change / first_close) * 100
            if first_close != 0
            else None
        )

        if percentage_change is None:
            trend = "unknown"
        elif percentage_change > 1:
            trend = "upward"
        elif percentage_change < -1:
            trend = "downward"
        else:
            trend = "stable"

        return {
            "assetId": asset_id,
            "dataSourceId": data_source_id,
            "startBusinessDate": str(start_business_date),
            "endBusinessDate": str(end_business_date),
            "recordCount": len(records),
            "minClose": min(closes),
            "maxClose": max(closes),
            "avgClose": round(mean(closes), 2),
            "firstClose": first_close,
            "lastClose": last_close,
            "absoluteChange": round(absolute_change, 2),
            "percentageChange": round(percentage_change, 2) if percentage_change is not None else None,
            "minVolume": min(volumes) if volumes else None,
            "maxVolume": max(volumes) if volumes else None,
            "avgVolume": round(mean(volumes), 2) if volumes else None,
            "trend": trend
        }
    
    def compare_assets(
        self,
        asset_id_1: str,
        asset_id_2: str,
        data_source_id: str,
        start_business_date: date,
        end_business_date: date,
    ) -> dict:
        summary_1 = self.summarize_asset(
            asset_id=asset_id_1,
            data_source_id=data_source_id,
            start_business_date=start_business_date,
            end_business_date=end_business_date,
        )

        summary_2 = self.summarize_asset(
            asset_id=asset_id_2,
            data_source_id=data_source_id,
            start_business_date=start_business_date,
            end_business_date=end_business_date,
        )

        change_1 = summary_1.get("percentageChange")
        change_2 = summary_2.get("percentageChange")

        if change_1 is None or change_2 is None:
            winner = None
            explanation = "Comparison cannot determine a stronger performer because one asset has missing percentage change data."
        elif change_1 > change_2:
            winner = asset_id_1
            explanation = f"{asset_id_1} had the stronger percentage change."
        elif change_2 > change_1:
            winner = asset_id_2
            explanation = f"{asset_id_2} had the stronger percentage change."
        else:
            winner = "tie"
            explanation = "Both assets had the same percentage change."

        return {
            "assetId1": asset_id_1,
            "assetId2": asset_id_2,
            "dataSourceId": data_source_id,
            "startBusinessDate": str(start_business_date),
            "endBusinessDate": str(end_business_date),
            "asset1Summary": summary_1,
            "asset2Summary": summary_2,
            "strongerPerformer": winner,
            "explanation": explanation
        }
    
    def predict_next_close(
        self,
        asset_id: str,
        data_source_id: str,
        start_business_date: date,
        end_business_date: date,
    ) -> dict:
        records = self.time_series_repository.find_latest_range(
            asset_id=asset_id,
            data_source_id=data_source_id,
            start_business_date=start_business_date,
            end_business_date=end_business_date,
        )

        if len(records) < 2:
            return {
                "assetId": asset_id,
                "dataSourceId": data_source_id,
                "startBusinessDate": str(start_business_date),
                "endBusinessDate": str(end_business_date),
                "message": "At least two records are required to make a prediction."
            }

        # Records are returned newest first, so reverse to oldest -> newest.
        chronological_records = list(reversed(records))

        closes = [
            record["values"]["close"]
            for record in chronological_records
            if "close" in record.get("values", {})
        ]

        if len(closes) < 2:
            return {
                "assetId": asset_id,
                "dataSourceId": data_source_id,
                "startBusinessDate": str(start_business_date),
                "endBusinessDate": str(end_business_date),
                "message": "At least two close values are required to make a prediction."
            }

        daily_changes = [
            closes[i] - closes[i - 1]
            for i in range(1, len(closes))
        ]

        average_daily_change = mean(daily_changes)
        last_close = closes[-1]
        predicted_next_close = last_close + average_daily_change

        if average_daily_change > 0:
            signal = "positive"
        elif average_daily_change < 0:
            signal = "negative"
        else:
            signal = "neutral"

        return {
            "assetId": asset_id,
            "dataSourceId": data_source_id,
            "startBusinessDate": str(start_business_date),
            "endBusinessDate": str(end_business_date),
            "model": "average_daily_close_change",
            "recordCount": len(closes),
            "lastClose": round(last_close, 2),
            "averageDailyChange": round(average_daily_change, 2),
            "predictedNextClose": round(predicted_next_close, 2),
            "signal": signal,
            "explanation": (
                "Prediction is computed by adding the average daily close-price change "
                "from the selected interval to the latest close price."
            )
        }
    
    def summarize_activity(
        self,
        asset_id: str,
        data_source_id: str,
        start_business_date: date,
        end_business_date: date,
    ) -> dict:
        records = self.time_series_repository.find_latest_range(
            asset_id=asset_id,
            data_source_id=data_source_id,
            start_business_date=start_business_date,
            end_business_date=end_business_date,
        )

        if not records:
            return {
                "assetId": asset_id,
                "dataSourceId": data_source_id,
                "startBusinessDate": str(start_business_date),
                "endBusinessDate": str(end_business_date),
                "recordCount": 0,
                "message": "No records found for the selected interval."
            }

        # Records are returned newest first, so reverse for trend calculations.
        chronological_records = list(reversed(records))

        activity_values = [
            record["values"]["activity"]
            for record in chronological_records
            if "activity" in record.get("values", {})
        ]

        if not activity_values:
            return {
                "assetId": asset_id,
                "dataSourceId": data_source_id,
                "startBusinessDate": str(start_business_date),
                "endBusinessDate": str(end_business_date),
                "recordCount": len(records),
                "message": "Records found, but no activity values are available."
            }

        first_activity = activity_values[0]
        last_activity = activity_values[-1]

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

        return {
            "assetId": asset_id,
            "dataSourceId": data_source_id,
            "startBusinessDate": str(start_business_date),
            "endBusinessDate": str(end_business_date),
            "metric": "activity",
            "recordCount": len(activity_values),
            "minActivity": min(activity_values),
            "maxActivity": max(activity_values),
            "avgActivity": round(mean(activity_values), 6),
            "firstActivity": first_activity,
            "lastActivity": last_activity,
            "absoluteChange": round(absolute_change, 6),
            "percentageChange": round(percentage_change, 2) if percentage_change is not None else None,
            "trend": trend,
            "explanation": (
                "Activity summary is computed from Nasdaq Data Link RTAT10 "
                "retail trading activity values stored in the warehouse."
            )
        }