from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import db_models, schemas

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/start", response_model=schemas.SessionOut)
def start_session(payload: schemas.SessionCreate, db: Session = Depends(get_db)):
    session = db_models.NavSession(device_id=payload.device_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
