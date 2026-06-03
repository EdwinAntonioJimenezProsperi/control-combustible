"""Esquemas Pydantic para validación de entrada/salida de la API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PersonaCreate(BaseModel):
    carnet: str = Field(min_length=1, max_length=40)
    nombre: str = Field(default="", max_length=120)

    @field_validator("carnet", "nombre")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class PersonaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    carnet: str
    nombre: str
    creado_en: datetime


class CompraCreate(BaseModel):
    carnet: str = Field(min_length=1, max_length=40)
    litros: float = Field(default=0.0, ge=0)

    @field_validator("carnet")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class CompraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    carnet: str
    litros: float
    fecha: datetime


class EstadoCarnet(BaseModel):
    """Indica si un carnet puede comprar ahora mismo."""

    carnet: str
    registrado: bool
    puede_comprar: bool
    motivo: str
    ultima_compra: datetime | None = None
    proxima_habilitacion: datetime | None = None
    nombre: str | None = None
