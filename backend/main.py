import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv

from database import engine, Base, get_db
import models  # garante que os models são registrados antes do create_all
from routers import empresa, socio
import crud

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        crud._load_cache(db)
        crud._get_mes_atual(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Busca CNPJ", version="1.0.0", lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=500)

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(empresa.router)
app.include_router(socio.router)


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/v1/info")
def info(db: Session = Depends(get_db)):
    return {"mes_atual": crud._get_mes_atual(db)}
