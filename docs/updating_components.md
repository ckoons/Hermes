# Updating Tekton Components to Use Hermes Services

This guide describes how to update existing Tekton components to use the centralized services provided by Hermes.

## Overview

Tekton components should leverage Hermes for:

1. **Database Services**: Vector, key-value, graph, and other database types
2. **Logging**: Centralized logging infrastructure
3. **Service Registration**: Registering and discovering services
4. **Message Bus**: Inter-component communication

## Updating Database Access

### Step 1: Add Hermes as a Dependency

```python
# In your setup.py or requirements.txt
# Add Hermes as a dependency
"hermes-tekton>=1.0.0"
```

### Step 2: Import Hermes Database Client

```python
from hermes.utils.database_helper import DatabaseClient

# Initialize database client with your component ID
db_client = DatabaseClient(component_id="your_component.module")
```

### Step 3: Replace Direct Database Access

#### Before

```python
# Direct FAISS access
import faiss
import numpy as np

# Create FAISS index
index = faiss.IndexFlatIP(1536)
vectors = np.array([...], dtype=np.float32)
faiss.normalize_L2(vectors)
index.add(vectors)

# Search
query = np.array([...], dtype=np.float32)
faiss.normalize_L2(query)
distances, indices = index.search(query, 5)
```

#### After

```python
# Using Hermes database services
async def search_vectors():
    # Get vector database
    vector_db = await db_client.get_vector_db(namespace="your_namespace")
    
    # Store vectors
    for i, vec in enumerate(your_vectors):
        await vector_db.store(
            id=f"item-{i}",
            vector=vec,
            metadata={"source": "your_component"}
        )
    
    # Search
    results = await vector_db.search(
        query_vector=your_query,
        limit=5
    )
    
    return results
```

### Step 4: Add Graceful Fallback

```python
async def get_database():
    try:
        # Try to use Hermes database services
        vector_db = await db_client.get_vector_db(namespace="your_namespace")
        return vector_db
    except ImportError:
        # Hermes not available, fall back to local implementation
        print("Hermes database services not available, using fallback")
        return YourFallbackDatabase()
```

## Updating Logging

### Step 1: Import Hermes Logger

```python
from hermes.core.logging import get_logger

# Get a logger for your component
logger = get_logger("your_component.module")
```

### Step 2: Replace Existing Logging

#### Before

```python
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log messages
logger.info("Operation started")
logger.warning("Potential issue detected")
logger.error("Operation failed: %s", error_message)
```

#### After

```python
from hermes.core.logging import get_logger

# Get a logger for your component
logger = get_logger("your_component.module")

# Log messages
logger.info("Operation started")
logger.warning("Potential issue detected")
logger.error(f"Operation failed: {error_message}")
```

### Step 3: Add Structured Logging

```python
# Log with additional context
logger.info("Vector search completed", 
            extra={
                "operation": "vector_search",
                "duration_ms": 15.4,
                "results_count": 5,
                "namespace": "your_namespace"
            })
```

## Adding Service Registration

### Step 1: Import Hermes Registration

```python
from hermes.core.registration import ServiceRegistry
```

### Step 2: Register Your Service

```python
async def register_service():
    # Initialize service registry
    registry = ServiceRegistry()
    await registry.start()
    
    # Register your service
    success = await registry.register(
        service_id="your_component-main",
        name="Your Component Service",
        version="1.0.0",
        endpoint="http://localhost:8080",
        capabilities=["your_capability"],
        metadata={
            "description": "Your component description",
            "config": {"key": "value"}
        }
    )
    
    if success:
        logger.info("Successfully registered with Hermes")
    else:
        logger.warning("Failed to register with Hermes")
```

### Step 3: Add Health Updates

```python
async def update_health():
    # Initialize service registry
    registry = ServiceRegistry()
    
    # Update health status
    await registry.update_health(
        service_id="your_component-main",
        status="healthy",
        metrics={
            "response_time_ms": 250,
            "requests_per_minute": 15,
            "error_rate": 0.01
        }
    )
```

## Using the Message Bus

### Step 1: Import Hermes Message Bus

```python
from hermes.core.message_bus import MessageBus
```

### Step 2: Subscribe to Topics

```python
async def start_message_listener():
    # Initialize message bus
    bus = MessageBus()
    await bus.start()
    
    # Subscribe to topics
    await bus.subscribe("engram.memory.updated", handle_memory_update)
    await bus.subscribe("ergon.tools.registered", handle_tool_registration)
```

### Step 3: Handle Messages

```python
async def handle_memory_update(message):
    logger.info(f"Received memory update: {message}")
    # Process the message
    
async def handle_tool_registration(message):
    logger.info(f"Received tool registration: {message}")
    # Process the message
```

### Step 4: Publish Messages

```python
async def notify_component_event(event_type, data):
    # Initialize message bus
    bus = MessageBus()
    
    # Publish message
    await bus.publish(
        topic=f"your_component.{event_type}",
        message={
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
    )
```

## Complete Integration Example

Here's a complete example showing integration with all Hermes services:

```python
import asyncio
from datetime import datetime
from hermes.utils.database_helper import DatabaseClient
from hermes.core.logging import get_logger
from hermes.core.registration import ServiceRegistry
from hermes.core.message_bus import MessageBus

# Initialize logger
logger = get_logger("your_component.main")

class YourComponent:
    def __init__(self):
        self.db_client = DatabaseClient(component_id="your_component")
        self.registry = ServiceRegistry()
        self.message_bus = MessageBus()
    
    async def start(self):
        # Start services
        await self.registry.start()
        await self.message_bus.start()
        
        # Register with Hermes
        await self.registry.register(
            service_id="your_component-main",
            name="Your Component",
            version="1.0.0",
            endpoint="http://localhost:8080",
            capabilities=["your_capability"],
            metadata={"description": "Your component description"}
        )
        
        # Subscribe to messages
        await self.message_bus.subscribe("engram.memory.updated", self.handle_memory_update)
        
        logger.info("Your component started successfully")
    
    async def handle_memory_update(self, message):
        logger.info(f"Received memory update: {message}")
        
        # Store in database
        vector_db = await self.db_client.get_vector_db(namespace="your_namespace")
        await vector_db.store(
            id=f"memory-{message['id']}",
            vector=message.get("vector"),
            metadata={"source": "engram", "timestamp": datetime.now().isoformat()},
            text=message.get("content")
        )
        
        # Notify about processing
        await self.message_bus.publish(
            topic="your_component.memory_processed",
            message={
                "type": "memory_processed",
                "timestamp": datetime.now().isoformat(),
                "memory_id": message["id"]
            }
        )
    
    async def update_health(self):
        await self.registry.update_health(
            service_id="your_component-main",
            status="healthy",
            metrics={
                "response_time_ms": 250,
                "requests_per_minute": 15,
                "error_rate": 0.01
            }
        )

# Run the component
async def main():
    component = YourComponent()
    await component.start()
    
    # Keep running
    while True:
        await component.update_health()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing the Integration

1. **Ensure Hermes is Running**: Verify that Hermes is running and accessible
2. **Test with Fallbacks**: Test your component with and without Hermes being available
3. **Check Service Registry**: Verify that your service appears in the registry
4. **Validate Message Bus**: Test message publishing and subscription
5. **Monitor Logs**: Check that logs are being properly captured by Hermes