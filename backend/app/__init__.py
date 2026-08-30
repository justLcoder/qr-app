"""Marks this directory as the importable FastAPI application package.

The package itself has no startup behavior. Uvicorn imports ``app.main`` to
obtain the FastAPI application, while the sibling modules provide its routes,
models, configuration, and supporting services.
"""
