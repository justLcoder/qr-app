# Backend

This folder contains the server-side half of QR Studio. It exposes the HTTP API used by the browser, authenticates users, creates QR-code records, serves QR image downloads, and handles the public dynamic-QR redirect URL.

`app/` is the FastAPI application package. Its route handlers coordinate validation, database access, authentication, and QR-generation services. `tests/` contains API-level tests that exercise the application through FastAPI's test client rather than calling route functions directly.

The backend reads local settings from `.env` (created from `.env.example`) and uses PostgreSQL during normal local development. Docker runs that database; the backend itself runs directly in a Python virtual environment.
