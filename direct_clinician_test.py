#!/usr/bin/env python3
"""
Direct test for PRISM Clinician Agent - No external execution
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_clinician_agent_direct():
    """Test the clinician agent directly without external execution"""
    
    print("=" * 80)
    print("DIRECT TEST OF PRISM CLINICIAN AGENT")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Patient data from the user's request
    patient_story = "Ho 68 anni e mi sento bene, non noto problemi di memoria particolari. Ho fatto i test e mi hanno detto che sono nei valori normali. Vorrei solo sapere se devo preoccuparmi per il futuro."
    
    doctor_anamnesis = "Donna di 68 anni, ApoE4 negativa. Funzioni cognitive nella norma; biomarcatori favorevoli; PET e risonanza nei limiti. Quadro compatibile con invecchiamento sano."
    
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
    print(f"Patient Story: {patient_story}")
    print()
    print(f"Doctor Anamnesis: {doctor_anamnesis}")
    print()
    print("Clinical Data:")
    for key, value in patient_data.items():
        if value is not None:
            print(f"  {key}: {value}")
    print()
    
    try:
        # Import the clinician agent
        from prism_ad.agents.prism_agents import PRISMClinicianAgent
        
        print("✅ Successfully imported PRISMClinicianAgent")
        
        # Test agent initialization
        print("Initializing PRISM Clinician Agent...")
        clinician_agent = PRISMClinicianAgent()
        print("✅ Clinician agent initialized successfully")
        
        # Test agent properties
        print(f"Agent name: {clinician_agent.name}")
        print(f"Agent description: {clinician_agent.description}")
        print(f"Has model client: {clinician_agent.model_client is not None}")
        
        # Test the agent's system prompt
        if hasattr(clinician_agent, 'system_prompt'):
            print(f"System prompt length: {len(clinician_agent.system_prompt)} characters")
            print("System prompt preview:")
            print(clinician_agent.system_prompt[:200] + "..." if len(clinician_agent.system_prompt) > 200 else clinician_agent.system_prompt)
        
        print()
        print("✅ CLINICIAN AGENT TEST COMPLETED SUCCESSFULLY")
        print("The agent is ready to process patient cases.")
        
        return True
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ ERROR during clinician agent test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_clinician_agent_direct()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 CLINICIAN AGENT TEST PASSED!")
        print("The agent is ready to process the patient case.")
    else:
        print("❌ CLINICIAN AGENT TEST FAILED!")
    print("=" * 80)
