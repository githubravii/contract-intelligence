from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.database import init_db
from app.api import ingest, extract, ask, audit, webhook, admin
from app.utils.logger import logger
from app.utils.metrics import REQUEST_COUNT, REQUEST_DURATION
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Contract Intelligence API")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Contract Intelligence API")

app = FastAPI(
    title="Contract Intelligence API",
    description="AI-powered contract analysis and risk detection",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingest"])
app.include_router(extract.router, prefix="/api/v1", tags=["Extract"])
app.include_router(ask.router, prefix="/api/v1", tags=["Ask"])
app.include_router(audit.router, prefix="/api/v1", tags=["Audit"])
app.include_router(webhook.router, prefix="/api/v1", tags=["Webhooks"])
app.include_router(admin.router, tags=["Admin"])

@app.get("/")
async def root():
    return {
        "message": "Contract Intelligence API",
        "version": "1.0.0",
        "docs": "/docs"
    }