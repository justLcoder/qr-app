# Backend tests

These are integration-style API tests. They create a FastAPI `TestClient`, make HTTP requests against the real route definitions, and assert observable behavior such as status codes, redirect locations, response headers, and analytics counts.

The current tests set `DATABASE_URL` to a local SQLite test database before importing the application. That lets the tests run without PostgreSQL, while production/local development normally uses the PostgreSQL configuration in `backend/.env`.
