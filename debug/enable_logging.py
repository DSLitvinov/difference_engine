"""
Debug helper script to enable detailed logging for Difference Engine addon

Run this in Blender's Python console to see detailed debug output:
    exec(open("/path/to/difference_engine/debug/enable_logging.py").read())

Or add to your Blender startup script for persistent logging.
"""

import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s',
    stream=sys.stdout,
    force=True  # Override existing configuration
)

# Enable debug logging for all addon modules
addon_modules = [
    'classes.material_exporter',
    'classes.material_importer',
    'classes.delta_exporter',
    'classes.version_manager',
    'classes.utils',
    'classes.operators.export_operator',
    'classes.operators.import_operator',
]

for module_name in addon_modules:
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

print("✓ Debug logging enabled for Difference Engine addon")
print("  Log level: DEBUG")
print(f"  Modules: {len(addon_modules)} modules")

