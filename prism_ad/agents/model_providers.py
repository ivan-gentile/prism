"""Model provider abstraction for supporting multiple LLM providers (OpenAI, FastWeb)"""
import os
from typing import Dict, Any, Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient
from prism_ad.config import (
    PROVIDER_CONFIGS, AGENT_MODEL_MAP, 
    FASTWEB_TOKENS, FASTWEB_MODEL,
    AGENT_FASTWEB_MODEL_OVERRIDE
)


class ModelProviderFactory:
    """Factory class to create model clients for different providers"""
    
    @staticmethod
    def create_client(provider_type: str, agent_name: Optional[str] = None, **override_kwargs):
        """
        Create a model client for the specified provider.
        
        Args:
            provider_type: Either "primary" (OpenAI) or "fastweb"
            agent_name: Optional agent name to determine specific model selection
            **override_kwargs: Optional parameters to override default config
            
        Returns:
            OpenAIChatCompletionClient configured for the provider
        """
        if provider_type not in PROVIDER_CONFIGS:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        config = PROVIDER_CONFIGS[provider_type].copy()
        
        # Handle FastWeb model-specific JWT tokens
        if provider_type == "fastweb":
            # Check if there's an agent-specific model override
            if agent_name and agent_name in AGENT_FASTWEB_MODEL_OVERRIDE:
                fastweb_model = AGENT_FASTWEB_MODEL_OVERRIDE[agent_name]
                config["model"] = fastweb_model
                # Get the JWT token for this specific model
                config["api_key"] = FASTWEB_TOKENS.get(fastweb_model)
                if not config["api_key"]:
                    print(f"⚠️ No JWT token found for FastWeb model: {fastweb_model}")
                    # Fall back to default model
                    config["model"] = FASTWEB_MODEL
                    config["api_key"] = FASTWEB_TOKENS.get(FASTWEB_MODEL)
            else:
                # Use the default FastWeb model and its token
                config["model"] = FASTWEB_MODEL
                config["api_key"] = FASTWEB_TOKENS.get(FASTWEB_MODEL)
            
            if config.get("api_key"):
                print(f"🔑 Using FastWeb model: {config['model']}")
        
        # Apply any overrides
        config.update(override_kwargs)
        
        # Validate required fields
        if not config.get("api_key"):
            raise ValueError(f"API key/JWT token not configured for provider: {provider_type}")
        
        # Create the client
        # Both OpenAI and FastWeb use OpenAI-compatible API format
        # For FastWeb, the JWT token is passed as the api_key
        
        # For non-OpenAI models, we need to provide model_info
        if provider_type == "fastweb":
            # FastWeb models need model_info to work with autogen
            # Determine model family based on model name
            model_name = config["model"]
            if "llama" in model_name.lower():
                family = "llama"
            elif "gemma" in model_name.lower():
                family = "gemma"
            elif "miia" in model_name.lower():
                family = "fastweb"
            else:
                family = "unknown"
            
            # Create model_info with all required fields for AutoGen v0.4.7+
            model_info = {
                "model": config["model"],
                "family": family,
                "vision": False,
                "function_calling": False,
                "json_output": False,
                "structured_output": False,  # Required in v0.4.7+
                "context_length": 4096,      # Default context length
                "max_tokens": 2048,          # Default max tokens
                "supports_function_calling": False,  # FastWeb doesn't support OpenAI-style functions
                "supports_vision": False,
            }
            
            # Create HTTP client with SSL verification disabled for FastWeb
            import httpx
            http_client = httpx.AsyncClient(verify=False)
            
            client = OpenAIChatCompletionClient(
                model=config["model"],
                api_key=config["api_key"],
                base_url=config.get("base_url"),
                temperature=config.get("temperature", 0.2),
                model_info=model_info,
                http_client=http_client
            )
        else:
            # Standard OpenAI models
            client = OpenAIChatCompletionClient(
                model=config["model"],
                api_key=config["api_key"],
                base_url=config.get("base_url"),
                temperature=config.get("temperature", 0.2)
            )
        
        return client
    
    @staticmethod
    def get_client_for_agent(agent_name: str, **override_kwargs):
        """
        Get the appropriate model client for a specific agent based on configuration.
        
        Args:
            agent_name: Name of the agent (e.g., "parser", "classifier")
            **override_kwargs: Optional parameters to override default config
            
        Returns:
            OpenAIChatCompletionClient configured for the agent's provider
        """
        # Determine provider based on agent mapping
        provider_type = AGENT_MODEL_MAP.get(agent_name, "primary")
        
        # Handle special cases where tool support is required
        if agent_name == "quant_model":
            # Force primary provider for agents that need tool/function calling
            # (FastWeb doesn't support OpenAI-style function calling)
            provider_type = "primary"
            print(f"ℹ️ Agent '{agent_name}' requires tool support, using primary provider")
        
        return ModelProviderFactory.create_client(provider_type, agent_name=agent_name, **override_kwargs)


class MultiProviderAgentSystem:
    """Helper class to manage agents with different model providers"""
    
    def __init__(self):
        self.clients = {}
        self.provider_info = {}
    
    def get_or_create_client(self, agent_name: str) -> OpenAIChatCompletionClient:
        """
        Get or create a model client for the specified agent.
        Uses caching to avoid creating duplicate clients.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Model client for the agent
        """
        if agent_name not in self.clients:
            provider_type = AGENT_MODEL_MAP.get(agent_name, "primary")
            self.clients[agent_name] = ModelProviderFactory.get_client_for_agent(agent_name)
            
            # Get actual model being used (may be overridden for FastWeb)
            if provider_type == "fastweb":
                actual_model = AGENT_FASTWEB_MODEL_OVERRIDE.get(agent_name, FASTWEB_MODEL)
            else:
                actual_model = PROVIDER_CONFIGS[provider_type]["model"]
            
            self.provider_info[agent_name] = {
                "provider": provider_type,
                "model": actual_model,
                "base_url": PROVIDER_CONFIGS[provider_type].get("base_url")
            }
            
            # Log provider assignment
            provider_label = "FastWeb" if provider_type == "fastweb" else "OpenAI"
            print(f"🔧 Agent '{agent_name}' using {provider_label} ({actual_model})")
        
        return self.clients[agent_name]
    
    def get_provider_summary(self) -> Dict[str, Any]:
        """Get a summary of which agents are using which providers"""
        summary = {
            "fastweb_enabled": os.getenv("FASTWEB_ENABLED", "false").lower() == "true",
            "agent_assignments": {}
        }
        
        for agent_name in AGENT_MODEL_MAP:
            provider_type = AGENT_MODEL_MAP[agent_name]
            
            # Get actual model for this agent
            if provider_type == "fastweb":
                model = AGENT_FASTWEB_MODEL_OVERRIDE.get(agent_name, FASTWEB_MODEL)
            else:
                model = PROVIDER_CONFIGS.get(provider_type, {}).get("model", "Unknown")
            
            summary["agent_assignments"][agent_name] = {
                "provider": "FastWeb" if provider_type == "fastweb" else "OpenAI",
                "model": model,
                "active": agent_name in self.clients
            }
        
        return summary
    
    async def close_all(self):
        """Close all model clients"""
        for agent_name, client in self.clients.items():
            if client:
                await client.close()
                print(f"🔒 Closed client for agent '{agent_name}'")
        self.clients.clear()
        self.provider_info.clear()
