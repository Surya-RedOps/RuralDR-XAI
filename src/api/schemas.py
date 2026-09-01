"""
API Request & Response Schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from ..core.contracts import ScreeningResult


class HealthResponse(BaseModel):
    status: str
    version: str
    device: str
    gpu_available: bool
    gpu_name: Optional[str] = None
    offline_mode: bool = True


class ScreeningApiResponse(BaseModel):
    success: bool
    result: ScreeningResult
    visual_urls: Dict[str, str] = {}
    message: str = "Screening analysis completed successfully."


class BatchSyncResponse(BaseModel):
    synced_count: int
    status: str
    timestamp: str
