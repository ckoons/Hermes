"""
MCP Service - Hermes integration for Multimodal Cognitive Protocol.

This module provides a service for multimodal information processing,
enabling components to handle and process multimodal content.
"""

import time
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union, Set

from hermes.core.service_discovery import ServiceRegistry
from hermes.core.message_bus import MessageBus
from hermes.core.registration import RegistrationManager

logger = logging.getLogger(__name__)

class MCPService:
    """
    Service for multimodal information processing in Hermes.
    
    This class provides a service for multimodal information processing,
    enabling components to handle and process multimodal content.
    """
    
    def __init__(
        self,
        service_registry: ServiceRegistry,
        message_bus: MessageBus,
        registration_manager: Optional[RegistrationManager] = None
    ):
        """
        Initialize the MCP service.
        
        Args:
            service_registry: Service registry to use
            message_bus: Message bus to use
            registration_manager: Optional registration manager to use
        """
        self.service_registry = service_registry
        self.message_bus = message_bus
        self.registration_manager = registration_manager
        
        # Internal state
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.processors: Dict[str, Dict[str, Any]] = {}
        
        # Initialize channels
        self._channels_initialized = False
        
        logger.info("MCP service initialized")
    
    async def initialize(self):
        """Initialize the service and set up channels."""
        if self._channels_initialized:
            return
            
        # Create tools channel
        await self.message_bus.create_channel(
            'mcp.tools',
            description='Channel for MCP tools'
        )
        
        # Create context channel
        await self.message_bus.create_channel(
            'mcp.contexts',
            description='Channel for MCP contexts'
        )
        
        # Create processor channel
        await self.message_bus.create_channel(
            'mcp.processors',
            description='Channel for MCP processors'
        )
        
        # Subscribe to channels
        await self.message_bus.subscribe_async(
            'mcp.tools',
            self._handle_tool_message
        )
        
        await self.message_bus.subscribe_async(
            'mcp.contexts',
            self._handle_context_message
        )
        
        await self.message_bus.subscribe_async(
            'mcp.processors',
            self._handle_processor_message
        )
        
        self._channels_initialized = True
        logger.info("MCP service channels initialized")
    
    async def register_tool(self, tool_spec: Dict[str, Any]) -> str:
        """
        Register a tool with the MCP service.
        
        Args:
            tool_spec: Tool specification
            
        Returns:
            Tool ID
        """
        # Validate tool specification
        required_fields = ["name", "description", "schema"]
        for field in required_fields:
            if field not in tool_spec:
                logger.error(f"Tool specification missing required field: {field}")
                return ""
        
        # Generate tool ID if not provided
        tool_id = tool_spec.get("id") or f"tool-{uuid.uuid4()}"
        
        # Add registration metadata
        tool_spec["id"] = tool_id
        tool_spec["registered_at"] = time.time()
        
        # Store tool
        self.tools[tool_id] = tool_spec
        
        # Register with service registry if available
        if self.registration_manager:
            self.registration_manager.register_component(
                component_id=f"mcp.tool.{tool_id}",
                name=tool_spec["name"],
                version=tool_spec.get("version", "1.0.0"),
                component_type="mcp_tool",
                endpoint="",
                capabilities=tool_spec.get("tags", []),
                metadata={
                    "mcp_tool": True,
                    "tool_spec": tool_spec
                }
            )
        
        # Publish tool registration event
        await self.message_bus.publish(
            'mcp.tools',
            {
                'type': 'tool_registered',
                'tool_id': tool_id,
                'tool_spec': tool_spec
            }
        )
        
        logger.info(f"Tool registered: {tool_spec['name']} ({tool_id})")
        return tool_id
    
    async def unregister_tool(self, tool_id: str) -> bool:
        """
        Unregister a tool from the MCP service.
        
        Args:
            tool_id: Tool ID to unregister
            
        Returns:
            True if unregistration successful
        """
        if tool_id not in self.tools:
            logger.warning(f"Tool not found: {tool_id}")
            return False
            
        # Remove tool
        tool = self.tools.pop(tool_id)
        
        # Unregister from service registry if available
        if self.registration_manager:
            self.registration_manager.unregister_component(
                component_id=f"mcp.tool.{tool_id}",
                token_str=""  # Token not used here
            )
        
        # Publish tool unregistration event
        await self.message_bus.publish(
            'mcp.tools',
            {
                'type': 'tool_unregistered',
                'tool_id': tool_id
            }
        )
        
        logger.info(f"Tool unregistered: {tool_id}")
        return True
    
    async def register_processor(self, processor_spec: Dict[str, Any]) -> str:
        """
        Register a processor with the MCP service.
        
        Args:
            processor_spec: Processor specification
            
        Returns:
            Processor ID
        """
        # Validate processor specification
        required_fields = ["name", "description", "capabilities"]
        for field in required_fields:
            if field not in processor_spec:
                logger.error(f"Processor specification missing required field: {field}")
                return ""
        
        # Generate processor ID if not provided
        processor_id = processor_spec.get("id") or f"processor-{uuid.uuid4()}"
        
        # Add registration metadata
        processor_spec["id"] = processor_id
        processor_spec["registered_at"] = time.time()
        
        # Store processor
        self.processors[processor_id] = processor_spec
        
        # Register with service registry if available
        if self.registration_manager:
            self.registration_manager.register_component(
                component_id=f"mcp.processor.{processor_id}",
                name=processor_spec["name"],
                version=processor_spec.get("version", "1.0.0"),
                component_type="mcp_processor",
                endpoint=processor_spec.get("endpoint", ""),
                capabilities=processor_spec.get("capabilities", []),
                metadata={
                    "mcp_processor": True,
                    "processor_spec": processor_spec
                }
            )
        
        # Publish processor registration event
        await self.message_bus.publish(
            'mcp.processors',
            {
                'type': 'processor_registered',
                'processor_id': processor_id,
                'processor_spec': processor_spec
            }
        )
        
        logger.info(f"Processor registered: {processor_spec['name']} ({processor_id})")
        return processor_id
    
    async def create_context(
        self,
        data: Dict[str, Any],
        source: Dict[str, Any],
        context_id: Optional[str] = None
    ) -> str:
        """
        Create a new context.
        
        Args:
            data: Context data
            source: Context source information
            context_id: Optional ID for the context
            
        Returns:
            Context ID
        """
        # Generate context ID if not provided
        context_id = context_id or f"ctx-{uuid.uuid4()}"
        
        # Create context
        context = {
            "id": context_id,
            "data": data,
            "source": source,
            "created_at": time.time(),
            "updated_at": time.time(),
            "history": [
                {
                    "operation": "created",
                    "timestamp": time.time(),
                    "source": source
                }
            ]
        }
        
        # Store context
        self.contexts[context_id] = context
        
        # Publish context creation event
        await self.message_bus.publish(
            'mcp.contexts',
            {
                'type': 'context_created',
                'context_id': context_id,
                'context': context
            }
        )
        
        logger.info(f"Context created: {context_id}")
        return context_id
    
    async def update_context(
        self,
        context_id: str,
        updates: Dict[str, Any],
        source: Dict[str, Any],
        operation: str = "update"
    ) -> bool:
        """
        Update a context.
        
        Args:
            context_id: ID of the context to update
            updates: Updates to apply
            source: Update source information
            operation: Update operation type
            
        Returns:
            True if update successful
        """
        if context_id not in self.contexts:
            logger.warning(f"Context not found: {context_id}")
            return False
            
        context = self.contexts[context_id]
        
        # Deep merge updates into context data
        context["data"] = self._deep_merge(context["data"], updates)
        context["updated_at"] = time.time()
        
        # Add history entry
        context["history"].append({
            "operation": operation,
            "timestamp": time.time(),
            "source": source,
            "keys": list(updates.keys())
        })
        
        # Publish context update event
        await self.message_bus.publish(
            'mcp.contexts',
            {
                'type': 'context_updated',
                'context_id': context_id,
                'updates': updates,
                'operation': operation
            }
        )
        
        logger.info(f"Context updated: {context_id}")
        return True
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an MCP message.
        
        Args:
            message: MCP message to process
            
        Returns:
            Processing result
        """
        # Validate message
        required_fields = ["id", "version", "source", "content"]
        for field in required_fields:
            if field not in message:
                logger.error(f"MCP message missing required field: {field}")
                return {
                    "error": f"Missing required field: {field}"
                }
        
        # Find appropriate processor
        processors = await self._find_processors_for_message(message)
        
        if not processors:
            logger.warning("No suitable processor found for message")
            return {
                "error": "No suitable processor found for message"
            }
            
        # Select first processor (in a more sophisticated implementation,
        # we would select based on capabilities, load, etc.)
        processor_id = processors[0]
        processor = self.processors[processor_id]
        
        # Check if processor has an endpoint
        endpoint = processor.get("endpoint")
        if not endpoint:
            logger.warning(f"Processor {processor_id} has no endpoint")
            return {
                "error": f"Processor {processor_id} has no endpoint"
            }
            
        # In a real implementation, we would send the message to the processor
        # For now, just simulate processing
        
        # Create processing result
        result = {
            "id": f"response-{message['id']}",
            "version": message["version"],
            "timestamp": time.time(),
            "source": {
                "component": "mcp.service",
                "processor": processor_id
            },
            "destination": message.get("source", {}),
            "context": message.get("context", {}),
            "content": [
                {
                    "type": "text",
                    "format": "text/plain",
                    "data": "Message processed by MCP service",
                    "metadata": {
                        "role": "assistant"
                    }
                }
            ],
            "processed_by": processor_id
        }
        
        logger.info(f"Message {message['id']} processed by {processor_id}")
        return result
    
    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            tool_id: ID of the tool to execute
            parameters: Tool parameters
            context: Optional execution context
            
        Returns:
            Tool execution result
        """
        if tool_id not in self.tools:
            logger.warning(f"Tool not found: {tool_id}")
            return {
                "success": False,
                "error": f"Tool not found: {tool_id}"
            }
            
        tool = self.tools[tool_id]
        
        # Check if tool has an endpoint
        endpoint = tool.get("endpoint")
        if not endpoint:
            logger.warning(f"Tool {tool_id} has no endpoint")
            return {
                "success": False,
                "error": f"Tool {tool_id} has no endpoint"
            }
            
        # In a real implementation, we would send the request to the tool endpoint
        # For now, just simulate execution
        
        # Create execution result
        result = {
            "success": True,
            "tool_id": tool_id,
            "tool_name": tool["name"],
            "result": {
                "message": f"Tool {tool_id} executed successfully",
                "parameters": parameters
            },
            "execution_time": 0.1
        }
        
        # Publish tool execution event
        await self.message_bus.publish(
            'mcp.tools',
            {
                'type': 'tool_executed',
                'tool_id': tool_id,
                'parameters': parameters,
                'result': result
            }
        )
        
        logger.info(f"Tool executed: {tool_id}")
        return result
    
    async def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a tool.
        
        Args:
            tool_id: Tool ID to retrieve
            
        Returns:
            Tool information or None if not found
        """
        tool = self.tools.get(tool_id)
        return tool.copy() if tool else None
    
    async def get_processor(self, processor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a processor.
        
        Args:
            processor_id: Processor ID to retrieve
            
        Returns:
            Processor information or None if not found
        """
        processor = self.processors.get(processor_id)
        return processor.copy() if processor else None
    
    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a context.
        
        Args:
            context_id: Context ID to retrieve
            
        Returns:
            Context or None if not found
        """
        context = self.contexts.get(context_id)
        return context.copy() if context else None
    
    async def _find_processors_for_message(self, message: Dict[str, Any]) -> List[str]:
        """
        Find processors that can handle a message.
        
        Args:
            message: MCP message
            
        Returns:
            List of processor IDs
        """
        matching_processors = []
        
        # Get message content types
        content_types = set()
        for content_item in message.get("content", []):
            content_type = content_item.get("type")
            if content_type:
                content_types.add(content_type)
                
        # Get requested capabilities
        requested_capabilities = message.get("processing", {}).get("capabilities_required", [])
        
        # Find processors with matching capabilities
        for processor_id, processor in self.processors.items():
            capabilities = processor.get("capabilities", [])
            
            # Check if processor supports all required content types
            supports_content_types = all(
                content_type in capabilities for content_type in content_types
            )
            
            # Check if processor has all requested capabilities
            has_capabilities = all(
                capability in capabilities for capability in requested_capabilities
            )
            
            if supports_content_types and has_capabilities:
                matching_processors.append(processor_id)
        
        return matching_processors
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            updates: Updates to apply
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Replace or add value
                result[key] = value
                
        return result
    
    async def _handle_tool_message(self, message: Dict[str, Any]):
        """
        Handle tool messages.
        
        Args:
            message: Tool message
        """
        message_type = message.get('type')
        
        if message_type == 'register_tool':
            # Register tool
            tool_spec = message.get('tool_spec')
            if tool_spec:
                await self.register_tool(tool_spec)
                
        elif message_type == 'unregister_tool':
            # Unregister tool
            tool_id = message.get('tool_id')
            if tool_id:
                await self.unregister_tool(tool_id)
                
        elif message_type == 'execute_tool':
            # Execute tool
            tool_id = message.get('tool_id')
            parameters = message.get('parameters')
            if tool_id and parameters:
                await self.execute_tool(tool_id, parameters, message.get('context'))
    
    async def _handle_context_message(self, message: Dict[str, Any]):
        """
        Handle context messages.
        
        Args:
            message: Context message
        """
        message_type = message.get('type')
        
        if message_type == 'create_context':
            # Create context
            data = message.get('data')
            source = message.get('source')
            if data and source:
                await self.create_context(
                    data=data,
                    source=source,
                    context_id=message.get('context_id')
                )
                
        elif message_type == 'update_context':
            # Update context
            context_id = message.get('context_id')
            updates = message.get('updates')
            source = message.get('source')
            if context_id and updates and source:
                await self.update_context(
                    context_id=context_id,
                    updates=updates,
                    source=source,
                    operation=message.get('operation', 'update')
                )
    
    async def _handle_processor_message(self, message: Dict[str, Any]):
        """
        Handle processor messages.
        
        Args:
            message: Processor message
        """
        message_type = message.get('type')
        
        if message_type == 'register_processor':
            # Register processor
            processor_spec = message.get('processor_spec')
            if processor_spec:
                await self.register_processor(processor_spec)
                
        elif message_type == 'process_message':
            # Process message
            mcp_message = message.get('message')
            if mcp_message:
                result = await self.process_message(mcp_message)
                
                # Publish processing result
                await self.message_bus.publish(
                    'mcp.processors',
                    {
                        'type': 'message_processed',
                        'message_id': mcp_message.get('id'),
                        'result': result
                    }
                )