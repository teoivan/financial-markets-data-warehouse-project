from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import date, datetime


class TimeSeriesCreate(BaseModel):
    assetId: str
    dataSourceId: str
    businessDate: date
    values: Dict[str, float] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class TimeSeriesRecord(BaseModel):
    assetId: str
    dataSourceId: str
    businessDate: date
    businessYear: int
    values: Dict[str, float] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    systemTime: datetime
    deleted: bool = False