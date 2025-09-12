#!/usr/bin/env python3
"""
Test script for PRISM system with FastWeb Llama-70B model
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

if OPENAI_API_KEY == "your-api-key-here":
    print("WARNING: Please set your FastWeb API key in the OPENAI_API_KEY environment variable")
    print("You can set it by running: $env:OPENAI_API_KEY='your-actual-fastweb-key'")
    sys.exit(1)

print(f"Using model: {MODEL_NAME}")
print(f"Using base URL: {BASE_URL}")
print(f"API Key: {OPENAI_API_KEY[:10]}...")

from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.data.patient_model import PatientData, ApoE4Status

async def test_fastweb_llama():
    """Test the system with FastWeb Llama-3.3-70B model"""
    
    print("=" * 80)
    print("TESTING PRISM SYSTEM WITH FASTWEB LLAMA-3.3-70B")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Patient data
    patient_data = PatientData(
        patient_id="TEST_FASTWEB_LLAMA_001",
        age=68,
        sex="F",
        education_years=16,
        apoe4_copies=ApoE4Status.ZERO_COPIES,
        csf_abeta42=1210,
        csf_abeta40=6648,
        csf_ptau181=22,
        csf_total_tau=210,
        amyloid_pet_suvr=1.30,
        hippocampus_volume_left=2.3,
        hippocampus_volume_right=2.3,
        mmse_score=27,
        cdr_sum=0.0,
        adas_cog13=None,
        adcs_pacc_score=0.3
    )
    
    print("PATIENT DATA:")
    print("-" * 40)
    print(f"Age: {patient_data.age}")
    print(f"Sex: {patient_data.sex}")
    print(f"Education: {patient_data.education_years} years")
    print(f"ApoE4: {patient_data.apoe4_copies.value}")
    print(f"MMSE: {patient_data.mmse_score}")
    print(f"CDR: {patient_data.cdr_sum}")
    print(f"CSF Abeta42: {patient_data.csf_abeta42} pg/ml")
    print(f"CSF p-tau181: {patient_data.csf_ptau181} pg/ml")
    print(f"CSF t-tau: {patient_data.csf_total_tau} pg/ml")
    print(f"PET PIB SUVR: {patient_data.amyloid_pet_suvr}")
    print(f"Hippocampus Volume: {patient_data.hippocampus_volume_left + patient_data.hippocampus_volume_right} ml")
    print()
    
    try:
        # Initialize the PRISM system with FastWeb configuration
        print("Initializing PRISM Agent System with FastWeb Llama-3.3-70B...")
        prism_system = PRISMAgentSystem(
            model_name=MODEL_NAME,
            api_key=OPENAI_API_KEY,
            base_url=BASE_URL
        )
        await prism_system.initialize_agents()
        print("PRISM system initialized successfully")
        
        # Test the clinician FASTWEB agent
        print("\nTesting Clinician FASTWEB Agent with FastWeb Llama-3.3-70B...")
        print("-" * 40)
        
        # Run the clinician FASTWEB agent
        clinician_fastweb_result = await prism_system._run_clinician_fastweb_agent(patient_data)
        
        print("\nCLINICIAN FASTWEB AGENT RESULT (FASTWEB LLAMA-3.3-70B):")
        print("=" * 50)
        print(clinician_fastweb_result)
        print("=" * 50)
        
        # Clean up
        await prism_system.close()
        
        print("\nFASTWEB LLAMA-3.3-70B TEST COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        print(f"ERROR during FastWeb Llama-3.3-70B test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Starting PRISM FastWeb Llama-3.3-70B Test...")
    print()
    
    success = await test_fastweb_llama()
    
    print("\n" + "=" * 80)
    if success:
        print("FASTWEB LLAMA-3.3-70B TEST PASSED!")
    else:
        print("FASTWEB LLAMA-3.3-70B TEST FAILED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
