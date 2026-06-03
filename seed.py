"""Genera datos de prueba: registra N carnets (por defecto 10.000 habitantes).

Uso:
    python seed.py            # 10.000 personas
    python seed.py 5000       # cantidad personalizada
"""
from __future__ import annotations

import sys
import time

from app.database import SessionLocal, init_db
from app.models import Persona


def seed(n: int = 10_000) -> None:
    init_db()
    db = SessionLocal()
    try:
        existentes = {c for (c,) in db.query(Persona.carnet).all()}
        nuevos = []
        for i in range(1, n + 1):
            carnet = f"CARNET-{i:06d}"
            if carnet in existentes:
                continue
            nuevos.append(Persona(carnet=carnet, nombre=f"Habitante {i}"))
        t0 = time.perf_counter()
        db.bulk_save_objects(nuevos)
        db.commit()
        dt = time.perf_counter() - t0
        print(f"Insertados {len(nuevos)} carnets en {dt:.2f}s "
              f"(total ahora: {db.query(Persona).count()}).")
    finally:
        db.close()


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    seed(cantidad)
