# Update Components

This directory contains the refactored implementation of the Update Components system for Tekton. The system was previously implemented as a single monolithic file (`update_all_components.py`) but has now been refactored into a more modular structure for better maintainability and extensibility.

## Directory Structure

- **core/**: Core functionality for update management
  - `args.py`: Command-line arguments handling
  - `manager.py`: Update coordination and management
  
- **updaters/**: Component-specific update implementations
  - `engram.py`: Updater for Engram component
  - `ergon.py`: Updater for Ergon component
  - `athena.py`: Updater for Athena component
  - `harmonia.py`: Updater for Harmonia component
  - `hermes.py`: Updater for Hermes's internal components
  
- **utils/**: Utility functions for file and code manipulation
  - `file.py`: File manipulation utilities
  - `code.py`: Code analysis and modification utilities
  - `module.py`: Module importing utilities
  
- **templates/**: Reusable templates for code generation
  - `logging_imports.py`: Templates for centralizing logging

## Backward Compatibility

The original `update_all_components.py` file now serves as a compatibility layer, importing and re-exporting classes and functions from the new structure. This ensures that existing scripts using the update functionality will continue to work without modification.

## Usage

The script can be invoked the same way as before:

```bash
python update_all_components.py --components engram ergon
```

This will update the specified components to use Hermes centralized services.

## Key Features

- **Component Updaters**: Specialized updaters for each Tekton component
- **Template System**: Reusable templates for consistent code generation
- **Code Analysis**: Intelligent analysis of Python code to identify logging patterns
- **Safe Modifications**: Non-destructive file modification with fallbacks
- **Compatibility Layer**: Backward compatibility with existing scripts
- **Modular Design**: Easy to extend with new updaters or template types