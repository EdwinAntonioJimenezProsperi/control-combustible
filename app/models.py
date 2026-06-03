"""Modelos de datos: Persona (comprador) y Compra (carga de combustible)."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Persona(Base):
    """Habitante registrado, identificado por su número de carnet.

    El carnet tiene un índice ÚNICO, por lo que la búsqueda de un carnet es
    O(log n) (índice B-tree). Para una población de 10.000+ habitantes la
    consulta es prácticamente instantánea.
    """

    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    carnet: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    compras: Mapped[list[Compra]] = relationship(
        back_populates="persona",
        cascade="all, delete-orphan",
        order_by="Compra.fecha.desc()",
    )


class Compra(Base):
    """Registro de una compra/carga de combustible."""

    __tablename__ = "compras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    persona_id: Mapped[int] = mapped_column(
        ForeignKey("personas.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Carnet desnormalizado para poder filtrar el historial sin join.
    carnet: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    litros: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True, server_default=func.now()
    )

    persona: Mapped[Persona] = relationship(back_populates="compras")
