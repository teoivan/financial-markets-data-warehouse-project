from fastapi import FastAPI

from app.database import create_indexes
from app.api.assets import router as assets_router
from app.api.data_sources import router as data_sources_router
from app.api.time_series import router as time_series_router
from app.api.analytics import router as analytics_router

app = FastAPI(
    title="Financial Markets Data Warehouse",
    description="Temporal NoSQL data warehouse for financial markets data",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    create_indexes()


app.include_router(assets_router, prefix="/api/v1")
app.include_router(data_sources_router, prefix="/api/v1")
app.include_router(time_series_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "Financial Markets Data Warehouse"
    }