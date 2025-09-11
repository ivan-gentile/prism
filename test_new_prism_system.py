#!/usr/bin/env python3
"""
Test script for the updated PRISM-AD system with new agent prompts
"""

import asyncio
import json
from prism_ad.agents.prism_agents import PRISMAgentSystem

# Sample patient data for testing
SAMPLE_PATIENT_DATA = {
    "patient_id": "TEST_001",
    "age": 68.0,
    "sex": "F",
    "education_years": 16.0,
    "apoe4_copies": "1",  # One copy of ApoE4
    "csf_abeta42": 480.0,
    "csf_abeta40": 8000.0,
    "csf_ptau181": 23.0,
    "csf_total_tau": 310.0,
    "hippocampus_volume_left": 3000.0,
    "hippocampus_volume_right": 3200.0,
    "amyloid_pet_suvr": 1.4,
    "mmse_score": 29.0,
    "moca_score": 26.0,
    "cdr_sum": 0.0,
    "adas_cog13": 9.0,
    "memory_complaints": True,
    "functional_impairment": False
}

async def test_prism_system():
    """Test the updated PRISM-AD system"""
    print("🧪 Testing Updated PRISM-AD System")
    print("="*50)
    
    # Initialize the system
    prism_system = PRISMAgentSystem()
    
    try:
        # Initialize agents
        await prism_system.initialize_agents()
        
        # Process patient data
        print(f"\n📋 Processing patient: {SAMPLE_PATIENT_DATA['patient_id']}")
        print(f"Age: {SAMPLE_PATIENT_DATA['age']}, Sex: {SAMPLE_PATIENT_DATA['sex']}")
        print(f"MMSE: {SAMPLE_PATIENT_DATA['mmse_score']}, CDR: {SAMPLE_PATIENT_DATA['cdr_sum']}")
        print(f"CSF Aβ42: {SAMPLE_PATIENT_DATA['csf_abeta42']} pg/mL")
        print(f"CSF p-tau181: {SAMPLE_PATIENT_DATA['csf_ptau181']} pg/mL")
        print(f"Amyloid PET SUVR: {SAMPLE_PATIENT_DATA['amyloid_pet_suvr']}")
        
        # Run the complete pipeline
        final_report = await prism_system.process_patient(SAMPLE_PATIENT_DATA)
        
        print("\n" + "="*60)
        print("📄 FINAL REPORT")
        print("="*60)
        print(final_report)
        
        # Display processing results for each agent
        print("\n" + "="*60)
        print("🔍 AGENT PROCESSING RESULTS")
        print("="*60)
        
        for agent_name in ["rag", "clinician", "cox", "consensus", "final_response"]:
            if agent_name in prism_system.processing_results:
                print(f"\n{agent_name.upper()} AGENT:")
                print("-" * 30)
                result = prism_system.processing_results[agent_name]
                print(result[:500] + "..." if len(result) > 500 else result)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await prism_system.close()

if __name__ == "__main__":
    asyncio.run(test_prism_system())
