# FAISS Vector Adapter

A high-performance vector database adapter that uses Facebook AI Similarity Search (FAISS) for efficient similarity search with hardware acceleration.

## Overview

The FAISS Vector Adapter provides a VectorDatabaseAdapter implementation that offers:

- Fast and efficient similarity search
- Support for both CPU and GPU acceleration
- Vector normalization and handling
- Automatic index selection based on dataset size
- Metadata filtering
- Persistence to disk

## Module Structure

The adapter has been refactored into a modular structure:

- `__init__.py`: Re-exports the adapter for backward compatibility
- `adapter.py`: Main adapter class with initialization and interface methods
- `index.py`: Index creation and management functions
- `operations.py`: Vector operations (store, search, get, list, delete)
- `utils.py`: Utility functions like filtering and ID mapping

## Usage

```python
from hermes.adapters.vector.faiss import FAISSVectorAdapter

# Initialize adapter
adapter = FAISSVectorAdapter(
    namespace="my_namespace",
    config={
        "vector_dim": 1536,  # Default for OpenAI embeddings
        "use_gpu": True,     # Use GPU if available
        "base_path": "/path/to/data"
    }
)

# Connect to database
await adapter.connect()

# Store a vector
await adapter.store(
    id="vector1",
    vector=[0.1, 0.2, ...],  # Your embedding vector
    metadata={"source": "document1", "type": "text"},
    text="This is the original text"
)

# Search for similar vectors
results = await adapter.search(
    query_vector=[0.15, 0.25, ...],
    limit=10,
    filter={"type": "text"}
)

# Get a specific vector
vector = await adapter.get("vector1")

# List vectors
vectors = await adapter.list(
    limit=100,
    offset=0,
    filter={"source": "document1"}
)

# Delete a vector
await adapter.delete(id="vector1")

# Disconnect from database
await adapter.disconnect()
```

## Implementation Details

### Index Selection

The adapter automatically selects the most appropriate FAISS index based on:

- Dataset size
- Whether GPU is available
- Performance requirements

For large datasets (>10K vectors on CPU, >1K on GPU), the adapter uses an IVF (Inverted File) index with a configurable number of centroids. For smaller datasets, it uses a flat index for maximum recall.

### Data Storage

Vectors are stored:

- In memory for fast access
- On disk for persistence between runs
- With a separate index file for fast similarity search

### Filtering

The adapter supports filtering on metadata fields:

- Simple key-value matching
- Nested field access (e.g., `"metadata.user.id"`)
- Efficient filtering after vector search for best performance