# Database Management System

This module was refactored from a single large file (`database_manager.py`) into a more modular structure to improve maintainability and readability, following the Tekton engineering guidelines on file size (under 500 lines per file).

## Module Structure

- `database_types.py`: Contains enum definitions for database types and backends
- `adapters.py`: Contains abstract base classes for different database adapters
- `factory.py`: Contains the factory for creating database adapters
- `manager.py`: Contains the main DatabaseManager class
- `__init__.py`: Exports the main classes and functions

## Compatibility 

The main `database_manager.py` file in the parent directory acts as a compatibility layer, re-exporting the key components from the modular structure. This ensures backward compatibility with existing code that imports from the original location.

## Usage

The functionality remains the same, but the code is now more modular and easier to maintain. Import the classes and functions as before:

```python
from hermes.core.database_manager import DatabaseManager, DatabaseType, DatabaseBackend
```

Or import directly from the new structure:

```python
from hermes.core.database.manager import DatabaseManager
from hermes.core.database.database_types import DatabaseType, DatabaseBackend
```