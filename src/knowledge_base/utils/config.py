"""
Configuration management for the knowledge base application.

This module handles loading and validating configuration from multiple sources:
1. Environment variables
2. Configuration files
3. Default values

Configuration is loaded in the following order (later sources override earlier ones):
1. Default values
2. Global configuration file
3. User configuration file
4. Environment variables
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import yaml
from dotenv import load_dotenv

from .logger import get_logger

logger = get_logger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    connection_string: str = "postgresql://postgres:postgres@localhost:5432/knowledge_base"
    max_connections: int = 5
    enable_caching: bool = True
    pool_size: int = 5
    overflow: int = 10

@dataclass
class AIConfig:
    """AI/ML configuration settings."""
    openai_api_key: Optional[str] = None
    local_model_path: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    use_local_models: bool = False
    cache_embeddings: bool = True

@dataclass
class StorageConfig:
    """File storage configuration settings."""
    base_path: Path = Path.home() / "knowledge_base"
    cache_path: Path = Path.home() / "knowledge_base" / "cache"
    file_path: Path = Path.home() / "knowledge_base" / "files"
    max_cache_size: int = 5_000_000_000  # 5GB
    max_file_size: int = 100_000_000     # 100MB

@dataclass
class Config:
    """Main configuration class."""
    database: DatabaseConfig = DatabaseConfig()
    ai: AIConfig = AIConfig()
    storage: StorageConfig = StorageConfig()
    debug: bool = False

class ConfigurationError(Exception):
    """Raised when there is an error in configuration."""
    pass

def load_config_file(file_path: Path) -> Dict[str, Any]:
    """Load configuration from a YAML or JSON file.
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        Dictionary of configuration values
        
    Raises:
        ConfigurationError: If file cannot be loaded
    """
    try:
        if not file_path.exists():
            return {}
            
        with open(file_path) as f:
            if file_path.suffix == '.yaml' or file_path.suffix == '.yml':
                return yaml.safe_load(f)
            else:
                return json.load(f)
    except Exception as e:
        raise ConfigurationError(f"Error loading config file {file_path}: {e}")

def load_env_vars() -> Dict[str, Any]:
    """Load configuration from environment variables.
    
    Returns:
        Dictionary of configuration values from environment
    """
    load_dotenv()
    
    config = {}
    
    # Database configuration
    if db_url := os.getenv('DB_CONN_STRING'):
        config.setdefault('database', {})['connection_string'] = db_url
    
    # AI configuration
    if api_key := os.getenv('OPENAI_API_KEY'):
        config.setdefault('ai', {})['openai_api_key'] = api_key
    
    if model_path := os.getenv('LOCAL_MODEL_PATH'):
        config.setdefault('ai', {})['local_model_path'] = model_path
    
    # Storage configuration
    if base_path := os.getenv('DSV_KB_PATH'):
        config.setdefault('storage', {})['base_path'] = Path(base_path)
    
    # Debug mode
    if debug := os.getenv('DEBUG'):
        config['debug'] = debug.lower() in ('true', '1', 'yes')
    
    return config

def create_paths(config: Config) -> None:
    """Create necessary directories from configuration.
    
    Args:
        config: Configuration object
        
    Raises:
        ConfigurationError: If directories cannot be created
    """
    try:
        config.storage.base_path.mkdir(parents=True, exist_ok=True)
        config.storage.cache_path.mkdir(parents=True, exist_ok=True)
        config.storage.file_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ConfigurationError(f"Error creating directories: {e}")

def validate_config(config: Config) -> None:
    """Validate configuration values.
    
    Args:
        config: Configuration object
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Check database configuration
    if not config.database.connection_string:
        raise ConfigurationError("Database connection string must be provided")
    
    # Check storage paths
    if not config.storage.base_path.is_absolute():
        raise ConfigurationError("Storage base path must be absolute")
    
    # Check AI configuration
    if not config.ai.use_local_models and not config.ai.openai_api_key:
        logger.warning("No OpenAI API key provided and local models not enabled")

def load_config() -> Config:
    """Load configuration from all sources.
    
    Returns:
        Configured Config object
        
    Raises:
        ConfigurationError: If configuration cannot be loaded or is invalid
    """
    try:
        # Start with default configuration
        config = Config()
        
        # Load configuration files
        global_config = load_config_file(Path("/etc/knowledge_base/config.yaml"))
        user_config = load_config_file(Path.home() / ".config" / "knowledge_base" / "config.yaml")
        local_config = load_config_file(Path("config.yaml"))
        
        # Load environment variables
        env_config = load_env_vars()
        
        # Update configuration in order
        configs = [global_config, user_config, local_config, env_config]
        for cfg in configs:
            if db_cfg := cfg.get('database'):
                config.database = DatabaseConfig(**{
                    **vars(config.database),
                    **db_cfg
                })
            
            if ai_cfg := cfg.get('ai'):
                config.ai = AIConfig(**{
                    **vars(config.ai),
                    **ai_cfg
                })
            
            if storage_cfg := cfg.get('storage'):
                # Convert string paths to Path objects
                if 'base_path' in storage_cfg:
                    storage_cfg['base_path'] = Path(storage_cfg['base_path'])
                if 'cache_path' in storage_cfg:
                    storage_cfg['cache_path'] = Path(storage_cfg['cache_path'])
                if 'file_path' in storage_cfg:
                    storage_cfg['file_path'] = Path(storage_cfg['file_path'])
                
                config.storage = StorageConfig(**{
                    **vars(config.storage),
                    **storage_cfg
                })
            
            if 'debug' in cfg:
                config.debug = cfg['debug']
        
        # Validate configuration
        validate_config(config)
        
        # Create necessary directories
        create_paths(config)
        
        return config
        
    except Exception as e:
        raise ConfigurationError(f"Error loading configuration: {e}")

# Singleton configuration instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Global Config object
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config