"""Lógica de negocio: registro de personas, validación y registro de compras."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.config import COOLDOWN_DAYS


class ReglaNegocioError(Exception):
    """Error de regla de negocio (p. ej. carnet ya cargó en la ventana)."""


def _aware(dt: datetime | None) -> datetime | None:
    """Garantiza datetimes con zona horaria (SQLite los devuelve naive)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def buscar_persona(db: Session, carnet: str) -> models.Persona | None:
    """Búsqueda O(log n) por índice único en ``carnet``."""
    carnet = carnet.strip()
    return db.scalar(select(models.Persona).where(models.Persona.carnet == carnet))


def registrar_persona(db: Session, carnet: str, nombre: str = "") -> models.Persona:
    carnet = carnet.strip()
    if not carnet:
        raise ReglaNegocioError("El número de carnet es obligatorio.")
    if buscar_persona(db, carnet) is not None:
        raise ReglaNegocioError(f"El carnet {carnet} ya está registrado.")
    persona = models.Persona(carnet=carnet, nombre=nombre.strip())
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


def ultima_compra(db: Session, persona: models.Persona) -> models.Compra | None:
    return db.scalar(
        select(models.Compra)
        .where(models.Compra.persona_id == persona.id)
        .order_by(models.Compra.fecha.desc())
        .limit(1)
    )


def estado_carnet(db: Session, carnet: str) -> dict:
    """Devuelve si el carnet puede comprar ahora y por qué."""
    carnet = carnet.strip()
    persona = buscar_persona(db, carnet)
    if persona is None:
        return {
            "carnet": carnet,
            "registrado": False,
            "puede_comprar": False,
            "motivo": "El carnet no está registrado.",
            "ultima_compra": None,
            "proxima_habilitacion": None,
            "nombre": None,
        }

    ultima = ultima_compra(db, persona)
    ahora = datetime.now(UTC)
    if ultima is None:
        return {
            "carnet": carnet,
            "registrado": True,
            "puede_comprar": True,
            "motivo": "Habilitado: sin compras previas.",
            "ultima_compra": None,
            "proxima_habilitacion": None,
            "nombre": persona.nombre,
        }

    ultima_fecha = _aware(ultima.fecha)
    proxima = ultima_fecha + timedelta(days=COOLDOWN_DAYS)
    if ahora >= proxima:
        return {
            "carnet": carnet,
            "registrado": True,
            "puede_comprar": True,
            "motivo": "Habilitado: ya pasó la ventana de espera.",
            "ultima_compra": ultima_fecha,
            "proxima_habilitacion": None,
            "nombre": persona.nombre,
        }

    return {
        "carnet": carnet,
        "registrado": True,
        "puede_comprar": False,
        "motivo": (
            f"Bloqueado: ya cargó el {ultima_fecha:%Y-%m-%d %H:%M} UTC. "
            f"Debe esperar {COOLDOWN_DAYS} día(s)."
        ),
        "ultima_compra": ultima_fecha,
        "proxima_habilitacion": proxima,
        "nombre": persona.nombre,
    }


def registrar_compra(
    db: Session, carnet: str, litros: float = 0.0
) -> models.Compra:
    """Registra una compra validando la ventana de espera (cooldown)."""
    carnet = carnet.strip()
    persona = buscar_persona(db, carnet)
    if persona is None:
        raise ReglaNegocioError(
            f"El carnet {carnet} no está registrado. Regístrelo antes de comprar."
        )

    estado = estado_carnet(db, carnet)
    if not estado["puede_comprar"]:
        raise ReglaNegocioError(estado["motivo"])

    compra = models.Compra(persona_id=persona.id, carnet=carnet, litros=litros)
    db.add(compra)
    db.commit()
    db.refresh(compra)
    return compra


def listar_personas(
    db: Session, q: str | None = None, limit: int = 100, offset: int = 0
) -> list[models.Persona]:
    stmt = select(models.Persona)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            models.Persona.carnet.ilike(like) | models.Persona.nombre.ilike(like)
        )
    stmt = stmt.order_by(models.Persona.creado_en.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))


def listar_compras(
    db: Session,
    carnet: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[models.Compra]:
    stmt = select(models.Compra)
    if carnet:
        stmt = stmt.where(models.Compra.carnet == carnet.strip())
    if desde:
        stmt = stmt.where(models.Compra.fecha >= desde)
    if hasta:
        stmt = stmt.where(models.Compra.fecha <= hasta)
    stmt = stmt.order_by(models.Compra.fecha.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))


def estadisticas(db: Session) -> dict:
    total_personas = db.scalar(select(func.count()).select_from(models.Persona)) or 0
    total_compras = db.scalar(select(func.count()).select_from(models.Compra)) or 0

    inicio_dia = datetime.now(UTC).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    compras_hoy = (
        db.scalar(
            select(func.count())
            .select_from(models.Compra)
            .where(models.Compra.fecha >= inicio_dia)
        )
        or 0
    )
    litros_hoy = (
        db.scalar(
            select(func.coalesce(func.sum(models.Compra.litros), 0.0)).where(
                models.Compra.fecha >= inicio_dia
            )
        )
        or 0.0
    )
    return {
        "total_personas": total_personas,
        "total_compras": total_compras,
        "compras_hoy": compras_hoy,
        "litros_hoy": float(litros_hoy),
        "cooldown_dias": COOLDOWN_DAYS,
    }
