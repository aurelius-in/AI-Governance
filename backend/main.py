import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from app.core.config import settings
from app.core.database import engine
from app.api.v1.api import api_router
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()

# Setup OpenTelemetry
def setup_telemetry():
    """Setup OpenTelemetry tracing and metrics"""
    if settings.OTEL_ENDPOINT:
        resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
        
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)
        
        # Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name="jaeger",
            agent_port=6831,
        )
        trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument(engine=engine)
        
        # Instrument requests
        RequestsInstrumentor().instrument()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AI Governance Dashboard")
    setup_telemetry()
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Governance Dashboard")

# Create FastAPI app
app = FastAPI(
    title="AI Governance Dashboard",
    description="Enterprise AI Governance Platform with LLM Proxy, Policies as Code, and Safety Guardrails",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with trace ID"""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("http_request") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        
        # Get trace ID for logging
        trace_id = format(span.get_span_context().trace_id, "032x")
        
        logger.info(
            "Incoming request",
            method=request.method,
            url=str(request.url),
            trace_id=trace_id
        )
        
        response = await call_next(request)
        
        span.set_attribute("http.status_code", response.status_code)
        
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            trace_id=trace_id
        )
        
        # Add trace ID to response headers
        response.headers["X-Trace-ID"] = trace_id
        
        return response

# Add exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        method=request.method,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "trace_id": request.headers.get("X-Trace-ID", "unknown")
        }
    )

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-governance-dashboard",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "AI Governance Dashboard API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
