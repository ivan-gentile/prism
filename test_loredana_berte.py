"""Test case for Loredana Bertè - Example B from Campione-utenti.md"""
import asyncio
import json
from datetime import datetime

# Add parent directory to path
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prism_ad.agents.prism_agents import PRISMAgentSystem


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
    # Assuming ADCS-PACC 0.4 and RAVLT Trial 1 = 6 are not directly available in our model
    
    # CSF biomarkers - francamente sfavorevoli
    "csf_abeta42": 550,     # molto ridotto (< 600 is abnormal)
    "csf_abeta40": 7857,    # calculated from ratio 0.07: 550/0.07 = ~7857
    "csf_ptau181": 42,      # patologica (> 30 is abnormal)
    "csf_total_tau": 350,   # molto elevata (< 400 is normal, so this is normal)
    
    # Imaging
    "amyloid_pet_suvr": 1.3,  # positiva per depositi amiloidi significativi (= threshold)
    "hippocampus_volume_left": 2150,   # 4.3 ml = 4300 mm³, so per hemisphere ~2150
    "hippocampus_volume_right": 2150,  # volume già ridotto
    
    # Clinical observations
    "memory_complaints": True,     # sottili alterazioni
    "functional_impairment": False # preserved function
}

# Expected outcome: the patient should progress to Stage 3 (MCI AD) within 5 years
# Baseline stage should be Stage2 (pathological biomarkers but normal cognition)


async def test_loredana_berte():
    """Test Loredana Bertè case specifically"""
    print("\n" + "="*60)
    print("🧾 TESTING LOREDANA BERTÈ CASE")
    print("Example B from Campione-utenti.md")
    print("="*60)
    
    # Display patient profile
    print(f"Patient: {LOREDANA_BERTE_BASELINE['patient_id']}")
    print(f"Age: {LOREDANA_BERTE_BASELINE['age']} years")
    print(f"Sex: {LOREDANA_BERTE_BASELINE['sex']}")
    print(f"ApoE4: {LOREDANA_BERTE_BASELINE['apoe4_copies']} copy (eterozigote)")
    print(f"MMSE: {LOREDANA_BERTE_BASELINE['mmse_score']}/30")
    print(f"CDR: {LOREDANA_BERTE_BASELINE['cdr_sum']}")
    print(f"CSF Aβ42: {LOREDANA_BERTE_BASELINE['csf_abeta42']} pg/ml (very low)")
    print(f"CSF p-tau181: {LOREDANA_BERTE_BASELINE['csf_ptau181']} pg/ml (elevated)")
    print(f"Amyloid PET: {LOREDANA_BERTE_BASELINE['amyloid_pet_suvr']} SUVR (positive)")
    print(f"Hippocampus: {LOREDANA_BERTE_BASELINE['hippocampus_volume_left'] + LOREDANA_BERTE_BASELINE['hippocampus_volume_right']} mm³ total")
    
    print("\nExpected baseline stage: Stage2 (pathological biomarkers, normal cognition)")
    print("Expected 5-year outcome: High risk of progression to Stage3 (MCI AD)")
    print("-" * 60)
    
    # Initialize system
    system = PRISMAgentSystem()
    
    try:
        # Initialize agents
        print("\n🔧 Initializing PRISM-AD system...")
        await system.initialize_agents()
        
        # Test stage determination
        from prism_ad.data.patient_model import PatientData
        patient = PatientData(**LOREDANA_BERTE_BASELINE)
        determined_stage = system._determine_fda_stage(patient)
        
        print(f"\n📊 Stage determination test:")
        print(f"   Determined stage: {determined_stage}")
        
        # Process patient through full pipeline
        print(f"\n🏥 Processing through full agent pipeline...")
        final_report = await system.process_patient(LOREDANA_BERTE_BASELINE)
        
        print(f"\n" + "🎯 "*20)
        print("FINAL ASSESSMENT RESULTS")
        print("="*60)
        print(final_report)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"loredana_berte_test_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"Loredana Bertè Test Results - {timestamp}\n")
            f.write("="*60 + "\n\n")
            f.write(f"Determined baseline stage: {determined_stage}\n\n")
            f.write("Final Report:\n")
            f.write(final_report)
        
        print(f"\n💾 Results saved to: {report_filename}")
        
        # Analysis
        print(f"\n" + "📋 "*20)
        print("ANALYSIS")
        print("="*60)
        print(f"✅ Baseline stage determined: {determined_stage}")
        if "Stage2" in determined_stage:
            print("✅ Correct! Patient has pathological biomarkers but normal cognition")
        elif "Stage3" in determined_stage:
            print("⚠️  Stage3 at baseline - check if cognitive impairment was detected")
        else:
            print("❌ Unexpected stage - review staging logic")
            
        if "Stage3" in final_report or "MCI" in final_report:
            print("✅ System appears to predict progression to Stage3/MCI")
        else:
            print("⚠️  Check if progression risk to Stage3 is being estimated")
            
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await system.close()
        print("\n🔒 System shutdown complete")


async def main():
    """Main test function"""
    print("\n" + "🚀 "*20)
    print("LOREDANA BERTÈ CASE TEST")
    print("Testing Stage Determination and Risk Assessment")
    print("🚀 "*20)
    
    await test_loredana_berte()
    
    print("\n" + "✅ "*20)
    print("TEST COMPLETED")
    print("✅ "*20)


if __name__ == "__main__":
    # Run the async test
    asyncio.run(main())

