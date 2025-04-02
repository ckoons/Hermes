# Tekton Centralized Logging System (CLS)

This directory contains the refactored implementation of the Tekton Centralized Logging System (CLS). The system was previously implemented as a single monolithic file (`logging.py`) but has now been refactored into a more modular structure for better maintainability and extensibility.

## Directory Structure

- **base/**: Core data structures and types
  - `levels.py`: Log level definitions
  - `entry.py`: Structured log entry implementation
  
- **storage/**: Storage implementations for log entries
  - `file_storage.py`: File-based storage with in-memory caching
  
- **management/**: Log processing and management
  - `manager.py`: Central manager for log processing
  
- **interface/**: User-facing API
  - `logger.py`: Logger interface for components
  
- **utils/**: Utility functions
  - `helpers.py`: Helper functions for initialization and logger creation

## Backward Compatibility

The original `logging.py` file now serves as a compatibility layer, importing and re-exporting all classes and functions from the new structure. This ensures that existing code using the Centralized Logging System will continue to work without modification.

## Usage

The API remains the same as before. Here's a simple example:

```python
from hermes.core.logging import get_logger, LogLevel

# Get a logger for your component
logger = get_logger("my.component")

# Log messages at different levels
logger.info("Starting operation")
logger.debug("Processing item", context={"item_id": "123"})
logger.error("Operation failed", code="ERR001", stack_trace="...")

# Create a logger with additional context
context_logger = logger.with_context({"user_id": "456"})
context_logger.info("User action")  # Will include user_id in context

# Create a logger with correlation ID for tracing
correlation_logger = logger.with_correlation("abc-123-def-456")
correlation_logger.info("Correlated event")  # Will use the same correlation ID
```

## Advanced Features

- **Structured Logging**: All logs include structured metadata and context
- **Correlation IDs**: Track operations across components with correlation IDs
- **Effective Timestamps**: Support for event time vs. logging time
- **In-memory Caching**: Recent logs are cached for efficient querying
- **File-based Storage**: Logs are stored in date-based directories for easier management