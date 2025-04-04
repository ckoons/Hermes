"""
API Endpoints - REST API for the Hermes Unified Registration Protocol.

This module provides FastAPI endpoints for component registration,
heartbeat monitoring, and service discovery.
"""

import time
import logging
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from hermes.core.registration import (
    RegistrationManager,
    generate_component_id,
    format_component_info
)
from hermes.core.service_discovery import ServiceRegistry
from hermes.core.message_bus import MessageBus

# Configure logger
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Hermes Registration API",
    description="API for the Unified Registration Protocol",
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

# Dependency to get registration manager
def get_registration_manager():
    """Get the registration manager instance."""
    # In a real implementation, this would be a singleton or stored in app state
    # For now, we'll create a new instance each time
    service_registry = ServiceRegistry()
    message_bus = MessageBus()
    
    # Start health check monitoring
    service_registry.start()
    
    return RegistrationManager(
        service_registry=service_registry,
        message_bus=message_bus,
        secret_key="tekton-secret-key"  # In production, this would be loaded from environment
    )

# Pydantic models for request/response validation

class ComponentRegistrationRequest(BaseModel):
    """Model for component registration requests."""
    component_id: Optional[str] = None
    name: str
    version: str
    component_type: str = Field(..., alias="type")
    endpoint: str
    capabilities: List[str] = []
    metadata: Dict[str, Any] = {}
    
    class Config:
        allow_population_by_field_name = True

class ComponentRegistrationResponse(BaseModel):
    """Model for component registration responses."""
    success: bool
    component_id: str
    token: Optional[str] = None
    message: Optional[str] = None

class HeartbeatRequest(BaseModel):
    """Model for heartbeat requests."""
    component_id: str
    status: Dict[str, Any] = {}

class HeartbeatResponse(BaseModel):
    """Model for heartbeat responses."""
    success: bool
    timestamp: float
    message: Optional[str] = None

class ServiceQueryRequest(BaseModel):
    """Model for service query requests."""
    capability: Optional[str] = None
    component_type: Optional[str] = None
    healthy_only: bool = False

class ServiceResponse(BaseModel):
    """Model for service information."""
    component_id: str
    name: str
    version: str
    component_type: str = Field(..., alias="type")
    endpoint: str
    capabilities: List[str]
    metadata: Dict[str, Any]
    healthy: Optional[bool] = None
    last_heartbeat: Optional[float] = None
    
    class Config:
        allow_population_by_field_name = True

# API endpoints

@app.post("/register", response_model=ComponentRegistrationResponse)
async def register_component(
    registration: ComponentRegistrationRequest,
    manager: RegistrationManager = Depends(get_registration_manager)
):
    """
    Register a component with the Tekton ecosystem.
    
    This endpoint allows components to register their presence,
    capabilities, and connection information.
    """
    # Generate component ID if not provided
    component_id = registration.component_id
    if not component_id:
        component_id = generate_component_id(
            name=registration.name,
            component_type=registration.component_type
        )
    
    # Register component
    success, token_str = manager.register_component(
        component_id=component_id,
        name=registration.name,
        version=registration.version,
        component_type=registration.component_type,
        endpoint=registration.endpoint,
        capabilities=registration.capabilities,
        metadata=registration.metadata
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Registration failed")
    
    return ComponentRegistrationResponse(
        success=True,
        component_id=component_id,
        token=token_str,
        message="Component registered successfully"
    )

@app.post("/heartbeat", response_model=HeartbeatResponse)
async def send_heartbeat(
    heartbeat: HeartbeatRequest,
    x_authentication_token: str = Header(...),
    manager: RegistrationManager = Depends(get_registration_manager)
):
    """
    Send a heartbeat to indicate a component is still active.
    
    This endpoint allows components to maintain their active status
    and update their health information.
    """
    # Send heartbeat
    success = manager.send_heartbeat(
        component_id=heartbeat.component_id,
        token_str=x_authentication_token,
        status=heartbeat.status
    )
    
    if not success:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return HeartbeatResponse(
        success=True,
        timestamp=time.time(),
        message="Heartbeat received"
    )

@app.post("/unregister")
async def unregister_component(
    component_id: str,
    x_authentication_token: str = Header(...),
    manager: RegistrationManager = Depends(get_registration_manager)
):
    """
    Unregister a component from the Tekton ecosystem.
    
    This endpoint allows components to cleanly remove themselves
    from the registry when shutting down.
    """
    # Unregister component
    success = manager.unregister_component(
        component_id=component_id,
        token_str=x_authentication_token
    )
    
    if not success:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return {"success": True, "message": "Component unregistered successfully"}

@app.post("/query", response_model=List[ServiceResponse])
async def query_services(
    query: ServiceQueryRequest,
    manager: RegistrationManager = Depends(get_registration_manager)
):
    """
    Query available services based on criteria.
    
    This endpoint allows components to discover other components
    based on capabilities, type, and health status.
    """
    # Get service registry from manager
    registry = manager.service_registry
    
    # Query services
    if query.capability:
        # Find by capability
        services = registry.find_by_capability(query.capability)
    else:
        # Get all services
        all_services = registry.get_all_services()
        services = [
            {"id": service_id, **service_info}
            for service_id, service_info in all_services.items()
        ]
    
    # Filter by component type if specified
    if query.component_type:
        services = [
            service for service in services
            if service.get("metadata", {}).get("type") == query.component_type
        ]
    
    # Filter by health status if requested
    if query.healthy_only:
        services = [
            service for service in services
            if service.get("healthy", False)
        ]
    
    # Format response
    response = []
    for service in services:
        component_id = service.get("id")
        response.append(ServiceResponse(
            component_id=component_id,
            name=service.get("name", "Unknown"),
            version=service.get("version", "Unknown"),
            type=service.get("metadata", {}).get("type", "Unknown"),
            endpoint=service.get("endpoint", ""),
            capabilities=service.get("capabilities", []),
            metadata=service.get("metadata", {}),
            healthy=service.get("healthy"),
            last_heartbeat=service.get("last_heartbeat")
        ))
    
    return response

@app.get("/health")
async def health_check():
    """
    Check the health of the registration service.
    
    This endpoint allows monitoring systems to verify that
    the registration service is operating correctly.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "0.1.0"
    }

# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Registration API starting up")
    # In a real implementation, this would initialize the registration manager
    # and any other required services
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Registration API shutting down")
    # In a real implementation, this would clean up resources
    pass