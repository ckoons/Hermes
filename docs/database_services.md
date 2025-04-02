# Hermes Database Services

Hermes provides a centralized set of database services that can be used by all Tekton components. These services abstract away the underlying database implementations, providing a consistent interface for various data storage and retrieval needs.

## Available Database Types

### 1. Vector Database

Optimized for storing and retrieving vector embeddings used in semantic search:

```python
from hermes.utils.database_helper import DatabaseClient

# Initialize client
db_client = DatabaseClient(component_id="engram.memory")

# Get vector database for a specific namespace
vector_db = await db_client.get_vector_db(namespace="conversations")

# Store a vector with metadata and text
await vector_db.store(
    id="memory-123",
    vector=[0.1, 0.2, 0.3, ...],  # Vector embedding
    metadata={"timestamp": "2025-03-30T12:34:56Z", "user": "alice"},
    text="This is the full text associated with the vector"
)

# Search for similar vectors
results = await vector_db.search(
    query_vector=[0.15, 0.22, 0.31, ...],
    limit=5,
    filter={"user": "alice"}
)
```

### 2. Key-Value Database

For simple key-value storage with optional expiration:

```python
# Get key-value database
kv_db = await db_client.get_key_value_db(namespace="cache")

# Store values
await kv_db.set("user:alice", {"name": "Alice", "role": "admin"})
await kv_db.set("session:123", {"user_id": "alice", "active": True}, expiration=3600)  # 1 hour

# Retrieve values
user = await kv_db.get("user:alice")

# Check if key exists
exists = await kv_db.exists("session:123")

# Delete key
await kv_db.delete("session:123")

# Batch operations
await kv_db.set_batch({
    "counter:1": 42,
    "counter:2": 73,
    "counter:3": 19
})
```

### 3. Graph Database

For storing and querying interconnected data:

```python
# Get graph database
graph_db = await db_client.get_graph_db(namespace="knowledge")

# Add nodes
await graph_db.add_node(
    id="person:alice",
    labels=["Person", "Employee"],
    properties={"name": "Alice", "role": "Developer"}
)

await graph_db.add_node(
    id="project:tekton",
    labels=["Project"],
    properties={"name": "Tekton", "status": "Active"}
)

# Add relationships
await graph_db.add_relationship(
    source_id="person:alice",
    target_id="project:tekton",
    type="WORKS_ON",
    properties={"since": "2025-01-01", "role": "Lead Developer"}
)

# Query the graph
results = await graph_db.query(
    query="""
    MATCH (p:Person)-[r:WORKS_ON]->(proj:Project)
    WHERE proj.name = $project_name
    RETURN p, r, proj
    """,
    params={"project_name": "Tekton"}
)
```

## Database Backends

Each database type supports multiple backend implementations:

### Vector Database Backends

- **FAISS**: High-performance vector similarity search with GPU acceleration
- **LanceDB**: Document-oriented vector database (via Engram integration)
- **Fallback**: Simple in-memory implementation for systems without specialized databases

### Key-Value Database Backends

- **Redis**: Fast in-memory data structure store
- **Local**: Simple file-based implementation for development/testing

### Graph Database Backends

- **Neo4j**: Industry-standard graph database with Cypher query language
- **Memory**: Simple in-memory implementation for development/testing

## Namespace Isolation

All database operations occur within a specific namespace to isolate data from different components:

```python
# Different namespaces for different data types
conversations_db = await db_client.get_vector_db(namespace="conversations")
thinking_db = await db_client.get_vector_db(namespace="thinking")
projects_db = await db_client.get_vector_db(namespace="projects")
```

## Hardware-Aware Optimization

The database services automatically select the most appropriate backend based on available hardware:

- CUDA-enabled GPUs for FAISS GPU acceleration
- Apple Metal for optimized performance on Apple Silicon
- Fallback to CPU implementations when specialized hardware is unavailable

## Integration with Other Tekton Components

### Engram Integration

```python
from engram.integrations.hermes.memory_adapter import HermesMemoryService

# Initialize memory service with Hermes integration
memory = HermesMemoryService(client_id="claude")

# Add a memory (uses Hermes vector database)
await memory.add(
    content="Important information to remember",
    namespace="conversations",
    metadata={"timestamp": "2025-03-30T12:34:56Z"}
)

# Search memories (uses Hermes vector search)
results = await memory.search("important information", namespace="conversations")
```

### Athena Integration

```python
from athena.integrations.hermes.knowledge_adapter import HermesKnowledgeAdapter

# Initialize knowledge service with Hermes integration
knowledge = HermesKnowledgeAdapter()

# Store knowledge entities (uses Hermes graph database)
await knowledge.add_entity("Person", "Alice", {"role": "Developer"})
await knowledge.add_entity("Project", "Tekton", {"status": "Active"})
await knowledge.add_relationship("Person", "Alice", "WORKS_ON", "Project", "Tekton")

# Query knowledge graph (uses Hermes graph queries)
developers = await knowledge.query_entities("Person", {"role": "Developer"})
```

## Configuration

Database services can be configured through:

1. Environment variables
2. Configuration files
3. Programmatic configuration

Example configuration:

```python
from hermes.utils.database_helper import configure_databases

configure_databases(
    vector_db={
        "backend": "faiss",
        "use_gpu": True,
        "default_dimensions": 1536
    },
    key_value_db={
        "backend": "redis",
        "host": "localhost",
        "port": 6379
    },
    graph_db={
        "backend": "neo4j",
        "uri": "bolt://localhost:7687",
        "username": "neo4j",
        "password": "password"
    }
)
```

## Best Practices

1. **Use Namespaces Properly**:
   - Separate data by logical category
   - Use consistent naming conventions
   - Document namespace purposes

2. **Handle Connection Management**:
   - Use the context manager pattern for database access
   - Close connections explicitly when done
   - Handle connection errors gracefully

3. **Optimize for Your Use Case**:
   - Vector search: Use appropriate dimensions and indexing
   - Key-value: Set appropriate expiration times
   - Graph: Design schemas for efficient querying