from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class AssetCreate(BaseModel):
    assetId: str
    symbol: str
    name: str
    assetClass: str
    region: str
    description: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Asset(BaseModel):
    assetId: str
    symbol: str
    name: str
    assetClass: str
    region: str
    description: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    systemTime: datetime
    deleted: bool = False