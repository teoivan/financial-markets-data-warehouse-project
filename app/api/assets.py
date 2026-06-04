from fastapi import APIRouter, HTTPException, Query

from app.models.asset import AssetCreate
from app.repositories.asset_repository import AssetRepository

router = APIRouter(prefix="/assets", tags=["Assets"])

repository = AssetRepository()


@router.post("")
def create_asset(asset: AssetCreate):
    return repository.save(asset)


@router.get("")
def list_assets(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    return {
        "offset": offset,
        "limit": limit,
        "data": repository.find_all_latest(offset, limit)
    }


@router.get("/{asset_id}")
def get_asset(asset_id: str):
    asset = repository.find_latest(asset_id)

    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    return asset


@router.delete("/{asset_id}")
def delete_asset(asset_id: str):
    deleted = repository.mark_deleted(asset_id)

    if deleted is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {
        "message": "Asset marked as deleted using temporal marker record",
        "asset": deleted
    }

@router.post("/{assetId}/deactivate")
def deactivate_asset(assetId: str, reason: str | None = None):
    deactivated_asset = AssetRepository().deactivate(
        asset_id=assetId,
        reason=reason,
    )

    if not deactivated_asset:
        raise HTTPException(
            status_code=404,
            detail=f"Asset {assetId} not found"
        )

    return {
        "message": "Asset deactivated using temporal marker. No record was physically deleted.",
        "data": deactivated_asset
    }