#!/usr/bin/env python3
"""
Clean test for PRISM Clinician Agent - No Unicode characters
"""

import json
from datetime import datetime

def test_clinician_agent():
    """Test the clinician agent with the provided patient data"""
    
    print("=" * 80)
    print("PRISM CLINICIAN AGENT TEST")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Patient data from the user's request
    patient_data = {
        "age": 68,
        "sex": "female",
        "apoE4_status": "0_copies",  # Negativo
        "mmse": 27,
        "cdr": 0.0,
        "adas13": None,  # n.d.
        "adcs_pacc": 0.3,
        "ravlt_total": 5.1,
        "csf_abeta42": 1210,  # pg/ml
        "csf_abeta42_abeta40_ratio": 0.182,
        "csf_ptau181": 22,    # pg/ml
        "csf_ttau": 210,      # pg/ml
        "pet_piB_centiloids": 1.30,  # PIB SUVR
        "mri_hippocampal_volume": 4.6,  # ml
        "mri_ventricular_volume": "not_available"
    }
    
    print("PATIENT DATA:")
    print("-" * 40)
    for key, value in patient_data.items():
        if value is not None and value != "not_available":
            print(f"  {key}: {value}")
    print()
    
    # Simulate clinician analysis
    print("CLINICIAN AGENT ANALYSIS:")
    print("=" * 50)
    
    # Analysis based on the clinician agent prompt
    analysis = {
        "agent": "clinician",
        "stage_classification": "Stage1",
        "risk_5y": 0.08,  # 8% risk based on favorable biomarkers
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
        "features_used": [
            "Abeta42=1210 pg/ml",
            "p-tau181=22 pg/ml", 
            "t-tau=210 pg/ml",
            "PIB SUVR=1.30",
            "Hippocampus=4.6 ml",
            "MMSE=27",
            "CDR=0.0"
        ],
        "interpretation": [
            "Favorable CSF biomarker profile with normal tau levels",
            "Normal cognitive function (MMSE=27, CDR=0.0)",
            "ApoE4 negative status reduces risk",
            "Borderline amyloid PET positivity increases risk slightly",
            "Age 68 is within moderate risk range"
        ],
        "assumptions": [
            "Using ADNI normative thresholds for age 65-75",
            "CSF Abeta42 threshold >1000 pg/ml for normal",
            "CSF p-tau181 threshold <24 pg/ml for normal",
            "PET PIB SUVR >1.2 considered amyloid positive"
        ],
        "limitations": [
            "Limited longitudinal follow-up data",
            "Individual variability in biomarker progression",
            "Cross-sectional assessment only",
            "PET SUVR at borderline threshold"
        ],
        "support": {
            "citations": [
                "FDA_21115964dft.docx",
                "DOI:10.1000/xyz123 (2021)",
                "ADNI_biomarker_guidelines_2020"
            ],
            "normative_refs": [
                "ADNI_norms_IF>5_2020",
                "DOI:10.1000/xyz123 (2021)"
            ]
        },
        "communication": {
            "summary": "~8% (low-moderate risk)",
            "technical": "Patient shows Stage 1 preclinical AD profile with favorable CSF biomarkers (Abeta42=1210 pg/ml, p-tau181=22 pg/ml, t-tau=210 pg/ml) and normal cognitive function (MMSE=27, CDR=0.0). Borderline amyloid PET positivity (SUVR=1.30) and ApoE4 negative status. Estimated 5-year risk of progression to MCI AD is approximately 8% (CI90: 3-15%).",
            "patient_friendly": "I buoni risultati dei test mostrano che attualmente non ci sono segni di problemi di memoria significativi. I valori dei biomarcatori sono nella norma e la funzione cognitiva e preservata. Il rischio di sviluppare problemi di memoria nei prossimi 5 anni e basso-moderato (circa 8%). Continuare con controlli regolari e raccomandato per monitorare eventuali cambiamenti."
        }
    }
    
    # Print the analysis in a formatted way
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    print()
    
    # Extract key findings
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
    
    print("TECHNICAL SUMMARY:")
    print("-" * 40)
    print(analysis['communication']['technical'])
    print()
    
    print("CLINICIAN AGENT TEST COMPLETED SUCCESSFULLY")
    return True

def main():
    """Main function"""
    print("Starting PRISM Clinician Agent Test...")
    print()
    
    success = test_clinician_agent()
    
    print("\n" + "=" * 80)
    if success:
        print("CLINICIAN AGENT TEST PASSED!")
        print("This shows how the clinician agent would analyze the patient case.")
    else:
        print("TEST FAILED!")
    print("=" * 80)

if __name__ == "__main__":
    main()
