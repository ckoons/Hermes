"""
LLM adapter for Hermes.

This module provides a client for interacting with LLMs through the Tekton LLM Adapter.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)

class LLMAdapter:
    """Client for interacting with LLMs through the Tekton LLM Adapter."""
    
    def __init__(self, adapter_url: Optional[str] = None):
        """
        Initialize the LLM adapter.
        
        Args:
            adapter_url: URL for the LLM adapter service
        """
        # Default to the environment variable or standard port from the Single Port Architecture
        rhetor_port = os.environ.get("RHETOR_PORT", "8003")
        default_adapter_url = f"http://localhost:{rhetor_port}"
        
        self.adapter_url = adapter_url or os.environ.get("LLM_ADAPTER_URL", default_adapter_url)
        self.default_provider = os.environ.get("LLM_PROVIDER", "anthropic")
        self.default_model = os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
        
    async def get_available_providers(self) -> Dict[str, Any]:
        """
        Get available LLM providers.
        
        Returns:
            Dict of available providers and their models
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.adapter_url}/providers", timeout=5.0) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to get providers: {response.status}")
        except Exception as e:
            logger.error(f"Error getting providers: {e}")
        
        # Return default providers if the API call fails
        return {
            self.default_provider: {
                "available": True,
                "models": [
                    {"id": self.default_model, "name": "Default Model"},
                    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
                    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
                ]
            }
        }
    
    def get_current_provider_and_model(self) -> Tuple[str, str]:
        """
        Get the current provider and model.
        
        Returns:
            Tuple of (provider_id, model_id)
        """
        return (self.default_provider, self.default_model)
    
    def set_provider_and_model(self, provider_id: str, model_id: str) -> None:
        """
        Set the provider and model to use.
        
        Args:
            provider_id: Provider ID
            model_id: Model ID
        """
        self.default_provider = provider_id
        self.default_model = model_id
    
    async def analyze_message(self, message_content: str, message_type: str = "standard") -> Dict[str, Any]:
        """
        Analyze a message using LLM.
        
        Args:
            message_content: Message content
            message_type: Type of message (standard, log, registration, etc.)
            
        Returns:
            Analysis results
        """
        try:
            # Try to use the LLM adapter service
            prompt = """
            Analyze the following message that was sent through the Hermes message bus. 
            Extract key information such as:
            1. Message purpose - What is the goal of this message?
            2. Components involved - Which components are mentioned or interacting?
            3. Data contents - What key data is being transmitted?
            4. Priority - How urgent or important does this message appear to be?
            
            Provide a brief summary of what this message is trying to accomplish in the system.
            
            Message:
            """
            
            message_data = {
                "message": f"{prompt}\n\n{message_content}",
                "context_id": f"hermes:message_analysis:{message_type}",
                "task_type": "analysis",
                "component": "hermes",
                "streaming": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.adapter_url}/message", 
                    json=message_data,
                    timeout=30.0
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_analysis_response(result)
                    else:
                        logger.warning(f"Failed to analyze message: {response.status}")
                        
            # If we get here, the request failed
            return {
                "purpose": "Unknown",
                "components": [],
                "data_summary": "Could not analyze message",
                "priority": "Unknown",
                "summary": "Failed to connect to LLM service."
            }
            
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return {
                "purpose": "Unknown",
                "components": [],
                "data_summary": "Error in analysis",
                "priority": "Unknown",
                "summary": f"Error analyzing message: {str(e)}"
            }
    
    async def analyze_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a service registration using LLM.
        
        Args:
            service_data: Service registration data
            
        Returns:
            Analysis results
        """
        try:
            # Try to use the LLM adapter service
            prompt = """
            Analyze the following service registration in the Tekton platform. 
            Extract key information such as:
            1. Service capabilities - What functionality does this service provide?
            2. Dependencies - What other services might this service depend on?
            3. Integration points - How would other services interact with this one?
            4. Potential use cases - What problems does this service solve?
            
            Provide a brief summary of this service's role in the system.
            
            Service Data:
            """
            
            message_data = {
                "message": f"{prompt}\n\n{json.dumps(service_data, indent=2)}",
                "context_id": "hermes:service_analysis",
                "task_type": "analysis",
                "component": "hermes",
                "streaming": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.adapter_url}/message", 
                    json=message_data,
                    timeout=30.0
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_service_analysis_response(result)
                    else:
                        logger.warning(f"Failed to analyze service: {response.status}")
                        
            # If we get here, the request failed
            return {
                "capabilities": [],
                "dependencies": [],
                "integration_points": [],
                "use_cases": [],
                "summary": "Failed to connect to LLM service."
            }
            
        except Exception as e:
            logger.error(f"Error analyzing service: {e}")
            return {
                "capabilities": [],
                "dependencies": [],
                "integration_points": [],
                "use_cases": [],
                "summary": f"Error analyzing service: {str(e)}"
            }
    
    async def chat(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Send a chat message to the LLM.
        
        Args:
            message: User message
            chat_history: Optional chat history for context
            
        Returns:
            LLM response
        """
        try:
            # Prepare message data
            message_data = {
                "messages": [],
                "context_id": "hermes:chat",
                "task_type": "chat",
                "component": "hermes",
                "streaming": False,
                "model": self.default_model,
                "provider": self.default_provider
            }
            
            # Add system message
            system_message = {
                "role": "system",
                "content": """You are a helpful assistant for the Hermes component in the Tekton platform. 
                Hermes provides message bus and service discovery capabilities for the Tekton system.
                You can help users understand how Hermes works, how services register and communicate,
                and provide debugging assistance for message routing and service discovery issues."""
            }
            message_data["messages"].append(system_message)
            
            # Add chat history if provided
            if chat_history:
                message_data["messages"].extend(chat_history)
            
            # Add the current user message
            message_data["messages"].append({
                "role": "user",
                "content": message
            })
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.adapter_url}/chat", 
                    json=message_data,
                    timeout=60.0
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "message": result.get("message", ""),
                            "success": True
                        }
                    else:
                        logger.warning(f"Failed to get chat response: {response.status}")
                        
            # If we get here, the request failed
            return {
                "message": "I'm having trouble connecting to my language model service. Please try again later.",
                "success": False
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "message": f"I encountered an error: {str(e)}. Please try again later.",
                "success": False
            }
    
    async def streaming_chat(self, 
                            message: str, 
                            callback: Any,
                            chat_history: Optional[List[Dict[str, str]]] = None):
        """
        Send a chat message to the LLM with streaming response.
        
        Args:
            message: User message
            callback: Callback function to receive streaming chunks
            chat_history: Optional chat history for context
        """
        try:
            # Prepare message data
            message_data = {
                "messages": [],
                "context_id": "hermes:chat:streaming",
                "task_type": "chat",
                "component": "hermes",
                "streaming": True,
                "model": self.default_model,
                "provider": self.default_provider
            }
            
            # Add system message
            system_message = {
                "role": "system",
                "content": """You are a helpful assistant for the Hermes component in the Tekton platform. 
                Hermes provides message bus and service discovery capabilities for the Tekton system.
                You can help users understand how Hermes works, how services register and communicate,
                and provide debugging assistance for message routing and service discovery issues."""
            }
            message_data["messages"].append(system_message)
            
            # Add chat history if provided
            if chat_history:
                message_data["messages"].extend(chat_history)
            
            # Add the current user message
            message_data["messages"].append({
                "role": "user",
                "content": message
            })
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.adapter_url}/chat/stream", 
                    json=message_data,
                    timeout=60.0
                ) as response:
                    if response.status == 200:
                        # Process the stream
                        async for line in response.content:
                            if line:
                                try:
                                    line_text = line.decode('utf-8').strip()
                                    if line_text.startswith('data: '):
                                        line_text = line_text[6:]  # Remove 'data: ' prefix
                                    if line_text and line_text != '[DONE]':
                                        try:
                                            chunk = json.loads(line_text)
                                            await callback(chunk)
                                        except json.JSONDecodeError:
                                            logger.error(f"Error decoding JSON: {line_text}")
                                except Exception as e:
                                    logger.error(f"Error processing stream chunk: {e}")
                        
                        # Signal that streaming is complete
                        await callback({"done": True})
                    else:
                        logger.warning(f"Failed to get streaming response: {response.status}")
                        error_text = await response.text()
                        await callback({
                            "chunk": "I'm having trouble connecting to my language model service.",
                            "error": error_text,
                            "done": True
                        })
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            await callback({
                "chunk": f"I encountered an error: {str(e)}. Please try again later.",
                "error": str(e),
                "done": True
            })
    
    def _parse_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LLM message analysis response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed analysis
        """
        message = response.get("message", "")
        
        # Extract key information using basic parsing
        # More sophisticated implementations could use structured outputs
        
        # Extract message purpose
        purpose = "Unknown"
        for line in message.split("\n"):
            if "purpose" in line.lower() or "goal" in line.lower():
                if ":" in line:
                    purpose = line.split(":", 1)[1].strip()
                    break
        
        # Extract components
        components = []
        components_section = False
        for line in message.split("\n"):
            if "components" in line.lower() and ":" in line:
                components_section = True
                components_text = line.split(":", 1)[1].strip()
                if components_text:
                    components = [c.strip() for c in components_text.split(",")]
                continue
            
            if components_section and line.strip():
                if ":" in line:  # New section
                    components_section = False
                elif line.strip().startswith("-"):
                    comp = line.strip()[1:].strip()
                    if comp:
                        components.append(comp)
        
        # Extract data summary
        data_summary = "Unknown"
        for line in message.split("\n"):
            if "data" in line.lower() and "content" in line.lower() and ":" in line:
                data_summary = line.split(":", 1)[1].strip()
                break
        
        # Extract priority
        priority = "Unknown"
        for line in message.split("\n"):
            if "priority" in line.lower() and ":" in line:
                priority = line.split(":", 1)[1].strip()
                break
        
        # Extract summary
        summary = ""
        summary_section = False
        for line in message.split("\n"):
            if "summary" in line.lower() and ":" in line:
                summary_section = True
                summary = line.split(":", 1)[1].strip()
                continue
            
            if summary_section and line.strip():
                if ":" in line and any(kw in line.lower() for kw in ["purpose", "components", "data", "priority"]):
                    summary_section = False
                else:
                    summary += " " + line.strip()
        
        if not summary:
            # If we couldn't find an explicit summary, use the last paragraph
            paragraphs = [p for p in message.split("\n\n") if p.strip()]
            if paragraphs:
                summary = paragraphs[-1].strip()
        
        return {
            "purpose": purpose,
            "components": components,
            "data_summary": data_summary,
            "priority": priority,
            "summary": summary,
            "full_analysis": message
        }
    
    def _parse_service_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LLM service analysis response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed analysis
        """
        message = response.get("message", "")
        
        # Extract capabilities, dependencies, etc. using basic parsing
        capabilities = []
        dependencies = []
        integration_points = []
        use_cases = []
        summary = ""
        
        current_section = None
        
        for line in message.split("\n"):
            line = line.strip()
            if not line:
                continue
            
            if "capabilities" in line.lower() and ":" in line:
                current_section = "capabilities"
                continue
            elif "dependencies" in line.lower() and ":" in line:
                current_section = "dependencies"
                continue
            elif "integration" in line.lower() and ":" in line:
                current_section = "integration_points"
                continue
            elif "use case" in line.lower() and ":" in line:
                current_section = "use_cases"
                continue
            elif "summary" in line.lower() and ":" in line:
                current_section = "summary"
                summary = line.split(":", 1)[1].strip()
                continue
            
            if current_section == "capabilities" and line.startswith("-"):
                capabilities.append(line[1:].strip())
            elif current_section == "dependencies" and line.startswith("-"):
                dependencies.append(line[1:].strip())
            elif current_section == "integration_points" and line.startswith("-"):
                integration_points.append(line[1:].strip())
            elif current_section == "use_cases" and line.startswith("-"):
                use_cases.append(line[1:].strip())
            elif current_section == "summary":
                summary += " " + line
        
        if not summary:
            # If we couldn't find an explicit summary, use the last paragraph
            paragraphs = [p for p in message.split("\n\n") if p.strip()]
            if paragraphs:
                summary = paragraphs[-1].strip()
        
        return {
            "capabilities": capabilities,
            "dependencies": dependencies,
            "integration_points": integration_points,
            "use_cases": use_cases,
            "summary": summary,
            "full_analysis": message
        }