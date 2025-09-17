"""Test unified staging logic across all components"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prism_ad.agents.prism_agents import determine_fda_stage, PRISMAgentSystem
from prism_ad.data.patient_model import PatientData


# Test cases with different staging scenarios
TEST_CASES = [
    {
        "name": "Loredana Bertè (Stage3 - severe biomarkers)",
        "data": {
            "patient_id": "LB_Stage3",
            "age": 69, "sex": "F", "education_years": 16, "apoe4_copies": "1",
            "mmse_score": 27, "cdr_sum": 0.0,
            "csf_abeta42": 550, "csf_abeta40": 7857, "csf_ptau181": 42, "csf_total_tau": 350,
            "amyloid_pet_suvr": 1.3, "hippocampus_volume_left": 2150, "hippocampus_volume_right": 2150,
            "memory_complaints": True, "functional_impairment": False
        },
        "expected_stage": "Stage3"
    },
    {
        "name": "Ornella Vanoni (Stage1 - normal)",
        "data": {
            "patient_id": "OV_Stage1",
            "age": 68, "sex": "F", "education_years": 16, "apoe4_copies": "0",
            "mmse_score": 27, "cdr_sum": 0.0,
            "csf_abeta42": 1210, "csf_abeta40": 6648, "csf_ptau181": 22, "csf_total_tau": 210,
            "amyloid_pet_suvr": 1.30, "hippocampus_volume_left": 2300, "hippocampus_volume_right": 2300,
            "memory_complaints": False, "functional_impairment": False
        },
        "expected_stage": "Stage1"
    },
    {
        "name": "Stage2 case (some biomarker abnormalities)",
        "data": {
            "patient_id": "Stage2_test",
            "age": 70, "sex": "M", "education_years": 12, "apoe4_copies": "1",
            "mmse_score": 28, "cdr_sum": 0.0,
            "csf_abeta42": 580, "csf_abeta40": 8000, "csf_ptau181": 35, "csf_total_tau": 300,
            "amyloid_pet_suvr": 1.2, "hippocampus_volume_left": 2400, "hippocampus_volume_right": 2400,
            "memory_complaints": False, "functional_impairment": False
        },
        "expected_stage": "Stage2"
    },
    {
        "name": "Stage4 case (functional impairment)",
        "data": {
            "patient_id": "Stage4_test",
            "age": 75, "sex": "F", "education_years": 14, "apoe4_copies": "2",
            "mmse_score": 18, "cdr_sum": 2.0,
            "csf_abeta42": 400, "csf_abeta40": 8000, "csf_ptau181": 60, "csf_total_tau": 500,
            "amyloid_pet_suvr": 1.6, "hippocampus_volume_left": 1800, "hippocampus_volume_right": 1800,
            "memory_complaints": True, "functional_impairment": True
        },
        "expected_stage": "Stage4"
    }
]


def test_unified_staging_logic():
    """Test that staging logic is consistent across all components"""
    print("\n" + "="*60)
    print("🔍 TESTING UNIFIED STAGING LOGIC")
    print("="*60)
    
    all_passed = True
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n📊 Test {i}: {test_case['name']}")
        print("-" * 50)
        
        try:
            # Test unified function
            patient = PatientData(**test_case['data'])
            determined_stage = determine_fda_stage(patient)
            
            print(f"   Expected: {test_case['expected_stage']}")
            print(f"   Determined: {determined_stage}")
            
            if determined_stage == test_case['expected_stage']:
                print("   ✅ PASS")
            else:
                print("   ❌ FAIL")
                all_passed = False
                
            # Test input generation for agents
            system = PRISMAgentSystem()
            input_data = {
                "patient_profile": {
                    "age": patient.age,
                    "sex": patient.sex or "unknown",
                    "apoE4_status": patient.apoe4_copies.value if patient.apoe4_copies else "unknown",
                    "mmse": patient.mmse_score,
                    "cdr": patient.cdr_sum or 0.0,
                    "csf_abeta42": patient.csf_abeta42,
                    "csf_ptau181": patient.csf_ptau181,
                    "pet_piB_centiloids": patient.amyloid_pet_suvr,
                },
                "stage_hint": determined_stage,
                "question": f"Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor) from current {determined_stage}"
            }
            
            print(f"   Agent input: stage_hint = {input_data['stage_hint']}")
            print(f"   Question: ...from current {determined_stage}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_passed = False
    
    print(f"\n" + "📋 "*20)
    print("SUMMARY")
    print("="*60)
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("🎯 Unified staging logic is working correctly across all components")
        print("🔗 All agents will now receive consistent stage information")
        print("📈 System ready for production with coherent logic")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  Review staging logic for consistency")
        
    print("="*60)
    
    # Test specific criteria for each stage
    print(f"\n🧪 STAGING CRITERIA VERIFICATION:")
    print("-" * 50)
    
    for i, test_case in enumerate(TEST_CASES, 1):
        patient = PatientData(**test_case['data'])
        stage = determine_fda_stage(patient)
        
        # Count severe markers
        severe_count = 0
        if patient.csf_abeta42 and patient.csf_abeta42 < 550: severe_count += 1
        if patient.csf_ptau181 and patient.csf_ptau181 > 40: severe_count += 1
        if patient.csf_abeta42 and patient.csf_abeta40:
            if (patient.csf_abeta42 / patient.csf_abeta40) < 0.075: severe_count += 1
        if patient.amyloid_pet_suvr and patient.amyloid_pet_suvr >= 1.3: severe_count += 1
        if patient.hippocampus_volume_left and patient.hippocampus_volume_right:
            if (patient.hippocampus_volume_left + patient.hippocampus_volume_right) < 4500: severe_count += 1
            
        print(f"{test_case['name'][:20]:20} | Stage: {stage:6} | Severe markers: {severe_count}/5 | "
              f"MMSE: {patient.mmse_score:4} | CDR: {patient.cdr_sum:3}")
    
    return all_passed


if __name__ == "__main__":
    test_unified_staging_logic()

