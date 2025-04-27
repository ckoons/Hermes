"""
API Server - Main entry point for the Hermes API server.

This module provides the main application server for the Hermes API,
integrating all API endpoints and initializing required services.
"""

import os
import sys
import logging
import uvicorn
import asyncio
import subprocess
import signal
import atexit
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hermes.core.service_discovery import ServiceRegistry
from hermes.core.message_bus import MessageBus
from hermes.core.registration import RegistrationManager
from hermes.core.database.manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import API endpoints
from hermes.api.endpoints import app as api_app
from hermes.api.database import api_router as database_router
from hermes.api.llm_endpoints import llm_router

# Main FastAPI application
app = FastAPI(
    title="Hermes API",
    description="Unified Registration Protocol and Database Services API",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API endpoints
app.mount("/api", api_app)

# Add database API routes
api_app.include_router(database_router)

# Add LLM API routes
api_app.include_router(llm_router)

# Create service registry and message bus instances
service_registry = ServiceRegistry()
message_bus = MessageBus()

# Create registration manager
registration_manager = RegistrationManager(
    service_registry=service_registry,
    message_bus=message_bus,
    secret_key=os.environ.get("HERMES_SECRET_KEY", "tekton-secret-key"),
)

# Create LLM adapter
from hermes.core.llm_adapter import LLMAdapter
llm_adapter = LLMAdapter()

# Create database manager
database_manager = DatabaseManager(
    base_path=os.environ.get("HERMES_DATA_DIR", "~/.tekton/data")
)

# Track the database MCP server process
database_mcp_process = None

# Add application state
app.state.service_registry = service_registry
app.state.message_bus = message_bus
app.state.registration_manager = registration_manager
app.state.database_manager = database_manager
app.state.llm_adapter = llm_adapter

async def start_database_mcp_server():
    """Start the Database MCP server as a separate process."""
    global database_mcp_process
    
    # Get configuration from environment
    db_mcp_port = os.environ.get("DB_MCP_PORT", "8002")
    db_mcp_host = os.environ.get("DB_MCP_HOST", "127.0.0.1")
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"
    data_dir = os.environ.get("HERMES_DATA_DIR", "~/.tekton/data")
    
    # Find the script path
    project_root = Path(__file__).parent.parent.parent.parent
    script_path = project_root / "scripts" / "run_database_mcp.py"
    
    if not script_path.exists():
        logger.error(f"Database MCP server script not found at {script_path}")
        return False
    
    # Build command arguments
    cmd = [
        sys.executable,
        str(script_path),
        "--port", db_mcp_port,
        "--host", db_mcp_host,
        "--data-dir", data_dir
    ]
    
    if debug_mode:
        cmd.append("--debug")
    
    try:
        # Start the process
        logger.info(f"Starting Database MCP server: {' '.join(cmd)}")
        database_mcp_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Register cleanup function
        atexit.register(stop_database_mcp_server)
        
        # Wait a bit for the server to start
        await asyncio.sleep(2)
        
        # Check if the process is still running
        if database_mcp_process.poll() is None:
            logger.info("Database MCP server started successfully")
            return True
        else:
            # Process has terminated
            stdout, stderr = database_mcp_process.communicate()
            logger.error(f"Database MCP server failed to start: {stderr}")
            return False
    except Exception as e:
        logger.error(f"Error starting Database MCP server: {e}")
        return False

def stop_database_mcp_server():
    """Stop the Database MCP server process."""
    global database_mcp_process
    
    if database_mcp_process:
        logger.info("Stopping Database MCP server")
        
        try:
            # Send SIGTERM signal
            database_mcp_process.terminate()
            
            # Wait for graceful shutdown (max 5 seconds)
            try:
                database_mcp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                database_mcp_process.kill()
            
            logger.info("Database MCP server stopped")
        except Exception as e:
            logger.error(f"Error stopping Database MCP server: {e}")
        
        database_mcp_process = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Hermes API server starting up")
    
    # Start service registry health check monitoring
    service_registry.start()
    
    # Start database MCP server in a separate process
    await start_database_mcp_server()
    
    # Register the API server itself
    component_id = "hermes-api"
    success, _ = registration_manager.register_component(
        component_id=component_id,
        name="Hermes API Server",
        version="0.1.0",
        component_type="hermes",
        endpoint=f"http://localhost:{os.environ.get('PORT', '8000')}/api",
        capabilities=["registration", "service_discovery", "message_bus", "database"],
        metadata={
            "description": "Central registration and messaging service for Tekton ecosystem"
        }
    )
    
    if success:
        logger.info(f"Hermes API server registered with ID: {component_id}")
    else:
        logger.warning("Failed to register Hermes API server")
    
    # Register the database MCP server
    db_component_id = "hermes-database-mcp"
    db_port = os.environ.get("DB_MCP_PORT", "8002")
    
    success, _ = registration_manager.register_component(
        component_id=db_component_id,
        name="Hermes Database MCP Server",
        version="0.1.0",
        component_type="hermes",
        endpoint=f"http://localhost:{db_port}",
        capabilities=["database", "mcp"],
        metadata={
            "description": "Database services provider for Tekton ecosystem",
            "supported_databases": ["vector", "graph", "key_value", "document", "cache", "relation"]
        }
    )
    
    if success:
        logger.info(f"Database MCP server registered with ID: {db_component_id}")
    else:
        logger.warning("Failed to register Database MCP server")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Hermes API server shutting down")
    
    # Stop service registry monitoring
    service_registry.stop()
    
    # Close all database connections
    await database_manager.close_all_connections()
    
    # Stop the database MCP server
    stop_database_mcp_server()

@app.get("/")
async def root():
    """Root endpoint that redirects to the API documentation."""
    return {"message": "Welcome to Hermes API. Visit /docs for API documentation."}

def run_server():
    """Run the Hermes API server."""
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting Hermes API server on {host}:{port}")
    uvicorn.run(
        "hermes.api.app:app",
        host=host,
        port=port,
        reload=os.environ.get("DEBUG", "False").lower() == "true"
    )

if __name__ == "__main__":
    run_server()