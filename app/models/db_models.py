import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class NavSession(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)

    accel_x = Column(Float)
    accel_y = Column(Float)
    accel_z = Column(Float)
    gyro_x = Column(Float)
    gyro_y = Column(Float)
    gyro_z = Column(Float)

    gnss_lat = Column(Float, nullable=True)
    gnss_lng = Column(Float, nullable=True)
    gnss_available = Column(Boolean, default=False)


class PositionEstimate(Base):
    __tablename__ = "position_estimates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)

    raw_dr_lat = Column(Float)
    raw_dr_lng = Column(Float)
    corrected_lat = Column(Float)
    corrected_lng = Column(Float)

    confidence = Column(Float)
    drift_estimate_m = Column(Float)
    gnss_available = Column(Boolean, default=False)
