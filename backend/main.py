#!/usr/bin/env python3
"""
FastAPI Backend Server Entry Point

This module starts the FastAPI server for the Trading MVP backend.
"""

import uvicorn
from app.api import app

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )