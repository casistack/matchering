#!/usr/bin/env python3
"""
Enhanced Matchering Backend Runner

Development server runner for the FastAPI backend application.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get configuration from environment
    host = os.getenv("MATCHERING_HOST", "127.0.0.1")
    port = int(os.getenv("MATCHERING_PORT", "8000"))
    debug = os.getenv("MATCHERING_DEBUG", "false").lower() == "true"
    
    print(f"Starting Enhanced Matchering API...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Environment: {os.getenv('MATCHERING_ENVIRONMENT', 'development')}")
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        access_log=debug,
        log_level="info" if debug else "warning"
    )