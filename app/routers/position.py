import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.models import db_models, schemas

router = APIRouter(tags=["position"])


@router.get("/position/current/{session_id}", response_model=schemas.PositionOut)
def get_current_position(session_id: UUID, db: Session = Depends(get_db)):
    latest = (
        db.query(db_models.PositionEstimate)
        .filter_by(session_id=session_id)
        .order_by(db_models.PositionEstimate.timestamp.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No position data yet for this session")
    return latest


@router.get("/session/{session_id}/path", response_model=schemas.PathOut)
def get_path(session_id: UUID, db: Session = Depends(get_db)):
    points = (
        db.query(db_models.PositionEstimate)
        .filter_by(session_id=session_id)
        .order_by(db_models.PositionEstimate.timestamp.asc())
        .all()
    )
    return {"session_id": session_id, "points": points}


@router.websocket("/position/stream/{session_id}")
async def stream_position(websocket: WebSocket, session_id: UUID):
    await websocket.accept()
    last_seen_ts = None
    try:
        while True:
            db = SessionLocal()
            try:
                query = db.query(db_models.PositionEstimate).filter_by(session_id=session_id)
                if last_seen_ts:
                    query = query.filter(db_models.PositionEstimate.timestamp > last_seen_ts)
                new_points = query.order_by(db_models.PositionEstimate.timestamp.asc()).all()

                for point in new_points:
                    await websocket.send_json({
                        "timestamp": point.timestamp.isoformat(),
                        "corrected_lat": point.corrected_lat,
                        "corrected_lng": point.corrected_lng,
                        "confidence": point.confidence,
                        "drift_estimate_m": point.drift_estimate_m,
                        "gnss_available": point.gnss_available,
                    })
                    last_seen_ts = point.timestamp
            finally:
                db.close()

            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
