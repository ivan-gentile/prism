#!/usr/bin/env python3
"""
Test Plan Parser V2 - Estrae dati pazienti dal nuovo formato Campione-utenti.md
"""

import re
import json
from typing import List, Dict, Any, Optional
from prism_ad.data.patient_model import PatientData, ApoE4Status

class PatientDataParserV2:
    """Parser per il nuovo formato del file markdown"""
    
    def __init__(self, markdown_file: str):
        self.markdown_file = markdown_file
        self.patients = []
    
    def parse_all_patients(self) -> List[Dict[str, Any]]:
        """Estrae tutti i pazienti dal file markdown"""
        with open(self.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Dividi per separatori ---
        cases = content.split('---')
        
        for i, case in enumerate(cases):
            if case.strip():
                patient_data = self._parse_single_case(case, i + 1)
                if patient_data:
                    self.patients.append(patient_data)
        
        return self.patients
    
    def _parse_single_case(self, case_text: str, case_number: int) -> Optional[Dict[str, Any]]:
        """Estrae dati da un singolo caso"""
        try:
            # Estrai nome paziente ed età
            name_match = re.search(r'🧾 Example [A-Z] — (.+?) \((\d+) anni\)', case_text)
            if name_match:
                patient_name = name_match.group(1).strip()
                age = int(name_match.group(2))
            else:
                patient_name = f"Paziente_{case_number}"
                age = 70  # Default
            
            # Estrai anamnesi del dottore
            doctor_anamnesis = self._extract_doctor_anamnesis(case_text)
            
            # Estrai dati della tabella
            baseline_data, followup_data = self._extract_table_data(case_text)
            
            # Estrai outcome
            outcome = self._extract_outcome(case_text)
            
            # Crea PatientData object dal baseline
            patient_data = self._create_patient_data(
                case_number, patient_name, baseline_data, doctor_anamnesis
            )
            
            return {
                'case_number': case_number,
                'patient_name': patient_name,
                'doctor_anamnesis': doctor_anamnesis,
                'baseline_data': baseline_data,
                'followup_data': followup_data,
                'patient_data': patient_data,
                'outcome': outcome
            }
            
        except Exception as e:
            print(f"Errore nel parsing del caso {case_number}: {e}")
            return None
    
    def _extract_doctor_anamnesis(self, case_text: str) -> str:
        """Estrae l'anamnesi del dottore"""
        pattern = r'Anamnesi del Dottore\s*\n(.+?)(?=\n\nTabella|\nTabella|$)'
        match = re.search(pattern, case_text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_table_data(self, case_text: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Estrae i dati della tabella (baseline e 5 anni)"""
        # Trova la sezione della tabella
        table_pattern = r'Tabella\s*\n\s*\n(.+?)(?=\n\nOutcome|$)'
        table_match = re.search(table_pattern, case_text, re.DOTALL)
        
        if not table_match:
            return {}, {}
        
        table_text = table_match.group(1)
        lines = table_text.strip().split('\n')
        
        baseline_data = {}
        followup_data = {}
        
        for line in lines[1:]:  # Skip header
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 3:
                    variable = parts[0].strip()
                    baseline_value = parts[1].strip()
                    followup_value = parts[2].strip()
                    
                    baseline_data[variable] = self._parse_value(baseline_value)
                    followup_data[variable] = self._parse_value(followup_value)
        
        return baseline_data, followup_data
    
    def _extract_outcome(self, case_text: str) -> Dict[str, Any]:
        """Estrae l'outcome a 5 anni"""
        outcome_pattern = r'Outcome: (.+)'
        outcome_match = re.search(outcome_pattern, case_text)
        
        if not outcome_match:
            return {'diagnosis': 'unknown', 'progression': False}
        
        outcome_text = outcome_match.group(1).strip()
        
        # Determina se c'è stata progressione
        progression = False
        diagnosis = 'unknown'
        
        if '✅' in outcome_text and 'no-disease' in outcome_text:
            progression = False
            diagnosis = 'no-disease'
        elif '⚠️' in outcome_text and ('MCI AD' in outcome_text or 'Stage 3' in outcome_text):
            progression = True
            diagnosis = 'MCI AD / Stage 3 FDA'
        
        return {
            'raw_text': outcome_text,
            'diagnosis': diagnosis,
            'progression': progression
        }
    
    def _parse_value(self, value_str: str) -> Any:
        """Converte stringa in valore appropriato"""
        if not value_str or value_str.strip() == "":
            return None
        
        value_str = value_str.strip()
        
        # Gestisci valori booleani/categorici
        if value_str.lower() in ['negative', 'no']:
            return False
        elif value_str.lower().startswith('positive'):
            return True
        elif value_str in ['Female', 'Male']:
            return value_str
        elif 'Caucasian' in value_str:
            return value_str
        
        # Prova a convertire in numero
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            return value_str
    
    def _create_patient_data(self, case_number: int, patient_name: str, baseline_data: Dict[str, Any], 
                           doctor_anamnesis: str) -> PatientData:
        """Crea oggetto PatientData dai dati baseline"""
        
        # Gestisci ApoE4
        apoe4_status = ApoE4Status.ZERO_COPIES
        apoe4_carrier = baseline_data.get('ApoE4 carrier', False)
        if apoe4_carrier:
            if isinstance(apoe4_carrier, str) and '1 allele' in apoe4_carrier:
                apoe4_status = ApoE4Status.ONE_COPY
            elif apoe4_carrier is True:
                apoe4_status = ApoE4Status.ONE_COPY
        
        # Gestisci sesso
        gender = baseline_data.get('Gender', 'Female')
        sex = 'F' if gender == 'Female' else 'M'
        
        # Calcola CSF Aβ40 dal rapporto se disponibile
        csf_abeta42 = baseline_data.get('CSF Aβ42 (pg/ml)')
        csf_ratio = baseline_data.get('CSF Aβ42/Aβ40 ratio')
        csf_abeta40 = None
        if csf_abeta42 and csf_ratio and csf_ratio > 0:
            csf_abeta40 = csf_abeta42 / csf_ratio
        
        return PatientData(
            patient_id=f"Example_{case_number}_{patient_name.replace(' ', '_')}",
            age=float(baseline_data.get('Age', 70)),
            sex=sex,
            education_years=float(baseline_data.get('Educational level', 16)),
            apoe4_copies=apoe4_status,
            mmse_score=baseline_data.get('MMSE'),
            cdr_sum=baseline_data.get('CDR', 0),
            adas_cog13=None,  # Non disponibile nel nuovo formato
            csf_abeta42=csf_abeta42,
            csf_abeta40=csf_abeta40,
            csf_ptau181=baseline_data.get('CSF p-tau181 (pg/ml)'),
            csf_total_tau=baseline_data.get('CSF t-tau (pg/ml)'),
            amyloid_pet_suvr=baseline_data.get('PET PIB SUVR cortex'),
            hippocampus_volume_left=baseline_data.get('MRI Hippocampus (ml)', 0) / 2 if baseline_data.get('MRI Hippocampus (ml)') else None,
            hippocampus_volume_right=baseline_data.get('MRI Hippocampus (ml)', 0) / 2 if baseline_data.get('MRI Hippocampus (ml)') else None,
            ventricular_volume=None,
            adcs_pacc_score=baseline_data.get('ADCS-PACC')
        )

def main():
    """Test del parser V2"""
    parser = PatientDataParserV2("prism_ad/agents/Campione-utenti.md")
    patients = parser.parse_all_patients()
    
    print(f"Parsed {len(patients)} patients:")
    for patient in patients:
        print(f"\nCaso {patient['case_number']}: {patient['patient_name']}")
        print(f"Età: {patient['patient_data'].age}")
        print(f"ApoE4: {patient['patient_data'].apoe4_copies}")
        print(f"MMSE baseline: {patient['baseline_data'].get('MMSE')}")
        print(f"MMSE 5 anni: {patient['followup_data'].get('MMSE')}")
        print(f"Outcome: {patient['outcome']['diagnosis']} (Progressione: {patient['outcome']['progression']})")
        print(f"Anamnesi: {patient['doctor_anamnesis'][:100]}...")

if __name__ == "__main__":
    main()
