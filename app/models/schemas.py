from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class SessionCreate(BaseModel):
    device_id: str


class SessionOut(BaseModel):
    id: UUID
    device_id: str
    start_time: datetime

    class Config:
        from_attributes = True


class SensorReadingIn(BaseModel):
    timestamp: datetime
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    gnss_lat: Optional[float] = None
    gnss_lng: Optional[float] = None
    gnss_available: bool = False


class SensorBatchIn(BaseModel):
    session_id: UUID
    readings: List[SensorReadingIn]


class PositionOut(BaseModel):
    timestamp: datetime
    raw_dr_lat: float
    raw_dr_lng: float
    corrected_lat: float
    corrected_lng: float
    confidence: float
    drift_estimate_m: float
    gnss_available: bool

    class Config:
        from_attributes = True


class PathOut(BaseModel):
    session_id: UUID
    points: List[PositionOut]
