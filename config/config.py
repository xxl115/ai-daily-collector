"""Configuration management for the application."""
from __future__ import annotations

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration."""
    provider: str = "local"  # "local" or "d1"
    
    # Cloudflare D1 settings
    account_id: Optional[str] = None
    database_id: Optional[str] = None
    api_token: Optional[str] = None
    
    # Local database settings
    connection_string: Optional[str] = None


@dataclass
class AppConfig:
    """Application configuration."""
    # Environment
    environment: str = "development"  # "development", "staging", "production"
    
    # Database
    database: DatabaseConfig = None  # type: ignore
    
    # Ingestion settings
    max_articles_per_source: int = 50
    ingestion_timeout: int = 300  # seconds
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()


def load_config_from_env() -> AppConfig:
    """Load configuration from environment variables.
    
    Environment Variables:
        ENVIRONMENT: Application environment (development/staging/production)
        
        # Database
        DATABASE_PROVIDER: "local" or "d1"
        
        # Cloudflare D1 (when provider="d1")
        CF_ACCOUNT_ID: Cloudflare account ID
        CF_D1_DATABASE_ID: D1 database ID
        CF_API_TOKEN: Cloudflare API token
        
        # Local DB (when provider="local")
        DATABASE_URL: Local database connection string
        
        # Ingestion
        MAX_ARTICLES_PER_SOURCE: Max articles per source (default: 50)
        INGESTION_TIMEOUT: Timeout in seconds (default: 300)
        
        # Logging
        LOG_LEVEL: Logging level (default: INFO)
        LOG_FORMAT: Log format - json or text (default: json)
    
    Returns:
        AppConfig instance
    """
    config = AppConfig()
    
    # Environment
    config.environment = os.getenv("ENVIRONMENT", "development")
    
    # Database configuration
    config.database.provider = os.getenv("DATABASE_PROVIDER", "local")
    config.database.account_id = os.getenv("CF_ACCOUNT_ID")
    config.database.database_id = os.getenv("CF_D1_DATABASE_ID")
    config.database.api_token = os.getenv("CF_API_TOKEN")
    config.database.connection_string = os.getenv("DATABASE_URL")
    
    # Ingestion settings
    config.max_articles_per_source = int(
        os.getenv("MAX_ARTICLES_PER_SOURCE", "50")
    )
    config.ingestion_timeout = int(
        os.getenv("INGESTION_TIMEOUT", "300")
    )
    
    # Logging
    config.log_level = os.getenv("LOG_LEVEL", "INFO")
    config.log_format = os.getenv("LOG_FORMAT", "json")
    
    return config


def get_storage_adapter(config: Optional[AppConfig] = None):
    """Get appropriate storage adapter based on configuration.
    
    Args:
        config: Application configuration (loads from env if not provided)
        
    Returns:
        StorageAdapter instance (D1StorageAdapter or LocalDBAdapter)
    """
    if config is None:
        config = load_config_from_env()
    
    if config.database.provider == "d1":
        from ingestor.storage.d1_adapter import D1StorageAdapter
        
        # Validate required D1 config
        if not all([
            config.database.account_id,
            config.database.database_id,
            config.database.api_token
        ]):
            raise ValueError(
                "D1 provider requires CF_ACCOUNT_ID, CF_D1_DATABASE_ID, "
                "and CF_API_TOKEN environment variables"
            )
        
        return D1StorageAdapter(
            account_id=config.database.account_id,
            database_id=config.database.database_id,
            api_token=config.database.api_token
        )
    else:
        from ingestor.storage.db import LocalDBAdapter
        return LocalDBAdapter(connection_string=config.database.connection_string)
