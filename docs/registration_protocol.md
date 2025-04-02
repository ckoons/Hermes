# Hermes Registration Protocol

The Hermes Registration Protocol defines how components within the Tekton ecosystem register themselves, discover each other, and maintain service health information.

## Core Concepts

### 1. Service Registry

The central registry maintains information about all available services:

- Service identifier
- Service type
- Capabilities
- Endpoint information
- Health status
- Metadata

### 2. Service Discovery

Components can discover other services based on:

- Service type (e.g., "llm", "memory", "vector-db")
- Specific capabilities (e.g., "reasoning", "tool_use")
- Health status

### 3. Health Monitoring

The registry periodically checks service health through:

- Heartbeat monitoring
- Endpoint validation
- Performance metrics collection

## Registration Process

### Step 1: Service Registration

Services register themselves with the central registry:

```python
from hermes.core.registration import ServiceRegistry

# Initialize service registry
registry = ServiceRegistry()

# Register a service
registry.register(
    service_id="claude-main",
    name="Claude 3 Opus",
    version="20240229",
    endpoint="http://localhost:11434",
    capabilities=["llm", "reasoning", "tool_use", "image_understanding"],
    metadata={
        "client_id": "main",
        "model": "claude-3-opus-20240229",
        "provider": "anthropic"
    }
)
```

### Step 2: Service Discovery

Other components can discover registered services:

```python
from hermes.core.registration import ServiceRegistry

# Initialize service registry
registry = ServiceRegistry()

# Find services with specific capabilities
llm_services = registry.find_services(
    capabilities=["llm", "reasoning"],
    status="healthy"
)

# Get a specific service by ID
claude_service = registry.get_service("claude-main")
```

### Step 3: Heartbeat and Health Updates

Services periodically update their health status:

```python
# Update health status
registry.update_health(
    service_id="claude-main",
    status="healthy",
    metrics={
        "response_time_ms": 250,
        "requests_per_minute": 15,
        "error_rate": 0.01
    }
)
```

## Protocol Message Format

The registration protocol uses a simple JSON message format:

### Registration Message

```json
{
  "action": "register",
  "service_id": "claude-main",
  "name": "Claude 3 Opus",
  "version": "20240229",
  "endpoint": "http://localhost:11434",
  "capabilities": ["llm", "reasoning", "tool_use", "image_understanding"],
  "metadata": {
    "client_id": "main",
    "model": "claude-3-opus-20240229",
    "provider": "anthropic"
  }
}
```

### Health Update Message

```json
{
  "action": "health_update",
  "service_id": "claude-main",
  "status": "healthy",
  "timestamp": "2025-03-30T12:34:56Z",
  "metrics": {
    "response_time_ms": 250,
    "requests_per_minute": 15,
    "error_rate": 0.01
  }
}
```

## Security Considerations

The registration protocol includes security measures:

1. **Authentication**: Services must authenticate before registering
2. **Authorization**: Only authorized components can modify service information
3. **Encryption**: Communication is encrypted using TLS
4. **Validation**: All messages are validated against the protocol schema

## Integration with Other Tekton Components

### Engram Integration

```python
# Register Engram memory service
registry.register(
    service_id="engram-memory",
    name="Engram Memory Service",
    version="1.0.0",
    endpoint="http://localhost:8000",
    capabilities=["memory", "vector_search"],
    metadata={
        "storage_type": "faiss",
        "vector_dimensions": 1536
    }
)
```

### Ergon Integration

```python
# Register Ergon tool service
registry.register(
    service_id="ergon-tools",
    name="Ergon Tool Service",
    version="1.0.0",
    endpoint="http://localhost:8080",
    capabilities=["tool_registry", "tool_execution"],
    metadata={
        "available_tools": ["web_search", "calculator", "code_execution"]
    }
)
```

## Implementation Notes

- The registry maintains an in-memory cache with periodic persistence
- Service health is validated through regular heartbeat checks
- Services that fail health checks are marked as unhealthy
- Services that don't respond for an extended period are removed from the registry