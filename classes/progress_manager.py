"""
Progress management for long-running operations in Difference Engine addon
"""
import bpy
import logging
from typing import Optional, Callable, Any
from contextlib import contextmanager

# Setup logging
logger = logging.getLogger(__name__)


class DFM_ProgressManager:
    """Manages progress reporting for long-running operations"""
    
    @staticmethod
    @contextmanager
    def progress_context(operation_name: str, total_steps: int, 
                        update_callback: Optional[Callable[[int, str], None]] = None):
        """
        Context manager for progress tracking.
        
        Args:
            operation_name: Name of the operation for display
            total_steps: Total number of steps in the operation
            update_callback: Optional callback function for custom progress updates
        """
        progress_manager = DFM_ProgressManager(operation_name, total_steps, update_callback)
        try:
            yield progress_manager
        finally:
            progress_manager.finish()
    
    def __init__(self, operation_name: str, total_steps: int, 
                 update_callback: Optional[Callable[[int, str], None]] = None):
        self.operation_name = operation_name
        self.total_steps = total_steps
        self.current_step = 0
        self.update_callback = update_callback
        self.start_time = None
        
        # Initialize progress
        self._update_progress(0, f"Starting {operation_name}")
    
    def _update_progress(self, step: int, message: str = ""):
        """Update progress display"""
        self.current_step = step
        progress_percent = (step / self.total_steps) * 100 if self.total_steps > 0 else 0
        
        # Update Blender's progress bar if available
        try:
            if hasattr(bpy.context, 'window_manager'):
                bpy.context.window_manager.progress_update(progress_percent)
        except Exception as e:
            logger.debug(f"Failed to update Blender progress: {e}")
        
        # Call custom callback if provided
        if self.update_callback:
            try:
                self.update_callback(step, message)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
        
        # Log progress
        if step % max(1, self.total_steps // 10) == 0 or step == self.total_steps:  # Log every 10% or final step
            logger.info(f"{self.operation_name}: {progress_percent:.1f}% - {message}")
    
    def step(self, message: str = ""):
        """Advance to next step"""
        self._update_progress(self.current_step + 1, message)
    
    def set_step(self, step: int, message: str = ""):
        """Set specific step"""
        self._update_progress(min(step, self.total_steps), message)
    
    def finish(self, message: str = "Completed"):
        """Finish the operation"""
        self._update_progress(self.total_steps, message)
        
        # Clear Blender progress bar
        try:
            if hasattr(bpy.context, 'window_manager'):
                bpy.context.window_manager.progress_end()
        except Exception as e:
            logger.debug(f"Failed to clear Blender progress: {e}")


def with_progress(operation_name: str, total_steps: int):
    """
    Decorator for adding progress tracking to functions.
    
    Args:
        operation_name: Name of the operation for display
        total_steps: Total number of steps in the operation
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with DFM_ProgressManager.progress_context(operation_name, total_steps) as progress:
                # Pass progress manager as first argument if function expects it
                if 'progress' in func.__code__.co_varnames:
                    return func(progress, *args, **kwargs)
                else:
                    return func(*args, **kwargs)
        return wrapper
    return decorator


class DFM_BatchProcessor:
    """Utility class for processing large datasets in batches with progress"""
    
    @staticmethod
    def process_in_batches(data: list, batch_size: int, processor_func: Callable,
                          operation_name: str = "Processing", 
                          progress_callback: Optional[Callable[[int, str], None]] = None) -> list:
        """
        Process data in batches with progress tracking.
        
        Args:
            data: List of items to process
            batch_size: Size of each batch
            processor_func: Function to process each batch
            operation_name: Name for progress display
            progress_callback: Optional progress callback
            
        Returns:
            List of processed results
        """
        if not data:
            return []
        
        total_batches = (len(data) + batch_size - 1) // batch_size
        
        with DFM_ProgressManager.progress_context(operation_name, total_batches, progress_callback) as progress:
            results = []
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                try:
                    batch_result = processor_func(batch)
                    results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
                    
                    progress.step(f"Processed batch {batch_num}/{total_batches}")
                    
                except Exception as e:
                    logger.error(f"Failed to process batch {batch_num}: {e}")
                    progress.step(f"Failed batch {batch_num}/{total_batches}")
                    continue
            
            return results
