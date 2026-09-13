from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import db_models, schemas
from app.ml.kalman_filter import DeadReckoningEKF
from app.ml.drift_corrector import AIMotionEstimator, AdaptiveErrorModel, ImuSample

router = APIRouter(prefix="/sensor", tags=["sensor"])

_active_filters: dict[str, DeadReckoningEKF] = {}
_last_timestamp: dict[str, datetime] = {}

estimator = AIMotionEstimator()
error_model = AdaptiveErrorModel()


@router.post("/ingest")
def ingest_batch(payload: schemas.SensorBatchIn, db: Session = Depends(get_db)):
    session_id = str(payload.session_id)

    session = db.query(db_models.NavSession).filter_by(id=payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    results = []

    for reading in payload.readings:
        db.add(db_models.SensorReading(
            session_id=payload.session_id,
            timestamp=reading.timestamp,
            accel_x=reading.accel_x, accel_y=reading.accel_y, accel_z=reading.accel_z,
            gyro_x=reading.gyro_x, gyro_y=reading.gyro_y, gyro_z=reading.gyro_z,
            gnss_lat=reading.gnss_lat, gnss_lng=reading.gnss_lng,
            gnss_available=reading.gnss_available,
        ))

        if session_id not in _active_filters:
            if not reading.gnss_available:
                continue
            _active_filters[session_id] = DeadReckoningEKF(reading.gnss_lat, reading.gnss_lng)
            _last_timestamp[session_id] = reading.timestamp
            continue

        ekf = _active_filters[session_id]
        dt = (reading.timestamp - _last_timestamp[session_id]).total_seconds()
        dt = max(dt, 1e-3)
        _last_timestamp[session_id] = reading.timestamp

        heading_rad = 0.0
        sample = ImuSample(
            accel_x=reading.accel_x, accel_y=reading.accel_y, accel_z=reading.accel_z,
            gyro_x=reading.gyro_x, gyro_y=reading.gyro_y, gyro_z=reading.gyro_z,
        )
        motion = estimator.estimate([sample], heading_rad)
        q_scale = error_model.adjust(motion)
        ekf.Q *= q_scale

        raw_lat_before, raw_lng_before = ekf.position()
        ekf.predict(dt, motion.accel_north, motion.accel_east)
        raw_dr_lat, raw_dr_lng = ekf.position()

        if reading.gnss_available and reading.gnss_lat is not None:
            ekf.update_gnss(reading.gnss_lat, reading.gnss_lng)

        corrected_lat, corrected_lng = ekf.position()

        estimate = db_models.PositionEstimate(
            session_id=payload.session_id,
            timestamp=reading.timestamp,
            raw_dr_lat=raw_dr_lat, raw_dr_lng=raw_dr_lng,
            corrected_lat=corrected_lat, corrected_lng=corrected_lng,
            confidence=ekf.confidence(),
            drift_estimate_m=ekf.drift_estimate_m(),
            gnss_available=reading.gnss_available,
        )
        db.add(estimate)
        results.append(estimate)

    db.commit()
    return {"processed": len(payload.readings), "positions": len(results)}
