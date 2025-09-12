#!/usr/bin/env python
"""Test FastWeb JWT authentication and configuration"""
import os
import sys

# Force FastWeb to be enabled for this test
os.environ["FASTWEB_ENABLED"] = "true"

from prism_ad.config import (
    FASTWEB_ENABLED, FASTWEB_MODEL, FASTWEB_API_KEY,
    FASTWEB_BASE_URL, FASTWEB_TOKENS, PROVIDER_CONFIGS
)

def test_jwt_configuration():
    """Test JWT token configuration"""
    print("\n" + "="*60)
    print("🔐 FastWeb JWT Configuration Test")
    print("="*60)
    
    print(f"\n📋 Configuration:")
    print(f"  • FastWeb Enabled: {FASTWEB_ENABLED}")
    print(f"  • Base URL: {FASTWEB_BASE_URL}")
    print(f"  • Default Model: {FASTWEB_MODEL}")
    
    print(f"\n🔑 JWT Token Status:")
    print(f"  • Token for {FASTWEB_MODEL}: {'✅ Configured' if FASTWEB_API_KEY else '❌ Missing'}")
    
    if FASTWEB_API_KEY:
        # Show first/last 20 chars of token for verification
        token_preview = FASTWEB_API_KEY[:30] + "..." + FASTWEB_API_KEY[-20:]
        print(f"  • Token preview: {token_preview}")
    
    print(f"\n📦 Available Models with Tokens:")
    for model, token in FASTWEB_TOKENS.items():
        has_token = bool(token) and not token.startswith("your_")
        status = "✅" if has_token else "❌"
        print(f"  {status} {model}")
    
    print(f"\n🔧 Provider Configuration:")
    fastweb_config = PROVIDER_CONFIGS.get("fastweb", {})
    print(f"  • API Key in config: {'✅ Set' if fastweb_config.get('api_key') else '❌ Missing'}")
    print(f"  • Base URL in config: {fastweb_config.get('base_url', 'Not set')}")
    print(f"  • Model in config: {fastweb_config.get('model', 'Not set')}")
    
    return bool(FASTWEB_API_KEY)

def test_simple_api_call():
    """Test a simple API call to FastWeb"""
    if not FASTWEB_API_KEY:
        print("\n❌ Cannot test API call - no JWT token configured")
        return False
    
    print("\n🧪 Testing API Connection...")
    
    try:
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        import httpx
        
        # Create HTTP client with SSL verification disabled for FastWeb
        http_client = httpx.AsyncClient(verify=False)
        
        # Create a test client
        client = OpenAIChatCompletionClient(
            model=FASTWEB_MODEL,
            api_key=FASTWEB_API_KEY,
            base_url=FASTWEB_BASE_URL,
            temperature=0.2,
            model_info={
                "model": FASTWEB_MODEL,
                "family": "fastweb" if "miia" in FASTWEB_MODEL.lower() else ("llama" if "llama" in FASTWEB_MODEL.lower() else "unknown"),
                "vision": False,
                "function_calling": False,
                "json_output": False,
                "structured_output": False,  # Required in v0.4.7+
                "context_length": 4096,
                "max_tokens": 2048,
                "supports_function_calling": False,
                "supports_vision": False,
            },
            http_client=http_client
        )
        
        print(f"  ✅ Client created successfully")
        print(f"  • Model: {FASTWEB_MODEL}")
        print(f"  • URL: {FASTWEB_BASE_URL}")
        
        # Try a simple completion
        import asyncio
        
        async def test_completion():
            try:
                from autogen_agentchat.agents import AssistantAgent
                
                agent = AssistantAgent(
                    name="test_agent",
                    model_client=client,
                    system_message="You are a helpful assistant. Reply with a single sentence.",
                    max_tool_iterations=1
                )
                
                result = await agent.run(task="Say 'FastWeb connection successful!' if you can read this.")
                
                if result and result.messages:
                    response = result.messages[-1].content
                    print(f"\n  🤖 Response: {response[:200]}")
                    return True
                else:
                    print(f"\n  ⚠️ No response received")
                    return False
                    
            except Exception as e:
                print(f"\n  ❌ API call failed: {str(e)}")
                return False
            finally:
                await client.close()
        
        return asyncio.run(test_completion())
        
    except Exception as e:
        print(f"\n  ❌ Failed to create client: {str(e)}")
        return False

def main():
    """Main test runner"""
    print("\n🚀 FastWeb JWT Authentication Test")
    
    # Test configuration
    config_ok = test_jwt_configuration()
    
    if not config_ok:
        print("\n❌ JWT token not configured properly")
        print("\n💡 To fix this:")
        print("1. Ensure FASTWEB_ENABLED=true in your .env")
        print("2. The JWT tokens are already embedded in config.py")
        print("3. Check that FASTWEB_MODEL matches one of the available models")
        return 1
    
    # Test API connection
    print("\n" + "-"*60)
    api_ok = test_simple_api_call()
    
    if api_ok:
        print("\n✅ All tests passed! FastWeb JWT authentication is working.")
        return 0
    else:
        print("\n⚠️ JWT token is configured but API call failed.")
        print("   This might be due to network issues or expired tokens.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
