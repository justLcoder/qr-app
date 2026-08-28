# QR Studio

QR Studio generates static and dynamic URL QR codes. Dynamic codes use a short redirect URL, so their destination can be updated after printing and scan counts can be measured.

## Stack

- API: FastAPI, SQLAlchemy, PostgreSQL
- Web: React, TypeScript, Vite, Tailwind CSS
- Local services: Docker Compose

## Run locally

1. Copy `backend/.env.example` to `backend/.env` and set a non-default `SECRET_KEY`.
2. Start PostgreSQL: `docker compose up -d db`.
3. In `backend`, create a virtualenv, install `pip install -r requirements.txt`, then run `uvicorn app.main:app --reload`.
4. In `frontend`, run `npm install` then `npm run dev`.

The API is available at `http://localhost:8000`; interactive API docs are at `/docs`.

## Tests

Run backend tests with `cd backend && pytest`.
