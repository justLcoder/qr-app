# Core infrastructure

This folder contains cross-cutting backend infrastructure rather than QR-specific business rules.

- `config.py` loads typed environment-based settings once per process.
- `database.py` creates the SQLAlchemy engine and supplies one database session per request.
- `security.py` hashes passwords and creates or validates signed JWT access tokens.

Other application modules import these utilities instead of constructing database connections or security helpers themselves. Keeping them here makes configuration and security decisions easier to find and change consistently.
