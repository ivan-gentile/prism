#!/usr/bin/env python3
"""
Test PRISM System with High-Risk Patient
Donna di 69 anni, portatrice di ApoE4 (1 allele). 
Liquor e PET compatibili con patologia amiloide/tau in fase preclinica.
"""

import asyncio
import sys
import os
from datetime import datetime
from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.data.patient_model import PatientData, ApoE4Status

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")

async def test_high_risk_patient():
    """Test the system with high-risk patient data"""
    print("=" * 80)
    print("TESTING PRISM SYSTEM WITH HIGH-RISK PATIENT")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # High-risk patient data
    patient_data = PatientData(
        patient_id="HIGH_RISK_001",
        age=69.0,
        sex="F",
        education_years=16.0,
        apoe4_copies=ApoE4Status.ONE_COPY,  # 1 allele ApoE4
        mmse_score=28.0,  # Cognitivi quasi normali
        cdr_sum=0.0,  # Quasi normali
        adas_cog13=8.0,  # Quasi normali
        csf_abeta42=450.0,  # Basso (patologico)
        csf_abeta40=8000.0,  # Normal range
        csf_ptau181=35.0,  # Alto (patologico)
        csf_total_tau=400.0,  # Alto (patologico)
        amyloid_pet_suvr=1.4,  # Alto (patologico)
        hippocampus_volume_left=2.8,  # Ridotto per l'età
        hippocampus_volume_right=2.9,  # Ridotto per l'età
        ventricular_volume=45.0  # Normale
    )
    
    print("HIGH-RISK PATIENT DATA:")
    print("-" * 40)
    print(f"Age: {patient_data.age}")
    print(f"Sex: {patient_data.sex}")
    print(f"Education: {patient_data.education_years} years")
    print(f"ApoE4: {patient_data.apoe4_copies.value} ({patient_data.apoe4_copies.name})")
    print(f"MMSE: {patient_data.mmse_score}")
    print(f"CDR: {patient_data.cdr_sum}")
    print(f"CSF Abeta42: {patient_data.csf_abeta42} pg/ml (LOW - pathological)")
    print(f"CSF p-tau181: {patient_data.csf_ptau181} pg/ml (HIGH - pathological)")
    print(f"CSF t-tau: {patient_data.csf_total_tau} pg/ml (HIGH - pathological)")
    print(f"PET PIB SUVR: {patient_data.amyloid_pet_suvr} (HIGH - pathological)")
    print(f"Hippocampus Volume: {(patient_data.hippocampus_volume_left + patient_data.hippocampus_volume_right) / 2:.1f} ml (REDUCED)")
    print()
    
    print("Initializing PRISM Agent System...")
    prism_system = PRISMAgentSystem(
        model_name=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        base_url=BASE_URL
    )
    await prism_system.initialize_agents()
    print("PRISM system initialized successfully")
    print()
    
    # Test all remaining agents
    agents_to_test = [
        ("clinician", "Clinician Agent (GPT-4o-mini)"),
        ("clinician_gpt4o", "Clinician Agent GPT4o (GPT-4o)"),
        ("cox", "Cox Agent (Statistical)")
    ]
    
    results = {}
    
    for agent_key, agent_name in agents_to_test:
        print(f"Testing {agent_name}...")
        print("-" * 50)
        
        try:
            if agent_key == "clinician":
                result = await prism_system._run_clinician_agent(patient_data)
            elif agent_key == "clinician_gpt4o":
                result = await prism_system._run_clinician_gpt4o_agent(patient_data)
            elif agent_key == "cox":
                result = await prism_system._run_cox_agent(patient_data)
            
            results[agent_key] = result
            print(f"{agent_name} completed successfully")
            
        except Exception as e:
            print(f"Error testing {agent_name}: {e}")
            results[agent_key] = f"Error: {e}"
        
        print()
    
    # Display results
    print("=" * 80)
    print("HIGH-RISK PATIENT ANALYSIS RESULTS")
    print("=" * 80)
    
    for agent_key, agent_name in agents_to_test:
        if agent_key in results:
            print(f"\n{agent_name.upper()} RESULT:")
            print("=" * 50)
            print(results[agent_key])
            print()
    
    await prism_system.close()
    print("HIGH-RISK PATIENT TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    print("Starting PRISM High-Risk Patient Test...")
    asyncio.run(test_high_risk_patient())
