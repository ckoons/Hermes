"""
LLM Chat Endpoints - REST API for interacting with the LLM adapter.

This module provides FastAPI endpoints for LLM-powered chat and analysis
through the Rhetor LLM adapter.
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from hermes.core.llm_adapter import LLMAdapter

# Configure logger
logger = logging.getLogger(__name__)

# Create API router
llm_router = APIRouter(prefix="/llm", tags=["llm"])

# Initialize LLM adapter
llm_adapter = LLMAdapter()

# Pydantic models for request/response validation

class ChatMessage(BaseModel):
    """Model for chat messages."""
    role: str
    content: str
    timestamp: Optional[float] = None

class ChatRequest(BaseModel):
    """Model for chat requests."""
    message: str
    history: Optional[List[ChatMessage]] = []
    stream: bool = False
    model: Optional[str] = None
    provider: Optional[str] = None

class ChatResponse(BaseModel):
    """Model for chat responses."""
    message: str
    model: str
    provider: str
    timestamp: float

class AnalyzeMessageRequest(BaseModel):
    """Model for message analysis requests."""
    message: str
    message_type: str = "standard"

class AnalyzeServiceRequest(BaseModel):
    """Model for service analysis requests."""
    service_data: Dict[str, Any]

class AnalysisResponse(BaseModel):
    """Model for analysis responses."""
    analysis: Dict[str, Any]
    timestamp: float

class ProvidersResponse(BaseModel):
    """Model for available providers response."""
    providers: Dict[str, Any]
    current_provider: str
    current_model: str

# API endpoints

@llm_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the LLM and get a response.
    
    This endpoint allows components to interact with the LLM
    for text generation.
    """
    try:
        # Convert history format
        chat_history = []
        if request.history:
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.history
            ]
        
        # If provider/model specified, set it for this request
        if request.provider and request.model:
            llm_adapter.set_provider_and_model(request.provider, request.model)
        
        # Get provider and model info
        provider, model = llm_adapter.get_current_provider_and_model()
        
        # Send chat message to LLM
        response = await llm_adapter.chat(request.message, chat_history)
        
        return ChatResponse(
            message=response["message"],
            model=model,
            provider=provider,
            timestamp=time.time()
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@llm_router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Send a message to the LLM and get a streaming response.
    
    This endpoint allows components to interact with the LLM
    for streaming text generation.
    """
    try:
        # Convert history format
        chat_history = []
        if request.history:
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.history
            ]
        
        # If provider/model specified, set it for this request
        if request.provider and request.model:
            llm_adapter.set_provider_and_model(request.provider, request.model)
        
        # Create async generator for streaming response
        async def generate():
            # Buffer for collecting chunks
            buffer = []
            
            # Callback to handle streaming chunks
            async def handle_chunk(chunk):
                # Format the chunk
                chunk_text = chunk.get("chunk", "")
                done = chunk.get("done", False)
                error = chunk.get("error", None)
                
                if error:
                    # Send error as event
                    data = json.dumps({"error": error, "done": True})
                    yield f"data: {data}\n\n"
                    return
                
                if done:
                    # Signal the end of streaming
                    yield "data: [DONE]\n\n"
                    return
                
                if chunk_text:
                    # Send chunk as event
                    data = json.dumps({"chunk": chunk_text, "done": False})
                    yield f"data: {data}\n\n"
            
            # Start streaming
            await llm_adapter.streaming_chat(
                request.message,
                handle_chunk,
                chat_history
            )
        
        # Return streaming response
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    except Exception as e:
        logger.error(f"Error in chat stream endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing streaming chat: {str(e)}")

@llm_router.post("/analyze/message", response_model=AnalysisResponse)
async def analyze_message(request: AnalyzeMessageRequest):
    """
    Analyze a message using the LLM.
    
    This endpoint allows components to analyze message content
    for various purposes.
    """
    try:
        analysis = await llm_adapter.analyze_message(
            request.message,
            request.message_type
        )
        
        return AnalysisResponse(
            analysis=analysis,
            timestamp=time.time()
        )
    except Exception as e:
        logger.error(f"Error in analyze message endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing message: {str(e)}")

@llm_router.post("/analyze/service", response_model=AnalysisResponse)
async def analyze_service(request: AnalyzeServiceRequest):
    """
    Analyze a service registration using the LLM.
    
    This endpoint allows components to analyze service data
    to extract capabilities and dependencies.
    """
    try:
        analysis = await llm_adapter.analyze_service(request.service_data)
        
        return AnalysisResponse(
            analysis=analysis,
            timestamp=time.time()
        )
    except Exception as e:
        logger.error(f"Error in analyze service endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing service: {str(e)}")

@llm_router.get("/providers", response_model=ProvidersResponse)
async def get_providers():
    """
    Get available LLM providers and models.
    
    This endpoint allows components to discover available
    LLM providers and models.
    """
    try:
        providers = await llm_adapter.get_available_providers()
        provider, model = llm_adapter.get_current_provider_and_model()
        
        return ProvidersResponse(
            providers=providers,
            current_provider=provider,
            current_model=model
        )
    except Exception as e:
        logger.error(f"Error in get providers endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting providers: {str(e)}")

@llm_router.post("/provider")
async def set_provider(provider: str, model: str):
    """
    Set the LLM provider and model to use.
    
    This endpoint allows components to select which
    LLM provider and model to use for subsequent requests.
    """
    try:
        llm_adapter.set_provider_and_model(provider, model)
        
        return {
            "success": True,
            "provider": provider,
            "model": model,
            "message": f"Provider set to {provider} with model {model}"
        }
    except Exception as e:
        logger.error(f"Error in set provider endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error setting provider: {str(e)}")

# WebSocket endpoint for chat
@llm_router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    
    This endpoint allows components to establish a WebSocket connection
    for real-time, bi-directional chat with the LLM.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse client message
                request_data = json.loads(data)
                message = request_data.get("message", "")
                
                if not message:
                    await websocket.send_json({
                        "error": "No message provided",
                        "success": False
                    })
                    continue
                
                # Extract options
                chat_history = request_data.get("history", [])
                provider = request_data.get("provider")
                model = request_data.get("model")
                
                # Set provider/model if specified
                if provider and model:
                    llm_adapter.set_provider_and_model(provider, model)
                
                # Get current provider/model
                current_provider, current_model = llm_adapter.get_current_provider_and_model()
                
                # Callback for streaming response
                async def handle_chunk(chunk):
                    chunk_text = chunk.get("chunk", "")
                    done = chunk.get("done", False)
                    error = chunk.get("error", None)
                    
                    if error:
                        await websocket.send_json({
                            "error": error,
                            "success": False,
                            "done": True
                        })
                        return
                    
                    if chunk_text:
                        await websocket.send_json({
                            "chunk": chunk_text,
                            "done": False,
                            "success": True
                        })
                    
                    if done:
                        await websocket.send_json({
                            "done": True,
                            "success": True,
                            "provider": current_provider,
                            "model": current_model
                        })
                
                # Start streaming response
                await llm_adapter.streaming_chat(
                    message,
                    handle_chunk,
                    chat_history
                )
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON format",
                    "success": False
                })
            except Exception as e:
                logger.error(f"Error in WebSocket chat: {e}")
                await websocket.send_json({
                    "error": f"Error processing chat: {str(e)}",
                    "success": False
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "error": f"WebSocket error: {str(e)}",
                "success": False
            })
        except:
            pass