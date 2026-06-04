from fastapi import APIRouter, HTTPException, Query

from app.models.data_source import DataSourceCreate
from app.repositories.data_source_repository import DataSourceRepository

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])

repository = DataSourceRepository()


@router.post("")
def create_data_source(data_source: DataSourceCreate):
    return repository.save(data_source)


@router.get("")
def list_data_sources(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    return {
        "offset": offset,
        "limit": limit,
        "data": repository.find_all_latest(offset, limit)
    }


@router.get("/{data_source_id}")
def get_data_source(data_source_id: str):
    data_source = repository.find_latest(data_source_id)

    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    return data_source

@router.post("/{dataSourceId}/deactivate")
def deactivate_data_source(dataSourceId: str, reason: str | None = None):
    deactivated_data_source = DataSourceRepository().deactivate(
        data_source_id=dataSourceId,
        reason=reason,
    )

    if not deactivated_data_source:
        raise HTTPException(
            status_code=404,
            detail=f"Data source {dataSourceId} not found"
        )

    return {
        "message": "Data source deactivated using temporal marker. No record was physically deleted.",
        "data": deactivated_data_source
    }