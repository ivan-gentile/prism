#!/usr/bin/env python3
"""
Test script for PRISM Clinician Agent
Tests the clinician agent with a specific patient case
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prism_ad.agents.prism_agents import PRISMClinicianAgent
from prism_ad.config import Config

async def test_clinician_agent():
    """Test the clinician agent with the provided patient data"""
    
    print("=" * 80)
    print("TESTING PRISM CLINICIAN AGENT")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Patient data
    patient_story = """
    «Ho 68 anni e mi sento bene, non noto problemi di memoria particolari. Ho fatto i test e mi hanno detto che sono nei valori normali. Vorrei solo sapere se devo preoccuparmi per il futuro.»
    """
    
    doctor_anamnesis = """
    Donna di 68 anni, ApoE4 negativa. Funzioni cognitive nella norma; biomarcatori favorevoli; PET e risonanza nei limiti. Quadro compatibile con invecchiamento sano.
    """
    
    # Patient data table
    patient_data = {
        "age": 68,
        "gender": "F",
        "ethnicity": "Caucasica",
        "education_years": 16,
        "apoe4": "Negativo",
        "cdr": 0,
        "mmse": 27,
        "moca": None,
        "adas_cog": None,
        "adas13": None,
        "adcs_pacc": 0.3,
        "ravlt_trial1": 5.1,
        "faq": None,
        "csf_t_tau": 210,  # pg/ml
        "csf_p_tau181": 22,  # pg/ml
        "csf_p_tau217": None,
        "csf_ab42": 1210,  # pg/ml
        "csf_ab42_ab40_ratio": 0.182,
        "pet_pib_suvr": 1.30,
        "pet_av45_suvr": None,
        "mri_hippocampi_total": 4.6,  # ml
        "mri_entorhinal": None,
        "mri_temporal_med": None,
        "mri_total_brain": None,
        "mri_ventricles": None
    }
    
    print("PATIENT INFORMATION:")
    print("-" * 40)
    print(f"Patient Story: {patient_story.strip()}")
    print()
    print(f"Doctor Anamnesis: {doctor_anamnesis.strip()}")
    print()
    print("Clinical Data:")
    for key, value in patient_data.items():
        if value is not None:
            print(f"  {key}: {value}")
    print()
    
    try:
        # Initialize the clinician agent
        print("Initializing PRISM Clinician Agent...")
        clinician_agent = PRISMClinicianAgent()
        
        # Test the agent
        print("Testing clinician agent...")
        print("-" * 40)
        
        # Create a comprehensive patient context
        patient_context = {
            "patient_story": patient_story,
            "doctor_anamnesis": doctor_anamnesis,
            "clinical_data": patient_data,
            "request": "Racconto del paziente"
        }
        
        # Get the agent's response
        response = await clinician_agent.process_patient_case(patient_context)
        
        print("CLINICIAN AGENT RESPONSE:")
        print("=" * 50)
        print(response)
        print("=" * 50)
        
        # Test individual methods
        print("\nTesting individual agent methods...")
        print("-" * 40)
        
        # Test cognitive assessment
        print("1. Testing cognitive assessment...")
        cognitive_assessment = await clinician_agent.assess_cognitive_status(patient_data)
        print(f"Cognitive Assessment: {cognitive_assessment}")
        print()
        
        # Test biomarker analysis
        print("2. Testing biomarker analysis...")
        biomarker_analysis = await clinician_agent.analyze_biomarkers(patient_data)
        print(f"Biomarker Analysis: {biomarker_analysis}")
        print()
        
        # Test risk assessment
        print("3. Testing risk assessment...")
        risk_assessment = await clinician_agent.assess_risk_factors(patient_data)
        print(f"Risk Assessment: {risk_assessment}")
        print()
        
        # Test clinical recommendation
        print("4. Testing clinical recommendation...")
        recommendation = await clinician_agent.provide_clinical_recommendation(patient_context)
        print(f"Clinical Recommendation: {recommendation}")
        print()
        
        print("✅ CLINICIAN AGENT TEST COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"❌ ERROR during clinician agent test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Main test function"""
    print("Starting PRISM Clinician Agent Test...")
    print()
    
    success = await test_clinician_agent()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
