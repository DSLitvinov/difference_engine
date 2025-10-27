"""
Configuration management for Difference Engine addon
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class DFM_Config:
    """Configuration settings for Difference Engine"""
    
    # Performance settings
    DEFAULT_CHUNK_SIZE: int = 1000
    MAX_SEARCH_RESULTS: int = 20
    MAX_UI_LIST_ROWS: int = 10
    
    # Version control settings
    AUTO_COMPRESS_THRESHOLD: int = 10
    INDEX_UPDATE_INTERVAL: int = 300  # seconds
    
    # File operation settings
    MAX_FILE_SIZE_MB: int = 100
    BACKUP_RETENTION_DAYS: int = 30
    
    # UI settings
    AUTO_REFRESH_ENABLED: bool = True
    SHOW_DEBUG_INFO: bool = False
    
    # Security settings
    ALLOWED_FILE_EXTENSIONS: tuple = ('.json', '.png', '.jpg', '.jpeg', '.tga', '.bmp', '.exr')
    MAX_PATH_LENGTH: int = 255
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'DFM_Config':
        """Load configuration from JSON file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    data = json.load(f)
                return cls(**data)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return cls()  # Return default config
    
    def save_to_file(self, config_path: str) -> bool:
        """Save configuration to JSON file"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(asdict(self), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            return False
    
    def validate(self) -> bool:
        """Validate configuration values"""
        if self.DEFAULT_CHUNK_SIZE <= 0:
            logger.error("DEFAULT_CHUNK_SIZE must be positive")
            return False
        
        if self.MAX_SEARCH_RESULTS <= 0:
            logger.error("MAX_SEARCH_RESULTS must be positive")
            return False
        
        if self.AUTO_COMPRESS_THRESHOLD < 0:
            logger.error("AUTO_COMPRESS_THRESHOLD must be non-negative")
            return False
        
        return True


class DFM_ConfigManager:
    """Manages configuration for Difference Engine"""
    
    _instance: Optional['DFM_ConfigManager'] = None
    _config: Optional[DFM_Config] = None
    
    def __new__(cls) -> 'DFM_ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = DFM_Config()
    
    @property
    def config(self) -> DFM_Config:
        """Get current configuration"""
        return self._config
    
    def load_config(self, base_path: str) -> bool:
        """Load configuration from addon directory"""
        try:
            config_path = os.path.join(base_path, 'config.json')
            self._config = DFM_Config.load_from_file(config_path)
            
            if not self._config.validate():
                logger.warning("Invalid configuration detected, using defaults")
                self._config = DFM_Config()
                return False
            
            logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = DFM_Config()
            return False
    
    def save_config(self, base_path: str) -> bool:
        """Save current configuration"""
        try:
            config_path = os.path.join(base_path, 'config.json')
            return self._config.save_to_file(config_path)
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """Update configuration values"""
        try:
            for key, value in kwargs.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
                else:
                    logger.warning(f"Unknown configuration key: {key}")
            
            return self._config.validate()
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False


# Global configuration manager instance
config_manager = DFM_ConfigManager()
