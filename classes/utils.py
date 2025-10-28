"""
Utility functions for Difference Machine addon
"""
import re
import math
import os
import logging
from typing import Any, Union, List, Dict, Optional, Tuple
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)


def sanitize_path_component(name: Any) -> str:
    """
    Remove potentially dangerous characters from path components.
    
    Prevents directory traversal attacks and invalid filenames.
    
    Args:
        name: The path component to sanitize
        
    Returns:
        Sanitized string safe for use in file paths
        
    Raises:
        ValueError: If name is None or empty after sanitization
    """
    if not name:
        raise ValueError("Path component cannot be None or empty")
    
    # Convert to string and remove path separators and special characters
    safe_name = re.sub(r'[/\\:*?"<>|]', '_', str(name))
    
    # Remove leading/trailing dots and spaces
    safe_name = safe_name.strip('. ')
    
    # Prevent empty names after sanitization
    if not safe_name:
        raise ValueError("Path component becomes empty after sanitization")
    
    # Limit length to prevent filesystem issues
    if len(safe_name) > 100:  # Reasonable limit for filenames
        safe_name = safe_name[:100]
        logger.warning(f"Path component truncated to 100 characters: {safe_name}")
    
    return safe_name


def safe_float(value: Any) -> float:
    """
    Convert a value to float, handling NaN and Inf values.
    
    Args:
        value: Value to convert to float
        
    Returns:
        float: Safe float value (NaN and Inf replaced with 0.0)
        
    Raises:
        ValueError: If value cannot be converted to float
    """
    if value is None:
        logger.warning("None value provided to safe_float, returning 0.0")
        return 0.0
    
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            logger.warning(f"Invalid float value detected: {value}, replacing with 0.0")
            return 0.0
        return f
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to convert {value} to float: {e}, returning 0.0")
        return 0.0


def convert_to_json_serializable(obj: Any) -> Union[None, bool, str, int, float, List[Any], Dict[str, Any]]:
    """
    Recursively convert Blender types to JSON-serializable Python types.
    
    Handles Blender-specific types like Vector, Color, and ensures all
    numeric values are safe for JSON serialization.
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON-serializable Python object
    """
    if obj is None:
        return None
    
    # Handle strings and booleans first
    if isinstance(obj, (str, bool, type(None))):
        return obj
    
    # Handle numbers - convert Blender numeric types to Python types
    if hasattr(obj, '__float__'):
        try:
            return safe_float(obj)
        except (TypeError, ValueError):
            pass
    
    if hasattr(obj, '__int__'):
        try:
            return int(obj)
        except (TypeError, ValueError):
            pass
    
    # Handle iterables (Vector, Color, lists, tuples, etc.)
    if hasattr(obj, '__iter__'):
        try:
            return [convert_to_json_serializable(item) for item in obj]
        except (TypeError, ValueError):
            pass
    
    # Handle dictionaries
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    
    # Fallback - try to convert to string or return None
    try:
        return str(obj)
    except Exception:
        return None


def validate_file_path(file_path: str, must_exist: bool = False, must_be_file: bool = False, allow_absolute: bool = False) -> bool:
    """
    Validate a file path for security and correctness.
    
    Args:
        file_path: Path to validate
        must_exist: Whether the path must exist
        must_be_file: Whether the path must be a file (not directory)
        allow_absolute: Whether to allow absolute paths (for export operations)
        
    Returns:
        True if path is valid, False otherwise
    """
    if not file_path or not isinstance(file_path, str):
        logger.error("File path is None or not a string")
        return False
    
    # Check for path traversal attempts - prevent relative paths
    if '..' in file_path:
        logger.error(f"Potentially dangerous path detected: {file_path}")
        return False
    
    # Prevent absolute paths unless explicitly allowed
    if os.path.isabs(file_path) and not allow_absolute:
        logger.error(f"Absolute path not allowed: {file_path}")
        return False
    
    # Check for leading path separators and relative components
    normalized = os.path.normpath(file_path)
    if normalized != file_path and file_path.lstrip('.' + os.sep) != file_path:
        logger.error(f"Path contains relative components: {file_path}")
        return False
    
    # Prevent backslash manipulation on Windows
    if '\\' in file_path and os.sep != '\\':
        logger.error(f"Invalid path separator detected: {file_path}")
        return False
    
    # Check path length
    if len(file_path) > 255:
        logger.error(f"Path too long: {len(file_path)} characters")
        return False
    
    if must_exist:
        if not os.path.exists(file_path):
            logger.error(f"Path does not exist: {file_path}")
            return False
        
        if must_be_file and not os.path.isfile(file_path):
            logger.error(f"Path is not a file: {file_path}")
            return False
    
    return True


def validate_directory_path(dir_path: str, create_if_missing: bool = False, allow_absolute: bool = False) -> bool:
    """
    Validate a directory path and optionally create it.
    
    Args:
        dir_path: Directory path to validate
        create_if_missing: Whether to create directory if it doesn't exist
        allow_absolute: Whether to allow absolute paths (for export operations)
        
    Returns:
        True if directory is valid/exists, False otherwise
    """
    if not validate_file_path(dir_path, allow_absolute=allow_absolute):
        return False
    
    if not os.path.exists(dir_path):
        if create_if_missing:
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                return False
        else:
            logger.error(f"Directory does not exist: {dir_path}")
            return False
    
    if not os.path.isdir(dir_path):
        logger.error(f"Path is not a directory: {dir_path}")
        return False
    
    return True


def safe_vector3(vec: Any) -> List[float]:
    """
    Convert 3D vector to list with safe floats.
    
    Args:
        vec: Vector object with x, y, z components
        
    Returns:
        List of 3 safe float values
        
    Raises:
        ValueError: If vector is invalid
    """
    if not vec:
        raise ValueError("Vector cannot be None")
    
    try:
        # Try to access x, y, z attributes
        if hasattr(vec, 'x') and hasattr(vec, 'y') and hasattr(vec, 'z'):
            result = [safe_float(vec.x), safe_float(vec.y), safe_float(vec.z)]
        elif hasattr(vec, '__len__') and len(vec) >= 3:
            # Handle list-like objects
            result = [safe_float(vec[0]), safe_float(vec[1]), safe_float(vec[2])]
        else:
            raise ValueError("Vector does not have expected x,y,z attributes or length >= 3")
        
        # Check for invalid values
        if any(math.isnan(v) or math.isinf(v) for v in result):
            logger.warning("Invalid vector detected, replacing with zeros")
            return [0.0, 0.0, 0.0]
        
        return result
        
    except (AttributeError, IndexError, TypeError) as e:
        logger.error(f"Failed to convert vector to safe float list: {e}")
        raise ValueError(f"Invalid vector format: {e}")


def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        data: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
        
    Raises:
        ValueError: If chunk_size is invalid
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    if not data:
        return []
    
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB, or 0.0 if file doesn't exist
    """
    try:
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)  # Convert to MB
        return 0.0
    except Exception as e:
        logger.error(f"Failed to get file size for {file_path}: {e}")
        return 0.0


def is_safe_file_extension(file_path: str, allowed_extensions: Tuple[str, ...] = None) -> bool:
    """
    Check if file has a safe extension.
    
    Args:
        file_path: Path to check
        allowed_extensions: Tuple of allowed extensions (defaults to common safe extensions)
        
    Returns:
        True if extension is safe, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = ('.json', '.png', '.jpg', '.jpeg', '.tga', '.bmp', '.exr')
    
    try:
        ext = Path(file_path).suffix.lower()
        return ext in allowed_extensions
    except Exception as e:
        logger.error(f"Failed to check file extension for {file_path}: {e}")
        return False


def validate_export_data_size(data: Dict[str, Any], max_size_mb: float = 100.0) -> bool:
    """
    Validate that export data size is within acceptable limits.
    
    Args:
        data: Data dictionary to validate
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        True if data size is acceptable, False otherwise
        
    Raises:
        DFM_ValidationError: If data size exceeds limits
    """
    try:
        import json
        import sys
        
        # Estimate size by serializing to JSON
        json_str = json.dumps(data, separators=(',', ':'))  # Compact format
        size_bytes = sys.getsizeof(json_str)
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb > max_size_mb:
            logger.warning(f"Export data size ({size_mb:.2f} MB) exceeds limit ({max_size_mb} MB)")
            return False
        
        logger.debug(f"Export data size: {size_mb:.2f} MB")
        return True
        
    except Exception as e:
        logger.error(f"Failed to validate data size: {e}")
        return False


def estimate_mesh_memory_usage(vertex_count: int, face_count: int, uv_layer_count: int = 0) -> float:
    """
    Estimate memory usage for mesh data in MB.
    
    Args:
        vertex_count: Number of vertices
        face_count: Number of faces
        uv_layer_count: Number of UV layers
        
    Returns:
        Estimated memory usage in MB
    """
    # Rough estimates based on typical Blender data structures
    vertex_memory = vertex_count * 3 * 4  # 3 floats * 4 bytes per float
    face_memory = face_count * 4 * 4  # 4 ints * 4 bytes per int
    uv_memory = vertex_count * uv_layer_count * 2 * 4  # 2 floats per UV layer
    
    total_bytes = vertex_memory + face_memory + uv_memory
    return total_bytes / (1024 * 1024)  # Convert to MB

