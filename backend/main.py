#!/usr/bin/env python3
"""
FastAPI Backend Entry Point for Trading Dashboard

This is the main entry point for launching the FastAPI server with uvicorn.
The server provides REST API endpoints for the trading dashboard frontend.
"""

import uvicorn
from app.api import app

if __name__ == "__main__":
    # Run the FastAPI application with uvicorn
    # In development: uvicorn main:app --reload --port 8000
    uvicorn.run(
        "app.api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )