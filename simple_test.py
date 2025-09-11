#!/usr/bin/env python3
"""
Simple test to verify the PRISM-AD system integration
"""

def test_imports():
    """Test that all modules can be imported correctly"""
    print("🧪 Testing PRISM-AD System Integration")
    print("="*50)
    
    try:
        # Test agent prompts import
        print("📋 Testing agent prompts import...")
        from prism_ad.agents.agent_prompts import (
            RAG_AGENT_PROMPT,
            CLINICIAN_AGENT_PROMPT,
            COX_AGENT_PROMPT,
            CONSENSUS_AGENT_PROMPT,
            FINAL_RESPONSE_AGENT_PROMPT
        )
        print("✅ Agent prompts imported successfully")
        
        # Test agent system import
        print("🤖 Testing agent system import...")
        from prism_ad.agents.prism_agents import PRISMAgentSystem
        print("✅ Agent system imported successfully")
        
        # Test patient model import
        print("👤 Testing patient model import...")
        from prism_ad.data.patient_model import PatientData
        print("✅ Patient model imported successfully")
        
        # Test configuration import
        print("⚙️ Testing configuration import...")
        from prism_ad.config import OPENAI_API_KEY, MODEL_NAME
        print("✅ Configuration imported successfully")
        
        print("\n" + "="*50)
        print("🎉 ALL IMPORTS SUCCESSFUL!")
        print("="*50)
        
        # Display prompt summaries
        print("\n📝 AGENT PROMPTS SUMMARY:")
        print("-" * 30)
        print(f"RAG Agent: {len(RAG_AGENT_PROMPT)} characters")
        print(f"Clinician Agent: {len(CLINICIAN_AGENT_PROMPT)} characters")
        print(f"Cox Agent: {len(COX_AGENT_PROMPT)} characters")
        print(f"Consensus Agent: {len(CONSENSUS_AGENT_PROMPT)} characters")
        print(f"Final Response Agent: {len(FINAL_RESPONSE_AGENT_PROMPT)} characters")
        
        # Test system initialization
        print("\n🔧 Testing system initialization...")
        system = PRISMAgentSystem()
        print("✅ System initialized successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_patient_data_validation():
    """Test patient data validation"""
    print("\n👤 Testing patient data validation...")
    
    try:
        from prism_ad.data.patient_model import PatientData
        
        # Sample patient data
        sample_data = {
            "patient_id": "TEST_001",
            "age": 68.0,
            "sex": "F",
            "education_years": 16.0,
            "apoe4_copies": "1",
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
        
        # Create patient object
        patient = PatientData(**sample_data)
        print("✅ Patient data validated successfully")
        print(f"   Patient ID: {patient.patient_id}")
        print(f"   Age: {patient.age}, Sex: {patient.sex}")
        print(f"   MMSE: {patient.mmse_score}, CDR: {patient.cdr_sum}")
        print(f"   CSF Aβ42: {patient.csf_abeta42} pg/mL")
        print(f"   CSF p-tau181: {patient.csf_ptau181} pg/mL")
        
        return True
        
    except Exception as e:
        print(f"❌ Patient data validation error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting PRISM-AD Integration Test")
    print("="*60)
    
    # Run tests
    import_success = test_imports()
    validation_success = test_patient_data_validation()
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    print(f"Import Test: {'✅ PASSED' if import_success else '❌ FAILED'}")
    print(f"Validation Test: {'✅ PASSED' if validation_success else '❌ FAILED'}")
    
    if import_success and validation_success:
        print("\n🎉 ALL TESTS PASSED! System is ready for use.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    print("="*60)
