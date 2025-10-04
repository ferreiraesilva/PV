# SAFV

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
3. Start the development stack (default profile is `dev`): `docker compose --profile dev up --build`
   - The app container waits for PostgreSQL, applies Alembic migrations, and seeds baseline data from `db/seeds.sql` (set `APPLY_SEEDS=false` to skip).
   - The Vite frontend runs at `http://localhost:5173` via the `frontend-dev` service.
4. Access the API at `http://localhost:8000/health` and interactive docs at `http://localhost:8000/docs`.
5. Run tests inside the container: `docker compose --profile dev exec app make test`
6. Stop and clean up: `docker compose --profile dev down` (add `-v` to drop database volumes).

pgAdmin is included in the `dev` profile. Visit `http://localhost:5050` using the credentials defined in `.env` if you need a visual client.

## Makefile shortcuts
```bash
make run          # local uvicorn (without Docker)
make lint         # ruff + black --check
make format       # black
make test         # pytest with coverage
make docker-build # docker compose build (uses active profiles)
make docker-up    # docker compose up (uses active profiles)
make docker-down  # docker compose down (uses active profiles)
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
�   +-- __init__.py
�   +-- main.py
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

## Production deployment (Docker Compose)
The production stack runs four long-lived services: PostgreSQL, FastAPI backend, React frontend, and an nginx gateway that terminates HTTPS for `labs4ideas.com.br` subdomains. Certificates are provisioned through Let's Encrypt using `certbot`.

### 1. Prepare environment variables
1. Copy the sample file: `cp .env.example .env`
2. Review the variables at the bottom of `.env`:
   - `COMPOSE_PROFILES` should be set to `prod` (or export `COMPOSE_PROFILES=prod` before running compose commands).
   - `API_SERVER_NAME`, `FRONTEND_SERVER_NAME`, `WWW_SERVER_NAME`.
   - `WWW_UPSTREAM_URL` must point to the current HostGator origin for the corporate website (e.g. `https://gatorXXXX.hostgator.com/~labs4ideas`).
   - `WWW_PROXY_HOST` normally remains `www.labs4ideas.com.br`.
   - `LETSENCRYPT_EMAIL` should be a monitored mailbox. Set `LETSENCRYPT_STAGING=1` for a dry-run, then back to `0`.

### 2. Build images
```bash
docker compose --profile prod build
```

### 3. Issue TLS certificates once DNS already points to this host
```bash
chmod +x docker/nginx/init-letsencrypt.sh
API_SERVER_NAME=api.labs4ideas.com.br \
FRONTEND_SERVER_NAME=pv.labs4ideas.com.br \
WWW_SERVER_NAME=www.labs4ideas.com.br \
LETSENCRYPT_EMAIL=infra@labs4ideas.com.br \
./docker/nginx/init-letsencrypt.sh
```
The script will
1. start the nginx container (profile `prod`)
2. request certificates for the three hostnames via HTTP-01 challenge (`/.well-known/acme-challenge`)
3. reload nginx after the certificates are stored under the shared `/etc/letsencrypt` volume.

Whenever certificates approach expiry, renew them with:
```bash
docker compose --profile prod run --rm certbot certbot renew \
  --webroot -w /var/www/certbot
# reload nginx so the new certs are picked up
docker compose --profile prod exec nginx nginx -s reload
```
Automating this renewal via cron is recommended.

### 4. Run the stack
```bash
docker compose --profile prod up -d
```
- `api.labs4ideas.com.br` proxies to the FastAPI container.
- `pv.labs4ideas.com.br` proxies to the Vite-built frontend container (served via `serve` on port 4173).
- `www.labs4ideas.com.br` proxies to the upstream HostGator site defined by `WWW_UPSTREAM_URL`, keeping the current corporate site online while DNS now targets this stack.

### 5. Backend database notes
- The backend waits for PostgreSQL, applies Alembic migrations, and only seeds data when `APPLY_SEEDS=true` **and** `db/seeds.sql` exists.
- `postgres_data` volume persists data across deployments.

### 6. Frontend image
- Multi-stage build located at `frontend/Dockerfile`.
- Builds static assets (`npm run build`) and serves them with `serve` inside the runtime container (`PORT=4173`).
- Bundle is reverse-proxied via nginx and available at `https://pv.labs4ideas.com.br`.

### 7. Corporate site proxying
`www.labs4ideas.com.br` is reverse proxied to the HostGator origin. Update DNS A/AAAA records for `www`, `api`, and `pv` to this server. If/when the corporate site is migrated off HostGator, point `WWW_UPSTREAM_URL` to the new internal service and reload nginx.
