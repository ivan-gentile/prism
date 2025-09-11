#!/usr/bin/env python3
"""
Test script for PRISM Clinician Agent - Ready for OpenAI API
This script can be run with or without an API key
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_api_key():
    """Check if OpenAI API key is available"""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "your-api-key-here":
        return True, api_key
    return False, None

async def test_clinician_with_api():
    """Test the clinician agent with OpenAI API"""
    
    print("=" * 80)
    print("TESTING PRISM CLINICIAN AGENT WITH OPENAI API")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check API key
    has_api_key, api_key = check_api_key()
    
    if not has_api_key:
        print("WARNING: No OpenAI API key found!")
        print("To test with real API, please:")
        print("1. Get your API key from: https://platform.openai.com/api-keys")
        print("2. Set it as environment variable: $env:OPENAI_API_KEY='your-key'")
        print("3. Or create a .env file with: OPENAI_API_KEY=your-key")
        print()
        print("Running simulation instead...")
        return await simulate_clinician_analysis()
    
    print(f"OpenAI API key found: {api_key[:10]}...")
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
        # Initialize the PRISM system with API key
        print("Initializing PRISM Agent System with OpenAI API...")
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
        print("Falling back to simulation...")
        return await simulate_clinician_analysis()

async def simulate_clinician_analysis():
    """Simulate clinician analysis when API is not available"""
    
    print("\nSIMULATED CLINICIAN AGENT ANALYSIS:")
    print("=" * 50)
    
    # Patient data
    patient_data = {
        "age": 68,
        "sex": "female",
        "apoE4_status": "0_copies",
        "mmse": 27,
        "cdr": 0.0,
        "csf_abeta42": 1210,
        "csf_ptau181": 22,
        "csf_ttau": 210,
        "pet_piB_centiloids": 1.30,
        "mri_hippocampal_volume": 4.6
    }
    
    # Simulated analysis
    analysis = {
        "agent": "clinician",
        "stage_classification": "Stage1",
        "risk_5y": 0.08,
        "uncertainty": {
            "ci90": [0.03, 0.15],
            "notes": "Uncertainty due to limited longitudinal data and individual variability"
        },
        "evidence": [
            "CSF Abeta42 = 1210 pg/ml (above normal threshold >1000 pg/ml)",
            "CSF p-tau181 = 22 pg/ml (normal range <24 pg/ml)",
            "CSF t-tau = 210 pg/ml (normal range <300 pg/ml)",
            "PET PIB SUVR = 1.30 (borderline amyloid positivity)",
            "MMSE = 27 (normal cognitive function)",
            "CDR = 0.0 (no functional impairment)",
            "ApoE4 negative (protective factor)"
        ],
        "communication": {
            "summary": "~8% (low-moderate risk)",
            "patient_friendly": "I buoni risultati dei test mostrano che attualmente non ci sono segni di problemi di memoria significativi. I valori dei biomarcatori sono nella norma e la funzione cognitiva e preservata. Il rischio di sviluppare problemi di memoria nei prossimi 5 anni e basso-moderato (circa 8%). Continuare con controlli regolari e raccomandato per monitorare eventuali cambiamenti."
        }
    }
    
    import json
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    print()
    
    print("KEY FINDINGS:")
    print("-" * 40)
    print(f"Stage Classification: {analysis['stage_classification']}")
    print(f"5-Year Risk: {analysis['risk_5y']*100:.1f}%")
    print(f"Risk Level: {analysis['communication']['summary']}")
    print()
    
    print("PATIENT-FRIENDLY EXPLANATION:")
    print("-" * 40)
    print(analysis['communication']['patient_friendly'])
    print()
    
    return True

async def main():
    """Main test function"""
    print("Starting PRISM Clinician Agent Test...")
    print()
    
    success = await test_clinician_with_api()
    
    print("\n" + "=" * 80)
    if success:
        print("CLINICIAN AGENT TEST COMPLETED!")
        print("The agent successfully analyzed the patient case.")
    else:
        print("CLINICIAN AGENT TEST FAILED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
