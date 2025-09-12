"""Test script for FastWeb integration and benchmarking"""
import asyncio
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, List

from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.agents.model_providers import ModelProviderFactory, MultiProviderAgentSystem
from prism_ad.config import FASTWEB_ENABLED, AGENT_MODEL_MAP, PROVIDER_CONFIGS


async def test_provider_factory():
    """Test the provider factory functionality"""
    print("\n" + "="*60)
    print("TEST 1: Provider Factory")
    print("="*60)
    
    try:
        # Test creating OpenAI client
        print("\n🔧 Testing OpenAI provider...")
        openai_client = ModelProviderFactory.create_client("primary")
        print("✅ OpenAI client created successfully")
        
        # Test creating FastWeb client (if enabled)
        if FASTWEB_ENABLED and PROVIDER_CONFIGS["fastweb"].get("api_key"):
            print("\n🔧 Testing FastWeb provider...")
            fastweb_client = ModelProviderFactory.create_client("fastweb")
            print("✅ FastWeb client created successfully")
        else:
            print("\n⚠️ FastWeb not enabled or API key not configured")
        
        # Test agent-specific client creation
        print("\n🔧 Testing agent-specific clients...")
        for agent_name in ["parser", "classifier", "quant_model"]:
            client = ModelProviderFactory.get_client_for_agent(agent_name)
            provider = AGENT_MODEL_MAP.get(agent_name, "primary")
            print(f"  • {agent_name}: {provider} provider")
        
        print("\n✅ Provider factory test completed successfully")
        
    except Exception as e:
        print(f"\n❌ Provider factory test failed: {str(e)}")
        raise


async def test_single_agent_comparison():
    """Test a single agent with both providers for comparison"""
    print("\n" + "="*60)
    print("TEST 2: Single Agent Provider Comparison")
    print("="*60)
    
    if not FASTWEB_ENABLED:
        print("⚠️ FastWeb not enabled. Skipping comparison test.")
        return
    
    test_prompt = """Analyze the following patient data and identify key risk factors:
    
    Patient: 72-year-old male
    - MMSE score: 24/30
    - Family history: Mother had Alzheimer's
    - Recent memory complaints
    - Difficulty with complex tasks
    """
    
    results = {}
    
    # Test with OpenAI
    print("\n📊 Testing with OpenAI...")
    start_time = time.time()
    try:
        from autogen_agentchat.agents import AssistantAgent
        openai_client = ModelProviderFactory.create_client("primary")
        openai_agent = AssistantAgent(
            name="test_agent_openai",
            model_client=openai_client,
            system_message="You are a medical analyst specializing in Alzheimer's risk assessment.",
            max_tool_iterations=1
        )
        
        openai_result = await openai_agent.run(task=test_prompt)
        openai_time = time.time() - start_time
        
        results["openai"] = {
            "response": openai_result.messages[-1].content if openai_result.messages else "No response",
            "time": openai_time,
            "model": PROVIDER_CONFIGS["primary"]["model"]
        }
        print(f"✅ OpenAI completed in {openai_time:.2f}s")
        await openai_client.close()
    except Exception as e:
        print(f"❌ OpenAI test failed: {str(e)}")
        results["openai"] = {"error": str(e)}
    
    # Test with FastWeb
    print("\n📊 Testing with FastWeb...")
    start_time = time.time()
    try:
        from autogen_agentchat.agents import AssistantAgent
        fastweb_client = ModelProviderFactory.create_client("fastweb")
        fastweb_agent = AssistantAgent(
            name="test_agent_fastweb",
            model_client=fastweb_client,
            system_message="You are a medical analyst specializing in Alzheimer's risk assessment.",
            max_tool_iterations=1
        )
        
        fastweb_result = await fastweb_agent.run(task=test_prompt)
        fastweb_time = time.time() - start_time
        
        results["fastweb"] = {
            "response": fastweb_result.messages[-1].content if fastweb_result.messages else "No response",
            "time": fastweb_time,
            "model": PROVIDER_CONFIGS["fastweb"]["model"]
        }
        print(f"✅ FastWeb completed in {fastweb_time:.2f}s")
        await fastweb_client.close()
    except Exception as e:
        print(f"❌ FastWeb test failed: {str(e)}")
        results["fastweb"] = {"error": str(e)}
    
    # Compare results
    print("\n📈 Comparison Results:")
    print("-" * 40)
    for provider, data in results.items():
        if "error" not in data:
            print(f"\n{provider.upper()}:")
            print(f"  Model: {data['model']}")
            print(f"  Time: {data['time']:.2f}s")
            print(f"  Response preview: {data['response'][:200]}...")
    
    return results


async def test_full_pipeline_benchmark():
    """Run the full PRISM pipeline and benchmark performance"""
    print("\n" + "="*60)
    print("TEST 3: Full Pipeline Benchmark")
    print("="*60)
    
    # Sample clinical data
    clinical_text = """
    Patient ID: TEST001
    Date of Assessment: 2024-01-15
    
    Demographics:
    - Age: 68 years
    - Sex: Female
    - Education: 16 years
    
    Clinical History:
    - Family history of Alzheimer's disease (mother)
    - Mild memory complaints for 2 years
    - Difficulty with financial management
    
    Cognitive Assessment:
    - MMSE: 25/30
    - MoCA: 23/30
    - CDR: 0.5
    
    Biomarkers:
    - CSF Aβ42: 450 pg/mL (low)
    - CSF p-tau: 48 pg/mL (elevated)
    - CSF total tau: 520 pg/mL (elevated)
    
    Imaging:
    - Hippocampal volume: Mild atrophy bilaterally
    - Amyloid PET: Positive
    
    Genetic:
    - APOE genotype: ε3/ε4
    """
    
    print(f"\n🚀 Running full pipeline...")
    print(f"FastWeb Enabled: {FASTWEB_ENABLED}")
    
    # Initialize system
    system = PRISMAgentSystem()
    await system.initialize_agents()
    
    # Track timing for each agent
    agent_timings = {}
    
    try:
        # Run the full pipeline with timing
        overall_start = time.time()
        
        # Parse clinical text
        print("\n📋 Step 1: Parsing clinical text...")
        start = time.time()
        parsed_data = await system.parse_clinical_text(clinical_text)
        agent_timings["parser"] = time.time() - start
        print(f"  ✅ Completed in {agent_timings['parser']:.2f}s")
        
        # Validate data
        print("\n✔️ Step 2: Validating data...")
        start = time.time()
        validation_result = await system.validate_data(parsed_data)
        agent_timings["validator"] = time.time() - start
        print(f"  ✅ Completed in {agent_timings['validator']:.2f}s")
        
        # Run classification
        print("\n🏷️ Step 3: FDA Classification...")
        start = time.time()
        classification = await system.classify_fda_stage(parsed_data)
        agent_timings["classifier"] = time.time() - start
        print(f"  ✅ Completed in {agent_timings['classifier']:.2f}s")
        
        # Run quantitative model
        print("\n🔢 Step 4: Quantitative Risk Assessment...")
        start = time.time()
        quant_result = await system.run_quantitative_model(parsed_data)
        agent_timings["quant_model"] = time.time() - start
        print(f"  ✅ Completed in {agent_timings['quant_model']:.2f}s")
        
        # Calculate risk
        print("\n⚠️ Step 5: Risk Calculation...")
        start = time.time()
        risk_assessment = await system.calculate_risk(
            patient_data=parsed_data,
            classification=classification,
            quant_result=quant_result
        )
        agent_timings["risk_calculator"] = time.time() - start
        print(f"  ✅ Completed in {agent_timings['risk_calculator']:.2f}s")
        
        # Generate report
        print("\n📄 Step 6: Generating Report...")
        start = time.time()
        report = await system.generate_report(
            patient_data=parsed_data,
            validation=validation_result,
            classification=classification,
            risk_assessment=risk_assessment,
            quant_result=quant_result
        )
        agent_timings["reporter"] = time.time() - start
        print(f"  ✅ Completed in {agent_timings['reporter']:.2f}s")
        
        overall_time = time.time() - overall_start
        
        # Generate benchmark report
        benchmark_report = {
            "timestamp": datetime.now().isoformat(),
            "fastweb_enabled": FASTWEB_ENABLED,
            "agent_timings": agent_timings,
            "overall_time": overall_time,
            "agent_providers": {}
        }
        
        # Add provider information for each agent
        provider_summary = system.provider_system.get_provider_summary()
        for agent_name in agent_timings.keys():
            agent_info = provider_summary["agent_assignments"].get(agent_name, {})
            benchmark_report["agent_providers"][agent_name] = {
                "provider": agent_info.get("provider", "Unknown"),
                "model": agent_info.get("model", "Unknown"),
                "time": agent_timings[agent_name]
            }
        
        # Print benchmark summary
        print("\n" + "="*60)
        print("📊 BENCHMARK SUMMARY")
        print("="*60)
        print(f"\nOverall Pipeline Time: {overall_time:.2f}s")
        print(f"FastWeb Integration: {'ENABLED' if FASTWEB_ENABLED else 'DISABLED'}")
        
        print("\n🏃 Agent Performance:")
        print("-" * 40)
        for agent_name, timing in agent_timings.items():
            provider_info = benchmark_report["agent_providers"][agent_name]
            print(f"{agent_name:20} {timing:6.2f}s  ({provider_info['provider']}: {provider_info['model']})")
        
        # Save benchmark report
        report_filename = f"benchmark_fastweb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(benchmark_report, f, indent=2)
        print(f"\n💾 Benchmark report saved to: {report_filename}")
        
        # Save clinical report
        if report:
            report_filename = f"clinical_report_fastweb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(report.model_dump() if hasattr(report, 'model_dump') else report, f, indent=2, default=str)
            print(f"💾 Clinical report saved to: {report_filename}")
        
        return benchmark_report
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await system.close()


async def main():
    """Main test runner"""
    print("\n" + "🧪 FASTWEB INTEGRATION TEST SUITE " + "🧪")
    print("="*60)
    
    # Check configuration
    print("\n📋 Current Configuration:")
    print(f"  • FastWeb Enabled: {FASTWEB_ENABLED}")
    if FASTWEB_ENABLED:
        from prism_ad.config import FASTWEB_MODEL, FASTWEB_TOKENS
        jwt_configured = bool(FASTWEB_TOKENS.get(FASTWEB_MODEL))
        print(f"  • FastWeb JWT Token: {'✅ Configured' if jwt_configured else '❌ Missing'}")
        print(f"  • FastWeb Model: {FASTWEB_MODEL}")
        print(f"  • FastWeb URL: {PROVIDER_CONFIGS['fastweb'].get('base_url', 'Not configured')}")
        print(f"  • Available Models: {', '.join(FASTWEB_TOKENS.keys())}")
    print(f"  • OpenAI API Key: {'✅ Configured' if PROVIDER_CONFIGS['primary'].get('api_key') else '❌ Missing'}")
    print(f"  • OpenAI Model: {PROVIDER_CONFIGS['primary'].get('model', 'Not configured')}")
    
    # Print agent assignments
    print("\n🤖 Agent Provider Assignments:")
    for agent_name, provider in AGENT_MODEL_MAP.items():
        provider_label = "FastWeb" if provider == "fastweb" else "OpenAI"
        print(f"  • {agent_name:20} → {provider_label}")
    
    try:
        # Run tests
        await test_provider_factory()
        
        if FASTWEB_ENABLED:
            await test_single_agent_comparison()
        
        benchmark = await test_full_pipeline_benchmark()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        
        return benchmark
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Set environment variable for testing (can be overridden)
    if "FASTWEB_ENABLED" not in os.environ:
        print("\n⚠️ FASTWEB_ENABLED not set in environment.")
        response = input("Enable FastWeb integration for testing? (y/n): ").lower()
        os.environ["FASTWEB_ENABLED"] = "true" if response == 'y' else "false"
    
    asyncio.run(main())
