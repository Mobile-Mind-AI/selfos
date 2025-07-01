"""
AI Engine Configuration

Configuration settings for AI models, providers, and processing parameters.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AIProvider(Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class ModelSize(Enum):
    """Model size categories."""
    SMALL = "small"      # Fast, cheap, good for simple tasks
    MEDIUM = "medium"    # Balanced performance and cost
    LARGE = "large"      # High quality, more expensive


@dataclass
class ModelConfig:
    """Configuration for a specific AI model."""
    provider: AIProvider
    model_name: str
    max_tokens: int
    temperature: float
    timeout: int = 30
    cost_per_token: Optional[float] = None


class AIConfig:
    """Main configuration class for AI engine."""
    
    # Model configurations for different use cases
    MODELS = {
        "goal_decomposition": {
            AIProvider.OPENAI: ModelConfig(
                provider=AIProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                max_tokens=2000,
                temperature=0.7,
                timeout=45,  # Increased timeout for complex goal decomposition
                cost_per_token=0.0000015
            ),
            AIProvider.ANTHROPIC: ModelConfig(
                provider=AIProvider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.7,
                cost_per_token=0.000015
            ),
            AIProvider.LOCAL: ModelConfig(
                provider=AIProvider.LOCAL,
                model_name="mock-model",
                max_tokens=2000,
                temperature=0.7,
                cost_per_token=0.0
            )
        },
        "task_generation": {
            AIProvider.OPENAI: ModelConfig(
                provider=AIProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                max_tokens=1500,
                temperature=0.6,
                timeout=10,
                cost_per_token=0.0000015
            ),
            AIProvider.ANTHROPIC: ModelConfig(
                provider=AIProvider.ANTHROPIC,
                model_name="claude-3-haiku-20240307",
                max_tokens=1500,
                temperature=0.6,
                cost_per_token=0.00000025
            ),
            AIProvider.LOCAL: ModelConfig(
                provider=AIProvider.LOCAL,
                model_name="mock-model",
                max_tokens=1500,
                temperature=0.6,
                cost_per_token=0.0
            )
        },
        "conversation": {
            AIProvider.OPENAI: ModelConfig(
                provider=AIProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                max_tokens=1000,
                temperature=0.8,
                timeout=10,
                cost_per_token=0.0000015
            ),
            AIProvider.ANTHROPIC: ModelConfig(
                provider=AIProvider.ANTHROPIC,
                model_name="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.8,
                cost_per_token=0.00000025
            ),
            AIProvider.LOCAL: ModelConfig(
                provider=AIProvider.LOCAL,
                model_name="mock-model",
                max_tokens=1000,
                temperature=0.8,
                cost_per_token=0.0
            )
        }
    }
    
    def __init__(self):
        self.default_provider = self._get_default_provider()
        self.api_keys = self._load_api_keys()
        self.settings = self._load_settings()
    
    def _get_default_provider(self) -> AIProvider:
        """Get the default AI provider from environment."""
        provider_name = os.getenv("AI_PROVIDER", "openai").lower()
        try:
            return AIProvider(provider_name)
        except ValueError:
            return AIProvider.OPENAI
    
    def _load_api_keys(self) -> Dict[AIProvider, str]:
        """Load API keys from environment variables."""
        return {
            AIProvider.OPENAI: os.getenv("OPENAI_API_KEY", ""),
            AIProvider.ANTHROPIC: os.getenv("ANTHROPIC_API_KEY", ""),
            AIProvider.LOCAL: ""  # No key needed for local models
        }
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load additional settings from environment."""
        return {
            "enable_caching": os.getenv("AI_ENABLE_CACHING", "true").lower() == "true",
            "cache_ttl": int(os.getenv("AI_CACHE_TTL", "3600")),  # 1 hour
            "max_retries": int(os.getenv("AI_MAX_RETRIES", "3")),
            "rate_limit_requests": int(os.getenv("AI_RATE_LIMIT", "60")),  # per minute
            "enable_logging": os.getenv("AI_ENABLE_LOGGING", "true").lower() == "true",
            "log_level": os.getenv("AI_LOG_LEVEL", "INFO"),
            "fallback_provider": os.getenv("AI_FALLBACK_PROVIDER", "openai"),
            "enable_cost_tracking": os.getenv("AI_ENABLE_COST_TRACKING", "true").lower() == "true"
        }
    
    def get_model_config(self, use_case: str, provider: Optional[AIProvider] = None) -> ModelConfig:
        """Get model configuration for a specific use case."""
        if provider is None:
            provider = self.default_provider
        
        if use_case not in self.MODELS:
            raise ValueError(f"Unknown use case: {use_case}")
        
        if provider not in self.MODELS[use_case]:
            # Fallback to default provider
            provider = AIProvider.OPENAI
        
        return self.MODELS[use_case][provider]
    
    def get_api_key(self, provider: AIProvider) -> str:
        """Get API key for a specific provider."""
        key = self.api_keys.get(provider, "")
        if not key and provider != AIProvider.LOCAL:
            raise ValueError(f"No API key found for provider: {provider.value}")
        return key
    
    def is_provider_available(self, provider: AIProvider) -> bool:
        """Check if a provider is properly configured."""
        try:
            key = self.get_api_key(provider)
            return bool(key) or provider == AIProvider.LOCAL
        except ValueError:
            return False
    
    def get_available_providers(self) -> list[AIProvider]:
        """Get list of properly configured providers."""
        return [provider for provider in AIProvider if self.is_provider_available(provider)]
    
    def estimate_cost(self, use_case: str, token_count: int, provider: Optional[AIProvider] = None) -> float:
        """Estimate the cost for a specific request."""
        config = self.get_model_config(use_case, provider)
        if config.cost_per_token:
            return token_count * config.cost_per_token
        return 0.0
    
    @classmethod
    def create_development_config(cls) -> 'AIConfig':
        """Create a development configuration with sensible defaults."""
        config = cls()
        
        # Override with development-friendly settings
        config.settings.update({
            "enable_caching": True,
            "cache_ttl": 300,  # 5 minutes for development
            "max_retries": 2,
            "rate_limit_requests": 30,  # Lower limit for development
            "enable_logging": True,
            "log_level": "DEBUG",
            "fallback_provider": "local"  # Always fallback to mock for development
        })
        
        # Use local provider by default in development if AI_USE_MOCK is set
        if os.getenv("AI_USE_MOCK", "false").lower() == "true":
            config.default_provider = AIProvider.LOCAL
        
        return config
    
    @classmethod
    def create_production_config(cls) -> 'AIConfig':
        """Create a production configuration with optimized settings."""
        config = cls()
        
        # Override with production-optimized settings
        config.settings.update({
            "enable_caching": True,
            "cache_ttl": 3600,  # 1 hour
            "max_retries": 3,
            "rate_limit_requests": 100,
            "enable_logging": True,
            "log_level": "INFO"
        })
        
        return config