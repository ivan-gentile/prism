"""Test script for the NEW PRISM-AD architecture with text parsing and parallel models"""
import asyncio
import json
from datetime import datetime

# Add parent directory to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prism_ad.agents.prism_agents import PRISMAgentSystem


# Sample clinical text descriptions for testing the parser
SAMPLE_CLINICAL_TEXTS = [
    """72-year-old female presenting with memory complaints for the past 18 months. 
    MMSE score: 24, MoCA: 22. Patient is an ApoE4 carrier (heterozygous). 
    Recent CSF analysis shows: Aβ42 520 pg/mL, p-tau 35 pg/mL, total tau 420 pg/mL.
    Amyloid PET scan positive with SUVR 1.42. Hippocampal volume reduced bilaterally.
    Patient has 16 years of education. No significant functional impairment yet.""",
    
    """68 yo male with progressive cognitive decline. ApoE4 homozygous (2 copies).
    Cognitive testing: MMSE 22, significant deficits in memory and executive function.
    CSF biomarkers abnormal: Abeta42 450, ptau 48, total tau 550 pg/mL.
    PET imaging shows high amyloid burden (SUVR 1.65). 
    MRI reveals bilateral hippocampal atrophy. CDR sum of boxes: 4.0.
    Patient reporting difficulty with daily activities.""",
    
    """Healthy 65-year-old woman, no memory complaints. Routine screening shows:
    MMSE 29/30, MoCA 28/30. ApoE4 negative (0 copies). 
    Normal CSF profile: Aβ42 850 pg/mL, p-tau 18 pg/mL.
    Amyloid PET negative (SUVR 1.08). Normal brain MRI.
    18 years of education, physically active, no functional impairment.""",
    
    """Patient age 75 with mild memory issues. Limited data available:
    MMSE score 26. ApoE4 status unknown. No CSF data available.
    Clinical impression suggests early cognitive changes.
    Family history positive for Alzheimer's disease."""
]


async def test_text_parsing(system: PRISMAgentSystem, clinical_text: str, description: str):
    """Test the new architecture with text parsing"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")
    print(f"Input text preview: {clinical_text[:150]}...")
    
    try:
        # Process the clinical text through the new pipeline
        report = None
        async for message in system.process_patient(clinical_text):
            if isinstance(message, dict) and 'final_report' in message:
                report = message['final_report']
        
        # Display results
        print("\n" + "🎯 "*20)
        print("ASSESSMENT RESULTS (NEW ARCHITECTURE)")
        print("="*60)
        print(f"Patient ID: {report.patient_id}")
        print(f"FDA Stage: {report.fda_stage}")
        print(f"Risk Level: {report.risk_level}")
        print(f"\nExecutive Summary:")
        print(report.executive_summary[:300])
        
        if report.key_findings:
            print(f"\nKey Findings:")
            for finding in report.key_findings[:3]:
                print(f"  • {finding}")
                
        if report.recommendations:
            print(f"\nRecommendations:")
            for rec in report.recommendations[:3]:
                print(f"  • {rec}")
        
        # Save report
        report_filename = f"report_new_{description.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
        print(f"\n💾 Report saved to: {report_filename}")
        
        return report
        
    except Exception as e:
        print(f"❌ Error processing text: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_structured_data_backward_compatibility(system: PRISMAgentSystem):
    """Test that structured data still works (backward compatibility)"""
    print("\n" + "🔄 "*20)
    print("TESTING BACKWARD COMPATIBILITY")
    print("🔄 "*20)
    
    structured_data = {
        "patient_id": "PT_STRUCTURED_001",
        "age": 70,
        "sex": "M",
        "education_years": 14,
        "apoe4_copies": "1",
        "csf_abeta42": 580,
        "csf_ptau181": 32,
        "csf_total_tau": 380,
        "hippocampus_volume_left": 3200,
        "hippocampus_volume_right": 3150,
        "amyloid_pet_suvr": 1.35,
        "mmse_score": 25,
        "moca_score": 23,
        "cdr_sum": 2.0,
        "memory_complaints": True,
        "functional_impairment": False
    }
    
    try:
        report = None
        async for message in system.process_patient(structured_data):
            if isinstance(message, dict) and 'final_report' in message:
                report = message['final_report']
        print("✅ Backward compatibility test PASSED")
        print(f"   FDA Stage: {report.fda_stage}")
        print(f"   Risk Level: {report.risk_level}")
        return report
    except Exception as e:
        print(f"❌ Backward compatibility test FAILED: {e}")
        return None


async def main():
    """Main test function for new architecture"""
    print("\n" + "🚀 "*20)
    print("PRISM-AD NEW ARCHITECTURE TEST")
    print("Testing: Parser → Validator → Parallel Models → Aggregator → Reporter")
    print("🚀 "*20)
    
    # Initialize the system
    system = PRISMAgentSystem()
    
    try:
        # Initialize agents
        await system.initialize_agents()
        
        print("\nSelect test mode:")
        print("1. Test text parsing - MCI case")
        print("2. Test text parsing - High risk case")
        print("3. Test text parsing - Healthy case")
        print("4. Test text parsing - Incomplete data")
        print("5. Test all text samples")
        print("6. Test backward compatibility")
        print("7. Run complete test suite")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == "1":
            await test_text_parsing(system, SAMPLE_CLINICAL_TEXTS[0], "MCI_case")
        elif choice == "2":
            await test_text_parsing(system, SAMPLE_CLINICAL_TEXTS[1], "High_risk_case")
        elif choice == "3":
            await test_text_parsing(system, SAMPLE_CLINICAL_TEXTS[2], "Healthy_case")
        elif choice == "4":
            await test_text_parsing(system, SAMPLE_CLINICAL_TEXTS[3], "Incomplete_data")
        elif choice == "5":
            # Test all text samples
            descriptions = ["MCI_case", "High_risk_case", "Healthy_case", "Incomplete_data"]
            for text, desc in zip(SAMPLE_CLINICAL_TEXTS, descriptions):
                await test_text_parsing(system, text, desc)
                await asyncio.sleep(1)
        elif choice == "6":
            await test_structured_data_backward_compatibility(system)
        else:
            # Run complete test suite
            print("\nRunning complete test suite...")
            
            # Test text parsing
            print("\n--- TESTING TEXT PARSING ---")
            await test_text_parsing(system, SAMPLE_CLINICAL_TEXTS[0], "MCI_case")
            
            # Test backward compatibility
            print("\n--- TESTING BACKWARD COMPATIBILITY ---")
            await test_structured_data_backward_compatibility(system)
            
            print("\n--- TESTING PARALLEL MODEL EXECUTION ---")
            await test_text_parsing(system, SAMPLE_CLINICAL_TEXTS[1], "Parallel_test")
        
        print("\n" + "✅ "*20)
        print("ALL TESTS COMPLETED")
        print("✅ "*20)
        
        # Display architecture summary
        print("\n📊 NEW ARCHITECTURE SUMMARY:")
        print("1. ✅ Parser: Converts text to structured data")
        print("2. ✅ Validator: Ensures data quality")
        print("3. ✅ Parallel Models:")
        print("   - Quantitative Model: Numerical risk scoring")
        print("   - FDA Classifier: Regulatory staging")
        print("   - RAG (placeholder): Knowledge augmentation")
        print("4. ✅ Aggregator: Combines model outputs")
        print("5. ✅ Reporter: Generates clinical report")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await system.close()
        print("\n🔒 System shutdown complete")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
