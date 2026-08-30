# Application package

`app` is the Python package FastAPI imports when starting `uvicorn app.main:app`. `main.py` creates the FastAPI application and declares its routes. The surrounding modules keep related responsibilities together:

- `core/` configures settings, database sessions, and security primitives.
- `models.py` describes persistent database entities with SQLAlchemy.
- `schemas.py` describes validated API input and JSON output with Pydantic.
- `dependencies.py` provides reusable FastAPI dependencies, especially the current authenticated user.
- `services.py` contains QR-specific operations that do not belong in an HTTP route.

Routes connect these pieces: they receive a validated schema, obtain dependencies such as a database session, update ORM models, and return response schemas.
