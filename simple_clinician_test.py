#!/usr/bin/env python3
"""
Simple test for PRISM Clinician Agent
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_clinician():
    try:
        from prism_ad.agents.prism_agents import PRISMClinicianAgent
        
        print("Testing PRISM Clinician Agent...")
        
        # Patient data
        patient_data = {
            "age": 68,
            "gender": "F",
            "cdr": 0,
            "mmse": 27,
            "apoe4": "Negativo",
            "csf_ab42": 1210,
            "csf_t_tau": 210,
            "csf_p_tau181": 22,
            "pet_pib_suvr": 1.30
        }
        
        # Initialize agent
        agent = PRISMClinicianAgent()
        
        # Test basic functionality
        print("Agent initialized successfully!")
        
        # Test cognitive assessment
        cognitive = await agent.assess_cognitive_status(patient_data)
        print(f"Cognitive Assessment: {cognitive}")
        
        # Test biomarker analysis
        biomarkers = await agent.analyze_biomarkers(patient_data)
        print(f"Biomarker Analysis: {biomarkers}")
        
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_clinician())
