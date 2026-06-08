# URL Shortener API

A production-ready URL shortener built with **FastAPI** — shorten URLs, track analytics on every click, manage via JWT authentication.

## Features

- **Shorten URLs** — auto-generated 7-char codes or custom aliases
- **Expiration** — optional expiry date per short URL
- **Redirect** — 301 redirect with Redis caching for hot-path performance
- **Analytics** — every click tracked: timestamp, hashed IP, user-agent, referrer, device type
- **Authentication** — JWT-based register/login/logout with bcrypt password hashing
- **Rate limiting** — per-IP-per-endpoint sliding window (30/min shorten, 20/min auth)
- **Anonymous usage** — shorten URLs without an account
- **OpenAPI docs** — auto-generated interactive docs at `/docs`

## Project Structure

```
app/
├── main.py              # FastAPI entry point — lifespan, CORS, router registration
├── config.py            # pydantic-settings — reads .env
├── database.py          # SQLAlchemy engine + session factory
├── models/              # ORM models (database tables)
│   ├── user.py          # users: id, email, username, hashed_password
│   ├── url.py           # urls: short_code (indexed), original_url, expires_at
│   └── click.py         # clicks: url_id, timestamp, ip_hash, user_agent, device_type
├── schemas/             # Pydantic request/response models
├── api/v1/              # Route handlers
│   ├── auth.py          # POST/register, POST/login, POST/logout, GET/me
│   ├── urls.py          # POST/shorten, GET/stats/{short_code}
│   └── redirect.py      # GET/{short_code} → 301 redirect (Redis-cached)
├── services/            # Business logic layer
│   ├── auth.py          # AuthService: register, login, token creation
│   ├── url_shortener.py # Short code generation, collision prevention
│   └── analytics.py     # Click tracking, IP hashing, device detection
├── core/                # Infrastructure layer
│   ├── security.py      # bcrypt hashing, JWT encode/decode
│   └── redis.py         # Redis client with graceful degradation
├── utils/
│   └── rate_limiter.py  # Per-IP-per-path sliding window rate limiter
├── alembic/             # Database migration setup
├── Dockerfile           # Python 3.11 slim image
└── docker-compose.yml   # FastAPI + PostgreSQL 15 + Redis 7
```

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Local setup (SQLite)

```bash
# Clone
git clone https://github.com/thihaswe-work/url-shortener.git
cd url-shortener

# Virtual environment
python -m venv .venv

# Activate (Mac/Linux)
source .venv/bin/activate
# Activate (Windows - Git Bash)
source .venv/Scripts/activate
# Activate (Windows - PowerShell)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for the Swagger UI.

### Docker setup (PostgreSQL + Redis)

```bash
docker compose up --build
```

This runs three containers: FastAPI (port 8000), PostgreSQL 15 (port 5432), Redis 7 (port 6379).

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | No | Create a new account |
| POST | `/api/v1/auth/login` | No | Get JWT access token |
| POST | `/api/v1/auth/logout` | Yes | Log out |
| GET | `/api/v1/auth/me` | Yes | Get current user info |
| POST | `/api/v1/shorten` | Optional | Shorten a URL (works without auth) |
| GET | `/api/v1/stats/{short_code}` | Yes | Get click analytics (owner only) |
| GET | `/{short_code}` | No | 301 redirect to original URL |

## Testing Guide

### 1. Register a user

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","username":"alice","password":"secret123"}'
```

Expected: `201 Created` with user info.

### 2. Login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret123"}'
```

Expected: `200 OK` with `{"access_token": "eyJ...", "token_type": "bearer"}`. Save the token.

### 3. Shorten a URL

```bash
curl -X POST http://127.0.0.1:8000/api/v1/shorten \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"original_url":"https://example.com/very/long/url"}'
```

Expected: `201 Created` with `short_code`, `short_url`, etc.

**With custom alias and expiry:**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://news.com","custom_alias":"mynews","expires_at":"2026-12-31T23:59:59"}'
```

Note: this works **without authentication** (anonymous shortening).

### 4. Test the redirect

```bash
curl -L http://127.0.0.1:8000/mynews
```

Or open `http://127.0.0.1:8000/mynews` in your browser. You'll be redirected to `https://news.com`.

### 5. View analytics

```bash
curl -X GET http://127.0.0.1:8000/api/v1/stats/mynews \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected: `200 OK` with `total_clicks` and a list of `recent_clicks` showing device type, referrer, and timestamp.

### 6. Test collision detection

```bash
# Run this twice:
curl -X POST http://127.0.0.1:8000/api/v1/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://a.com","custom_alias":"mynews"}'
```

Expected: first call succeeds (`201`), second returns **409 Conflict** with `"Custom alias already in use"`.

### 7. Test expired URL

```bash
# Create a URL that expired 6 years ago
curl -X POST http://127.0.0.1:8000/api/v1/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://temp.com","custom_alias":"expired","expires_at":"2020-01-01T00:00:00"}'

# Visit it
curl http://127.0.0.1:8000/expired
```

Expected: **410 Gone** with `"Short URL has expired"`.

### 8. Test rate limiting

Hit `/api/v1/shorten` 31+ times in one minute. Expected: **429 Too Many Requests**.

## Reset Database

```bash
# Stop the server (Ctrl+C), then:
rm url_shortener.db
```

Restart the server — tables are recreated automatically on startup.

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (dev) / PostgreSQL 15 (prod) |
| Cache | Redis 7 |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Migrations | Alembic |
| Containerization | Docker + Docker Compose |
| Validation | Pydantic v2 |

## Environment Variables

All configurable via `.env` file (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./url_shortener.db` | Database connection string |
| `SECRET_KEY` | `change-me-...` | JWT signing key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `RATE_LIMIT_PER_MINUTE` | `60` | Global rate limit |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## License

MIT
