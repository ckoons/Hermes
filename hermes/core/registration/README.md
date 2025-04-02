# Unified Registration Protocol

This package implements the Unified Registration Protocol (URP) for Tekton components,
providing a single entry point for component registration, authentication, and
propagation of registration information to other Tekton systems.

## Overview

The URP enables components to register with the Tekton ecosystem, establish their
identity, and maintain their active status through heartbeats. It provides security
through token-based authentication and integrates with the service registry and
message bus for system-wide coordination.

## Module Structure

- **tokens.py**: Token generation and validation for security
- **manager.py**: Central registration manager implementation
- **client.py**: Client for components to interact with registration
- **handlers.py**: Event handlers for registration messages
- **types.py**: Type definitions and structures
- **utils.py**: Helper functions for registration operations

## Usage

### Setting up a Registration Manager

```python
from hermes.core.registration import RegistrationManager
from hermes.core.service_discovery import ServiceRegistry
from hermes.core.message_bus import MessageBus

# Create dependencies
service_registry = ServiceRegistry()
service_registry.start()

message_bus = MessageBus()
message_bus.connect()

# Create registration manager
manager = RegistrationManager(
    service_registry=service_registry,
    message_bus=message_bus,
    secret_key="your-secret-key"
)
```

### Using the Registration Client

```python
from hermes.core.registration import RegistrationClient
from hermes.core.message_bus import MessageBus

# Create message bus client
message_bus = MessageBus()
message_bus.connect()

# Create registration client
client = RegistrationClient(
    component_id="my-component-id",
    name="My Component",
    version="1.0.0",
    component_type="ergon",
    endpoint="http://localhost:8000",
    capabilities=["capability1", "capability2"],
    message_bus=message_bus
)

# Register with the system
await client.register()

# Later, unregister
await client.unregister()
```

## Security

The URP uses HMAC-SHA256 signed tokens for authentication. Each component receives
a token upon registration, which it must present for subsequent operations. Tokens
have an expiration time and are validated on each use.