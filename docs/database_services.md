# Hermes Database Services

## Overview

Hermes Database Services provides a centralized database solution for the Tekton ecosystem, offering a unified interface to access multiple database types through a single API. It abstracts away the complexities of database selection, connection management, and resource optimization, allowing components to focus on their core functionality.

## Key Features

- **Unified Interface**: Access different database types through a consistent API
- **Automatic Backend Selection**: Optimized for available hardware (GPU, Apple Silicon, etc.)
- **Namespace Isolation**: Data segregation between different components
- **Connection Pooling**: Efficient resource utilization
- **Multi-Protocol Access**: Support for both REST API and MCP protocol
- **Comprehensive Client Library**: Simple, idiomatic client code
- **Graceful Degradation**: Fallback to simpler backends when preferred ones are unavailable

## Architecture

Hermes Database Services consists of several components:

1. **Database Manager**: Core service that manages connections and adapters
2. **Database Adapters**: Type-specific implementations for each database type
3. **MCP Server**: Multi-Capability Provider server for MCP protocol access
4. **REST API**: RESTful API endpoints for direct HTTP access
5. **Client Library**: Easy-to-use client code for Tekton components

## Tekton Integration Philosophy

The Hermes Database Services embodies Tekton's core philosophy:

- **Single Point of Control**: Hermes automatically manages all database services, starting and stopping them as needed. Components don't need to worry about service management.
- **Automatic Configuration**: Common configuration is shared across services, simplifying deployment and management.
- **Seamless Discovery**: Components automatically discover and connect to the appropriate database services without manual configuration.
- **Registration and Health Monitoring**: All database services are registered with Hermes and monitored for health status.
- **Resource Optimization**: Resources are shared and optimized across the ecosystem.

This approach allows Tekton to operate as a cohesive system rather than a collection of independent components, enhancing reliability, efficiency, and developer experience.

## Supported Database Types

| Type | Description | Use Cases | Available Backends |
|------|-------------|-----------|-------------------|
| Vector | Vector database for embeddings | Semantic search, similarity matching | FAISS, Qdrant, ChromaDB, LanceDB |
| Graph | Graph database for relationships | Knowledge graphs, network analysis | Neo4j, NetworkX |
| Key-Value | Key-value store for simple data | Caching, configuration storage | Redis, LevelDB, RocksDB |
| Document | Document database for unstructured data | Content storage, metadata | MongoDB, JSONDB |
| Cache | In-memory cache for temporary data | Session storage, result caching | Memory, Memcached |
| Relational | SQL database for structured data | User data, structured information | SQLite, PostgreSQL |

## Getting Started

### Component Registration

When the Hermes service starts, it automatically:

1. Starts the Database MCP server
2. Registers both services with the service registry
3. Sets up connections and resource sharing

This means component developers don't need to start or manage database services themselves - it's all handled by Hermes.

### Client Usage

```python
# Get a Hermes client
from hermes.api.client import HermesClient

client = HermesClient(
    component_id="my-component",
    component_name="My Component",
    component_type="analysis"
)

# Register with Hermes
await client.register()

# Get a database client
db = client.get_database_client()

# Use the database
vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
metadatas = [{"text": "Hello"}, {"text": "World"}]

# Store vectors
result = await db.vector_store(
    vectors=vectors,
    metadatas=metadatas,
    namespace="my-component"
)

# Search vectors
results = await db.vector_search(
    query_vector=[0.2, 0.3, 0.4],
    top_k=3,
    namespace="my-component"
)

# Cache a value
await db.cache_set(
    key="user:1234",
    value={"name": "Alice", "role": "Admin"},
    ttl=3600,
    namespace="my-component"
)

# Clean up
await client.close()
```

## Configuration

Hermes Database Services can be configured through environment variables:

- `HERMES_DATA_DIR`: Base directory for database storage (default: `~/.tekton/data`)
- `DB_MCP_PORT`: Port for the Database MCP server (default: `8002`)
- `DB_MCP_HOST`: Host for the Database MCP server (default: `127.0.0.1`)
- `HERMES_PORT`: Port for the main Hermes API (default: `8000`)
- `DEBUG`: Enable debug mode (default: `False`)

## Database-Specific Options

Each database type can be configured with specific options:

### Vector Database

```python
# Specific backend
await db.vector_store(
    vectors=vectors,
    backend="faiss"  # or "qdrant", "chromadb", "lancedb"
)

# With search filter
await db.vector_search(
    query_vector=query_vector,
    filter={"category": "science"}
)
```

### Graph Database

```python
# Add nodes and relationships
await db.graph_add_node(
    node_id="person1",
    labels=["Person"],
    properties={"name": "Alice"}
)

await db.graph_add_relationship(
    source_id="person1",
    target_id="person2",
    rel_type="KNOWS",
    properties={"since": 2020}
)

# Run Cypher query (Neo4j)
await db.graph_query(
    query="MATCH (p:Person)-[:KNOWS]->(f) RETURN p, f",
    parameters={}
)
```

## Developing Custom Adapters

Tekton's modular architecture allows for custom database adapters. To create a custom adapter:

1. Create a new adapter class that inherits from the appropriate base adapter
2. Implement the required methods
3. Register the adapter with the database factory

Custom adapters can then be used through the standard interface.

## Technical Details

### Data Storage

Each database type maintains separate data storage in the `HERMES_DATA_DIR` directory:

```
~/.tekton/data/
  ├── vector/
  │   ├── default/
  │   ├── my-component/
  │   └── another-component/
  ├── graph/
  ├── key_value/
  ├── document/
  ├── cache/
  └── relation/
```

### Namespace Isolation

Each component should use its own namespace for data isolation:

```python
# Component A
await db.kv_set(key="config", value={"mode": "A"}, namespace="component-a")

# Component B
await db.kv_set(key="config", value={"mode": "B"}, namespace="component-b")
```

This prevents namespace collisions and data leakage between components.

### Error Handling

The client library includes robust error handling and automatic reconnection:

```python
try:
    result = await db.vector_search(query_vector=[0.1, 0.2, 0.3])
except Exception as e:
    logger.error(f"Database error: {e}")
    # Fallback behavior
```

## Performance Considerations

- Vector operations with FAISS use GPU acceleration when available
- Connection pooling reduces overhead for frequent operations
- Use namespaces effectively to partition data for better performance
- Consider caching frequently accessed data using the cache database

## Security

- Data is isolated by namespace
- Authentication is handled through the registration process
- Components can only access databases after registration
- Database files are protected by filesystem permissions