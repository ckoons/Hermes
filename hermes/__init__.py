"""
Hermes - Vector Operations and Messaging Framework for Tekton

This module provides vector operations and inter-component messaging for the Tekton ecosystem.
"""

# Version information
__version__ = "0.1.0"

# Import the adapters module to ensure initialization
from . import adapters

# Define package exports
__all__ = ["adapters"]