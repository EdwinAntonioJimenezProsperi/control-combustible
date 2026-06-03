# ⛽ Sistema de Control de Compra de Combustible

Sistema web para controlar la compra de combustible en una población (10.000+
habitantes). Cada persona se identifica por su **número de carnet** y solo puede
cargar combustible **una vez por ventana de tiempo** (por defecto **1 vez por
semana**, configurable). Lleva el **historial de compras por fechas** y permite
verificar **de forma rápida** si un carnet ya cargó.

## Características

- **Registro de carnets** de los compradores (con nombre opcional).
- **Validación de compra**: un carnet solo puede cargar 1 vez dentro de la
  ventana definida por `COOLDOWN_DAYS` (por defecto 7 días = 1 vez por semana).
  Para "1 vez por día" usa `COOLDOWN_DAYS=1`.
- **Búsqueda óptima y rápida** del carnet mediante un **índice único** en la
  columna `carnet` (índice B-tree → búsqueda O(log n)). Para 10.000 habitantes
  la consulta es prácticamente instantánea.
- **Historial de compras por fechas**, con filtros por carnet y rango de fechas.
- **Interfaz web** simple + **API JSON**.
- Listo para desplegar en **Render** (free tier) con Postgres.

## Reglas de negocio

1. Para comprar, el carnet **debe estar registrado** previamente.
2. Un carnet **no puede comprar** si ya cargó dentro de los últimos
   `COOLDOWN_DAYS` días. El sistema indica la **fecha de próxima habilitación**.
3. Cada compra queda **contabilizada** en el historial con fecha y litros.

## Estructura

```
app/
  config.py      # variables de entorno (COOLDOWN_DAYS, DATABASE_URL, ...)
  database.py    # engine y sesión de SQLAlchemy
  models.py      # Persona (carnet único indexado) y Compra
  schemas.py     # validación Pydantic
  crud.py        # lógica de negocio (registro + validación de ventana)
  main.py        # FastAPI: API JSON + páginas web
  templates/     # interfaz web (Jinja2)
  static/        # CSS y JS
seed.py          # genera N carnets de prueba (por defecto 10.000)
tests/           # pruebas con pytest
render.yaml      # despliegue en Render
```

## Ejecutar en local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Abre http://localhost:8000
```

Variables opcionales:

```bash
export COOLDOWN_DAYS=7          # 1 = una vez al día, 7 = una vez por semana
export MAX_LITROS=100
export DATABASE_URL=sqlite:///./combustible.db   # o una URL de Postgres
```

Generar 10.000 habitantes de prueba:

```bash
python seed.py        # o: python seed.py 5000
```

## Pruebas y lint

```bash
pytest
ruff check .
```

## API

| Método | Ruta                              | Descripción                            |
|--------|-----------------------------------|----------------------------------------|
| POST   | `/api/personas`                   | Registrar un carnet                    |
| GET    | `/api/personas?q=`                | Listar / buscar carnets                |
| GET    | `/api/personas/{carnet}/estado`   | ¿Puede comprar ahora ese carnet?       |
| POST   | `/api/compras`                    | Registrar compra (valida la ventana)   |
| GET    | `/api/compras?carnet=&desde=&hasta=` | Historial de compras (filtros)      |
| GET    | `/api/estadisticas`               | Totales y compras del día              |
| GET    | `/health`                         | Healthcheck                            |

## Despliegue en Render (gratis)

1. Sube este repositorio a GitHub.
2. En [Render](https://dashboard.render.com) → **New** → **Blueprint** y
   selecciona el repo (Render detecta `render.yaml`).
3. Render crea el servicio web **y** una base de datos Postgres gratuita,
   inyectando `DATABASE_URL` automáticamente.
4. Al terminar el deploy tendrás una URL pública `https://<tu-app>.onrender.com`.

> Nota: el plan gratuito de Render suspende el servicio tras inactividad; la
> primera petición después de dormir puede tardar unos segundos.
