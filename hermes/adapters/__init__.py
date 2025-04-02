"""
Database adapters for various backend systems.

This package contains adapters for different database systems,
organized by database type, with fallback implementations.
"""

from pathlib import Path
from typing import Dict

# Ensure all adapter directories exist
adapter_dirs = [
    "vector",
    "graph", 
    "key_value",
    "document",
    "cache",
    "relation"
]

# Create adapter directories if they don't exist
for adapter_dir in adapter_dirs:
    Path(__file__).parent.joinpath(adapter_dir).mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = Path(__file__).parent.joinpath(adapter_dir, "__init__.py")
    if not init_file.exists():
        with open(init_file, "w") as f:
            f.write(f'"""\n{adapter_dir.title()} database adapters for the Hermes system.\n"""')