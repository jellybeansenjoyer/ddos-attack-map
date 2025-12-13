"""
FastAPI Main Application
DOS Attack Map - Backend API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from datetime import datetime

# Import routers
from app.api.routes import attacks, statistics, websocket, health

# Import database
from app_database import engine, test_connection

# Version
API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    """
    # Startup
    print("🚀 Starting DOS Attack Map API...")
    
    # Test database connection
    if test_connection():
        print("✅ Database connection successful")
    else:
        print("⚠️  Database connection failed")
    
    # Load ML model
    try:
        from ml_predictor import AttackPredictor
        app.state.ml_predictor = AttackPredictor()
        print("✅ ML model loaded successfully")
    except Exception as e:
        print(f"⚠️  ML model failed to load: {e}")
        app.state.ml_predictor = None
    
    print(f"✅ API ready on port {os.getenv('API_PORT', 8000)}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down DOS Attack Map API...")


# Create FastAPI app
app = FastAPI(
    title="DOS Attack Map API",
    description="Real-time DOS attack visualization and classification system",
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
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "attacks": "/api/attacks",
            "statistics": "/api/stats",
            "websocket": "/ws/attacks"
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
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
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
