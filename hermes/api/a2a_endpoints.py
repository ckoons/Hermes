"""
A2A Endpoints - REST API for Agent-to-Agent communication.

This module provides FastAPI endpoints for agent registration,
messaging, task management, and conversation management.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
a2a_router = APIRouter(
    prefix="/a2a",
    tags=["a2a"],
    responses={404: {"description": "Not found"}}
)

# Pydantic models for API

class AgentCard(BaseModel):
    """Model for agent card information."""
    agent_id: Optional[str] = None
    name: str
    version: str
    description: Optional[str] = None
    capabilities: Dict[str, Any]
    limitations: Optional[Dict[str, Any]] = None
    availability: Optional[Dict[str, Any]] = None
    endpoint: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentRegistrationResponse(BaseModel):
    """Model for agent registration responses."""
    success: bool
    agent_id: str
    message: Optional[str] = None


class MessageRequest(BaseModel):
    """Model for message requests."""
    id: Optional[str] = None
    sender: Dict[str, Any]
    recipients: List[Dict[str, Any]]
    type: str
    content: Dict[str, Any]
    conversation_id: Optional[str] = None
    reply_to: Optional[str] = None
    intent: Optional[str] = None
    priority: str = "normal"
    metadata: Optional[Dict[str, Any]] = None
    security: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Model for message responses."""
    success: bool
    message_id: str
    timestamp: float
    recipients: List[str]


class TaskSpec(BaseModel):
    """Model for task specifications."""
    id: Optional[str] = None
    name: str
    description: str
    required_capabilities: List[str]
    preferred_agent: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    deadline: Optional[float] = None
    priority: str = "normal"
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Model for task responses."""
    task_id: str
    status: str
    assigned_to: Optional[str] = None
    error: Optional[str] = None


class TaskStatusUpdate(BaseModel):
    """Model for task status updates."""
    status: str
    agent_id: Optional[str] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class ConversationRequest(BaseModel):
    """Model for conversation start requests."""
    participants: List[str]
    topic: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None


class ConversationResponse(BaseModel):
    """Model for conversation responses."""
    conversation_id: str
    participants: List[str]
    topic: str
    created_at: float


# Dependency to get A2A service from request state
async def get_a2a_service(request: Request):
    """Get the A2A service from request state."""
    if not hasattr(request.app.state, "a2a_service"):
        raise HTTPException(status_code=500, detail="A2A service not initialized")
    
    a2a_service = request.app.state.a2a_service
    
    # Ensure service is initialized
    await a2a_service.initialize()
    
    return a2a_service


# API endpoints

@a2a_router.post("/register", response_model=AgentRegistrationResponse)
async def register_agent(
    agent_card: AgentCard,
    a2a_service = Depends(get_a2a_service)
):
    """
    Register an agent with the A2A service.
    
    This endpoint allows agents to register their presence,
    capabilities, and connection information.
    """
    success = await a2a_service.register_agent(agent_card.dict())
    
    if not success:
        raise HTTPException(status_code=400, detail="Registration failed")
    
    return AgentRegistrationResponse(
        success=True,
        agent_id=agent_card.agent_id or "unknown",
        message="Agent registered successfully"
    )


@a2a_router.post("/unregister")
async def unregister_agent(
    agent_id: str,
    a2a_service = Depends(get_a2a_service)
):
    """
    Unregister an agent from the A2A service.
    
    This endpoint allows agents to cleanly remove themselves
    from the registry when shutting down.
    """
    success = await a2a_service.unregister_agent(agent_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"success": True, "message": "Agent unregistered successfully"}


@a2a_router.post("/message", response_model=MessageResponse)
async def send_message(
    message: MessageRequest,
    a2a_service = Depends(get_a2a_service)
):
    """
    Send a message to one or more agents.
    
    This endpoint allows agents to send messages to other agents
    based on agent ID or capabilities.
    """
    msg_dict = message.dict()
    
    # Add message ID if not provided
    if not message.id:
        msg_dict["id"] = f"msg-{int(time.time() * 1000)}"
    
    success = await a2a_service.send_message(msg_dict)
    
    if not success:
        raise HTTPException(status_code=400, detail="Message sending failed")
    
    # Get recipient IDs
    recipient_ids = []
    for recipient in message.recipients:
        if recipient.get("type") == "direct":
            recipient_ids.append(recipient.get("id", "unknown"))
        # Other recipient types would be resolved by the service
    
    return MessageResponse(
        success=True,
        message_id=msg_dict["id"],
        timestamp=time.time(),
        recipients=recipient_ids
    )


@a2a_router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_spec: TaskSpec,
    a2a_service = Depends(get_a2a_service)
):
    """
    Create a new task.
    
    This endpoint allows agents to create tasks that can be
    assigned to other agents based on capabilities.
    """
    result = await a2a_service.create_task(task_spec.dict())
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return TaskResponse(
        task_id=result["task_id"],
        status=result["status"],
        assigned_to=None  # Task will be assigned asynchronously if needed
    )


@a2a_router.post("/tasks/{task_id}/assign")
async def assign_task(
    task_id: str,
    agent_id: str,
    a2a_service = Depends(get_a2a_service)
):
    """
    Assign a task to a specific agent.
    
    This endpoint allows manual assignment of tasks to specific agents.
    """
    success = await a2a_service.assign_task(task_id, agent_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Task assignment failed")
    
    return {"success": True, "task_id": task_id, "assigned_to": agent_id}


@a2a_router.post("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    status_update: TaskStatusUpdate,
    a2a_service = Depends(get_a2a_service)
):
    """
    Update a task's status.
    
    This endpoint allows agents to update the status of tasks
    they are working on, including providing results.
    """
    success = await a2a_service.update_task_status(
        task_id=task_id,
        status=status_update.status,
        agent_id=status_update.agent_id,
        message=status_update.message,
        result=status_update.result
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"success": True, "task_id": task_id, "status": status_update.status}


@a2a_router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    a2a_service = Depends(get_a2a_service)
):
    """
    Get task information.
    
    This endpoint allows retrieval of information about a specific task.
    """
    task = await a2a_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@a2a_router.post("/conversations", response_model=ConversationResponse)
async def start_conversation(
    conversation_req: ConversationRequest,
    a2a_service = Depends(get_a2a_service)
):
    """
    Start a new conversation.
    
    This endpoint creates a new conversation between multiple agents.
    """
    conversation_id = await a2a_service.start_conversation(
        participants=conversation_req.participants,
        topic=conversation_req.topic,
        context=conversation_req.context,
        conversation_id=conversation_req.conversation_id
    )
    
    if not conversation_id:
        raise HTTPException(status_code=400, detail="Failed to start conversation")
    
    # Get the created conversation
    conversation = await a2a_service.get_conversation(conversation_id)
    
    return ConversationResponse(
        conversation_id=conversation_id,
        participants=conversation["participants"],
        topic=conversation["topic"],
        created_at=conversation["created_at"]
    )


@a2a_router.post("/conversations/{conversation_id}/messages")
async def add_to_conversation(
    conversation_id: str,
    message: MessageRequest,
    a2a_service = Depends(get_a2a_service)
):
    """
    Add a message to a conversation.
    
    This endpoint adds a message to an existing conversation.
    """
    # Ensure message has the conversation ID
    msg_dict = message.dict()
    msg_dict["conversation_id"] = conversation_id
    
    success = await a2a_service.add_to_conversation(conversation_id, msg_dict)
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "message_id": msg_dict.get("id")
    }


@a2a_router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    a2a_service = Depends(get_a2a_service)
):
    """
    Get conversation information.
    
    This endpoint retrieves information about a specific conversation.
    """
    conversation = await a2a_service.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@a2a_router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    a2a_service = Depends(get_a2a_service)
):
    """
    Get agent information.
    
    This endpoint retrieves information about a specific agent.
    """
    agent = await a2a_service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent