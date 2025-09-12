"""Quick demo of the new PRISM-AD architecture flow"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prism_ad.agents.prism_agents import PRISMAgentSystem


async def demo():
    """Run a quick demo of the new architecture"""
    print("\n" + "="*60)
    print("PRISM-AD NEW ARCHITECTURE DEMO")
    print("Flow: Prompt → Parser → Validator → [Parallel Models] → Aggregator → Reporter")
    print("="*60)
    
    # Sample clinical text
    clinical_text = """
    75-year-old male with memory complaints and cognitive decline over 2 years.
    MMSE score: 23/30, showing deficits in recall and orientation.
    Patient is ApoE4 positive (1 copy). 
    CSF analysis: Aβ42 480 pg/mL (low), p-tau 42 pg/mL (elevated).
    Amyloid PET positive with SUVR 1.48.
    Patient has difficulty managing finances but still independent in basic activities.
    """
    
    print("\n📝 INPUT TEXT:")
    print(clinical_text)
    
    # Initialize system
    system = PRISMAgentSystem()
    
    try:
        await system.initialize_agents()
        
        print("\n🚀 Processing through new pipeline...")
        print("-"*60)
        
        # Process the text
        report = await system.process_patient(clinical_text)
        
        # Display results
        print("\n" + "="*60)
        print("📊 FINAL RESULTS")
        print("="*60)
        print(f"FDA Stage: {report.fda_stage}")
        print(f"Risk Level: {report.risk_level}")
        print(f"Executive Summary: {report.executive_summary[:200]}...")
        print(f"\nKey Findings:")
        for finding in report.key_findings[:3]:
            print(f"  • {finding}")
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        await system.close()


if __name__ == "__main__":
    asyncio.run(demo())
