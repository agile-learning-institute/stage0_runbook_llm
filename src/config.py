"""
Configuration management module for stage0_runbook_llm.

This module provides a singleton Config class that manages application configuration
with support for configuration sources (environment variables, defaults).
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration manager for the application.
    
    The Config class provides centralized configuration management with a priority
    system for configuration sources:
    1. Environment variables
    2. Default values (defined in class)
    
    Configuration values are automatically typed based on their category:
    - Strings: Plain text values
    - Integers: Numeric values
    - Booleans: True/false flags
    
    Secret values are masked in the config_items tracking list to prevent
    accidental exposure in logs or API responses.
    
    Attributes:
        config_items (list): List of dictionaries tracking each config value's
            source and value (secrets are masked).
    
    Example:
        >>> config = Config()
        >>> print(config.REPO_ROOT)
        /workspace/repo
    """

    def __init__(self):
        """
        Initialize the Config instance.
        
        Reads configuration from environment variables or uses defaults,
        and configures logging based on LOG_LEVEL.
        """
        self.config_items = []
        
        # Declare instance variables to support IDE code assist
        self.REPO_ROOT = ''
        self.CONTEXT_ROOT = ''
        self.LOG_LEVEL = ''
        self.TRACKING_BREADCRUMB = ''
        self.LLM_PROVIDER = ''
        self.LLM_MODEL = ''
        self.LLM_BASE_URL = ''
        self.LLM_API_KEY = ''
        self.LLM_TEMPERATURE = 0.0
        self.LLM_MAX_TOKENS = 0

        # Default Values grouped by value type            
        self.config_strings = {
            "REPO_ROOT": "/workspace/repo",
            "CONTEXT_ROOT": "/workspace/context",
            "LOG_LEVEL": "INFO",
            "TRACKING_BREADCRUMB": "",
            "LLM_PROVIDER": "null",  # null, ollama, openai, azure
            "LLM_MODEL": "codellama",
            "LLM_BASE_URL": "http://localhost:11434",
        }
        
        self.config_ints = {
            "LLM_TEMPERATURE": "7",  # Stored as int (70 = 0.7), converted to float in accessor
            "LLM_MAX_TOKENS": "8192",
        }

        self.config_string_secrets = {  
            "LLM_API_KEY": ""
        }
        
        # Initialize configuration
        self.initialize()
        self.configure_logging()

    def initialize(self):
        """
        Initialize or re-initialize all configuration values.
        
        This method loads configuration values from environment variables
        or defaults and sets them as instance attributes.
        It also resets the config_items list.
        
        The method processes configuration in the following order:
        1. String configurations
        2. Integer configurations (converted to int)
        3. String secret configurations
        
        Each configuration value is tracked in config_items with its source
        (environment, or default) and value (secrets are masked).
        """
        self.config_items = []

        # Initialize Config Strings
        for key, default in self.config_strings.items():
            value = self._get_config_value(key, default, False)
            setattr(self, key, value)
            
        # Initialize Config Integers (note: LLM_TEMPERATURE is stored as int, used as float)
        for key, default in self.config_ints.items():
            value = int(self._get_config_value(key, default, False))
            setattr(self, key, value)
            
        # Initialize String Secrets
        for key, default in self.config_string_secrets.items():
            value = self._get_config_value(key, default, True)
            setattr(self, key, value)
            
        return

    def configure_logging(self):
        """
        Configure Python logging based on the LOG_LEVEL configuration.
        
        This method is called once during Config singleton initialization to set up
        Python logging with the configured level and format. It uses force=True to
        ensure logging is properly configured even if handlers already exist.
        
        The logging format includes timestamp, level, logger name, and message.
        """
        # Convert LOG_LEVEL string to logging constant
        if isinstance(self.LOG_LEVEL, str):
            logging_level = getattr(logging, self.LOG_LEVEL, logging.INFO)
            self.LOG_LEVEL = logging_level  # Store as integer
        elif isinstance(self.LOG_LEVEL, int):
            logging_level = self.LOG_LEVEL
        else:
            logging_level = logging.INFO
            self.LOG_LEVEL = logging_level
        
        # Configure logging with force=True to reconfigure even if handlers exist
        if sys.version_info >= (3, 8):
            logging.basicConfig(
                level=logging_level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                force=True
            )
        else:
            # For Python < 3.8, reset handlers manually first
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            logging.basicConfig(
                level=logging_level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

        # Ensure root logger level is set (child loggers inherit this)
        logging.root.setLevel(logging_level)

        # Log configuration initialization
        logger.info(f"Configuration Initialized: {self.config_items}")
        
        return
            
    def _get_config_value(self, name, default_value, is_secret):
        """
        Retrieve a configuration value using the priority system.
        
        Configuration sources are checked in this order:
        1. Environment variable: {name}
        2. Default value: {default_value}
        
        Args:
            name (str): The name of the configuration key.
            default_value (str): The default value to use if not found in env.
            is_secret (bool): If True, the value will be masked as "secret" in
                config_items tracking.
        
        Returns:
            str: The configuration value as a string (may need type conversion
                by the caller).
        
        Note:
            The source and value (masked if secret) are recorded in config_items
            for tracking and debugging purposes.
        """
        value = default_value
        from_source = "default"

        # Check for environment variable
        if os.getenv(name):
            value = os.getenv(name)
            from_source = "environment"

        # Record the source of the config value
        self.config_items.append({
            "name": name,
            "value": "secret" if is_secret else value,
            "from": from_source
        })
        return value
    
    def get_llm_temperature(self) -> float:
        """Get LLM temperature as float (stored as int * 10, e.g., 7 = 0.7)."""
        return self.LLM_TEMPERATURE / 10.0
    
    def get_default(self, name: str):
        """
        Get the default value for a configuration key.
        
        Args:
            name: The name of the configuration key
            
        Returns:
            The default value for the key, or None if not found
        """
        # Check config_ints
        if name in self.config_ints:
            return int(self.config_ints[name])
        # Check config_strings
        if name in self.config_strings:
            return self.config_strings[name]
        # Check config_string_secrets
        if name in self.config_string_secrets:
            return self.config_string_secrets[name]
        return None

