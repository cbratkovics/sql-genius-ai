# SQL Genius AI - Backend API

FastAPI-based backend service for SQL Genius AI with multi-tenant architecture, advanced security, and AI-powered SQL generation.

## Prerequisites

- Python 3.11+
- PostgreSQL 15
- Redis 7
- Docker & Docker Compose (optional)

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables (see `.env.example` for full list):
- `ANTHROPIC_API_KEY`: Claude API key for SQL generation
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `CORS_ORIGINS`: Comma-separated list of allowed origins

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Infrastructure Services

```bash
# Start PostgreSQL and Redis
docker-compose -f ../infrastructure/docker/docker-compose.yml up -d
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start the API Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## CORS Configuration

CORS is configured via the `CORS_ORIGINS` environment variable. Set it to a comma-separated list of allowed origins:

```bash
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

In production, avoid using `*` for security reasons.

## Health Checks

### API Health
```bash
curl http://localhost:8000/health
```

### Database Health
```bash
curl http://localhost:8000/api/v1/health/db
```

### Redis Health
```bash
curl http://localhost:8000/api/v1/health/redis
```

## Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

## Code Quality

### Format Code
```bash
ruff format .
isort .
```

### Lint Code
```bash
ruff check .
mypy .
```

## Project Structure

```
backend/
├── api/              # API routes and endpoints
│   ├── auth.py      # Authentication endpoints
│   ├── users.py     # User management
│   └── demo.py      # Demo endpoints
├── core/            # Core functionality
│   ├── config.py    # Settings and configuration
│   ├── database.py  # Database setup
│   └── security.py  # Security utilities
├── models/          # SQLAlchemy models
├── services/        # Business logic
│   └── ai/         # AI service integrations
├── tests/          # Test suite
└── main.py         # FastAPI application

<system-reminder>
The TodoWrite tool hasn't been used recently. If you're working on tasks that would benefit from tracking progress, consider using the TodoWrite tool to track progress. Also consider cleaning up the todo list if has become stale and no longer matches what you are working on. Only use it if it's relevant to the current work. This is just a gentle reminder - ignore if not applicable.


Here are the existing contents of your todo list:

[1. [completed] Create vercel.json with rewrites and headers
2. [completed] Add typed API client in lib/api.ts
3. [completed] Refactor frontend API calls to use relative paths
4. [completed] Create frontend .env.local.example
5. [completed] Add error boundary for App Router
6. [completed] Configure backend CORS middleware
7. [completed] Create backend .env.example
8. [completed] Update root README.md
9. [in_progress] Create/update backend README.md
10. [pending] Update frontend README.md
11. [pending] Move streamlit demo to demos folder
12. [pending] Create Makefile with standard targets
13. [pending] Add CI workflows for frontend and backend
14. [pending] Remove all emojis from the codebase
15. [pending] Create git branch and commit changes]
</system-reminder>
```

## Security Features

- JWT authentication with RSA256 signing
- Rate limiting per endpoint
- SQL injection prevention
- Input validation and sanitization
- Encrypted sensitive data storage

## Performance

- Async/await for all I/O operations
- Redis caching for frequently accessed data
- Connection pooling for database
- Query optimization and indexing

## Deployment

See the main [README.md](../README.md) for deployment instructions using Render.

For production deployment:
1. Set all required environment variables
2. Use production-grade database and Redis instances
3. Enable HTTPS/TLS
4. Configure proper CORS origins
5. Set `ENABLE_DOCS=false` in production