from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.services.analytics_service import AnalyticsService

from app.repositories.analytics_repository import AnalyticsRepository

router = APIRouter(prefix="/analytics", tags=["Analytics"])

analytics_repository = AnalyticsRepository()

analytics_service = AnalyticsService()


@router.get("/summary")
def get_asset_summary(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: date,
    endBusinessDate: date,
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

    return analytics_service.summarize_asset(
        asset_id=assetId,
        data_source_id=dataSourceId,
        start_business_date=startBusinessDate,
        end_business_date=endBusinessDate,
    )

@router.get("/compare")
def compare_assets(
    assetId1: str,
    assetId2: str,
    dataSourceId: str,
    startBusinessDate: date,
    endBusinessDate: date,
):
    if assetId1 == assetId2:
        raise HTTPException(
            status_code=400,
            detail="assetId1 and assetId2 must be different"
        )

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

    return analytics_service.compare_assets(
        asset_id_1=assetId1,
        asset_id_2=assetId2,
        data_source_id=dataSourceId,
        start_business_date=startBusinessDate,
        end_business_date=endBusinessDate,
    )

@router.get("/predict-next")
def predict_next_close(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: date,
    endBusinessDate: date,
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

    return analytics_service.predict_next_close(
        asset_id=assetId,
        data_source_id=dataSourceId,
        start_business_date=startBusinessDate,
        end_business_date=endBusinessDate,
    )

@router.post("/summary/persist")
def compute_and_persist_summary(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: date,
    endBusinessDate: date,
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

    summary = analytics_service.summarize_asset(
        asset_id=assetId,
        data_source_id=dataSourceId,
        start_business_date=startBusinessDate,
        end_business_date=endBusinessDate,
    )

    saved = analytics_repository.save_summary(summary)

    return {
        "message": "Analytics summary computed and persisted.",
        "result": saved
    }


@router.post("/predict-next/persist")
def compute_and_persist_prediction(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: date,
    endBusinessDate: date,
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

    prediction = analytics_service.predict_next_close(
        asset_id=assetId,
        data_source_id=dataSourceId,
        start_business_date=startBusinessDate,
        end_business_date=endBusinessDate,
    )

    saved = analytics_repository.save_prediction(prediction)

    return {
        "message": "Prediction computed and persisted.",
        "result": saved
    }


@router.get("/summary/results")
def list_persisted_summaries(
    assetId: str | None = None,
    dataSourceId: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    return {
        "limit": limit,
        "data": analytics_repository.find_latest_summaries(
            asset_id=assetId,
            data_source_id=dataSourceId,
            limit=limit,
        )
    }


@router.get("/prediction/results")
def list_persisted_predictions(
    assetId: str | None = None,
    dataSourceId: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    return {
        "limit": limit,
        "data": analytics_repository.find_latest_predictions(
            asset_id=assetId,
            data_source_id=dataSourceId,
            limit=limit,
        )
    }

@router.get("/activity-summary")
def get_activity_summary(
    assetId: str,
    dataSourceId: str,
    startBusinessDate: date,
    endBusinessDate: date,
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

    return analytics_service.summarize_activity(
        asset_id=assetId,
        data_source_id=dataSourceId,
        start_business_date=startBusinessDate,
        end_business_date=endBusinessDate,
    )