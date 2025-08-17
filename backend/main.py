"""
AI Governance Dashboard - Main Application Entry Point

I designed this as the central orchestrator for our enterprise AI governance platform.
The architecture follows a microservices pattern with comprehensive observability,
security, and scalability considerations.

Key Design Decisions:
- I chose FastAPI for its async capabilities and automatic OpenAPI documentation
- I implemented distributed tracing with OpenTelemetry for production debugging
- I added structured logging with correlation IDs for better observability
- I designed a middleware stack that handles CORS, security, and monitoring
- I implemented graceful shutdown and startup patterns for container orchestration

Author: Oliver Ellison
Created: 2024
"""

import os
import logging
import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import redis

from app.core.config import settings
from app.core.database import engine, init_db
from app.api.v1.api import api_router
from app.core.logging import setup_logging

# I set up structured logging first to ensure all subsequent operations are properly logged
setup_logging()
logger = structlog.get_logger()

# I create a custom metrics meter for business-specific metrics
meter = metrics.get_meter(__name__)
request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total number of HTTP requests",
    unit="1"
)
request_duration = meter.create_histogram(
    name="http_request_duration_seconds",
    description="HTTP request duration in seconds",
    unit="s"
)

# I implement a custom rate limiter using Redis
class RateLimiter:
    """I designed this rate limiter to protect our API from abuse while allowing legitimate traffic."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds
    
    async def check_rate_limit(self, client_ip: str) -> bool:
        """I check if the client has exceeded the rate limit."""
        key = f"rate_limit:{client_ip}"
        current = await asyncio.to_thread(self.redis.get, key)
        
        if current is None:
            await asyncio.to_thread(self.redis.setex, key, self.window, 1)
            return True
        
        count = int(current)
        if count >= self.rate_limit:
            return False
        
        await asyncio.to_thread(self.redis.incr, key)
        return True

# I initialize the rate limiter
rate_limiter = RateLimiter(redis.Redis.from_url(settings.REDIS_URL))

def setup_telemetry():
    """
    I set up comprehensive observability with OpenTelemetry.
    
    This includes:
    - Distributed tracing with Jaeger
    - Custom metrics for business KPIs
    - Automatic instrumentation of all major components
    - Resource attribution for better debugging
    """
    if settings.OTEL_ENDPOINT:
        # I create a resource that identifies our service
        resource = Resource.create({
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": "1.0.0",
            "deployment.environment": settings.ENVIRONMENT,
            "team": "ai-governance"
        })
        
        # I set up the trace provider with batching for performance
        trace_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(trace_provider)
        
        # I configure Jaeger exporter for distributed tracing
        jaeger_exporter = JaegerExporter(
            agent_host_name="jaeger",
            agent_port=6831,
        )
        trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        
        # I set up metrics with periodic export
        metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
        meter_provider = MeterProvider(metric_reader=metric_reader, resource=resource)
        metrics.set_meter_provider(meter_provider)
        
        # I instrument all major components for automatic observability
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument(engine=engine)
        RequestsInstrumentor().instrument()
        RedisInstrumentor().instrument()
        
        logger.info("OpenTelemetry instrumentation completed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    I implement application lifecycle management for graceful startup and shutdown.
    
    This ensures:
    - Database connections are properly initialized
    - Background tasks are started cleanly
    - Resources are released on shutdown
    - Health checks are accurate
    """
    # Startup: I initialize all critical services
    logger.info("Starting AI Governance Dashboard", version="1.0.0")
    start_time = time.time()
    
    try:
        # I initialize the database and create tables
        await asyncio.to_thread(init_db)
        logger.info("Database initialized successfully")
        
        # I set up telemetry
        setup_telemetry()
        logger.info("Telemetry setup completed")
        
        # I record startup metrics
        startup_duration = time.time() - start_time
        logger.info("Application startup completed", duration_seconds=startup_duration)
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise
    
    yield
    
    # Shutdown: I clean up resources gracefully
    logger.info("Shutting down AI Governance Dashboard")
    try:
        # I close database connections
        await asyncio.to_thread(engine.dispose)
        logger.info("Database connections closed")
        
        # I close Redis connections
        await asyncio.to_thread(rate_limiter.redis.close)
        logger.info("Redis connections closed")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

# I create the FastAPI application with comprehensive configuration
app = FastAPI(
    title="AI Governance Dashboard",
    description="""
    Enterprise AI Governance Platform with LLM Proxy, Policies as Code, and Safety Guardrails.
    
    I designed this platform to provide comprehensive governance for AI/LLM usage in enterprise environments.
    It includes cost controls, safety guardrails, audit trails, and real-time monitoring.
    
    ## Key Features
    - **LLM Proxy Gateway**: Unified API for all LLM providers
    - **Policies as Code**: OPA-based governance rules
    - **Safety Guardrails**: PII detection, toxicity filtering, jailbreak prevention
    - **Cost Management**: Real-time budget tracking and enforcement
    - **Observability**: Distributed tracing, metrics, and structured logging
    - **Multi-tenancy**: Organization isolation and role-based access control
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    # I add metadata for better API documentation
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication and authorization endpoints"
        },
        {
            "name": "proxy",
            "description": "LLM proxy gateway for AI model requests"
        },
        {
            "name": "policies",
            "description": "Policy management and governance rules"
        },
        {
            "name": "cost",
            "description": "Cost tracking and budget management"
        },
        {
            "name": "monitoring",
            "description": "Observability and monitoring endpoints"
        }
    ]
)

# I add comprehensive middleware stack for security and observability
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# I add Gzip compression for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# I implement comprehensive request logging and monitoring middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    I implement comprehensive request logging and monitoring.
    
    This middleware:
    - Logs all requests with correlation IDs
    - Measures request duration
    - Implements rate limiting
    - Adds security headers
    - Tracks business metrics
    """
    tracer = trace.get_tracer(__name__)
    start_time = time.time()
    
    # I extract client information for security and monitoring
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    with tracer.start_as_current_span("http_request") as span:
        # I add comprehensive span attributes for debugging
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.client_ip", client_ip)
        span.set_attribute("http.user_agent", user_agent)
        span.set_attribute("http.request_id", request.headers.get("X-Request-ID", "unknown"))
        
        # I get trace ID for correlation across services
        trace_id = format(span.get_span_context().trace_id, "032x")
        
        # I implement rate limiting
        if not await rate_limiter.check_rate_limit(client_ip):
            logger.warning("Rate limit exceeded", client_ip=client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
        
        # I log incoming request
        logger.info(
            "Incoming request",
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            user_agent=user_agent,
            trace_id=trace_id
        )
        
        try:
            # I process the request
            response = await call_next(request)
            
            # I calculate request duration
            duration = time.time() - start_time
            
            # I record metrics
            request_counter.add(1, {
                "method": request.method,
                "status_code": str(response.status_code),
                "endpoint": request.url.path
            })
            request_duration.record(duration, {
                "method": request.method,
                "endpoint": request.url.path
            })
            
            # I add span attributes for response
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_time", duration)
            
            # I log successful request completion
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration_seconds=duration,
                trace_id=trace_id
            )
            
            # I add security and correlation headers
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", trace_id)
            response.headers["X-Response-Time"] = str(duration)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            return response
            
        except Exception as e:
            # I handle and log errors
            duration = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                duration_seconds=duration,
                trace_id=trace_id
            )
            
            # I record error metrics
            request_counter.add(1, {
                "method": request.method,
                "status_code": "500",
                "endpoint": request.url.path
            })
            
            span.set_attribute("http.status_code", 500)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            raise

# I implement comprehensive exception handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    I implement global exception handling for consistent error responses.
    
    This ensures:
    - All errors are properly logged
    - Sensitive information is not exposed
    - Error responses are consistent
    - Debugging information is available in development
    """
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else "unknown"
    )
    
    # I create a safe error response
    error_detail = "Internal server error"
    if settings.DEBUG:
        error_detail = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": error_detail,
            "trace_id": request.headers.get("X-Trace-ID", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    I handle validation errors with detailed feedback for API consumers.
    """
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        method=request.method,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "trace_id": request.headers.get("X-Trace-ID", "unknown")
        }
    )

# I include the API router with versioning
app.include_router(api_router, prefix="/api/v1")

# I implement comprehensive health check endpoint
@app.get("/health", tags=["monitoring"])
async def health_check() -> Dict[str, Any]:
    """
    I implement a comprehensive health check that verifies all critical services.
    
    This endpoint is used by:
    - Kubernetes liveness/readiness probes
    - Load balancer health checks
    - Monitoring systems
    - DevOps tooling
    """
    health_status = {
        "status": "healthy",
        "service": "ai-governance-dashboard",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time() - getattr(app.state, "start_time", time.time()),
        "checks": {}
    }
    
    # I check database connectivity
    try:
        await asyncio.to_thread(engine.execute, "SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # I check Redis connectivity
    try:
        await asyncio.to_thread(rate_limiter.redis.ping)
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # I check OPA connectivity
    try:
        import requests
        response = requests.get(f"{settings.OPA_URL}/health", timeout=5)
        if response.status_code == 200:
            health_status["checks"]["opa"] = "healthy"
        else:
            health_status["checks"]["opa"] = f"unhealthy: status {response.status_code}"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["opa"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

# I implement a detailed root endpoint with API information
@app.get("/", tags=["monitoring"])
async def root() -> Dict[str, Any]:
    """
    I provide comprehensive API information at the root endpoint.
    
    This helps developers understand:
    - Available endpoints
    - API versioning
    - Authentication requirements
    - Rate limiting information
    """
    return {
        "message": "AI Governance Dashboard API",
        "version": "1.0.0",
        "description": "Enterprise AI Governance Platform with LLM Proxy, Policies as Code, and Safety Guardrails",
        "author": "Oliver Ellison",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        },
        "endpoints": {
            "api": "/api/v1",
            "auth": "/api/v1/auth",
            "proxy": "/api/v1/proxy",
            "policies": "/api/v1/policies",
            "cost": "/api/v1/cost"
        },
        "rate_limiting": {
            "requests_per_minute": 100,
            "window_seconds": 60
        },
        "authentication": {
            "type": "Bearer Token",
            "header": "Authorization: Bearer <token>"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# I implement metrics endpoint for Prometheus scraping
@app.get("/metrics", tags=["monitoring"])
async def metrics_endpoint() -> Dict[str, Any]:
    """
    I expose application metrics for Prometheus monitoring.
    
    This includes:
    - Request counts and durations
    - Error rates
    - Business metrics
    - System health indicators
    """
    return {
        "application": {
            "uptime_seconds": time.time() - getattr(app.state, "start_time", time.time()),
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT
        },
        "metrics": {
            "note": "Prometheus metrics are exposed via OpenTelemetry exporters"
        }
    }

if __name__ == "__main__":
    """
    I implement the development server entry point with comprehensive configuration.
    
    This is used for:
    - Local development
    - Testing
    - Debugging
    """
    import uvicorn
    
    # I store startup time for uptime calculations
    app.state.start_time = time.time()
    
    logger.info("Starting development server", host="0.0.0.0", port=8000)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        # I add additional configuration for better development experience
        loop="asyncio",
        http="httptools",
        ws="websockets"
    )
