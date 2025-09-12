"""Model provider abstraction for supporting multiple LLM providers (OpenAI, FastWeb)"""
import os
from typing import Dict, Any, Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient
from prism_ad.config import PROVIDER_CONFIGS, AGENT_MODEL_MAP


class ModelProviderFactory:
    """Factory class to create model clients for different providers"""
    
    @staticmethod
    def create_client(provider_type: str, **override_kwargs):
        """
        Create a model client for the specified provider.
        
        Args:
            provider_type: Either "primary" (OpenAI) or "fastweb"
            **override_kwargs: Optional parameters to override default config
            
        Returns:
            OpenAIChatCompletionClient configured for the provider
        """
        if provider_type not in PROVIDER_CONFIGS:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        config = PROVIDER_CONFIGS[provider_type].copy()
        
        # Apply any overrides
        config.update(override_kwargs)
        
        # Validate required fields
        if not config.get("api_key"):
            raise ValueError(f"API key not configured for provider: {provider_type}")
        
        # Create the client
        # Both OpenAI and FastWeb use OpenAI-compatible API format
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
            # (Assuming FastWeb might not support OpenAI-style function calling)
            provider_type = "primary"
            print(f"ℹ️ Agent '{agent_name}' requires tool support, using primary provider")
        
        return ModelProviderFactory.create_client(provider_type, **override_kwargs)


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
            self.provider_info[agent_name] = {
                "provider": provider_type,
                "model": PROVIDER_CONFIGS[provider_type]["model"],
                "base_url": PROVIDER_CONFIGS[provider_type].get("base_url")
            }
            
            # Log provider assignment
            provider_label = "FastWeb" if provider_type == "fastweb" else "OpenAI"
            model_name = PROVIDER_CONFIGS[provider_type]["model"]
            print(f"🔧 Agent '{agent_name}' using {provider_label} ({model_name})")
        
        return self.clients[agent_name]
    
    def get_provider_summary(self) -> Dict[str, Any]:
        """Get a summary of which agents are using which providers"""
        summary = {
            "fastweb_enabled": os.getenv("FASTWEB_ENABLED", "false").lower() == "true",
            "agent_assignments": {}
        }
        
        for agent_name in AGENT_MODEL_MAP:
            provider_type = AGENT_MODEL_MAP[agent_name]
            provider_config = PROVIDER_CONFIGS.get(provider_type, {})
            summary["agent_assignments"][agent_name] = {
                "provider": "FastWeb" if provider_type == "fastweb" else "OpenAI",
                "model": provider_config.get("model", "Unknown"),
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
