# Debug Tools

Debugging utilities for Difference Engine addon development and troubleshooting.

## enable_logging.py

Enables detailed debug output for material import/export operations.

### Usage

In Blender's **Scripting** workspace or Python Console:

```python
# Method 1: Auto-locate script (recommended)
import bpy
import os
addon_path = bpy.utils.user_resource('EXTENSIONS')
script = os.path.join(addon_path, 'user_default', 'difference_engine', 'debug', 'enable_logging.py')
exec(open(script).read())

# Method 2: Direct path (if you know the location)
exec(open("/path/to/difference_engine/debug/enable_logging.py").read())
```

### Debug Output

Once enabled, you'll see detailed logs for:

- ✓ Material export/import progress
- ✓ Node creation and type mapping
- ✓ Property restoration (ColorRamps, Curves, etc.)
- ✓ Texture loading and assignment
- ✓ Socket connections
- ✓ Error tracebacks with full context

### Disable Logging

Restart Blender or run:

```python
import logging
logging.getLogger().setLevel(logging.INFO)
```

