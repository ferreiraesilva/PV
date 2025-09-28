# safv

## Overview
safv (Financial Sales Analysis System) is a FastAPI monolith focused on financial simulations for receivables, portfolio insights, benchmarking, and recommendation flows. The platform enforces immutable auditing for every authenticated action, providing full traceability for decisions. The project runs entirely on Docker and docker-compose, with no managed cloud dependencies.

## Core Capabilities
- **FastAPI REST API** covering simulations (PV, PMT, FV) and valuation (NPV scenarios) with fully traceable business rules.
- **User management, JWT authentication with refresh tokens, and RBAC** enforced via roles and granular permissions.
- **Comprehensive auditing**: append-only logs with request context, masked payloads, and structured diffs.
- **Observability**: JSON structured logs, Prometheus metrics, `/health` and `/metrics` endpoints, and global error handling.
- **Quality**: unit and integration tests targeting 80%+ coverage, linting with ruff and black, and full type hints.

## Technical Stack
- **Language**: Python 3.13
- **Web Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy + Alembic
- **Authentication**: JWT (python-jose) + passlib[bcrypt]
- **Infrastructure**: Docker, docker-compose, Makefile for local automation
- **Quality Tooling**: pytest, pytest-cov, ruff, black

## Mandatory Auditing
Every authenticated request stores an entry in the `audit_logs` table containing:
- timestamp, request_id, user_id, role, ip, user_agent
- endpoint, method, status_code
- masked input and output payloads
- resource_type, resource_id, and structured diffs (JSONB)
The table is strictly append-only. Only read-only APIs with filters (date, user, resource, status) will be exposed for auditing.

## Running with docker-compose
1. Copy the example environment file: `cp .env.example .env`
2. Adjust secrets and credentials (`SECRET_KEY`, `POSTGRES_*`, etc.). Ensure `DATABASE_URL` points to the `postgres` service when running inside Docker.
3. Build and start the stack: `docker compose up --build`
   - The app container waits for PostgreSQL, applies Alembic migrations, and seeds baseline data from `db/seeds.sql` (set `APPLY_SEEDS=false` to skip).
4. Access the API at `http://localhost:8000/health` and interactive docs at `http://localhost:8000/docs`.
5. Run tests inside the container: `docker compose exec app make test`
6. Stop and clean up: `docker compose down` (add `-v` to drop database volumes).

Optional: enable pgAdmin with `docker compose --profile pgadmin up --build` and browse at `http://localhost:5050` using the credentials from `.env`.

## Makefile shortcuts
```bash
make run          # local uvicorn (without Docker)
make lint         # ruff + black --check
make format       # black
make test         # pytest with coverage
make docker-build # docker compose build
make docker-up    # docker compose up --build
make docker-down  # docker compose down
```

## Local Development without Docker
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
make run
```

## Initial Structure
```
.
+-- app/
¦   +-- __init__.py
¦   +-- main.py
+-- db/
+-- docs/
+-- tests/
+-- .env.example
+-- .gitignore
+-- Dockerfile
+-- docker-compose.yml
+-- LICENSE
+-- Makefile
+-- README.md
+-- requirements.txt
```

## Next Steps
- ETAPA 0: confirm understanding using PRD/SRS documentation.
- ETAPA 1+: define architecture, data model, OpenAPI contracts, and implementation.
