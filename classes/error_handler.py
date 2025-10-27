"""
Standardized error handling for Difference Engine addon
"""
import logging
import traceback
from typing import Any, Dict, Optional, Callable, Type
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)


class DFM_ErrorType(Enum):
    """Types of errors that can occur in Difference Engine"""
    VALIDATION_ERROR = "validation_error"
    FILE_OPERATION_ERROR = "file_operation_error"
    MATERIAL_ERROR = "material_error"
    GEOMETRY_ERROR = "geometry_error"
    INDEX_ERROR = "index_error"
    CONFIG_ERROR = "config_error"
    UI_ERROR = "ui_error"
    UNKNOWN_ERROR = "unknown_error"


class DFM_Error(Exception):
    """Base exception class for Difference Engine errors"""
    
    def __init__(self, message: str, error_type: DFM_ErrorType = DFM_ErrorType.UNKNOWN_ERROR, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.traceback = traceback.format_exc()
    
    def __str__(self) -> str:
        return f"[{self.error_type.value}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            'error_type': self.error_type.value,
            'message': self.message,
            'details': self.details,
            'traceback': self.traceback
        }


class DFM_ValidationError(DFM_Error):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(message, DFM_ErrorType.VALIDATION_ERROR, {'field': field, 'value': value})


class DFM_FileOperationError(DFM_Error):
    """Raised when file operations fail"""
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, DFM_ErrorType.FILE_OPERATION_ERROR, {'file_path': file_path, 'operation': operation})


class DFM_MaterialError(DFM_Error):
    """Raised when material operations fail"""
    def __init__(self, message: str, material_name: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, DFM_ErrorType.MATERIAL_ERROR, {'material_name': material_name, 'operation': operation})


class DFM_GeometryError(DFM_Error):
    """Raised when geometry operations fail"""
    def __init__(self, message: str, object_name: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, DFM_ErrorType.GEOMETRY_ERROR, {'object_name': object_name, 'operation': operation})


class DFM_IndexError(DFM_Error):
    """Raised when index operations fail"""
    def __init__(self, message: str, index_type: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, DFM_ErrorType.INDEX_ERROR, {'index_type': index_type, 'operation': operation})


class DFM_ErrorHandler:
    """Centralized error handling for Difference Engine"""
    
    @staticmethod
    def handle_operator_error(operator_instance: Any, error: Exception, 
                            context: Optional[str] = None) -> Dict[str, str]:
        """
        Handle errors in Blender operators with standardized reporting.
        
        Args:
            operator_instance: The operator instance that encountered the error
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            Dictionary with 'result' key indicating operator result
        """
        try:
            # Log the error with full context
            error_context = f" in {context}" if context else ""
            logger.error(f"Operator error{error_context}: {str(error)}")
            
            if isinstance(error, DFM_Error):
                # Handle our custom errors
                logger.error(f"Error details: {error.to_dict()}")
                
                # Report to Blender UI
                operator_instance.report({'ERROR'}, f"{error.error_type.value}: {error.message}")
                
                # Log specific error types
                if error.error_type == DFM_ErrorType.VALIDATION_ERROR:
                    logger.error("Validation error occurred - check input parameters")
                elif error.error_type == DFM_ErrorType.FILE_OPERATION_ERROR:
                    logger.error("File operation failed - check file paths and permissions")
                elif error.error_type == DFM_ErrorType.MATERIAL_ERROR:
                    logger.error("Material operation failed - check material data integrity")
                
            else:
                # Handle generic exceptions
                logger.error(f"Unexpected error: {traceback.format_exc()}")
                operator_instance.report({'ERROR'}, f"Unexpected error: {str(error)}")
            
            return {'CANCELLED'}
            
        except Exception as handler_error:
            # If error handling itself fails, log and return generic error
            logger.critical(f"Error handler failed: {handler_error}")
            logger.critical(f"Original error: {error}")
            operator_instance.report({'ERROR'}, "An unexpected error occurred")
            return {'CANCELLED'}
    
    @staticmethod
    def handle_function_error(function_name: str, error: Exception, 
                           context: Optional[str] = None) -> None:
        """
        Handle errors in utility functions with standardized logging.
        
        Args:
            function_name: Name of the function that encountered the error
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        try:
            error_context = f" in {context}" if context else ""
            logger.error(f"Function '{function_name}' error{error_context}: {str(error)}")
            
            if isinstance(error, DFM_Error):
                logger.error(f"Error details: {error.to_dict()}")
            else:
                logger.error(f"Unexpected error in {function_name}: {traceback.format_exc()}")
                
        except Exception as handler_error:
            logger.critical(f"Error handler failed for function '{function_name}': {handler_error}")
            logger.critical(f"Original error: {error}")
    
    @staticmethod
    def safe_execute(func: Callable, *args, **kwargs) -> tuple[Any, Optional[Exception]]:
        """
        Safely execute a function and return result with any exception.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Tuple of (result, exception) where exception is None if successful
        """
        try:
            result = func(*args, **kwargs)
            return result, None
        except Exception as e:
            DFM_ErrorHandler.handle_function_error(func.__name__, e)
            return None, e
    
    @staticmethod
    def validate_required_params(params: Dict[str, Any], required_keys: list[str]) -> None:
        """
        Validate that required parameters are present and not None.
        
        Args:
            params: Dictionary of parameters to validate
            required_keys: List of required parameter keys
            
        Raises:
            DFM_ValidationError: If required parameters are missing or None
        """
        for key in required_keys:
            if key not in params:
                raise DFM_ValidationError(f"Required parameter '{key}' is missing", field=key)
            
            if params[key] is None:
                raise DFM_ValidationError(f"Required parameter '{key}' cannot be None", field=key, value=None)
    
    @staticmethod
    def log_operation_start(operation: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log the start of an operation for debugging."""
        detail_str = f" - {details}" if details else ""
        logger.info(f"Starting operation: {operation}{detail_str}")
    
    @staticmethod
    def log_operation_success(operation: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log successful completion of an operation."""
        detail_str = f" - {details}" if details else ""
        logger.info(f"Operation completed successfully: {operation}{detail_str}")
    
    @staticmethod
    def log_operation_failure(operation: str, error: Exception, details: Optional[Dict[str, Any]] = None) -> None:
        """Log failure of an operation."""
        detail_str = f" - {details}" if details else ""
        logger.error(f"Operation failed: {operation}{detail_str} - {str(error)}")


def error_handler_decorator(error_type: DFM_ErrorType = DFM_ErrorType.UNKNOWN_ERROR):
    """
    Decorator to wrap functions with standardized error handling.
    
    Args:
        error_type: Type of error to raise if function fails
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                DFM_ErrorHandler.log_operation_start(func.__name__)
                result = func(*args, **kwargs)
                DFM_ErrorHandler.log_operation_success(func.__name__)
                return result
            except DFM_Error:
                # Re-raise our custom errors
                raise
            except Exception as e:
                # Wrap generic exceptions
                DFM_ErrorHandler.log_operation_failure(func.__name__, e)
                raise DFM_Error(f"Error in {func.__name__}: {str(e)}", error_type) from e
        return wrapper
    return decorator
