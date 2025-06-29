# Enhanced Matchering Backend

FastAPI-based backend for AI-powered audio mastering with reference-based and auto-mastering capabilities.

## Quick Start

### Prerequisites

- Python 3.11+
- Redis server (for task queue)
- PostgreSQL (for production) or SQLite (for development)

### Installation

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Start Redis server:**
```bash
redis-server
```

5. **Run the application:**
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## API Documentation

When running in development mode, interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

The backend follows the FastAPI architecture specified in `docs/architecture/enhanced-matchering-architecture.md`:

```
backend/
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── core/                 # Core configuration and utilities
│   ├── models/               # Database models
│   ├── services/             # Business logic services
│   └── workers/              # Celery task workers
├── tests/                    # Test suite
└── scripts/                  # Utility scripts
```

## Development

### Code Quality

The project uses strict type checking and code quality tools:

```bash
# Type checking
mypy app/

# Code formatting
black app/
isort app/

# Linting
flake8 app/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app
```

### Database Migrations

Using Alembic for database schema management:

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## API Endpoints

### Audio Management
- `POST /api/v1/audio/upload` - Upload audio files
- `GET /api/v1/audio/files` - List uploaded files
- `GET /api/v1/audio/files/{file_id}` - Get file metadata

### Processing
- `POST /api/v1/processing/auto-master` - Start AI auto-mastering
- `POST /api/v1/processing/reference-master` - Start reference mastering
- `GET /api/v1/processing/jobs/{job_id}/status` - Get job status
- `POST /api/v1/processing/jobs/{job_id}/cancel` - Cancel job
- `WS /api/v1/processing/ws/{job_id}` - Real-time progress updates

### Results
- `GET /api/v1/results/{job_id}` - Get processing results
- `GET /api/v1/results/{job_id}/download` - Download processed file
- `GET /api/v1/results/{job_id}/metadata` - Get detailed metadata

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `MATCHERING_DEBUG` | Enable debug mode | `false` |
| `MATCHERING_HOST` | Server host | `127.0.0.1` |
| `MATCHERING_PORT` | Server port | `8000` |
| `MATCHERING_SECRET_KEY` | Security secret key | Required |
| `MATCHERING_DATABASE_URL` | Database connection string | SQLite |
| `MATCHERING_REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |

## Deployment

### Production Deployment

1. **Set environment:**
```bash
export MATCHERING_ENVIRONMENT=production
```

2. **Use PostgreSQL:**
```bash
export MATCHERING_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/matchering
```

3. **Run with production ASGI server:**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker Deployment

```bash
# Build image
docker build -t enhanced-matchering-backend .

# Run container
docker run -p 8000:8000 enhanced-matchering-backend
```

## Monitoring

- Health check: `GET /health`
- Prometheus metrics: `GET /metrics` (when enabled)
- Structured logging with correlation IDs

## Security

- CORS configured for frontend origins
- Input validation on all endpoints
- File upload security with type checking
- Rate limiting (TODO)
- Authentication (TODO)

## Performance

- Async/await throughout for non-blocking I/O
- Connection pooling for database
- Redis caching for frequent queries
- Background task processing with Celery

---

For more detailed architecture information, see `docs/architecture/enhanced-matchering-architecture.md`.