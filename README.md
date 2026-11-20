# Ticketing API

A backend for event ticket booking, built to handle the hard part of ticketing: **many people fighting for the last seat at the same time**.

Built with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.0 (async)** and **Alembic**.

> 🚧 **Status:** In active development. See the [Roadmap](#roadmap) for what's done and what's next.

---

## Why This Project

Most CRUD demos never face real backend problems. This one is designed around them:

- **Race conditions:** 100 concurrent requests for 10 tickets must never oversell.
- **Idempotency:** a retried or double-clicked request must not create a duplicate booking.
- **Expiry:** unpaid bookings expire automatically and return stock.
- **Data integrity enforced in the database**, not only in application code.

## Tech Stack

| Layer                  | Choice                                          |
| ---------------------- | ----------------------------------------------- |
| Framework              | FastAPI                                         |
| Database               | PostgreSQL                                      |
| ORM                    | SQLAlchemy 2.0 (async, `asyncpg`)               |
| Migrations             | Alembic                                         |
| Config                 | Pydantic Settings                               |
| Auth _(planned)_       | JWT (access + refresh), Argon2 password hashing |
| Scheduling _(planned)_ | APScheduler                                     |
| Testing _(planned)_    | Pytest, pytest-asyncio, httpx                   |
| Tooling                | uv, Ruff, Docker Compose                        |

## Architecture

Layered, one responsibility per folder:

```
app/
├── main.py          # app creation, lifespan
├── api/             # HTTP layer: routing, validation, dependencies
├── core/            # config, security, exceptions
├── db/              # engine, session
├── models/          # SQLAlchemy models (tables)
├── schemas/         # Pydantic request/response models
├── services/        # business logic and transactions
└── tasks/           # background jobs (booking expiry)
```

| Layer       | Responsibility                               | Must not                              |
| ----------- | -------------------------------------------- | ------------------------------------- |
| `api/`      | Parse request, call service, return response | Contain business logic or raw queries |
| `services/` | Business rules, locking, transactions        | Know about HTTP                       |
| `models/`   | Table definitions                            | Contain business logic                |
| `schemas/`  | Shape of data in/out                         | Touch the database                    |

## Database Design

![ERD](docs/erd.png)

Core tables: `users`, `events`, `ticket_tiers`, `bookings`, `payments`.

Key design decisions:

- **UUIDs for public/sensitive IDs** (`users`, `bookings`, `payments`) to prevent enumeration (IDOR). Integer IDs for internal tables.
- **`UNIQUE (user_id, idem_key)` on bookings** makes idempotency a database guarantee, scoped per user.
- **`CHECK (sold >= 0 AND sold <= quota)` on ticket tiers** is the last line of defense against overselling.
- **`timestamptz` everywhere**, stored in UTC.
- **Prices stored as integers** in the smallest currency unit. Never floats for money.
- **Index on `bookings.expires_at`** to keep the expiry job fast.
- **Naming convention** on constraints so Alembic migrations stay predictable.

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose

### Setup

```bash
# 1. Clone
git clone https://github.com/<your-username>/ticketing-api.git
cd ticketing-api

# 2. Environment variables
cp .env.example .env

# 3. Install dependencies
uv sync

# 4. Start PostgreSQL
docker compose up -d db

# 5. Run the app
uv run uvicorn app.main:app --reload
```

On Windows PowerShell, use `copy .env.example .env` instead of `cp`.

The API is now at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

### Verify

```bash
curl http://localhost:8000/health
# {"status":"ok","db":"connected"}
```

### Environment Variables

| Variable       | Description        | Example                                                 |
| -------------- | ------------------ | ------------------------------------------------------- |
| `APP_NAME`     | Application title  | `My App`                                                |
| `DATABASE_URL` | Async Postgres URL | `postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE` |

## Roadmap

- [x] Project setup (uv, Docker Compose, Postgres)
- [x] Async DB connection and session management
- [x] Health check endpoint
- [ ] Models and first Alembic migration
- [ ] Auth: register, login, JWT, refresh token
- [ ] RBAC (admin / customer)
- [ ] Event and ticket tier management
- [ ] Booking flow (naive version)
- [ ] **Concurrency control** (row locking / atomic update) with proof via load test
- [ ] Idempotent booking requests
- [ ] Automatic booking expiry
- [ ] Payment simulation and idempotent webhook
- [ ] Test suite with CI (GitHub Actions)
- [ ] Deployment with live Swagger link

## Concurrency Handling

> _To be filled in once Phase 3 is done. Planned content:_
>
> 1. The bug: naive implementation under 100 concurrent requests (oversell evidence).
> 2. The fix and why this approach (`SELECT ... FOR UPDATE` vs atomic `UPDATE`).
> 3. Test results after the fix.

## API Overview

> _Endpoint table will be added as features land._

| Method | Endpoint  | Description                 | Auth   |
| ------ | --------- | --------------------------- | ------ |
| GET    | `/health` | Service and DB health check | Public |

## Development

```bash
# Run tests (planned)
uv run pytest --cov=app

# Lint and format
uv run ruff check --fix .
uv run ruff format .
```

## License

[MIT](./LICENSE)
