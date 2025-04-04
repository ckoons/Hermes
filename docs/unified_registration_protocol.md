# Unified Registration Protocol for Tekton Components

## Overview

The Unified Registration Protocol (URP) is the standardized mechanism for component registration, discovery, and communication within the Tekton ecosystem. This document provides comprehensive information about the protocol design, implementation, and usage.

## Core Concepts

### 1. Component Registration

All Tekton components must register with the central Hermes service to participate in the ecosystem. Registration includes:

- Unique component identification
- Component capabilities advertisement
- Endpoint information for communication
- Authentication token generation
- Health monitoring setup

### 2. Service Discovery

Components can discover other components based on:

- Component type (e.g., "llm", "memory", "vector-store")
- Specific capabilities (e.g., "vector_search", "text_generation")
- Component ID or name
- Health status

### 3. Heartbeat System

Components maintain their "active" status through regular heartbeats:

- Periodic signals sent to Hermes
- Status information included with heartbeats
- Automatic deregistration of components that fail to send heartbeats

## Implementation Details

### API Endpoints

The Unified Registration Protocol is implemented through a REST API with the following endpoints:

#### Register a Component

**POST /api/register**

Registers a component with the Tekton ecosystem.

**Request Body:**
```json
{
  "component_id": "engram-memory-14fd2c8b",
  "name": "Engram Memory Service",
  "version": "1.0.0",
  "type": "memory",
  "endpoint": "http://localhost:8001/engram",
  "capabilities": ["memory", "vector_search", "metadata_storage"],
  "metadata": {
    "description": "Long-term memory service for Tekton components",
    "storage_backend": "faiss"
  }
}
```

**Response:**
```json
{
  "success": true,
  "component_id": "engram-memory-14fd2c8b",
  "token": "eyJwYXlsb2FkIjp7ImNvbXBvbmVudF9pZCI6ImVuZ3JhbS1tZW1vcnktMTRmZDJjOGIiLCJ0b2tlbl9pZCI6IjU...",
  "message": "Component registered successfully"
}
```

#### Send Heartbeat

**POST /api/heartbeat**

Sends a heartbeat to indicate a component is still active.

**Request Body:**
```json
{
  "component_id": "engram-memory-14fd2c8b",
  "status": {
    "healthy": true,
    "memory_usage_mb": 256,
    "active_connections": 5
  }
}
```

**Headers:**
```
X-Authentication-Token: eyJwYXlsb2FkIjp7ImNvbXBvbmVudF9pZCI6ImVuZ3JhbS1tZW1vcnktMTRmZDJjOGIiLCJ0b2tlbl9pZCI6IjU...
```

**Response:**
```json
{
  "success": true,
  "timestamp": 1711809245.3251,
  "message": "Heartbeat received"
}
```

#### Unregister a Component

**POST /api/unregister**

Unregisters a component from the Tekton ecosystem.

**Query Parameters:**
- `component_id`: ID of the component to unregister

**Headers:**
```
X-Authentication-Token: eyJwYXlsb2FkIjp7ImNvbXBvbmVudF9pZCI6ImVuZ3JhbS1tZW1vcnktMTRmZDJjOGIiLCJ0b2tlbl9pZCI6IjU...
```

**Response:**
```json
{
  "success": true,
  "message": "Component unregistered successfully"
}
```

#### Query Services

**POST /api/query**

Queries available services based on criteria.

**Request Body:**
```json
{
  "capability": "vector_search",
  "component_type": "memory",
  "healthy_only": true
}
```

**Response:**
```json
[
  {
    "component_id": "engram-memory-14fd2c8b",
    "name": "Engram Memory Service",
    "version": "1.0.0",
    "type": "memory",
    "endpoint": "http://localhost:8001/engram",
    "capabilities": ["memory", "vector_search", "metadata_storage"],
    "metadata": {
      "description": "Long-term memory service for Tekton components",
      "storage_backend": "faiss"
    },
    "healthy": true,
    "last_heartbeat": 1711809245.3251
  }
]
```

### Client Usage

#### Using the HTTP API Client

The simplest way to integrate with the registration protocol is through the provided HTTP API client:

```python
from hermes.core.registration import RegistrationClientAPI

# Create client
client = RegistrationClientAPI(
    component_id="my-component-id",  # Optional, auto-generated if not provided
    name="My Component",
    version="1.0.0",
    component_type="processor",
    endpoint="http://localhost:8080/myapi",
    capabilities=["text_processing", "summarization"],
    api_endpoint="http://localhost:8000/api",  # Hermes API endpoint
    metadata={
        "description": "Text processing component",
        "author": "Tekton Team"
    }
)

# Register with Hermes
success = client.register()
if success:
    print(f"Registered successfully with token: {client.token[:10]}...")

# Find other services
vector_services = client.find_services(capability="vector_search")
for service in vector_services:
    print(f"Found service: {service['name']} at {service['endpoint']}")

# When shutting down
client.unregister()
```

#### Using the Message Bus Client

For components that need to communicate via the message bus:

```python
from hermes.api import HermesClient

# Create client
client = HermesClient(
    component_id="my-component-id",
    component_name="My Component",
    component_type="processor",
    hermes_endpoint="localhost:5555"
)

# Register with Hermes
await client.register()

# Publish a message
client.publish_message(
    topic="tekton.components.discovery",
    message={"action": "hello_world"},
    headers={"priority": "low"}
)

# Subscribe to a topic
def handle_message(message):
    print(f"Received message: {message}")

client.subscribe_to_topic(
    topic="tekton.events.processor",
    callback=handle_message
)

# When shutting down
await client.close()
```

## Security

The Unified Registration Protocol includes several security features:

### Token-Based Authentication

Each registered component receives a signed token that must be provided for subsequent operations:

```python
# Token structure (payload)
{
  "component_id": "engram-memory-14fd2c8b",
  "token_id": "5f8e3a1c-9d76-4b2e-b8f1-a13e4c9d7b2f",
  "iat": 1711809245,  # Issued at timestamp
  "exp": 1711812845   # Expiration timestamp (1 hour later)
}
```

The token is signed using HMAC-SHA256 with a secret key known only to the Hermes service.

### Authorization

- Components can only modify their own registration information
- Only components with valid tokens can send heartbeats or unregister
- The Hermes service validates all requests before processing

### Configuration

The following environment variables can be used to configure security aspects:

- `HERMES_SECRET_KEY`: Secret key for token generation and validation
- `TOKEN_EXPIRATION`: Token validity period in seconds (default: 3600)
- `ALLOW_ANONYMOUS_QUERIES`: Whether to allow querying services without authentication (default: true)

## Running the Registration Server

To run the registration server:

```bash
# From the Hermes directory
python scripts/run_registration_server.py --host 0.0.0.0 --port 8000 --secret-key my-secret-key

# Or with environment variables
export HOST=0.0.0.0
export PORT=8000
export HERMES_SECRET_KEY=my-secret-key
python scripts/run_registration_server.py
```

## Testing the Registration Protocol

For testing, a test script is provided:

```bash
# Run a full test cycle (register, heartbeat, query, unregister)
python scripts/test_registration.py --api-endpoint http://localhost:8000/api

# Test specific actions
python scripts/test_registration.py --action register
python scripts/test_registration.py --action query
```