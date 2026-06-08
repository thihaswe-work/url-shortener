# URL Shortener API

A production-ready URL shortener built with **FastAPI** — shorten URLs, track analytics on every click, manage via JWT authentication.

## Features

- **Web UI** — user-friendly interface at `http://localhost:8000` (register, login, shorten URLs, view stats, manage API keys)
- **Shorten URLs** — auto-generated 7-char codes or custom aliases (4-32 chars)
- **Expiration** — optional expiry date per short URL (auto-returns 410 Gone after)
- **Redirect** — 301 redirect with Redis caching for hot-path performance
- **Analytics** — every click tracked: timestamp, hashed IP, user-agent, referrer, device type
- **Authentication** — JWT-based register/login/logout with bcrypt password hashing
- **API Keys** — generate long-lived API keys for programmatic access (sent via `X-API-Key` header)
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
│   ├── click.py         # clicks: url_id, timestamp, ip_hash, user_agent, device_type
│   └── api_key.py       # api_keys: user_id, key_hash, key_prefix, name, is_active
├── schemas/             # Pydantic request/response models
│   └── api_key.py       # ApiKeyCreate, ApiKeyResponse, ApiKeyCreated, ApiKeyList
├── templates/           # Jinja2 web UI templates
│   ├── base.html        # Layout with Bootstrap 5, nav, auth state
│   ├── index.html       # Landing page with quick shorten form
│   ├── register.html    # Registration form
│   ├── login.html       # Login form
│   ├── dashboard.html   # URL list + create form + stats
│   ├── api_keys.html    # API key management
│   └── stats.html       # Click analytics per URL
├── api/v1/              # Route handlers
│   ├── auth.py          # POST/register, POST/login, POST/logout, GET/me, API key CRUD
│   ├── urls.py          # POST/shorten, GET/stats/{short_code}, GET/stats/all
│   ├── pages.py         # Web UI page routes (/, /login, /dashboard, etc.)
│   └── redirect.py      # GET/{short_code} → 301 redirect (Redis-cached)
├── services/            # Business logic layer
│   ├── auth.py          # AuthService: register, login, token creation
│   ├── url_shortener.py # Short code generation, collision prevention
│   ├── analytics.py     # Click tracking, IP hashing, device detection
│   └── api_key.py       # ApiKeyService: generate, validate, list, revoke
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
| GET | `/api/v1/auth/me` | Yes | Get current user info (JWT or API Key) |
| POST | `/api/v1/auth/api-keys` | Yes | Generate a new API key |
| GET | `/api/v1/auth/api-keys` | Yes | List your API keys |
| DELETE | `/api/v1/auth/api-keys/{id}` | Yes | Revoke an API key |
| POST | `/api/v1/shorten` | Optional | Shorten a URL (JWT or API Key) |
| GET | `/api/v1/stats/all` | Yes | List all your URLs with stats |
| GET | `/api/v1/stats/{short_code}` | Yes | Get click analytics (owner only) |
| GET | `/{short_code}` | No | 301 redirect to original URL |
| GET | `/` | No | Web UI — home page |
| GET | `/register` | No | Web UI — registration form |
| GET | `/login` | No | Web UI — login form |
| GET | `/dashboard` | No | Web UI — manage URLs |
| GET | `/api-keys` | No | Web UI — manage API keys |
| GET | `/stats/{short_code}` | No | Web UI — click analytics |

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

### 8. Test API keys

```bash
# Create an API key
curl -X POST http://127.0.0.1:8000/api/v1/auth/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name":"ci-key"}'

# Expected: 201 with raw_key (shown once), key_prefix, id
# Use the raw_key to authenticate without JWT:

# Get user info via API key
curl -X GET http://127.0.0.1:8000/api/v1/auth/me \
  -H "X-API-Key: shortener_abc123..."

# Shorten via API key
curl -X POST http://127.0.0.1:8000/api/v1/shorten \
  -H "Content-Type: application/json" \
  -H "X-API-Key: shortener_abc123..." \
  -d '{"original_url":"https://example.com","custom_alias":"api-test"}'

# List your API keys
curl -X GET http://127.0.0.1:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer YOUR_TOKEN"

# Revoke a key
curl -X DELETE http://127.0.0.1:8000/api/v1/auth/api-keys/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

The API key is stored as a SHA-256 hash. The raw key (`shortener_...`) is returned only once at creation.

### 9. Test rate limiting

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
