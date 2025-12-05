from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime

from app.schemas import HealthResponse
from app.database import engine
from app.config import settings
import redis

router = APIRouter()

@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    
    # Check database
    db_status = "healthy"
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"
    
    # Check Redis
    redis_status = "healthy"
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
    except Exception:
        redis_status = "unhealthy"
    
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        database=db_status,
        redis=redis_status
    )

@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest().decode('utf-8')