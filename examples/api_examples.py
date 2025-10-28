# Difference Engine API Examples

This document provides practical examples of using the Difference Engine addon API for common tasks.

## Basic Material Export/Import

### Exporting a Material

```python
import bpy
from classes.material_exporter import DFM_MaterialExporter

# Get the active object's first material
obj = bpy.context.active_object
if obj and obj.data.materials:
    material = obj.data.materials[0]
    
    # Export the material
    exporter = DFM_MaterialExporter()
    result = exporter.export_material(material, "/path/to/export/directory")
    
    if result:
        print(f"Material exported successfully: {result}")
    else:
        print("Material export failed")
```

### Importing a Material

```python
from classes.material_importer import DFM_MaterialImporter

# Import a material
material = DFM_MaterialImporter.import_material(
    "/path/to/material_MyMaterial.json",
    "/path/to/import/directory"
)

if material:
    print(f"Successfully imported: {material.name}")
    
    # Apply to current object
    obj = bpy.context.active_object
    if obj and obj.type == 'MESH':
        obj.data.materials.append(material)
```

## Version Control Operations

### Getting Object History

```python
from classes.version_manager import DFM_VersionManager

# Get commit history for an object
obj_name = "MyMesh"
history = DFM_VersionManager.get_object_history(obj_name)

print(f"Found {len(history)} commits for {obj_name}")
for commit in history[:5]:  # Show last 5 commits
    print(f"  {commit['timestamp']}: {commit['commit_message']}")
```

### Branch Management

```python
# Get all branches for an object
branches = DFM_VersionManager.get_object_branches("MyMesh")

print("Available branches:")
for branch in branches:
    print(f"  {branch['name']}: {branch['commit_count']} commits")
```

### Compressing Old Versions

```python
# Compress old versions to save space
DFM_VersionManager.compress_old_versions("MyMesh", keep_versions=5)
print("Old versions compressed")
```

## Error Handling

### Using Custom Error Types

```python
from classes.error_handler import (
    DFM_ValidationError, 
    DFM_FileOperationError,
    DFM_ErrorHandler
)

try:
    # Some operation that might fail
    result = risky_operation()
except DFM_ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Field: {e.details.get('field')}")
except DFM_FileOperationError as e:
    print(f"File error: {e.message}")
    print(f"File: {e.details.get('file_path')}")
except Exception as e:
    DFM_ErrorHandler.handle_function_error("my_function", e)
```

### Safe Function Execution

```python
from classes.error_handler import DFM_ErrorHandler

# Safely execute a function
result, error = DFM_ErrorHandler.safe_execute(my_function, arg1, arg2)

if error:
    print(f"Function failed: {error}")
else:
    print(f"Function succeeded: {result}")
```

## Utility Functions

### Path Sanitization

```python
from classes.utils import sanitize_path_component

# Sanitize user input for file paths
user_input = "My Mesh/Name*with?bad:chars"
safe_name = sanitize_path_component(user_input)
print(f"Safe name: {safe_name}")  # "My Mesh_Name_with_bad_chars"
```

### Data Validation

```python
from classes.utils import validate_export_data_size, estimate_mesh_memory_usage

# Check if mesh data is too large
mesh_data = {"vertices": [...], "faces": [...]}
if not validate_export_data_size(mesh_data, max_size_mb=50):
    print("Warning: Mesh data exceeds size limit")

# Estimate memory usage
memory_mb = estimate_mesh_memory_usage(10000, 5000, 2)
print(f"Estimated memory usage: {memory_mb:.2f} MB")
```

### Safe Type Conversion

```python
from classes.utils import safe_float, safe_vector3

# Convert potentially problematic values
value = safe_float("invalid")  # Returns 0.0
vector = safe_vector3([1.0, 2.0, 3.0])  # Returns [1.0, 2.0, 3.0]
```

## Progress Tracking

### Using Progress Manager

```python
from classes.progress_manager import DFM_ProgressManager

# Track progress for long operations
with DFM_ProgressManager.progress_context("Processing Data", 100) as progress:
    for i in range(100):
        # Do some work
        process_item(i)
        progress.step(f"Processed item {i}")
```

### Batch Processing

```python
from classes.progress_manager import DFM_BatchProcessor

# Process large datasets in batches
def process_batch(batch):
    return [item * 2 for item in batch]

data = list(range(1000))
results = DFM_BatchProcessor.process_in_batches(
    data, 
    batch_size=100, 
    processor_func=process_batch,
    operation_name="Doubling Numbers"
)
```

## Configuration Management

### Using Config Manager

```python
from classes.config import config_manager

# Update configuration
config_manager.update_config(
    DEFAULT_CHUNK_SIZE=2000,
    MAX_SEARCH_RESULTS=50
)

# Get current config
config = config_manager.config
print(f"Chunk size: {config.DEFAULT_CHUNK_SIZE}")

# Save configuration
config_manager.save_config("/path/to/addon/directory")
```

## Memory Management

### Cleaning Up Unused Images

```python
from classes.material_importer import DFM_MaterialImporter

# Clean up unused images to free memory
removed_count = DFM_MaterialImporter.cleanup_unused_images()
print(f"Removed {removed_count} unused images")
```

## Advanced Material Operations

### Working with Node Trees

```python
# Export complex node tree
material = bpy.data.materials["MyMaterial"]
if material.use_nodes:
    exporter = DFM_MaterialExporter()
    node_data = exporter.export_node_tree(material.node_tree, "/path/to/textures")
    print(f"Exported {len(node_data['nodes'])} nodes")
```

### Handling Large Textures

```python
import os

# Check texture size before loading
texture_path = "/path/to/texture.png"
if os.path.exists(texture_path):
    size_mb = os.path.getsize(texture_path) / (1024 * 1024)
    if size_mb > 50:
        print(f"Warning: Large texture ({size_mb:.1f} MB)")
```

## Migration Operations

### Running Data Migration

```python
from classes.migration import DFM_Migration

# Check if migration is needed
base_dir = "/path/to/.difference_machine"
if DFM_Migration.check_migration_needed(base_dir):
    print("Migration needed, running...")
    success = DFM_Migration.migrate_all_commits(base_dir)
    if success:
        print("Migration completed successfully")
    else:
        print("Migration failed")
```

## Complete Workflow Example

```python
"""
Complete example: Export object, modify it, and import previous version
"""

import bpy
from classes.material_exporter import DFM_MaterialExporter
from classes.material_importer import DFM_MaterialImporter
from classes.version_manager import DFM_VersionManager
from classes.operators.export_operator import DFM_SaveGeometryOperator
from classes.operators.import_operator import DFM_LoadGeometryOperator

def complete_workflow_example():
    # Get active object
    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH':
        print("Please select a mesh object")
        return
    
    # 1. Export current state
    print("Exporting current state...")
    exporter = DFM_SaveGeometryOperator()
    # Note: In real usage, you'd call this through the operator system
    # bpy.ops.object.save_geometry()
    
    # 2. Get history
    print("Getting version history...")
    history = DFM_VersionManager.get_object_history(obj.name)
    print(f"Found {len(history)} versions")
    
    # 3. Import previous version (if available)
    if len(history) > 1:
        previous_commit = history[1]  # Second most recent
        commit_path = previous_commit['commit_path']
        
        print(f"Importing previous version: {previous_commit['commit_message']}")
        # Note: In real usage, you'd call this through the operator system
        # bpy.ops.object.load_geometry(filepath=commit_path)
    
    # 4. Clean up
    print("Cleaning up unused images...")
    removed = DFM_MaterialImporter.cleanup_unused_images()
    print(f"Removed {removed} unused images")

# Run the example
if __name__ == "__main__":
    complete_workflow_example()
