"""
A2A Service - Hermes integration for Agent-to-Agent Communication Framework.

This module provides a service for agent-to-agent communication through
the Hermes message bus, enabling agents to register, discover, and
communicate with each other.
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

class A2AService:
    """
    Service for agent-to-agent communication in Hermes.
    
    This class provides a service for agent-to-agent communication,
    enabling agents to register, discover, and communicate with each other.
    """
    
    def __init__(
        self,
        service_registry: ServiceRegistry,
        message_bus: MessageBus,
        registration_manager: Optional[RegistrationManager] = None
    ):
        """
        Initialize the A2A service.
        
        Args:
            service_registry: Service registry to use
            message_bus: Message bus to use
            registration_manager: Optional registration manager to use
        """
        self.service_registry = service_registry
        self.message_bus = message_bus
        self.registration_manager = registration_manager
        
        # Internal state
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        # Initialize channels
        self._channels_initialized = False
        
        logger.info("A2A service initialized")
    
    async def initialize(self):
        """Initialize the service and set up channels."""
        if self._channels_initialized:
            return
            
        # Create agent registration channel
        await self.message_bus.create_channel(
            'a2a.registration',
            description='Channel for agent registration'
        )
        
        # Create message channel
        await self.message_bus.create_channel(
            'a2a.messages',
            description='Channel for agent messages'
        )
        
        # Create task channel
        await self.message_bus.create_channel(
            'a2a.tasks',
            description='Channel for task management'
        )
        
        # Create conversation channel
        await self.message_bus.create_channel(
            'a2a.conversations',
            description='Channel for conversation management'
        )
        
        # Subscribe to channels
        await self.message_bus.subscribe_async(
            'a2a.registration',
            self._handle_registration
        )
        
        await self.message_bus.subscribe_async(
            'a2a.messages',
            self._handle_message
        )
        
        await self.message_bus.subscribe_async(
            'a2a.tasks',
            self._handle_task
        )
        
        await self.message_bus.subscribe_async(
            'a2a.conversations',
            self._handle_conversation
        )
        
        self._channels_initialized = True
        logger.info("A2A service channels initialized")
    
    async def register_agent(self, agent_card: Dict[str, Any]) -> bool:
        """
        Register an agent with the A2A service.
        
        Args:
            agent_card: Agent card information
            
        Returns:
            True if registration successful
        """
        # Validate agent card
        required_fields = ["agent_id", "name", "version", "capabilities"]
        for field in required_fields:
            if field not in agent_card:
                logger.error(f"Agent card missing required field: {field}")
                return False
        
        agent_id = agent_card["agent_id"]
        
        # Store agent information
        self.agents[agent_id] = {
            "card": agent_card,
            "registered_at": time.time(),
            "last_seen": time.time()
        }
        
        # Register with service registry if available
        # This allows the agent to be discovered through standard Hermes mechanisms too
        if self.registration_manager:
            capabilities = []
            # Extract capabilities from agent card
            for category, category_capabilities in agent_card.get("capabilities", {}).items():
                if isinstance(category_capabilities, list):
                    capabilities.extend(category_capabilities)
                elif isinstance(category_capabilities, dict):
                    for domain, domain_capabilities in category_capabilities.items():
                        if isinstance(domain_capabilities, list):
                            capabilities.extend(domain_capabilities)
            
            # Register with service registry
            self.registration_manager.register_component(
                component_id=f"a2a.agent.{agent_id}",
                name=agent_card["name"],
                version=agent_card["version"],
                component_type="a2a_agent",
                endpoint=agent_card.get("endpoint", ""),
                capabilities=capabilities,
                metadata={
                    "a2a_agent": True,
                    "agent_card": agent_card
                }
            )
        
        # Publish registration event
        await self.message_bus.publish(
            'a2a.registration',
            {
                'type': 'agent_registered',
                'agent_id': agent_id,
                'agent_card': agent_card
            }
        )
        
        logger.info(f"Agent registered: {agent_card['name']} ({agent_id})")
        return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the A2A service.
        
        Args:
            agent_id: Agent ID to unregister
            
        Returns:
            True if unregistration successful
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent not found for unregistration: {agent_id}")
            return False
            
        # Remove agent information
        agent_info = self.agents.pop(agent_id)
        
        # Unregister from service registry if available
        if self.registration_manager:
            self.registration_manager.unregister_component(
                component_id=f"a2a.agent.{agent_id}",
                token_str=""  # Token not used here
            )
        
        # Publish unregistration event
        await self.message_bus.publish(
            'a2a.registration',
            {
                'type': 'agent_unregistered',
                'agent_id': agent_id
            }
        )
        
        logger.info(f"Agent unregistered: {agent_id}")
        return True
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send a message to one or more agents.
        
        Args:
            message: A2A message to send
            
        Returns:
            True if message sent successfully
        """
        # Validate message
        required_fields = ["id", "sender", "recipients", "type", "content"]
        for field in required_fields:
            if field not in message:
                logger.error(f"Message missing required field: {field}")
                return False
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = time.time()
            
        # Process recipients
        recipients = message.get("recipients", [])
        direct_recipients = []
        
        for recipient in recipients:
            recipient_type = recipient.get("type")
            
            if recipient_type == "direct":
                # Direct message to specific agent
                recipient_id = recipient.get("id")
                if recipient_id in self.agents:
                    direct_recipients.append(recipient_id)
                    
            elif recipient_type == "capability":
                # Message to agents with specific capability
                capability = recipient.get("capability")
                matching_agents = await self._find_agents_by_capability(capability)
                direct_recipients.extend(matching_agents)
                
            elif recipient_type == "broadcast":
                # Broadcast to all agents
                direct_recipients = list(self.agents.keys())
                break
        
        # Publish message for each recipient
        if not direct_recipients:
            logger.warning("No valid recipients for message")
            return False
            
        for recipient_id in direct_recipients:
            # Publish to agent-specific channel
            await self.message_bus.publish(
                f'agent.{recipient_id}',
                message
            )
            
        # Also publish to general message channel
        await self.message_bus.publish(
            'a2a.messages',
            message
        )
        
        logger.info(f"Message sent to {len(direct_recipients)} recipients")
        return True
    
    async def create_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new task.
        
        Args:
            task_spec: Task specification
            
        Returns:
            Created task information
        """
        # Validate task specification
        required_fields = ["name", "description", "required_capabilities"]
        for field in required_fields:
            if field not in task_spec:
                logger.error(f"Task specification missing required field: {field}")
                return {"error": f"Missing required field: {field}"}
                
        # Generate task ID if not provided
        task_id = task_spec.get("id") or f"task-{uuid.uuid4()}"
        
        # Create task
        task = {
            "id": task_id,
            "spec": task_spec,
            "status": "created",
            "created_at": time.time(),
            "updated_at": time.time(),
            "assigned_to": None,
            "result": None,
            "history": [
                {
                    "status": "created",
                    "timestamp": time.time(),
                    "agent_id": None,
                    "message": "Task created"
                }
            ]
        }
        
        # Store task
        self.tasks[task_id] = task
        
        # Publish task creation event
        await self.message_bus.publish(
            'a2a.tasks',
            {
                'type': 'task_created',
                'task_id': task_id,
                'task': task
            }
        )
        
        logger.info(f"Task created: {task_spec['name']} ({task_id})")
        
        # If preferred agent is specified, try to assign task
        preferred_agent = task_spec.get("preferred_agent")
        if preferred_agent and preferred_agent in self.agents:
            await self.assign_task(task_id, preferred_agent)
        
        return {
            "task_id": task_id,
            "status": "created"
        }
    
    async def assign_task(self, task_id: str, agent_id: str) -> bool:
        """
        Assign a task to an agent.
        
        Args:
            task_id: ID of the task to assign
            agent_id: ID of the agent to assign to
            
        Returns:
            True if assignment successful
        """
        if task_id not in self.tasks:
            logger.warning(f"Task not found: {task_id}")
            return False
            
        if agent_id not in self.agents:
            logger.warning(f"Agent not found: {agent_id}")
            return False
            
        task = self.tasks[task_id]
        
        # Update task status
        task["status"] = "assigned"
        task["assigned_to"] = agent_id
        task["updated_at"] = time.time()
        task["history"].append({
            "status": "assigned",
            "timestamp": time.time(),
            "agent_id": agent_id,
            "message": f"Task assigned to agent {agent_id}"
        })
        
        # Send task assignment message
        assignment_message = {
            "id": f"msg-{uuid.uuid4()}",
            "timestamp": time.time(),
            "sender": {
                "id": "hermes.a2a",
                "name": "Hermes A2A Service",
                "version": "1.0.0"
            },
            "recipients": [
                {
                    "id": agent_id,
                    "type": "direct"
                }
            ],
            "type": "command",
            "intent": "delegate_task",
            "content": {
                "format": "application/json",
                "data": task["spec"]
            }
        }
        
        await self.message_bus.publish(
            f'agent.{agent_id}',
            assignment_message
        )
        
        # Publish task assignment event
        await self.message_bus.publish(
            'a2a.tasks',
            {
                'type': 'task_assigned',
                'task_id': task_id,
                'agent_id': agent_id
            }
        )
        
        logger.info(f"Task {task_id} assigned to agent {agent_id}")
        return True
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        agent_id: Optional[str] = None,
        message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a task's status.
        
        Args:
            task_id: ID of the task to update
            status: New status
            agent_id: ID of the agent updating the status
            message: Optional status message
            result: Optional task result
            
        Returns:
            True if update successful
        """
        if task_id not in self.tasks:
            logger.warning(f"Task not found: {task_id}")
            return False
            
        task = self.tasks[task_id]
        
        # Update task
        task["status"] = status
        task["updated_at"] = time.time()
        
        if result is not None:
            task["result"] = result
            
        # Add history entry
        task["history"].append({
            "status": status,
            "timestamp": time.time(),
            "agent_id": agent_id,
            "message": message or f"Status changed to {status}"
        })
        
        # Publish task update event
        await self.message_bus.publish(
            'a2a.tasks',
            {
                'type': 'task_status_changed',
                'task_id': task_id,
                'status': status,
                'agent_id': agent_id,
                'result': result
            }
        )
        
        logger.info(f"Task {task_id} status updated to {status}")
        return True
    
    async def start_conversation(
        self,
        participants: List[str],
        topic: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Start a new conversation.
        
        Args:
            participants: List of participant agent IDs
            topic: Conversation topic
            context: Conversation context
            conversation_id: Optional ID for the conversation
            
        Returns:
            Conversation ID
        """
        # Generate conversation ID if not provided
        conversation_id = conversation_id or f"conv-{uuid.uuid4()}"
        
        # Create conversation
        conversation = {
            "id": conversation_id,
            "participants": participants,
            "topic": topic or "General conversation",
            "context": context or {},
            "created_at": time.time(),
            "last_message_at": time.time(),
            "message_count": 0
        }
        
        # Store conversation
        self.conversations[conversation_id] = conversation
        
        # Publish conversation creation event
        await self.message_bus.publish(
            'a2a.conversations',
            {
                'type': 'conversation_started',
                'conversation_id': conversation_id,
                'conversation': conversation
            }
        )
        
        logger.info(f"Conversation started: {conversation_id} with {len(participants)} participants")
        return conversation_id
    
    async def add_to_conversation(
        self,
        conversation_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            message: Message to add
            
        Returns:
            True if message added successfully
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation not found: {conversation_id}")
            return False
            
        conversation = self.conversations[conversation_id]
        
        # Ensure message has the conversation ID
        message["conversation_id"] = conversation_id
        
        # Update conversation metadata
        conversation["last_message_at"] = time.time()
        conversation["message_count"] += 1
        
        # Send message to all participants
        for participant_id in conversation["participants"]:
            # Skip sender
            if participant_id == message.get("sender", {}).get("id"):
                continue
                
            # Add recipient
            if "recipients" not in message:
                message["recipients"] = []
                
            message["recipients"].append({
                "id": participant_id,
                "type": "direct"
            })
            
        # Send the message
        await self.send_message(message)
        
        # Publish conversation message event
        await self.message_bus.publish(
            'a2a.conversations',
            {
                'type': 'message_added',
                'conversation_id': conversation_id,
                'message': message
            }
        )
        
        logger.info(f"Message added to conversation {conversation_id}")
        return True
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an agent.
        
        Args:
            agent_id: Agent ID to retrieve
            
        Returns:
            Agent information or None if not found
        """
        agent = self.agents.get(agent_id)
        return agent.copy() if agent else None
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a task.
        
        Args:
            task_id: Task ID to retrieve
            
        Returns:
            Task information or None if not found
        """
        task = self.tasks.get(task_id)
        return task.copy() if task else None
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a conversation.
        
        Args:
            conversation_id: Conversation ID to retrieve
            
        Returns:
            Conversation information or None if not found
        """
        conversation = self.conversations.get(conversation_id)
        return conversation.copy() if conversation else None
    
    async def _find_agents_by_capability(self, capability: str) -> List[str]:
        """
        Find agents with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agent IDs
        """
        matching_agents = []
        
        for agent_id, agent_info in self.agents.items():
            agent_card = agent_info.get("card", {})
            capabilities = agent_card.get("capabilities", {})
            
            # Check various capability structures
            found = False
            
            # Check top-level capabilities
            for category, category_capabilities in capabilities.items():
                if isinstance(category_capabilities, list) and capability in category_capabilities:
                    matching_agents.append(agent_id)
                    found = True
                    break
                    
                if isinstance(category_capabilities, dict):
                    for domain, domain_capabilities in category_capabilities.items():
                        if isinstance(domain_capabilities, list) and capability in domain_capabilities:
                            matching_agents.append(agent_id)
                            found = True
                            break
                            
                if found:
                    break
        
        return matching_agents
    
    async def _handle_registration(self, message: Dict[str, Any]):
        """
        Handle agent registration messages.
        
        Args:
            message: Registration message
        """
        message_type = message.get('type')
        
        if message_type == 'register_agent':
            # Register agent
            agent_card = message.get('agent_card')
            if agent_card:
                await self.register_agent(agent_card)
                
        elif message_type == 'unregister_agent':
            # Unregister agent
            agent_id = message.get('agent_id')
            if agent_id:
                await self.unregister_agent(agent_id)
                
        elif message_type == 'heartbeat':
            # Update agent heartbeat
            agent_id = message.get('agent_id')
            if agent_id and agent_id in self.agents:
                self.agents[agent_id]['last_seen'] = time.time()
    
    async def _handle_message(self, message: Dict[str, Any]):
        """
        Handle agent messages.
        
        Args:
            message: Agent message
        """
        # Basic message validation
        if not isinstance(message, dict) or 'recipients' not in message:
            return
            
        # Forward message to recipients
        await self.send_message(message)
    
    async def _handle_task(self, message: Dict[str, Any]):
        """
        Handle task management messages.
        
        Args:
            message: Task message
        """
        message_type = message.get('type')
        
        if message_type == 'create_task':
            # Create task
            task_spec = message.get('task_spec')
            if task_spec:
                await self.create_task(task_spec)
                
        elif message_type == 'assign_task':
            # Assign task
            task_id = message.get('task_id')
            agent_id = message.get('agent_id')
            if task_id and agent_id:
                await self.assign_task(task_id, agent_id)
                
        elif message_type == 'update_task_status':
            # Update task status
            task_id = message.get('task_id')
            status = message.get('status')
            if task_id and status:
                await self.update_task_status(
                    task_id=task_id,
                    status=status,
                    agent_id=message.get('agent_id'),
                    message=message.get('message'),
                    result=message.get('result')
                )
    
    async def _handle_conversation(self, message: Dict[str, Any]):
        """
        Handle conversation messages.
        
        Args:
            message: Conversation message
        """
        message_type = message.get('type')
        
        if message_type == 'start_conversation':
            # Start conversation
            participants = message.get('participants')
            if participants:
                await self.start_conversation(
                    participants=participants,
                    topic=message.get('topic'),
                    context=message.get('context'),
                    conversation_id=message.get('conversation_id')
                )
                
        elif message_type == 'add_message':
            # Add message to conversation
            conversation_id = message.get('conversation_id')
            content_message = message.get('message')
            if conversation_id and content_message:
                await self.add_to_conversation(conversation_id, content_message)