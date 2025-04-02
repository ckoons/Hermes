# Database Adapters

This package contains the interface definitions for various types of database adapters used in Hermes.

## Overview

These adapter interfaces define a consistent API for database operations across different database technologies, allowing for a consistent programming model regardless of the underlying storage system.

## Adapter Types

- **DatabaseAdapter** - Base interface for all adapters (in `base.py`)
- **VectorDatabaseAdapter** - For vector similarity search (in `vector.py`)
- **GraphDatabaseAdapter** - For graph operations (in `graph.py`)
- **KeyValueDatabaseAdapter** - For key-value storage (in `key_value.py`)
- **DocumentDatabaseAdapter** - For document storage (in `document.py`)
- **CacheDatabaseAdapter** - For caching operations (in `cache.py`)
- **RelationalDatabaseAdapter** - For SQL operations (in `relational.py`)

## Creating a New Adapter

1. Choose the appropriate base adapter type for your database
2. Create a new class that inherits from the base adapter
3. Implement all required methods from the interface
4. Specify the database backend in the `backend` property

## Example

```python
from hermes.core.database.adapters import VectorDatabaseAdapter
from hermes.core.database.database_types import DatabaseBackend

class MyVectorAdapter(VectorDatabaseAdapter):
    @property
    def backend(self):
        return DatabaseBackend.CUSTOM
        
    async def connect(self):
        # Implementation
        pass
        
    # Implement all other required methods
```

## Integration

Adapters are used through the `DatabaseFactory` and `DatabaseManager` to provide a consistent interface to different database technologies.