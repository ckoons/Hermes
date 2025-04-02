# Hermes - Central Database Services and Messaging Framework for Tekton

<div align="center">
  <img src="images/icon.jpg" alt="Hermes Logo" width="800"/>
  <h3>Tekton<br>AI Driven Orchestration</h3>
</div>

Hermes is the central database and messaging framework for the Tekton ecosystem, providing centralized database services, registration protocol, and inter-component communication.

## Overview

Hermes serves as the "nervous system" of Tekton, handling all database operations and message passing between components. It supports:

- Unified Registration Protocol for all Tekton components
- Centralized Logging System with schema versioning
- Vector embedding generation and storage
- Knowledge graph and other database services
- Multiple database backends with namespace isolation
- Hardware-optimized implementations (Apple Silicon, NVIDIA)
- Inter-component message passing
- Event broadcasting and subscription
- Stream processing and transformation

## Architecture

Hermes consists of the following key components:

- **Registration Manager**: Unified Registration Protocol implementation
- **Service Registry**: Component discovery and health monitoring
- **Database Manager**: Centralized database services for all components
  - **Vector Database**: Embedding storage and similarity search
  - **Graph Database**: Knowledge graph storage and querying
  - **Key-Value Database**: Simple key-value storage
  - **Document Database**: Structured document storage
  - **Cache Database**: Temporary data caching
  - **Relational Database**: SQL-based structured storage
- **Messaging Bus**: Inter-component communication infrastructure
- **Logging System**: Centralized logging with schema versioning
- **Streaming Service**: Real-time data flow processing

## Technology Stack

- Python 3.9+
- Multiple vector backends (Qdrant, FAISS, LanceDB)
- ZeroMQ for messaging
- FastAPI for API endpoints
- Pydantic for data validation

## Installation

```bash
# Clone the repository
git clone https://github.com/YourOrganization/Hermes.git

# Install dependencies
cd Hermes
pip install -e .
```

## Usage

### Component Registration

```python
import asyncio
from hermes.utils.registration_helper import register_component

async def main():
    # Register your component with Hermes
    registration = await register_component(
        component_id="my_component_id",
        component_name="My Component",
        component_type="custom",
        component_version="1.0.0",
        capabilities=["custom.capability1", "custom.capability2"]
    )
    
    # Use registration for messaging
    registration.publish_message(
        topic="my.topic",
        message={"data": "Hello World"}
    )
    
    # Unregister when done
    await registration.unregister()
    await registration.close()

asyncio.run(main())
```

### Centralized Logging

```python
from hermes.utils.logging_helper import setup_logging

# Set up logging for your component
logger = setup_logging("my.component")

# Log at different levels
logger.fatal("Fatal error occurred", code="FATAL001")
logger.error("Error occurred", code="ERROR001")
logger.warn("Warning condition", code="WARN001")
logger.info("Informational message", code="INFO001")
logger.normal("System lifecycle event", code="NORMAL001")
logger.debug("Debug information", code="DEBUG001")
logger.trace("Trace information", code="TRACE001")

# Log with context
logger.info(
    "User action",
    code="USER001",
    context={
        "user_id": "user123",
        "action": "login",
        "ip_address": "192.168.1.1"
    }
)

# Create logger with correlation ID for tracking related events
correlation_logger = logger.with_correlation("transaction-123")
correlation_logger.info("Transaction started", code="TRANS001")
correlation_logger.info("Transaction completed", code="TRANS002")
```

### Centralized Database Services

```python
from hermes.utils.database_helper import DatabaseClient
import asyncio

async def main():
    # Create a client for your component
    db_client = DatabaseClient(component_id="my_component")
    
    # Get different database types with namespace isolation
    vector_db = await db_client.get_vector_db(namespace="documents")
    key_value_db = await db_client.get_key_value_db(namespace="settings")
    cache_db = await db_client.get_cache_db(namespace="temp")
    
    # Store vectors with metadata
    await vector_db.store(
        id="doc1",
        vector=[0.1, 0.2, 0.3, 0.4],
        metadata={"category": "article"},
        text="Example document content"
    )
    
    # Search for similar vectors
    results = await vector_db.search(
        query_vector=[0.15, 0.25, 0.35, 0.45],
        limit=5
    )
    
    # Store settings
    await key_value_db.set("api_key", "sk_1234567890")
    await key_value_db.set("user_prefs", {"theme": "dark"})
    
    # Cache temporary data
    await cache_db.set(
        "user_session",
        {"auth": True, "last_seen": "2025-03-30T12:34:56Z"},
        expiration=3600  # 1 hour
    )
    
    # Clean up connections when done
    await db_client.close()

asyncio.run(main())
```

### Database Access and Messaging

```python
from hermes.core import VectorEngine, MessageBus

# Vector operations
vector_engine = VectorEngine()
embedding = vector_engine.create_embedding("This is a test document")
vector_engine.store(document_id="doc1", embedding=embedding, metadata={"title": "Test"})
results = vector_engine.search("similar document", limit=5)

# Messaging
message_bus = MessageBus()
message_bus.subscribe("topic.events", callback_function)
message_bus.publish("topic.events", {"message": "Hello World"})
```

## Integration with Tekton

Hermes serves as the central hub for all Tekton components:

- **Unified Registration**: All components register once with Hermes
- **Centralized Database Services**:
  - **Engram**: Uses Hermes for memory storage
  - **Athena**: Uses Hermes for knowledge graph storage
  - **Ergon**: Uses Hermes for agent data storage
- **Inter-component Communication**:
  - Components communicate through Hermes messaging system
  - Event-driven architecture enables loose coupling
- **Centralized Logging**:
  - All components log through Hermes logging system
  - Consistent schema and categorization

## License

[Specify your license here]
