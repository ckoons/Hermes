# Centralized Logging Update

{component_name} has been updated to use the Centralized Logging System (CLS) from Hermes. This provides the following benefits:

1. **Structured Logging**: All logs follow a standardized schema
2. **Schema Versioning**: Log schema evolution is tracked for backward compatibility
3. **Effective Timestamps**: Distinguish between when an event occurred vs. when it was logged
4. **Log Levels**: Standardized log levels (FATAL, ERROR, WARN, INFO, NORMAL, DEBUG, TRACE)
5. **Contextual Information**: Rich context for all log entries
6. **Correlation**: Track related log entries across components
7. **Storage**: Logs are stored centrally for easier debugging and analysis

## Compatibility

The update is backward compatible - if Hermes is not available, {component_name} will fall back to using standard Python logging.

## How to Use

No changes are needed to use the basic logging functionality. For advanced features:

```python
# Access Hermes logging features if available
if USE_CENTRALIZED_LOGGING:
    # Log with context
    logger.info("User action", context={"user_id": "user123"})
    
    # Create correlated logger
    op_logger = logger.with_correlation("operation-123")
    op_logger.info("Operation started")
    op_logger.info("Operation completed")
```

## Next Steps

More {component_name} modules will be updated to use the Centralized Logging System in future updates.