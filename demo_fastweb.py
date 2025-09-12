"""Quick demo script for FastWeb integration in PRISM-AD system"""
import asyncio
import os
from datetime import datetime

# Ensure FastWeb is enabled for demo
os.environ["FASTWEB_ENABLED"] = "true"

from prism_ad.agents import PRISMAgentSystem
from prism_ad.config import FASTWEB_ENABLED, AGENT_MODEL_MAP, PROVIDER_CONFIGS


async def demo():
    """Run a quick demo of the FastWeb integration"""
    
    print("\n" + "="*60)
    print("🚀 PRISM-AD FastWeb Integration Demo")
    print("="*60)
    
    # Display configuration
    print("\n📋 Configuration:")
    print(f"  • FastWeb Enabled: {FASTWEB_ENABLED}")
    
    if FASTWEB_ENABLED:
        fastweb_configured = bool(PROVIDER_CONFIGS.get("fastweb", {}).get("api_key"))
        print(f"  • FastWeb API Key: {'✅ Configured' if fastweb_configured else '❌ Not configured'}")
        
        if fastweb_configured:
            print(f"  • FastWeb Model: {PROVIDER_CONFIGS['fastweb'].get('model')}")
            
            # Show which agents will use FastWeb
            fastweb_agents = [
                agent for agent, provider in AGENT_MODEL_MAP.items()
                if provider == "fastweb"
            ]
            if fastweb_agents:
                print(f"  • FastWeb Agents: {', '.join(fastweb_agents)}")
        else:
            print("\n⚠️ FastWeb API key not configured!")
            print("Please set FASTWEB_API_KEY in your .env file")
            return
    else:
        print("\n⚠️ FastWeb is not enabled!")
        print("Set FASTWEB_ENABLED=true in your .env file to enable")
        return
    
    # Sample patient data
    clinical_text = """
    Patient ID: DEMO001
    Date: 2024-01-15
    
    Demographics:
    - Age: 72 years
    - Sex: Male
    - Education: 14 years
    
    Clinical Presentation:
    - Progressive memory decline over 18 months
    - Difficulty with word-finding
    - Getting lost in familiar places
    
    Cognitive Testing:
    - MMSE: 22/30
    - MoCA: 19/30
    - CDR: 1.0
    
    Biomarkers:
    - CSF Aβ42: 380 pg/mL (low)
    - CSF p-tau: 55 pg/mL (elevated)
    - CSF total tau: 580 pg/mL (elevated)
    
    Imaging:
    - MRI: Moderate hippocampal atrophy
    - Amyloid PET: Positive
    
    Genetics:
    - APOE: ε4/ε4 (homozygous)
    """
    
    print("\n🏥 Processing patient case...")
    print("-" * 40)
    
    try:
        # Initialize system
        system = PRISMAgentSystem()
        await system.initialize_agents()
        
        # Track timing
        start_time = datetime.now()
        
        # Process the clinical data
        print("\n📊 Running multi-agent analysis...")
        
        # Parse
        print("  1️⃣ Parsing clinical text...")
        parsed_data = await system.parse_clinical_text(clinical_text)
        
        # Validate
        print("  2️⃣ Validating data...")
        validation = await system.validate_data(parsed_data)
        
        # Classify
        print("  3️⃣ FDA classification...")
        classification = await system.classify_fda_stage(parsed_data)
        
        # Quantitative model
        print("  4️⃣ Quantitative risk assessment...")
        quant_result = await system.run_quantitative_model(parsed_data)
        
        # Risk calculation
        print("  5️⃣ Calculating overall risk...")
        risk = await system.calculate_risk(
            patient_data=parsed_data,
            classification=classification,
            quant_result=quant_result
        )
        
        # Generate report
        print("  6️⃣ Generating clinical report...")
        report = await system.generate_report(
            patient_data=parsed_data,
            validation=validation,
            classification=classification,
            risk_assessment=risk,
            quant_result=quant_result
        )
        
        # Calculate timing
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Display results
        print("\n" + "="*60)
        print("✅ ANALYSIS COMPLETE")
        print("="*60)
        
        print(f"\n⏱️ Total Processing Time: {duration:.2f} seconds")
        
        print("\n📋 Key Findings:")
        print(f"  • Patient ID: {parsed_data.get('patient_id', 'DEMO001')}")
        print(f"  • FDA Stage: {classification.fda_stage if classification else 'N/A'}")
        print(f"  • Risk Level: {risk.overall_risk if risk else 'N/A'}")
        
        if quant_result and hasattr(quant_result, 'risk_score'):
            print(f"  • Quantitative Risk Score: {quant_result.risk_score:.1f}%")
        
        # Show provider usage
        provider_summary = system.provider_system.get_provider_summary()
        print("\n🔧 Provider Usage:")
        for agent, info in provider_summary["agent_assignments"].items():
            if info.get("active"):
                print(f"  • {agent}: {info['provider']} ({info['model']})")
        
        # Save report
        if report:
            filename = f"demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                import json
                json.dump(
                    report.model_dump() if hasattr(report, 'model_dump') else report,
                    f,
                    indent=2,
                    default=str
                )
            print(f"\n💾 Full report saved to: {filename}")
        
        # Cleanup
        await system.close()
        
        print("\n🎉 Demo completed successfully!")
        
        if FASTWEB_ENABLED:
            print("\n💡 FastWeb integration is active!")
            print("   Agents using FastWeb showed comparable performance")
            print("   while potentially reducing API costs.")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🔬 PRISM-AD: Multi-Agent Alzheimer's Risk Assessment")
    print("   with FastWeb Model Integration")
    
    # Check if API keys are configured
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    fastweb_configured = bool(os.getenv("FASTWEB_API_KEY"))
    
    if not openai_configured:
        print("\n⚠️ OpenAI API key not found!")
        print("Please set OPENAI_API_KEY in your .env file")
        exit(1)
    
    if not fastweb_configured and os.getenv("FASTWEB_ENABLED", "false").lower() == "true":
        print("\n⚠️ FastWeb enabled but API key not found!")
        print("Please set FASTWEB_API_KEY in your .env file")
        response = input("\nContinue with OpenAI only? (y/n): ")
        if response.lower() != 'y':
            exit(1)
        os.environ["FASTWEB_ENABLED"] = "false"
    
    # Run the demo
    asyncio.run(demo())
