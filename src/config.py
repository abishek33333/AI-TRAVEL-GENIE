"""
Configuration Management Module

Handles environment variables, API keys, and application settings.
"""

import os
import random
from typing import Literal
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

# Set random seeds for reproducibility
SEED = 42
random.seed(SEED)


class Settings(BaseSettings):
    """Application configuration from environment variables"""
    
    # LLM Provider Settings
    model_provider: Literal["groq", "openai", "anthropic"] = "groq"
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # Data Source APIs
    serpapi_api_key: str = ""
    openweathermap_api_key: str = ""
    gplaces_api_key: str = ""
    tavily_api_key: str = ""
    exchangerate_api_key: str = ""
    
    # Application Settings
    log_level: str = "INFO"
    max_tool_calls: int = 10
    cache_ttl: int = 3600  # seconds
    
    # Server Settings
    host: str = "127.0.0.1"
    port: int = 8001
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()


def validate_api_keys():
    """Validate that required API keys are present"""
    settings = get_settings()
    
    required_keys = {
        "GROQ_API_KEY": settings.groq_api_key,
        "SERPAPI_API_KEY": settings.serpapi_api_key,
        "OPENWEATHERMAP_API_KEY": settings.openweathermap_api_key,
        "GPLACES_API_KEY": settings.gplaces_api_key,
    }
    
    missing_keys = [key for key, value in required_keys.items() if not value]
    
    if missing_keys:
        raise ValueError(
            f"Missing required API keys: {', '.join(missing_keys)}\n"
            "Please set them in your .env file"
        )
    
    print("✅ All required API keys validated")


if __name__ == "__main__":
    # Test configuration loading
    settings = get_settings()
    print(f"Model Provider: {settings.model_provider}")
    print(f"Max Tool Calls: {settings.max_tool_calls}")
    print(f"Log Level: {settings.log_level}")
    
    try:
        validate_api_keys()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")