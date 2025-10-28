# Difference Engine - Blender Version Control Extension

A comprehensive version control system for Blender 3D models, providing Git-like functionality for managing mesh geometry, materials, textures, and transformations across different branches and commits.

## 🚀 Features

### Core Functionality
- **Version Control**: Save, load, and manage different versions of 3D models
- **Branch Management**: Create, switch, and manage multiple branches
- **Material Export/Import**: Full support for Blender materials including node trees, textures, and shaders
- **Selective Import**: Choose which components to import (geometry, materials, UV, transform)
- **Data Integrity**: Validation and restoration of corrupted data
- **Backup System**: Automatic backup and restore functionality

### Performance Optimizations
- **Batch Processing**: Optimized UV and geometry operations (5-10x faster)
- **Memory Management**: Chunked processing for large datasets
- **Compression**: Automatic compression of old versions to save disk space

### Security Features
- **Path Validation**: Prevents directory traversal attacks
- **File Extension Filtering**: Only allows safe file types
- **Input Sanitization**: Comprehensive input validation and sanitization

## 📁 Project Structure

```
difference_engine/
├── __init__.py                 # Main extension entry point
├── blender_manifest.toml       # Extension configuration
├── classes/                    # Core functionality modules
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── error_handler.py       # Standardized error handling
│   ├── utils.py               # Utility functions and validation
│   ├── material_exporter.py   # Material and texture export
│   ├── material_importer.py   # Material and texture import
│   ├── version_manager.py     # Version control operations
│   ├── migration.py           # Data migration utilities
│   └── operators/             # Blender operators
│       ├── __init__.py
│       ├── export_operator.py
│       ├── import_operator.py
│       ├── version_operators.py
│       ├── branch_operators.py
│       └── ui_operators.py
├── ui/                        # User interface components
│   ├── __init__.py
│   ├── ui_main.py            # Main UI module
│   ├── ui_helpers.py         # UI helper functions
│   ├── ui_lists.py           # UIList classes
│   ├── ui_panels.py          # Panel definitions
│   ├── ui_operators.py       # UI-specific operators
│   └── properties.py         # Scene properties
├── debug/                     # Debug utilities
│   ├── enable_logging.py
│   └── README.md
└── INDEX_STRUCTURE.md        # Index structure documentation
```

## 🛠️ Architecture

### Core Components

#### 1. Configuration Management (`config.py`)
- Centralized configuration system
- Persistent settings across Blender sessions
- Validation and type safety
- Singleton pattern for global access

#### 2. Error Handling (`error_handler.py`)
- Standardized error types and handling
- Comprehensive logging and reporting
- Decorator-based error handling
- Safe execution utilities

#### 3. Utilities (`utils.py`)
- Input validation and sanitization
- Safe data conversion functions
- File and path validation
- Memory-efficient data processing

#### 4. Material System
- **Exporter**: Handles complex node trees, textures, and shader properties
- **Importer**: Recreates materials with full fidelity
- **Validation**: Ensures data integrity during export/import

#### 5. Version Control
- **Version Manager**: Core version control operations
- **Index Manager**: Fast search and navigation
- **Migration**: Handles data structure updates

### UI Architecture

The UI is modularized for maintainability:

- **ui_main.py**: Main registration and coordination
- **ui_helpers.py**: Common UI patterns and utilities
- **ui_lists.py**: Custom UIList implementations
- **ui_panels.py**: Panel definitions and layouts
- **ui_operators.py**: UI-specific operators
- **properties.py**: Scene property definitions

## 🔧 Installation

1. Download the extension files
2. Place in Blender's extensions directory:
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\4.5\extensions\user_default\`
   - **macOS**: `~/Library/Application Support/Blender Foundation/Blender/4.5/extensions/user_default/`
   - **Linux**: `~/.config/blender/4.5/extensions/user_default/`
3. Enable in Blender's Extensions preferences
4. Find the "Difference Machine" panel in the 3D Viewport sidebar

## 📖 Usage

### Basic Workflow

1. **Select a mesh object** in the 3D Viewport
2. **Open the Difference Machine panel** in the sidebar
3. **Export**: Enter a commit message and click "Export Geometry"
4. **Import**: Select a version from history and choose import options
5. **Branch Management**: Create and switch between branches

### Advanced Features

#### Quick Search
- Use the Index Management panel to update indices
- Search through commits by message, author, or timestamp
- Near-instant results even with thousands of commits

#### Data Integrity
- Validate data integrity to check for corruption
- Automatic restoration of corrupted index files
- Backup and restore functionality

#### Selective Import
- Choose which components to import:
  - Geometry (vertices, faces)
  - Materials and textures
  - UV layouts
  - Object transformations
- Import as new object or apply to existing

## 🔒 Security

### Input Validation
- All file paths are validated and sanitized
- Directory traversal attacks are prevented
- File extensions are filtered for safety

### Error Handling
- Comprehensive error logging
- Graceful degradation on failures
- User-friendly error messages

### Data Integrity
- Validation of exported data
- Checksum verification for critical files
- Automatic backup before operations

## ⚡ Performance

### Optimizations Implemented
- **Batch UV Processing**: 5-10x faster using `foreach_set`
- **List Comprehensions**: 2-3x faster than append loops
- **Index-based Search**: Near-instant search results
- **Chunked Processing**: Memory-efficient for large datasets
- **Safe Vector Conversion**: Optimized NaN/Inf checking

### Memory Management
- Chunked processing for large UV datasets
- Efficient data structures
- Automatic cleanup of temporary data

## 🐛 Debugging

### Enable Debug Logging
```python
# In Blender's Python Console
exec(open("/path/to/difference_engine/debug/enable_logging.py").read())
```

### Debug Information
- Detailed operation logging
- Performance metrics
- Error tracebacks with context
- Material import/export progress

## 🔄 Migration

The extension includes automatic migration for data structure changes:
- Detects old data formats
- Migrates to new structure automatically
- Preserves all existing data
- Creates backups before migration

## 📊 Configuration

### Default Settings
```python
# Performance settings
DEFAULT_CHUNK_SIZE = 1000
MAX_SEARCH_RESULTS = 20
MAX_UI_LIST_ROWS = 10

# Version control settings
AUTO_COMPRESS_THRESHOLD = 10
INDEX_UPDATE_INTERVAL = 300  # seconds

# Security settings
ALLOWED_FILE_EXTENSIONS = ('.json', '.png', '.jpg', '.jpeg', '.tga', '.bmp', '.exr')
MAX_PATH_LENGTH = 255
```

### Customization
Configuration can be modified through the `config_manager`:
```python
from classes.config import config_manager

# Update settings
config_manager.update_config(
    DEFAULT_CHUNK_SIZE=2000,
    MAX_SEARCH_RESULTS=50
)

# Save configuration
config_manager.save_config("/path/to/addon")
```

## 🤝 Contributing

### Code Standards
- Type hints for all functions
- Comprehensive docstrings
- Error handling for all operations
- Logging for debugging
- Unit tests for core functionality

### Development Setup
1. Enable debug logging
2. Use the provided debug utilities
3. Follow the established error handling patterns
4. Add type hints to all new functions

## 📝 License

GPL-3.0-or-later

## 🆘 Support

For issues and feature requests, please refer to the project repository or contact the maintainer.

---

**Version**: 0.0.1  
**Blender Version**: 4.2.0+  
**Maintainer**: Dmitry Litvinov <nopomuk@yandex.ru>
