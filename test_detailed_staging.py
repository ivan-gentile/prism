"""Detailed test of staging logic for Loredana Bertè"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.data.patient_model import PatientData


# Loredana Bertè baseline data
LOREDANA_BERTE_BASELINE = {
    "patient_id": "Loredana_Berte_69",
    "age": 69,
    "sex": "F",
    "education_years": 16,
    "apoe4_copies": "1",  
    
    # Cognitive scores at baseline
    "mmse_score": 27,
    "cdr_sum": 0.0,
    
    # CSF biomarkers - francamente sfavorevoli
    "csf_abeta42": 550,     # molto ridotto (< 600 is abnormal)
    "csf_abeta40": 7857,    # calculated from ratio 0.07
    "csf_ptau181": 42,      # patologica (> 30 is abnormal)
    "csf_total_tau": 350,   # elevata
    
    # Imaging
    "amyloid_pet_suvr": 1.3,  # positiva per depositi amiloidi (>= 1.3)
    "hippocampus_volume_left": 2150,   # 4.3 ml total
    "hippocampus_volume_right": 2150,  
    
    # Clinical observations
    "memory_complaints": True,     
    "functional_impairment": False 
}


def test_detailed_staging():
    """Test detailed staging logic"""
    print("\n" + "="*60)
    print("🔍 DETAILED STAGING ANALYSIS FOR LOREDANA BERTÈ")
    print("="*60)
    
    # Create patient
    patient = PatientData(**LOREDANA_BERTE_BASELINE)
    
    print(f"\n📊 Patient Data:")
    print(f"   Age: {patient.age}")
    print(f"   MMSE: {patient.mmse_score}/30")
    print(f"   CDR: {patient.cdr_sum}")
    print(f"   CSF Aβ42: {patient.csf_abeta42} pg/ml")
    print(f"   CSF Aβ40: {patient.csf_abeta40} pg/ml")
    print(f"   CSF p-tau181: {patient.csf_ptau181} pg/ml")
    print(f"   CSF total tau: {patient.csf_total_tau} pg/ml")
    print(f"   Amyloid PET SUVR: {patient.amyloid_pet_suvr}")
    print(f"   Hippocampus total: {patient.hippocampus_volume_left + patient.hippocampus_volume_right} mm³")
    
    # Manual analysis of staging criteria
    print(f"\n🔍 Staging Criteria Analysis:")
    
    # Cognitive assessment
    has_cognitive_impairment = False
    has_functional_impairment = False
    
    if patient.cdr_sum == 0:
        print(f"   CDR = 0: Normal cognition")
        has_cognitive_impairment = False
    if patient.mmse_score >= 24:
        print(f"   MMSE ≥ 24: Normal cognition")
        
    # Biomarker analysis
    print(f"\n🧪 Biomarker Analysis:")
    
    # Severe markers count
    severe_markers_count = 0
    
    # CSF Aβ42
    if patient.csf_abeta42 < 550:
        print(f"   ✅ CSF Aβ42 < 550: {patient.csf_abeta42} pg/ml (SEVERE)")
        severe_markers_count += 1
    elif patient.csf_abeta42 < 600:
        print(f"   ⚠️  CSF Aβ42 < 600: {patient.csf_abeta42} pg/ml (abnormal)")
    else:
        print(f"   ✅ CSF Aβ42 normal: {patient.csf_abeta42} pg/ml")
        
    # CSF p-tau181
    if patient.csf_ptau181 > 40:
        print(f"   ✅ CSF p-tau181 > 40: {patient.csf_ptau181} pg/ml (SEVERE)")
        severe_markers_count += 1
    elif patient.csf_ptau181 > 30:
        print(f"   ⚠️  CSF p-tau181 > 30: {patient.csf_ptau181} pg/ml (abnormal)")
    else:
        print(f"   ✅ CSF p-tau181 normal: {patient.csf_ptau181} pg/ml")
        
    # Aβ42/Aβ40 ratio
    if patient.csf_abeta42 and patient.csf_abeta40:
        ratio = patient.csf_abeta42 / patient.csf_abeta40
        if ratio < 0.075:
            print(f"   ✅ Aβ42/Aβ40 ratio < 0.075: {ratio:.3f} (SEVERE)")
            severe_markers_count += 1
        elif ratio < 0.08:
            print(f"   ⚠️  Aβ42/Aβ40 ratio < 0.08: {ratio:.3f} (abnormal)")
        else:
            print(f"   ✅ Aβ42/Aβ40 ratio normal: {ratio:.3f}")
            
    # Amyloid PET
    if patient.amyloid_pet_suvr >= 1.3:
        print(f"   ✅ Amyloid PET ≥ 1.3: {patient.amyloid_pet_suvr} SUVR (SEVERE)")
        severe_markers_count += 1
    else:
        print(f"   ✅ Amyloid PET normal: {patient.amyloid_pet_suvr} SUVR")
        
    # Hippocampus volume
    if patient.hippocampus_volume_left and patient.hippocampus_volume_right:
        total_volume = patient.hippocampus_volume_left + patient.hippocampus_volume_right
        if total_volume < 4500:
            print(f"   ✅ Hippocampus < 4500 mm³: {total_volume} mm³ (SEVERE)")
            severe_markers_count += 1
        else:
            print(f"   ✅ Hippocampus normal: {total_volume} mm³")
    
    print(f"\n📈 Severe Markers Count: {severe_markers_count}/5")
    print(f"   Threshold for Stage3: ≥ 3 severe markers")
    
    if severe_markers_count >= 3:
        print(f"   🎯 Result: STAGE 3 (severe biomarker pathology)")
    elif severe_markers_count >= 1:
        print(f"   🎯 Result: STAGE 2 (biomarker pathology)")
    else:
        print(f"   🎯 Result: STAGE 1 (normal/minimal pathology)")
        
    # Test actual function
    from prism_ad.agents.prism_agents import determine_fda_stage
    determined_stage = determine_fda_stage(patient)
    
    print(f"\n🤖 System determination: {determined_stage}")
    
    if determined_stage == "Stage3":
        print("✅ PERFECT! Loredana Bertè is correctly classified as Stage3")
        print("   This matches the expected outcome: '⚠️ Diagnosi a 5 anni: MCI AD / Stage 3 FDA'")
    else:
        print("❌ Error in classification")


if __name__ == "__main__":
    test_detailed_staging()
