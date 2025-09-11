"""Test script for the PRISM-AD multi-agent system"""
import asyncio
import json
from datetime import datetime

# Add parent directory to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.data.patient_model import ApoE4Status


# Sample patient data for testing
SAMPLE_PATIENTS = [
    {
        "patient_id": "PT001",
        "age": 72,
        "sex": "F",
        "education_years": 16,
        "apoe4_copies": "1",  # One copy - moderate genetic risk
        "csf_abeta42": 520,  # Low - indicates amyloid pathology
        "csf_ptau181": 35,   # Elevated - indicates tau pathology
        "csf_total_tau": 420, # Elevated - neurodegeneration
        "hippocampus_volume_left": 3100,
        "hippocampus_volume_right": 3050,
        "amyloid_pet_suvr": 1.42,  # Positive for amyloid
        "mmse_score": 24,     # Mild cognitive impairment
        "moca_score": 22,
        "cdr_sum": 2.5,
        "memory_complaints": True,
        "functional_impairment": False
    },
    {
        "patient_id": "PT002",
        "age": 68,
        "sex": "M",
        "education_years": 12,
        "apoe4_copies": "2",  # Two copies - high genetic risk
        "csf_abeta42": 450,  # Very low - significant amyloid
        "csf_ptau181": 48,   # High tau
        "csf_total_tau": 550,
        "hippocampus_volume_left": 2800,  # Significant atrophy
        "hippocampus_volume_right": 2750,
        "amyloid_pet_suvr": 1.65,
        "mmse_score": 22,
        "moca_score": 20,
        "cdr_sum": 4.0,
        "memory_complaints": True,
        "functional_impairment": True
    },
    {
        "patient_id": "PT003",
        "age": 65,
        "sex": "F",
        "education_years": 18,
        "apoe4_copies": "0",  # No copies - lower genetic risk
        "csf_abeta42": 850,  # Normal
        "csf_ptau181": 18,   # Normal
        "csf_total_tau": 200,
        "hippocampus_volume_left": 3600,
        "hippocampus_volume_right": 3550,
        "amyloid_pet_suvr": 1.08,  # Negative for amyloid
        "mmse_score": 29,     # Normal cognition
        "moca_score": 28,
        "cdr_sum": 0,
        "memory_complaints": False,
        "functional_impairment": False
    }
]


async def test_single_patient(system: PRISMAgentSystem, patient_data: dict):
    """Test the system with a single patient"""
    print(f"\n{'='*60}")
    print(f"Testing Patient: {patient_data['patient_id']}")
    print(f"Age: {patient_data['age']}, Sex: {patient_data['sex']}")
    print(f"ApoE4 copies: {patient_data['apoe4_copies']}")
    print(f"MMSE: {patient_data['mmse_score']}")
    print(f"{'='*60}")
    
    try:
        # Process patient through the pipeline
        report = await system.process_patient(patient_data)
        
        # Display key results
        print("\n" + "🎯 " + "="*56)
        print("ASSESSMENT RESULTS")
        print("="*60)
        print(f"Patient ID: {report.patient_id}")
        print(f"Assessment Date: {report.assessment_date}")
        print(f"FDA Stage: {report.fda_stage}")
        print(f"Risk Level: {report.risk_level}")
        print(f"\nExecutive Summary:")
        print(report.executive_summary)
        
        if report.key_findings:
            print(f"\nKey Findings:")
            for finding in report.key_findings[:3]:
                print(f"  • {finding}")
                
        if report.recommendations:
            print(f"\nRecommendations:")
            for rec in report.recommendations[:3]:
                print(f"  • {rec}")
                
        print(f"\nFollow-up: {report.follow_up_timeline}")
        
        # Save detailed report
        report_filename = f"report_{patient_data['patient_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {report_filename}")
        
        return report
        
    except Exception as e:
        print(f"❌ Error processing patient: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_comparison_mode(system: PRISMAgentSystem):
    """Test multiple patients to show different risk profiles"""
    print("\n" + "🔬 "*20)
    print("COMPARATIVE ASSESSMENT MODE")
    print("Testing 3 patients with different risk profiles")
    print("🔬 "*20)
    
    results = []
    for patient_data in SAMPLE_PATIENTS:
        report = await test_single_patient(system, patient_data)
        if report:
            results.append(report)
        await asyncio.sleep(1)  # Brief pause between patients
    
    # Summary comparison
    if results:
        print("\n" + "📊 "*20)
        print("COMPARATIVE SUMMARY")
        print("="*60)
        print(f"{'Patient':<10} {'Age':<5} {'ApoE4':<8} {'MMSE':<6} {'Risk Level':<12}")
        print("-"*60)
        for i, report in enumerate(results):
            patient = SAMPLE_PATIENTS[i]
            print(f"{report.patient_id:<10} {patient['age']:<5} "
                  f"{patient['apoe4_copies']:<8} {patient['mmse_score']:<6} "
                  f"{report.risk_level:<12}")
        print("="*60)


async def main():
    """Main test function"""
    print("\n" + "🚀 "*20)
    print("PRISM-AD SYSTEM TEST")
    print("Alzheimer's Disease Risk Assessment Platform")
    print("🚀 "*20)
    
    # Initialize the system
    system = PRISMAgentSystem()
    
    try:
        # Initialize agents
        await system.initialize_agents()
        
        # Choose test mode
        print("\nSelect test mode:")
        print("1. Test single patient (PT001 - MCI case)")
        print("2. Test all sample patients (comparison)")
        print("3. Quick validation test")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            # Test single patient
            await test_single_patient(system, SAMPLE_PATIENTS[0])
        elif choice == "2":
            # Test all patients
            await test_comparison_mode(system)
        else:
            # Quick test with first patient
            print("\nRunning quick validation test...")
            await test_single_patient(system, SAMPLE_PATIENTS[0])
        
        print("\n" + "✅ "*20)
        print("TEST COMPLETED SUCCESSFULLY")
        print("✅ "*20)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await system.close()
        print("\n🔒 System shutdown complete")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
