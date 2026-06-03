"""Configuración de la aplicación leída desde variables de entorno."""
from __future__ import annotations

import os


def _normalize_db_url(url: str) -> str:
    """Render entrega URLs de Postgres como ``postgres://``.

    SQLAlchemy + psycopg necesitan el esquema ``postgresql+psycopg://``.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


# Cantidad de días que un carnet debe esperar entre compras.
# Por defecto 7 (una vez por semana, la restricción más fuerte del enunciado).
# Para "una vez por día" basta con poner COOLDOWN_DAYS=1.
COOLDOWN_DAYS: int = int(os.environ.get("COOLDOWN_DAYS", "7"))

# Litros máximos permitidos por compra (sólo informativo / validación simple).
MAX_LITROS: float = float(os.environ.get("MAX_LITROS", "100"))

# Base de datos: SQLite en local, Postgres en Render (vía DATABASE_URL).
DATABASE_URL: str = _normalize_db_url(
    os.environ.get("DATABASE_URL", "sqlite:///./combustible.db")
)
