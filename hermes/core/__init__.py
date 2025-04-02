"""
Core functionality for Hermes centralized database services and messaging.
"""

from hermes.core.vector_engine import VectorEngine
from hermes.core.message_bus import MessageBus
from hermes.core.service_discovery import ServiceRegistry
from hermes.core.registration import RegistrationManager, RegistrationClient, RegistrationToken
from hermes.core.logging import (
    LogLevel, LogEntry, LogManager, Logger, 
    init_logging, get_logger
)
from hermes.core.database_manager import (
    DatabaseType, DatabaseBackend, DatabaseManager,
    DatabaseAdapter, VectorDatabaseAdapter, GraphDatabaseAdapter,
    KeyValueDatabaseAdapter, DocumentDatabaseAdapter, CacheDatabaseAdapter,
    RelationalDatabaseAdapter, DatabaseFactory
)

__all__ = [
    # Vector operations
    "VectorEngine", 
    
    # Messaging and discovery
    "MessageBus", 
    "ServiceRegistry", 
    
    # Registration
    "RegistrationManager",
    "RegistrationClient",
    "RegistrationToken",
    
    # Logging
    "LogLevel",
    "LogEntry",
    "LogManager",
    "Logger",
    "init_logging",
    "get_logger",
    
    # Database Management
    "DatabaseType",
    "DatabaseBackend",
    "DatabaseManager",
    "DatabaseAdapter",
    "VectorDatabaseAdapter",
    "GraphDatabaseAdapter",
    "KeyValueDatabaseAdapter",
    "DocumentDatabaseAdapter",
    "CacheDatabaseAdapter",
    "RelationalDatabaseAdapter",
    "DatabaseFactory"
]