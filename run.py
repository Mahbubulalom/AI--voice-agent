"""
Update app.py to include API routes
"""

import os
import uvicorn
from fastapi import FastAPI
from src.api.routes import router as api_router

# Update main app to include the API routes
from app import app

# Include API routes
app.include_router(api_router)

# When running this file directly, start the server
if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    # Start uvicorn server
    uvicorn.run("app:app", host=host, port=port, reload=debug)
