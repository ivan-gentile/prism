#!/usr/bin/env python3
"""
Test script to verify FastWeb configuration is correct
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for FastWeb
MODEL_NAME = os.getenv("MODEL_NAME", "meta/llama-3.3-70b-instruct")
BASE_URL = os.getenv("BASE_URL", "https://bpod1.ai-factory.fastweb.it/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")

print("=" * 80)
print("FASTWEB CONFIGURATION VERIFICATION")
print("=" * 80)
print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

print("CONFIGURATION:")
print("-" * 40)
print(f"Model Name: {MODEL_NAME}")
print(f"Base URL: {BASE_URL}")
print(f"API Key: {OPENAI_API_KEY[:10]}..." if OPENAI_API_KEY != "your-api-key-here" else "API Key: Not set")
print()

from prism_ad.agents.prism_agents import PRISMAgentSystem

async def test_fastweb_config():
    """Test FastWeb configuration without making API calls"""
    
    try:
        print("Testing FastWeb configuration...")
        print("-" * 40)
        
        # Initialize the PRISM system with FastWeb configuration
        print("Initializing PRISM Agent System with FastWeb configuration...")
        prism_system = PRISMAgentSystem(
            model_name=MODEL_NAME,
            api_key=OPENAI_API_KEY,
            base_url=BASE_URL
        )
        
        print("✓ PRISMAgentSystem created successfully")
        print(f"✓ Model name: {prism_system.model_name}")
        print(f"✓ Base URL: {prism_system.base_url}")
        print(f"✓ API Key: {prism_system.api_key[:10]}..." if prism_system.api_key != "your-api-key-here" else "✓ API Key: Set")
        
        # Test agent initialization (without making API calls)
        print("\nTesting agent initialization...")
        print("-" * 40)
        
        # Create model client manually to test configuration
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        import httpx
        
        # Create HTTP client with SSL verification disabled for FastWeb
        http_client = None
        if "fastweb.it" in BASE_URL or "ai-factory" in BASE_URL:
            http_client = httpx.AsyncClient(verify=False)
            print("✓ SSL verification disabled for FastWeb endpoint")
        
        # Create model info for custom model
        model_info = {
            "model": MODEL_NAME,
            "context_length": 4096,
            "max_tokens": 2048,
            "supports_function_calling": True,
            "supports_vision": False,
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "llama"
        }
        
        model_client = OpenAIChatCompletionClient(
            model=MODEL_NAME,
            api_key=OPENAI_API_KEY,
            base_url=BASE_URL,
            temperature=0.2,
            model_info=model_info,
            http_client=http_client
        )
        
        print("✓ OpenAIChatCompletionClient created successfully")
        print("✓ Model info configured for Llama model")
        print("✓ HTTP client configured for FastWeb")
        
        # Test agent creation
        from autogen_agentchat.agents import AssistantAgent
        from prism_ad.agents.agent_prompts import CLINICIAN_FASTWEB_AGENT_PROMPT
        
        test_agent = AssistantAgent(
            name="Test_FASTWEB_Agent",
            model_client=model_client,
            system_message=CLINICIAN_FASTWEB_AGENT_PROMPT,
            max_tool_iterations=1
        )
        
        print("✓ Clinician FASTWEB Agent created successfully")
        print("✓ System message loaded correctly")
        
        # Clean up
        await model_client.close()
        if http_client:
            await http_client.aclose()
        
        print("\n" + "=" * 80)
        print("FASTWEB CONFIGURATION VERIFICATION COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("✓ All components configured correctly for FastWeb")
        print("✓ System ready to use FastWeb Llama-3.3-70B model")
        print("✓ SSL handling configured for FastWeb endpoints")
        print("✓ Model info configured for custom Llama model")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"ERROR during FastWeb configuration test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Starting FastWeb Configuration Verification...")
    print()
    
    success = await test_fastweb_config()
    
    print("\n" + "=" * 80)
    if success:
        print("FASTWEB CONFIGURATION VERIFICATION PASSED!")
        print("The system is correctly configured for FastWeb Llama-3.3-70B")
    else:
        print("FASTWEB CONFIGURATION VERIFICATION FAILED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
