#!/usr/bin/env python3
"""
Test script for PRISM Clinician Agent using .env file for API key
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_clinician_with_env():
    """Test the clinician agent using API key from .env file"""
    
    print("=" * 80)
    print("TESTING PRISM CLINICIAN AGENT WITH OPENAI API FROM .ENV")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check API key from .env
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in .env file!")
        print("Please make sure your .env file contains:")
        print("OPENAI_API_KEY=your-actual-api-key-here")
        return False
    
    print(f"OpenAI API key loaded from .env: {api_key[:10]}...")
    print()
    
    # Patient data from the user's request
    from prism_ad.data.patient_model import PatientData, ApoE4Status
    
    patient_data = PatientData(
        patient_id="TEST_001",
        age=68,
        sex="F",
        education_years=16,
        apoe4_copies=ApoE4Status.ZERO_COPIES,  # Negativo
        csf_abeta42=1210,  # pg/ml
        csf_abeta40=6648,  # Calculated from ratio: 1210/0.182
        csf_ptau181=22,    # pg/ml
        csf_total_tau=210, # pg/ml
        amyloid_pet_suvr=1.30,  # PIB SUVR
        hippocampus_volume_left=2.3,  # ml (half of total 4.6)
        hippocampus_volume_right=2.3, # ml (half of total 4.6)
        mmse_score=27,
        cdr_sum=0.0,
        adas_cog13=None,  # n.d.
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
        # Initialize the PRISM system with API key from .env
        print("Initializing PRISM Agent System with OpenAI API from .env...")
        from prism_ad.agents.prism_agents import PRISMAgentSystem
        
        prism_system = PRISMAgentSystem(api_key=api_key)
        await prism_system.initialize_agents()
        print("PRISM system initialized successfully")
        
        # Test only the clinician agent
        print("\nTesting Clinician Agent with OpenAI API...")
        print("-" * 40)
        
        # Run only the clinician agent
        clinician_result = await prism_system._run_clinician_agent(patient_data)
        
        print("\nCLINICIAN AGENT RESULT:")
        print("=" * 50)
        print(clinician_result)
        print("=" * 50)
        
        # Clean up
        await prism_system.close()
        
        print("\nCLINICIAN AGENT TEST COMPLETED SUCCESSFULLY")
        return True
        
    except Exception as e:
        print(f"ERROR during clinician agent test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Starting PRISM Clinician Agent Test with .env API key...")
    print()
    
    success = await test_clinician_with_env()
    
    print("\n" + "=" * 80)
    if success:
        print("CLINICIAN AGENT TEST PASSED!")
        print("The agent successfully analyzed the patient case using OpenAI API.")
    else:
        print("CLINICIAN AGENT TEST FAILED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
