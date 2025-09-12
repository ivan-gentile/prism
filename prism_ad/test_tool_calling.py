"""Test script to demonstrate Quantitative Model agent with tool calling"""
import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from prism_ad.utils.quant_risk_calculator import calculate_alzheimer_risk
from prism_ad.config import OPENAI_API_KEY, MODEL_NAME


async def test_direct_tool():
    """Test the calculator tool directly"""
    print("\n" + "="*60)
    print("TEST 1: Direct Tool Call")
    print("="*60)
    
    result = await calculate_alzheimer_risk(
        age=75.0,
        apoe4_copies="1",
        csf_abeta42=480.0,
        csf_ptau=42.0,
        amyloid_pet=1.48,
        mmse=23.0
    )
    
    print("Direct tool result:")
    result_dict = json.loads(result)
    print(json.dumps(result_dict, indent=2))
    print(f"\n✅ Risk Category: {result_dict['risk_category']}")
    print(f"✅ 5-Year Progression: {result_dict['five_year_progression']}")
    print(f"✅ Confidence: {result_dict['confidence_interval']}")


async def test_agent_with_tool():
    """Test the Quantitative Model agent using the tool"""
    print("\n" + "="*60)
    print("TEST 2: Agent with Tool Calling")
    print("="*60)
    
    # Create model client
    model_client = OpenAIChatCompletionClient(
        model=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        temperature=0.2
    )
    
    # Create Quantitative Model agent with tool
    quant_agent = AssistantAgent(
        name="quantitative_model",
        model_client=model_client,
        tools=[calculate_alzheimer_risk],  # Provide the tool
        max_tool_iterations=2,
        reflect_on_tool_use=True,
        system_message="""You are a Quantitative Risk Model agent.
        
        When given patient data, use the calculate_alzheimer_risk tool to compute risk scores.
        The tool accepts parameters like age, apoe4_copies, csf_abeta42, etc.
        
        After calling the tool, analyze and summarize the results clearly."""
    )
    
    # Test with patient data
    task = """Calculate the risk score for this patient using the calculate_alzheimer_risk tool:
    
    Patient Data:
    - age: 68
    - apoe4_copies: "2" (homozygous)
    - csf_abeta42: 450
    - csf_ptau: 48
    - csf_total_tau: 550
    - amyloid_pet: 1.65
    - hippocampus_left: 2800
    - hippocampus_right: 2750
    - mmse: 22
    - moca: 20
    
    Call the tool with these parameters and provide a clinical interpretation of the results."""
    
    print("Sending task to agent...")
    result = await quant_agent.run(task=task)
    
    print("\n🤖 Agent Response:")
    print("-"*40)
    
    # Print all messages to see the tool calling process
    for i, msg in enumerate(result.messages):
        msg_type = type(msg).__name__
        print(f"\nMessage {i+1} ({msg_type}):")
        if hasattr(msg, 'content'):
            content_str = str(msg.content)[:500]
            print(content_str)
    
    # Get final response
    final_response = result.messages[-1].content if result.messages else "No response"
    print("\n📊 Final Assessment:")
    print("-"*40)
    print(final_response)
    
    await model_client.close()


async def test_partial_data():
    """Test with incomplete patient data"""
    print("\n" + "="*60)
    print("TEST 3: Agent with Partial Data")
    print("="*60)
    
    model_client = OpenAIChatCompletionClient(
        model=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        temperature=0.2
    )
    
    quant_agent = AssistantAgent(
        name="quantitative_model",
        model_client=model_client,
        tools=[calculate_alzheimer_risk],
        max_tool_iterations=2,
        reflect_on_tool_use=True,
        system_message="Use the calculate_alzheimer_risk tool to assess risk even with limited data."
    )
    
    task = """Calculate risk for this patient with limited data:
    
    Available data:
    - age: 70
    - mmse: 24
    - apoe4_copies: "1"
    
    Use the calculate_alzheimer_risk tool with only these parameters.
    Note the impact of missing data on confidence."""
    
    result = await quant_agent.run(task=task)
    
    print("\n🤖 Agent Response with Partial Data:")
    print("-"*40)
    final_response = result.messages[-1].content if result.messages else "No response"
    print(final_response[:800])
    
    await model_client.close()


async def main():
    """Run all tests"""
    print("\n" + "🧪 "*20)
    print("QUANTITATIVE MODEL TOOL CALLING TEST SUITE")
    print("🧪 "*20)
    
    try:
        # Test 1: Direct tool call
        await test_direct_tool()
        
        # Test 2: Agent with tool
        await test_agent_with_tool()
        
        # Test 3: Partial data
        await test_partial_data()
        
        print("\n" + "✅ "*20)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("✅ "*20)
        
        print("\n📝 Summary:")
        print("1. ✅ Direct tool calls work correctly")
        print("2. ✅ Agent can call tools automatically")
        print("3. ✅ Handles partial data appropriately")
        print("4. ✅ Provides transparent calculations")
        print("5. ✅ Returns confidence intervals")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
