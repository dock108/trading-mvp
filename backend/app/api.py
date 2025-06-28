"""
FastAPI Application Configuration

Main FastAPI app instance with CORS middleware and route includes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .routes import config, strategies, files

# Create FastAPI application
app = FastAPI(
    title="Trading Dashboard API",
    description="REST API for the Trading MVP Web Dashboard",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Enable CORS for frontend development
# In production, this should be more restrictive
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(config.router, prefix="/api", tags=["configuration"])
app.include_router(strategies.router, prefix="/api", tags=["strategies"])
app.include_router(files.router, prefix="/api", tags=["files"])

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "Trading Dashboard API is running"}

# Mount static files for serving the React frontend (production use)
# In development, the React dev server will run separately
frontend_build_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "build")
if os.path.exists(frontend_build_path):
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="frontend")

# Root redirect for API documentation
@app.get("/")
async def root():
    """Root endpoint - redirects to API docs in development"""
    return {"message": "Trading Dashboard API", "docs": "/api/docs"}