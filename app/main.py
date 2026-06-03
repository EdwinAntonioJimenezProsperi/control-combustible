"""Aplicación FastAPI: API JSON + interfaz web para control de combustible."""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import COOLDOWN_DAYS, MAX_LITROS
from app.database import get_db, init_db

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Control de Compra de Combustible", version="1.0.0", lifespan=lifespan
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# ----------------------------- API JSON ----------------------------------- #


@app.post("/api/personas", response_model=schemas.PersonaOut, status_code=201)
def crear_persona(payload: schemas.PersonaCreate, db: Session = Depends(get_db)):
    try:
        return crud.registrar_persona(db, payload.carnet, payload.nombre)
    except crud.ReglaNegocioError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/personas", response_model=list[schemas.PersonaOut])
def get_personas(
    q: str | None = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return crud.listar_personas(db, q=q, limit=limit, offset=offset)


@app.get("/api/personas/{carnet}/estado", response_model=schemas.EstadoCarnet)
def get_estado(carnet: str, db: Session = Depends(get_db)):
    return crud.estado_carnet(db, carnet)


@app.post("/api/compras", response_model=schemas.CompraOut, status_code=201)
def crear_compra(payload: schemas.CompraCreate, db: Session = Depends(get_db)):
    if payload.litros > MAX_LITROS:
        raise HTTPException(
            status_code=422,
            detail=f"Los litros superan el máximo permitido ({MAX_LITROS}).",
        )
    try:
        return crud.registrar_compra(db, payload.carnet, payload.litros)
    except crud.ReglaNegocioError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/compras", response_model=list[schemas.CompraOut])
def get_compras(
    carnet: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int = Query(200, le=2000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return crud.listar_compras(
        db, carnet=carnet, desde=desde, hasta=hasta, limit=limit, offset=offset
    )


@app.get("/api/estadisticas")
def get_estadisticas(db: Session = Depends(get_db)):
    return crud.estadisticas(db)


# ----------------------------- Páginas web -------------------------------- #


@app.get("/", response_class=HTMLResponse)
def pagina_inicio(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "stats": crud.estadisticas(db),
            "cooldown_dias": COOLDOWN_DAYS,
            "max_litros": MAX_LITROS,
        },
    )


@app.get("/personas", response_class=HTMLResponse)
def pagina_personas(request: Request):
    return templates.TemplateResponse("personas.html", {"request": request})


@app.get("/historial", response_class=HTMLResponse)
def pagina_historial(request: Request):
    return templates.TemplateResponse("historial.html", {"request": request})
