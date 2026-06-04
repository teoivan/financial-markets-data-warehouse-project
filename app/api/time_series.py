from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query

from app.models.time_series import TimeSeriesCreate
from app.repositories.time_series_repository import TimeSeriesRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.data_source_repository import DataSourceRepository

router = APIRouter(prefix="/data", tags=["Time Series"])

repository = TimeSeriesRepository()
asset_repository = AssetRepository()
data_source_repository = DataSourceRepository()


@router.post("")
def create_time_series_record(record: TimeSeriesCreate):
    asset = asset_repository.find_latest(record.assetId)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    data_source = data_source_repository.find_latest(record.dataSourceId)
    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    return repository.save(record)


@router.get("")
def get_time_series_data(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: date,
    endBusinessDate: date,
    includeAttributes: bool = Query(False),
    asOfSystemTime: datetime | None = Query(None),
):
    if endBusinessDate <= startBusinessDate:
        raise HTTPException(
            status_code=400,
            detail="endBusinessDate must be after startBusinessDate"
        )

    interval_days = (endBusinessDate - startBusinessDate).days
    if interval_days > 366:
        raise HTTPException(
            status_code=400,
            detail="Date range too large. Maximum allowed interval is 366 days."
        )

    # Swagger may send timestamps with timezone, e.g. 2026-05-30T17:10:00Z.
    # PyMongo often returns/stores MongoDB datetimes as timezone-naive values.
    # This normalizes the input so MongoDB comparison works reliably.
    normalized_as_of_system_time = asOfSystemTime
    if normalized_as_of_system_time is not None and normalized_as_of_system_time.tzinfo is not None:
        normalized_as_of_system_time = normalized_as_of_system_time.replace(tzinfo=None)

    records = repository.find_latest_range(
        asset_id=assetId,
        data_source_id=dataSourceId,
        start_business_date=startBusinessDate,
        end_business_date=endBusinessDate,
        as_of_system_time=normalized_as_of_system_time,
    )

    response = {
        "data": {
            "assetId": assetId,
            "dataSourceId": dataSourceId,
            "startBusinessDate": str(startBusinessDate),
            "endBusinessDate": str(endBusinessDate),
            "asOfSystemTime": asOfSystemTime.isoformat() if asOfSystemTime else None,
            "records": records
        }
    }

    if includeAttributes:
        attributes = sorted({
            key
            for record in records
            for key in record.get("values", {}).keys()
        })
        response["attributes"] = attributes

    return response