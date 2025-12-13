"""
FastAPI Main Application
DOS Attack Map - Backend API with Cloudflare GraphQL Integration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
from datetime import datetime
import logging

# Import routers
from app.api.routes import attacks, statistics, websocket, health

# Import database
from app.database import engine, test_connection

# Import Cloudflare GraphQL task
from app.tasks.fetch_cloudflare_graphql import run_graphql_fetch_task

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
API_VERSION = "2.0.0"

# Scheduler instance
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    """
    # Startup
    logger.info("🚀 Starting DOS Attack Map API with Cloudflare GraphQL...")
    
    # Test database connection
    if test_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.warning("⚠️  Database connection failed")
    
    # Load ML model
    try:
        from app.ml.predictor import AttackPredictor
        app.state.ml_predictor = AttackPredictor()
        logger.info("✅ ML model loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️  ML model failed to load: {e}")
        app.state.ml_predictor = None
    
    # Setup Cloudflare GraphQL scheduler
    try:
        fetch_interval = int(os.getenv("FETCH_INTERVAL", "5"))
        
        # Add scheduled job
        scheduler.add_job(
            run_graphql_fetch_task,
            trigger=IntervalTrigger(minutes=fetch_interval),
            id="fetch_cloudflare_graphql",
            name="Fetch Cloudflare GraphQL Data",
            replace_existing=True
        )
        
        # Start scheduler
        scheduler.start()
        logger.info(f"⏰ GraphQL Scheduler started - fetching every {fetch_interval} minutes")
        
        # Run initial fetch (in background task to avoid blocking)
        logger.info("🔄 Scheduling initial Cloudflare GraphQL fetch...")
        import asyncio
        from app.tasks.fetch_cloudflare_graphql import fetch_cloudflare_data_graphql
        
        # Create background task for initial fetch
        asyncio.create_task(fetch_cloudflare_data_graphql())
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info(f"✅ API ready on port {os.getenv('API_PORT', 8000)}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DOS Attack Map API...")
    
    # Shutdown scheduler
    try:
        scheduler.shutdown()
        logger.info("✅ Scheduler shut down gracefully")
    except Exception as e:
        logger.error(f"❌ Error shutting down scheduler: {e}")


# Create FastAPI app
app = FastAPI(
    title="DOS Attack Map API (GraphQL Powered)",
    description="Real-time DOS attack visualization with Cloudflare GraphQL integration",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(attacks.router, prefix="/api/attacks", tags=["Attacks"])
app.include_router(statistics.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "name": "DOS Attack Map API",
        "version": API_VERSION,
        "graphql_enabled": True,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "attacks": "/api/attacks",
            "statistics": "/api/stats",
            "websocket": "/ws/attacks",
            "scheduler": "/scheduler/status"
        }
    }


# Scheduler status endpoint
@app.get("/scheduler/status")
async def scheduler_status():
    """Get Cloudflare GraphQL scheduler status"""
    try:
        jobs = scheduler.get_jobs()
        
        return {
            "running": scheduler.running,
            "state": str(scheduler.state),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                }
                for job in jobs
            ]
        }
    except Exception as e:
        return {
            "running": False,
            "error": str(e)
        }


# Cloudflare configuration endpoint
@app.get("/cloudflare/config")
async def cloudflare_config():
    """Get Cloudflare GraphQL configuration"""
    return {
        "demo_mode": os.getenv("CLOUDFLARE_DEMO_MODE", "true").lower() == "true",
        "fetch_interval_minutes": int(os.getenv("FETCH_INTERVAL", "5")),
        "zone_id_configured": bool(os.getenv("CLOUDFLARE_ZONE_ID")),
        "api_token_configured": bool(os.getenv("CLOUDFLARE_API_TOKEN"))
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
