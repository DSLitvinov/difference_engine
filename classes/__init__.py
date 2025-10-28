"""
Classes module for Difference Machine addon

This module is organized into logical components:
- config: Configuration management
- error_handler: Standardized error handling
- utils: Helper functions for data conversion and validation
- material_exporter: Material and texture export
- material_importer: Material and texture import
- version_manager: Version control management
- migration: Data migration utilities
- operators: All Blender operators for UI interaction
"""

# Import utility functions
from .utils import (
    convert_to_json_serializable, 
    sanitize_path_component, 
    safe_float,
    validate_file_path,
    validate_directory_path,
    safe_vector3,
    chunk_list,
    get_file_size_mb,
    is_safe_file_extension
)

# Import error handling
from .error_handler import (
    DFM_Error,
    DFM_ValidationError,
    DFM_FileOperationError,
    DFM_MaterialError,
    DFM_GeometryError,
    DFM_IndexError,
    DFM_ErrorHandler,
    error_handler_decorator
)

# Import configuration management
from .config import DFM_Config, DFM_ConfigManager, config_manager

# Import core classes
from .material_exporter import DFM_MaterialExporter
from .material_importer import DFM_MaterialImporter
from .version_manager import DFM_VersionManager
from .migration import DFM_Migration

# Import operators and classes list
from .operators import classes

# For backwards compatibility with old imports
from .operators import (
    DFM_SaveGeometryOperator,
    DFM_LoadGeometryOperator,
    DFM_LoadVersionOperator,
    DFM_CompareVersionsOperator,
    DFM_DeleteVersionOperator,
    DFM_CreateBranchOperator,
    DFM_SwitchBranchOperator,
    DFM_ListBranchesOperator,
    DFM_DeleteBranchOperator,
    DFM_GoToBranchOperator,
    DFM_ToggleImportAll_OT_operator,
    DFM_ToggleImportNone_OT_operator
)

__all__ = [
    # Configuration
    'DFM_Config',
    'DFM_ConfigManager',
    'config_manager',
    
    # Error handling
    'DFM_Error',
    'DFM_ValidationError',
    'DFM_FileOperationError',
    'DFM_MaterialError',
    'DFM_GeometryError',
    'DFM_IndexError',
    'DFM_ErrorHandler',
    'error_handler_decorator',
    
    # Utilities
    'convert_to_json_serializable',
    'sanitize_path_component',
    'safe_float',
    'validate_file_path',
    'validate_directory_path',
    'safe_vector3',
    'chunk_list',
    'get_file_size_mb',
    'is_safe_file_extension',
    
    # Core classes
    'DFM_MaterialExporter',
    'DFM_MaterialImporter',
    'DFM_VersionManager',
    'DFM_Migration',
    
    # Operators
    'DFM_SaveGeometryOperator',
    'DFM_LoadGeometryOperator',
    'DFM_LoadVersionOperator',
    'DFM_CompareVersionsOperator',
    'DFM_DeleteVersionOperator',
    'DFM_CreateBranchOperator',
    'DFM_SwitchBranchOperator',
    'DFM_ListBranchesOperator',
    'DFM_DeleteBranchOperator',
    'DFM_GoToBranchOperator',
    'DFM_ToggleImportAll_OT_operator',
    'DFM_ToggleImportNone_OT_operator',
    
    # Classes list for registration
    'classes'
]
