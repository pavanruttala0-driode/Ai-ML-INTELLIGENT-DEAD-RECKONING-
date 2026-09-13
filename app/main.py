from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.session import Base, engine
from app.routers import session, sensor, position

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(sensor.router)
app.include_router(position.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
