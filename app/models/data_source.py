from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class DataSourceCreate(BaseModel):
    dataSourceId: str
    provider: str
    dataset: str
    description: Optional[str] = None
    apiEndpoint: Optional[str] = None
    supportedAttributes: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class DataSource(BaseModel):
    dataSourceId: str
    provider: str
    dataset: str
    description: Optional[str] = None
    apiEndpoint: Optional[str] = None
    supportedAttributes: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    systemTime: datetime
    deleted: bool = False