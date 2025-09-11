"""Basic test to verify AutoGen works with the API key"""
import asyncio
import sys
sys.path.append('.')

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from prism_ad.config import OPENAI_API_KEY, MODEL_NAME


async def test_single_agent():
    """Test a single AutoGen agent with a simple query"""
    print("=" * 60)
    print("Testing AutoGen with GPT-4o-mini")
    print("=" * 60)
    
    try:
        # Create the model client
        model_client = OpenAIChatCompletionClient(
            model=MODEL_NAME,
            api_key=OPENAI_API_KEY,
            temperature=0.2
        )
        
        # Create a simple assistant agent
        agent = AssistantAgent(
            name="test_assistant",
            model_client=model_client,
            system_message="You are a helpful medical assistant specializing in Alzheimer's Disease risk assessment."
        )
        
        # Test with a simple medical query
        result = await agent.run(task="What are the main biomarkers for Alzheimer's Disease?")
        
        print("\nAgent Response:")
        print("-" * 40)
        # Print the last message (the actual response)
        if result.messages:
            last_message = result.messages[-1]
            if hasattr(last_message, 'content'):
                print(last_message.content)
        
        print("\n✅ AutoGen is working successfully!")
        
        # Close the model client
        await model_client.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check:")
        print("1. Your API key is valid")
        print("2. You have installed all required packages")
        print("3. You have internet connection")
        return False


async def test_multi_agent_conversation():
    """Test a simple multi-agent conversation"""
    print("\n" + "=" * 60)
    print("Testing Multi-Agent Conversation")
    print("=" * 60)
    
    try:
        # Create model client
        model_client = OpenAIChatCompletionClient(
            model=MODEL_NAME,
            api_key=OPENAI_API_KEY,
            temperature=0.2
        )
        
        # Create two agents with different personalities
        validator_agent = AssistantAgent(
            name="validator",
            model_client=model_client,
            system_message="You are a data validator. Check if the following patient data is valid: Age=75, ApoE4_copies=2, MMSE_score=22"
        )
        
        # Run the validator agent
        result = await validator_agent.run(task="Please validate the patient data and identify any concerns.")
        
        print("\nValidator Agent Response:")
        print("-" * 40)
        if result.messages:
            last_message = result.messages[-1]
            if hasattr(last_message, 'content'):
                print(last_message.content)
        
        # Create a second agent that uses the validator's output
        risk_agent = AssistantAgent(
            name="risk_assessor",
            model_client=model_client,
            system_message="You are a risk assessment specialist. Based on the validated data, provide a risk assessment."
        )
        
        # Pass the validator's output to the risk agent
        risk_result = await risk_agent.run(
            task=f"Based on this validation: {result.messages[-1].content if result.messages else ''}, assess the Alzheimer's risk level."
        )
        
        print("\nRisk Assessor Response:")
        print("-" * 40)
        if risk_result.messages:
            last_message = risk_result.messages[-1]
            if hasattr(last_message, 'content'):
                print(last_message.content)
        
        print("\n✅ Multi-agent conversation successful!")
        
        # Close the model client
        await model_client.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in multi-agent test: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n🚀 Starting AutoGen Tests\n")
    
    # Test 1: Single agent
    single_agent_success = await test_single_agent()
    
    if single_agent_success:
        # Test 2: Multi-agent conversation
        multi_agent_success = await test_multi_agent_conversation()
        
        if multi_agent_success:
            print("\n" + "=" * 60)
            print("🎉 All tests passed! AutoGen is ready for PRISM-AD development")
            print("=" * 60)
        else:
            print("\n⚠️ Single agent works but multi-agent needs debugging")
    else:
        print("\n⚠️ Basic setup needs to be fixed first")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
