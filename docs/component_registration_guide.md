# Tekton Component Registration Guide

This guide explains how to register Tekton components with the Hermes service registry using the standardized registration protocol.

## Overview

The Component Registration Protocol standardizes how Tekton components:

1. Register themselves with the Hermes service registry
2. Advertise their capabilities to other components 
3. Handle heartbeats for health monitoring
4. Gracefully unregister when shutting down

## Registration Workflow

1. **Initialize Registration Client**: Create a client with component details, capabilities, and dependencies
2. **Register Component**: Send registration information to Hermes
3. **Maintain Heartbeats**: Automatically send periodic heartbeats to indicate health
4. **Graceful Shutdown**: Handle signals and cleanly unregister when shutting down

## Component Registration Script

Each Tekton component should include a `register_with_hermes.py` script that follows the standardized template. This script:

- Can be run directly to register the component
- Supports command-line arguments and environment variables
- Handles graceful shutdown
- Maintains heartbeats
- Falls back to direct Hermes communication if standardized utilities are unavailable

### Usage

```bash
# Basic usage
python register_with_hermes.py

# With custom Hermes URL
python register_with_hermes.py --hermes-url http://hermes-server:8000/api

# With startup instructions file
python register_with_hermes.py --instructions-file path/to/instructions.json

# With custom component endpoint
python register_with_hermes.py --endpoint http://my-component:5000
```

## Standardized Utilities

The `tekton.utils.hermes_registration` module provides standardized utilities for component registration, including:

- **HermesRegistrationClient**: Main client for component registration
- **register_component()**: Convenience function for simple registration
- **load_startup_instructions()**: Helper for loading configuration from files

### Example Usage

```python
from tekton.utils.hermes_registration import register_component

client = await register_component(
    component_id="my-component",
    component_name="My Component",
    component_type="service",
    component_version="1.0.0",
    capabilities=[...],
    hermes_url="http://hermes-server:8000/api",
    dependencies=["other-component"],
    endpoint="http://my-component:5000"
)

# Client automatically maintains heartbeats

# Set up graceful shutdown
client.setup_signal_handlers()

# When shutting down
await client.close()
```

## Component Capability Definition

Capabilities should be defined in a standardized format that includes:

- Name
- Description
- Parameters with types

Example:

```python
capabilities = [
    {
        "name": "create_project",
        "description": "Create a new project",
        "parameters": {
            "name": "string",
            "description": "string (optional)",
            "metadata": "object (optional)"
        }
    },
    {
        "name": "get_project",
        "description": "Get project details",
        "parameters": {
            "project_id": "string"
        }
    }
]
```

## Component Dependencies

Dependencies should be specified as a list of component IDs that this component depends on:

```python
dependencies = ["prometheus.planning", "hermes.core.database"]
```

## Environment Variables

The registration system supports several environment variables:

- `HERMES_URL`: URL of the Hermes API
- `STARTUP_INSTRUCTIONS_FILE`: Path to JSON file with startup instructions
- `<COMPONENT>_API_ENDPOINT`: API endpoint for the component (e.g., `TELOS_API_ENDPOINT`)

## Startup Instructions File

Components can load configuration from a startup instructions JSON file:

```json
{
  "component_id": "telos.requirements",
  "name": "Telos Requirements Manager",
  "type": "requirements_management",
  "version": "0.1.0",
  "dependencies": ["prometheus.planning"],
  "hermes_url": "http://hermes-server:8000/api",
  "endpoint": "http://telos:5800",
  "capabilities": [...],
  "metadata": {
    "description": "Requirements management and refinement for Tekton",
    "ui_available": true
  }
}
```

## Implemented Components

The following components have been updated to use the standardized registration protocol:

1. **Sophia (ML Engine)**
   - Capabilities: Text embedding, classification, model management
   - Dependencies: Hermes database

2. **Prometheus (Planning Engine)**
   - Capabilities: Plan creation, complexity assessment, latent reasoning
   - Dependencies: Tekton latent reasoning

3. **Telos (Requirements Management)**
   - Capabilities: Project and requirement management, analysis, refinement
   - Dependencies: Prometheus planning

4. **Other components pending implementation:**
   - Harmonia (Workflow Engine)

## Best Practices

1. **Unique Component IDs**: Use a consistent naming scheme (e.g., `component.service`)
2. **Clear Capabilities**: Define capabilities with clear names, descriptions, and parameters
3. **Explicit Dependencies**: List all components your component depends on
4. **Graceful Shutdown**: Always handle shutdown signals properly
5. **Fallback Support**: Implement fallbacks for when standard utilities are unavailable
6. **Health Monitoring**: Ensure heartbeats are maintained for accurate health reporting

## Troubleshooting

### Common Issues

1. **Registration Failure**
   - Ensure Hermes is running and accessible
   - Check for correct URL and authentication

2. **Path Issues**
   - Ensure the component and Tekton core paths are properly added to the Python path

3. **Missing Dependencies**
   - Make sure to install all required dependencies

4. **Virtual Environment**
   - Run the registration script within the component's virtual environment

### Logs

Registration logs are stored in the component's log directory and include:

- Registration attempts
- Heartbeat status
- Shutdown events

## Next Steps

1. Implement registration scripts for remaining components
2. Develop comprehensive testing suite for registration validation
3. Implement discovery mechanism for components to find each other
4. Document API patterns for cross-component communication