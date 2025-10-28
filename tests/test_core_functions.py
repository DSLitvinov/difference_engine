"""
Unit tests for Difference Engine addon critical functions
"""
import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import the modules we want to test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.utils import (
    sanitize_path_component,
    safe_float,
    safe_vector3,
    validate_file_path,
    validate_directory_path,
    convert_to_json_serializable,
    validate_export_data_size,
    estimate_mesh_memory_usage,
    is_safe_file_extension
)
from classes.error_handler import (
    DFM_Error,
    DFM_ValidationError,
    DFM_FileOperationError,
    DFM_ErrorHandler
)
from classes.config import DFM_Config, DFM_ConfigManager


class TestUtils(unittest.TestCase):
    """Test utility functions"""
    
    def test_sanitize_path_component(self):
        """Test path component sanitization"""
        # Test normal names
        self.assertEqual(sanitize_path_component("test"), "test")
        self.assertEqual(sanitize_path_component("my_mesh"), "my_mesh")
        
        # Test dangerous characters
        self.assertEqual(sanitize_path_component("test/../file"), "test_.._file")
        self.assertEqual(sanitize_path_component("file:name"), "file_name")
        self.assertEqual(sanitize_path_component("file*name"), "file_name")
        
        # Test edge cases
        with self.assertRaises(ValueError):
            sanitize_path_component("")
        
        with self.assertRaises(ValueError):
            sanitize_path_component(None)
        
        # Test long names
        long_name = "a" * 150
        result = sanitize_path_component(long_name)
        self.assertEqual(len(result), 100)  # Should be truncated
    
    def test_safe_float(self):
        """Test safe float conversion"""
        # Test normal values
        self.assertEqual(safe_float(1.5), 1.5)
        self.assertEqual(safe_float("2.5"), 2.5)
        self.assertEqual(safe_float(3), 3.0)
        
        # Test edge cases
        self.assertEqual(safe_float(None), 0.0)
        self.assertEqual(safe_float("invalid"), 0.0)
        
        # Test NaN and Inf handling
        import math
        self.assertEqual(safe_float(float('nan')), 0.0)
        self.assertEqual(safe_float(float('inf')), 0.0)
        self.assertEqual(safe_float(float('-inf')), 0.0)
    
    def test_safe_vector3(self):
        """Test safe vector3 conversion"""
        # Mock vector with x, y, z attributes
        mock_vec = Mock()
        mock_vec.x = 1.0
        mock_vec.y = 2.0
        mock_vec.z = 3.0
        
        result = safe_vector3(mock_vec)
        self.assertEqual(result, [1.0, 2.0, 3.0])
        
        # Test list-like object
        result = safe_vector3([4.0, 5.0, 6.0])
        self.assertEqual(result, [4.0, 5.0, 6.0])
        
        # Test invalid vector
        with self.assertRaises(ValueError):
            safe_vector3(None)
        
        with self.assertRaises(ValueError):
            safe_vector3("invalid")
    
    def test_validate_file_path(self):
        """Test file path validation"""
        # Test valid paths
        self.assertTrue(validate_file_path("test.json"))
        self.assertTrue(validate_file_path("folder/test.json"))
        
        # Test dangerous paths
        self.assertFalse(validate_file_path("../test.json"))
        self.assertFalse(validate_file_path("test/../file.json"))
        
        # Test absolute paths
        self.assertFalse(validate_file_path("/absolute/path.json"))
        self.assertTrue(validate_file_path("/absolute/path.json", allow_absolute=True))
        
        # Test edge cases
        self.assertFalse(validate_file_path(""))
        self.assertFalse(validate_file_path(None))
    
    def test_validate_export_data_size(self):
        """Test export data size validation"""
        # Test small data
        small_data = {"test": "data"}
        self.assertTrue(validate_export_data_size(small_data))
        
        # Test large data
        large_data = {"test": "x" * 1000000}  # ~1MB
        result = validate_export_data_size(large_data, max_size_mb=0.1)
        self.assertFalse(result)
        
        # Test with higher limit
        result = validate_export_data_size(large_data, max_size_mb=2.0)
        self.assertTrue(result)
    
    def test_estimate_mesh_memory_usage(self):
        """Test mesh memory usage estimation"""
        # Test basic calculation
        memory = estimate_mesh_memory_usage(1000, 500, 2)
        expected = (1000 * 3 * 4 + 500 * 4 * 4 + 1000 * 2 * 2 * 4) / (1024 * 1024)
        self.assertAlmostEqual(memory, expected, places=2)
        
        # Test with no UV layers
        memory = estimate_mesh_memory_usage(1000, 500, 0)
        expected = (1000 * 3 * 4 + 500 * 4 * 4) / (1024 * 1024)
        self.assertAlmostEqual(memory, expected, places=2)
    
    def test_is_safe_file_extension(self):
        """Test file extension safety check"""
        # Test safe extensions
        self.assertTrue(is_safe_file_extension("test.json"))
        self.assertTrue(is_safe_file_extension("image.png"))
        self.assertTrue(is_safe_file_extension("texture.jpg"))
        
        # Test unsafe extensions
        self.assertFalse(is_safe_file_extension("script.py"))
        self.assertFalse(is_safe_file_extension("executable.exe"))
        
        # Test custom allowed extensions
        self.assertTrue(is_safe_file_extension("test.py", ('.py', '.json')))
        self.assertFalse(is_safe_file_extension("test.exe", ('.py', '.json')))


class TestErrorHandler(unittest.TestCase):
    """Test error handling system"""
    
    def test_dfm_error_creation(self):
        """Test DFM_Error creation"""
        error = DFM_Error("Test error", details={"key": "value"})
        self.assertEqual(str(error), "[unknown_error] Test error")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.details["key"], "value")
    
    def test_validation_error(self):
        """Test DFM_ValidationError"""
        error = DFM_ValidationError("Invalid input", field="test_field", value="bad_value")
        self.assertEqual(error.error_type.value, "validation_error")
        self.assertEqual(error.details["field"], "test_field")
        self.assertEqual(error.details["value"], "bad_value")
    
    def test_file_operation_error(self):
        """Test DFM_FileOperationError"""
        error = DFM_FileOperationError("File not found", file_path="/test/path", operation="read")
        self.assertEqual(error.error_type.value, "file_operation_error")
        self.assertEqual(error.details["file_path"], "/test/path")
        self.assertEqual(error.details["operation"], "read")
    
    def test_error_handler_validate_required_params(self):
        """Test parameter validation"""
        # Test valid parameters
        params = {"key1": "value1", "key2": "value2"}
        DFM_ErrorHandler.validate_required_params(params, ["key1", "key2"])
        
        # Test missing parameter
        with self.assertRaises(DFM_ValidationError):
            DFM_ErrorHandler.validate_required_params(params, ["key1", "key3"])
        
        # Test None parameter
        params_with_none = {"key1": "value1", "key2": None}
        with self.assertRaises(DFM_ValidationError):
            DFM_ErrorHandler.validate_required_params(params_with_none, ["key1", "key2"])


class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def test_config_creation(self):
        """Test DFM_Config creation"""
        config = DFM_Config()
        self.assertEqual(config.DEFAULT_CHUNK_SIZE, 1000)
        self.assertEqual(config.MAX_SEARCH_RESULTS, 20)
        self.assertTrue(config.AUTO_REFRESH_ENABLED)
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = DFM_Config()
        self.assertTrue(config.validate())
        
        # Test invalid configuration
        config.DEFAULT_CHUNK_SIZE = -1
        with self.assertRaises(ValueError):
            config.validate()
    
    def test_config_manager_singleton(self):
        """Test config manager singleton pattern"""
        manager1 = DFM_ConfigManager()
        manager2 = DFM_ConfigManager()
        self.assertIs(manager1, manager2)
    
    def test_config_save_load(self):
        """Test configuration save and load"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.json")
            
            # Test save
            config = DFM_Config()
            config.DEFAULT_CHUNK_SIZE = 2000
            self.assertTrue(config.save_to_file(config_path))
            
            # Test load
            loaded_config = DFM_Config.load_from_file(config_path)
            self.assertEqual(loaded_config.DEFAULT_CHUNK_SIZE, 2000)
    
    def test_config_update(self):
        """Test configuration update"""
        manager = DFM_ConfigManager()
        
        # Test valid update
        result = manager.update_config(DEFAULT_CHUNK_SIZE=2000, MAX_SEARCH_RESULTS=50)
        self.assertTrue(result)
        self.assertEqual(manager.config.DEFAULT_CHUNK_SIZE, 2000)
        self.assertEqual(manager.config.MAX_SEARCH_RESULTS, 50)
        
        # Test invalid update
        result = manager.update_config(DEFAULT_CHUNK_SIZE=-1)
        self.assertFalse(result)


class TestConvertToJsonSerializable(unittest.TestCase):
    """Test JSON serialization conversion"""
    
    def test_basic_types(self):
        """Test basic type conversion"""
        self.assertEqual(convert_to_json_serializable(None), None)
        self.assertEqual(convert_to_json_serializable(True), True)
        self.assertEqual(convert_to_json_serializable("test"), "test")
        self.assertEqual(convert_to_json_serializable(123), 123)
        self.assertEqual(convert_to_json_serializable(45.6), 45.6)
    
    def test_list_conversion(self):
        """Test list conversion"""
        result = convert_to_json_serializable([1, 2, 3])
        self.assertEqual(result, [1, 2, 3])
        
        # Test nested lists
        result = convert_to_json_serializable([[1, 2], [3, 4]])
        self.assertEqual(result, [[1, 2], [3, 4]])
    
    def test_dict_conversion(self):
        """Test dictionary conversion"""
        result = convert_to_json_serializable({"key": "value", "num": 123})
        self.assertEqual(result, {"key": "value", "num": 123})
    
    def test_blender_types(self):
        """Test Blender type conversion"""
        # Mock Blender vector
        mock_vector = Mock()
        mock_vector.__iter__ = Mock(return_value=iter([1.0, 2.0, 3.0]))
        
        result = convert_to_json_serializable(mock_vector)
        self.assertEqual(result, [1.0, 2.0, 3.0])


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestUtils))
    test_suite.addTest(unittest.makeSuite(TestErrorHandler))
    test_suite.addTest(unittest.makeSuite(TestConfig))
    test_suite.addTest(unittest.makeSuite(TestConvertToJsonSerializable))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
