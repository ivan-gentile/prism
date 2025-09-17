"""Test stage determination logic only"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prism_ad.agents.prism_agents import PRISMAgentSystem, determine_fda_stage
from prism_ad.data.patient_model import PatientData


# Loredana Bertè baseline data (69 anni)
LOREDANA_BERTE_BASELINE = {
    "patient_id": "Loredana_Berte_69",
    "age": 69,
    "sex": "F",
    "education_years": 16,
    "apoe4_copies": "1",  # Positive (1 allele) - eterozigote
    
    # Cognitive scores at baseline
    "mmse_score": 27,
    "cdr_sum": 0.0,
    
    # CSF biomarkers - francamente sfavorevoli
    "csf_abeta42": 550,     # molto ridotto (< 600 is abnormal)
    "csf_abeta40": 7857,    # calculated from ratio 0.07: 550/0.07 = ~7857
    "csf_ptau181": 42,      # patologica (> 30 is abnormal)
    "csf_total_tau": 350,   # elevata (but < 400 is normal)
    
    # Imaging
    "amyloid_pet_suvr": 1.3,  # positiva per depositi amiloidi (= threshold)
    "hippocampus_volume_left": 2150,   # 4.3 ml total, so per hemisphere ~2150
    "hippocampus_volume_right": 2150,  # volume già ridotto
    
    # Clinical observations
    "memory_complaints": True,     # sottili alterazioni
    "functional_impairment": False # preserved function
}

# Ornella Vanoni data for comparison (normal case)
ORNELLA_VANONI_BASELINE = {
    "patient_id": "Ornella_Vanoni_68",
    "age": 68,
    "sex": "F",
    "education_years": 16,
    "apoe4_copies": "0",  # Negative
    
    # Cognitive scores at baseline - normal
    "mmse_score": 27,
    "cdr_sum": 0.0,
    
    # CSF biomarkers - favorevoli
    "csf_abeta42": 1210,    # elevated (> 600 is normal)
    "csf_abeta40": 6648,    # calculated from ratio 0.182: 1210/0.182 = ~6648
    "csf_ptau181": 22,      # normale (< 30 is normal)
    "csf_total_tau": 210,   # normale (< 400 is normal)
    
    # Imaging
    "amyloid_pet_suvr": 1.30,  # negativa (< 1.3 threshold, but this is exactly at boundary)
    "hippocampus_volume_left": 2300,   # 4.6 ml total, so per hemisphere ~2300
    "hippocampus_volume_right": 2300,  # nella norma
    
    # Clinical observations
    "memory_complaints": False,
    "functional_impairment": False
}


def test_stage_determination():
    """Test only the stage determination logic"""
    print("\n" + "="*60)
    print("🧾 TESTING STAGE DETERMINATION LOGIC")
    print("="*60)
    
    # Initialize system (just to get the method)
    system = PRISMAgentSystem()
    
    # Test Loredana Bertè case
    print(f"\n📊 Testing Loredana Bertè (69 anni):")
    print(f"   MMSE: {LOREDANA_BERTE_BASELINE['mmse_score']}/30")
    print(f"   CDR: {LOREDANA_BERTE_BASELINE['cdr_sum']}")
    print(f"   CSF Aβ42: {LOREDANA_BERTE_BASELINE['csf_abeta42']} pg/ml (< 600 = abnormal)")
    print(f"   CSF p-tau181: {LOREDANA_BERTE_BASELINE['csf_ptau181']} pg/ml (> 30 = abnormal)")
    print(f"   Amyloid PET: {LOREDANA_BERTE_BASELINE['amyloid_pet_suvr']} SUVR (> 1.3 = positive)")
    
    # Convert to PatientData and determine stage
    patient_loredana = PatientData(**LOREDANA_BERTE_BASELINE)
    stage_loredana = determine_fda_stage(patient_loredana)
    
    print(f"   🎯 Determined stage: {stage_loredana}")
    
    # Analyze the logic
    print(f"\n   Analysis:")
    print(f"   - Cognitive impairment: {patient_loredana.mmse_score < 24 or patient_loredana.cdr_sum > 0}")
    print(f"   - Functional impairment: {patient_loredana.mmse_score < 20 or patient_loredana.cdr_sum >= 1.0}")
    print(f"   - Amyloid pathology: {patient_loredana.csf_abeta42 < 600 or patient_loredana.amyloid_pet_suvr > 1.3}")
    print(f"   - Tau pathology: {patient_loredana.csf_ptau181 > 30}")
    
    # Test Ornella Vanoni case for comparison
    print(f"\n📊 Testing Ornella Vanoni (68 anni) for comparison:")
    print(f"   MMSE: {ORNELLA_VANONI_BASELINE['mmse_score']}/30")
    print(f"   CDR: {ORNELLA_VANONI_BASELINE['cdr_sum']}")
    print(f"   CSF Aβ42: {ORNELLA_VANONI_BASELINE['csf_abeta42']} pg/ml")
    print(f"   CSF p-tau181: {ORNELLA_VANONI_BASELINE['csf_ptau181']} pg/ml")
    print(f"   Amyloid PET: {ORNELLA_VANONI_BASELINE['amyloid_pet_suvr']} SUVR")
    
    patient_ornella = PatientData(**ORNELLA_VANONI_BASELINE)
    stage_ornella = determine_fda_stage(patient_ornella)
    
    print(f"   🎯 Determined stage: {stage_ornella}")
    
    # Summary
    print(f"\n" + "📋 "*20)
    print("SUMMARY")
    print("="*60)
    print(f"Loredana Bertè (high risk case): {stage_loredana}")
    if stage_loredana == "Stage3":
        print("✅ Correct! Severe biomarker pathology with subtle cognitive changes (prodromal AD)")
    else:
        print("⚠️  Check logic - expected Stage3")
        
    print(f"Ornella Vanoni (normal case): {stage_ornella}")
    if stage_ornella == "Stage1":
        print("✅ Correct! Normal or minimal pathology")
    else:
        print("⚠️  Check logic - expected Stage1")
    
    print("="*60)
    print("Expected outcome for Loredana: Stage3 (MCI AD/Prodromal AD)")
    print("Expected outcome for Ornella: Stage1 → no progression (low risk)")


if __name__ == "__main__":
    test_stage_determination()
