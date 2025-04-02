# Hermes Logging System

The Hermes logging system provides a centralized logging infrastructure for all Tekton components. It offers a consistent interface for logging messages across the ecosystem while providing flexible output configuration.

## Core Features

- **Severity Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Component-based Logging**: Organize logs by component and sub-component
- **Namespace Isolation**: Segregate logs from different components
- **Configurable Output**: Format logs for different environments (development, production)
- **Rotation and Management**: Automatically rotate log files to prevent unbounded growth

## Usage

### Basic Logging

```python
from hermes.core.logging import get_logger

# Get a logger for a specific component
logger = get_logger("hermes.adapters.vector.faiss")

# Log messages at different levels
logger.debug("Debug message with detailed information")
logger.info("Informational message about normal operation")
logger.warning("Warning about potential issues")
logger.error("Error that prevented an operation")
logger.critical("Critical failure requiring immediate attention")
```

### Structured Logging

```python
# Log with additional structured data
logger.info("Database operation completed", 
            extra={
                "operation": "vector_search", 
                "duration_ms": 15.4,
                "results_count": 5
            })
```

### Configuration

The logging system can be configured through:

1. Environment variables
2. Configuration files
3. Programmatic configuration

Example configuration:

```python
from hermes.core.logging import configure_logging

configure_logging(
    level="INFO",               # Global log level
    component_levels={          # Component-specific levels
        "hermes.adapters": "DEBUG",
        "hermes.api": "WARNING"
    },
    output="console",           # Where to send logs (console, file, both)
    format="detailed",          # Log format (simple, detailed, json)
    log_dir="/var/log/tekton"   # Directory for log files
)
```

## Integration with Other Tekton Components

Other Tekton components can use the Hermes logging system by including it as a dependency:

```python
# In Engram code
from hermes.core.logging import get_logger

logger = get_logger("engram.memory")
logger.info("Memory operation completed")
```

## Best Practices

1. **Use Appropriate Levels**:
   - DEBUG: Detailed information for debugging
   - INFO: Confirmation of normal operation
   - WARNING: Indication of potential issues
   - ERROR: Operation failed but component can continue
   - CRITICAL: Component cannot function properly

2. **Structure Component Names**:
   - Use dot notation to indicate hierarchy
   - Start with the component name (e.g., "hermes", "engram")
   - Add subcomponents (e.g., "adapters.vector")
   - End with the specific module (e.g., "faiss")

3. **Include Context**:
   - Add relevant data using the `extra` parameter
   - Include operation durations for performance monitoring
   - Include identifiers to trace operations across components

## Implementation Details

The logging system is built on Python's standard library logging module with enhancements for:

- Automatic context enrichment
- JSON formatting for machine readability
- Colorized console output for human readability
- Integration with monitoring systems
- Performance optimizations for high-volume logging