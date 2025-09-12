#!/usr/bin/env python3
"""
Test Plan Parser - Estrae dati pazienti dal file Campione-utenti.md
"""

import re
import json
from typing import List, Dict, Any, Optional
from prism_ad.data.patient_model import PatientData, ApoE4Status

class PatientDataParser:
    """Parser per estrarre dati pazienti dal file markdown"""
    
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
            # Estrai nome paziente
            name_match = re.search(r'Caso \d+ — (.+)', case_text)
            patient_name = name_match.group(1).strip() if name_match else f"Paziente_{case_number}"
            
            # Estrai anamnesi del dottore
            doctor_anamnesis = self._extract_doctor_anamnesis(case_text)
            
            # Estrai dati della tabella
            baseline_data = self._extract_baseline_data(case_text)
            
            # Estrai rischio atteso
            expected_risk = self._extract_expected_risk(case_text)
            
            # Crea PatientData object
            patient_data = self._create_patient_data(
                case_number, patient_name, baseline_data, doctor_anamnesis, expected_risk
            )
            
            return {
                'case_number': case_number,
                'patient_name': patient_name,
                'doctor_anamnesis': doctor_anamnesis,
                'patient_data': patient_data,
                'expected_risk': expected_risk
            }
            
        except Exception as e:
            print(f"Errore nel parsing del caso {case_number}: {e}")
            return None
    
    def _extract_doctor_anamnesis(self, case_text: str) -> str:
        """Estrae l'anamnesi del dottore"""
        pattern = r'Anamnesi del Dottore\s*\n(.+?)(?=\n\n|\nTabella|\nRischio atteso|$)'
        match = re.search(pattern, case_text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_baseline_data(self, case_text: str) -> Dict[str, Any]:
        """Estrae i dati della tabella Anamnesi – Baseline"""
        # Trova la sezione della tabella
        table_pattern = r'Anamnesi – Baseline\s*\n(.+?)(?=\n\nRischio atteso|$)'
        table_match = re.search(table_pattern, case_text, re.DOTALL)
        
        if not table_match:
            return {}
        
        table_text = table_match.group(1)
        
        # Estrai i dati dalla tabella
        data = {}
        
        # Età, Genere, Etnia, Istruzione, ApoE4
        basic_info = re.search(r'Età: (\d+) \| Genere: ([MF]) \| Etnia: (\w+) \| Istruzione \(anni\): (\d+) \| ApoE4: (.+)', table_text)
        if basic_info:
            data['age'] = float(basic_info.group(1))
            data['sex'] = basic_info.group(2)
            data['education_years'] = float(basic_info.group(4))
            data['apoe4'] = basic_info.group(5)
        
        # CDR, MMSE, MoCA, ADAS-Cog/ADAS13, ADCS-PACC
        cognitive_info = re.search(r'CDR: ([0-9.]+) \| MMSE: ([0-9.–]+) \| MoCA: ([^|]+) \| ADAS-Cog/ADAS13: ([^|]+) \| ADCS-PACC: ([0-9.–]+)', table_text)
        if cognitive_info:
            data['cdr'] = self._parse_numeric_value(cognitive_info.group(1))
            data['mmse'] = self._parse_numeric_value(cognitive_info.group(2))
            data['moca'] = cognitive_info.group(3).strip()
            data['adas_cog'] = cognitive_info.group(4).strip()
            data['adcs_pacc'] = self._parse_numeric_value(cognitive_info.group(5))
        
        # RAVLT Trial 1 immediato, FAQ
        memory_info = re.search(r'RAVLT Trial 1 immediato: ([0-9.–]+) \| FAQ: ([^|]+)', table_text)
        if memory_info:
            data['ravlt'] = self._parse_numeric_value(memory_info.group(1))
            data['faq'] = memory_info.group(2).strip()
        
        # CSF: t-tau, p-tau181, p-tau217, Aβ42, Aβ42/Aβ40
        csf_info = re.search(r'CSF: t-tau = ([0-9.–]+) pg/ml \| p-tau181 = ([0-9.–]+) pg/ml \| p-tau217 = ([^|]+) \| Aβ42 = ([0-9.–]+) pg/ml \| Aβ42/Aβ40 = ([0-9.–]+)', table_text)
        if csf_info:
            data['csf_ttau'] = self._parse_numeric_value(csf_info.group(1))
            data['csf_ptau181'] = self._parse_numeric_value(csf_info.group(2))
            data['csf_ptau217'] = csf_info.group(3).strip()
            data['csf_abeta42'] = self._parse_numeric_value(csf_info.group(4))
            data['csf_abeta42_abeta40_ratio'] = self._parse_numeric_value(csf_info.group(5))
        
        # PET: PIB SUVR, AV45 SUVR
        pet_info = re.search(r'PET: PIB SUVR = ([0-9.–]+) \| AV45 SUVR = ([^|]+)', table_text)
        if pet_info:
            data['pet_pib_suvr'] = self._parse_numeric_value(pet_info.group(1))
            data['pet_av45_suvr'] = pet_info.group(2).strip()
        
        # MRI: Ippocampi tot, Entorinale, Temporale med, Cervello totale, Ventricoli
        mri_info = re.search(r'MRI: Ippocampi tot = ([0-9.–]+) ml \| Entorinale = ([^|]+) \| Temporale med = ([^|]+) \| Cervello totale = ([^|]+) \| Ventricoli = ([^|]+)', table_text)
        if mri_info:
            data['hippocampus_total'] = self._parse_numeric_value(mri_info.group(1))
            data['entorhinal'] = mri_info.group(2).strip()
            data['temporal_med'] = mri_info.group(3).strip()
            data['total_brain'] = mri_info.group(4).strip()
            data['ventricles'] = mri_info.group(5).strip()
        
        return data
    
    def _extract_expected_risk(self, case_text: str) -> Dict[str, Any]:
        """Estrae il rischio atteso"""
        # Cerca la sezione "Rischio atteso"
        risk_section = re.search(r'Rischio atteso\s*\n\s*\n(.+?)(?=\n\n---|$)', case_text, re.DOTALL)
        
        if not risk_section:
            return {'risk_percentage': 0.0, 'risk_category': 'unknown'}
        
        risk_text = risk_section.group(1)
        
        # Estrai riassunto breve
        summary_match = re.search(r'\* Riassunto breve: (.+?)(?=\n\*|$)', risk_text, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""
        
        # Estrai descrizione tecnica
        technical_match = re.search(r'\* Descrizione tecnica: (.+?)(?=\n\*|$)', risk_text, re.DOTALL)
        technical = technical_match.group(1).strip() if technical_match else ""
        
        # Estrai descrizione per il paziente
        patient_match = re.search(r'\* (?:Per il paziente|Descrizione per il paziente): "(.+?)"', risk_text, re.DOTALL)
        patient_desc = patient_match.group(1).strip() if patient_match else ""
        
        # Estrai percentuale dal riassunto breve
        risk_percentage = self._extract_risk_percentage(summary)
        
        return {
            'summary': summary,
            'technical_description': technical,
            'patient_description': patient_desc,
            'risk_percentage': risk_percentage,
            'risk_category': self._categorize_risk(risk_percentage)
        }
    
    def _extract_risk_percentage(self, summary: str) -> float:
        """Estrae la percentuale di rischio dal riassunto"""
        # Cerca pattern come "~8%", "~65%", "~40%", etc.
        percentage_match = re.search(r'~?(\d+(?:\.\d+)?)%', summary)
        if percentage_match:
            return float(percentage_match.group(1)) / 100.0
        
        # Cerca pattern come "Stage 3 ~7%", "Stage 4 ~3–4%"
        stage_match = re.search(r'Stage \d+ ~(\d+(?:\.\d+)?)%', summary)
        if stage_match:
            return float(stage_match.group(1)) / 100.0
        
        return 0.0
    
    def _categorize_risk(self, risk_percentage: float) -> str:
        """Categorizza il rischio in basso/moderato/alto"""
        if risk_percentage < 0.20:
            return "basso"
        elif risk_percentage < 0.50:
            return "moderato"
        else:
            return "alto"
    
    def _parse_numeric_value(self, value_str: str) -> Optional[float]:
        """Converte stringa in valore numerico, gestendo 'n.d.' e range"""
        if not value_str or value_str.strip() == "n.d.":
            return None
        
        # Gestisci range come "26–28"
        if "–" in value_str:
            parts = value_str.split("–")
            if len(parts) == 2:
                try:
                    return (float(parts[0]) + float(parts[1])) / 2.0
                except ValueError:
                    return None
        
        try:
            return float(value_str)
        except ValueError:
            return None
    
    def _create_patient_data(self, case_number: int, patient_name: str, baseline_data: Dict[str, Any], 
                           doctor_anamnesis: str, expected_risk: Dict[str, Any]) -> PatientData:
        """Crea oggetto PatientData dai dati estratti"""
        
        # Gestisci ApoE4
        apoe4_status = ApoE4Status.ZERO_COPIES
        if baseline_data.get('apoe4'):
            apoe4_str = baseline_data['apoe4'].lower()
            if 'positivo' in apoe4_str:
                if '2 alleli' in apoe4_str or 'e4/e4' in apoe4_str:
                    apoe4_status = ApoE4Status.TWO_COPIES
                else:
                    apoe4_status = ApoE4Status.ONE_COPY
        
        # Calcola volume ippocampale medio
        hippocampus_total = baseline_data.get('hippocampus_total', 0)
        hippocampus_avg = hippocampus_total / 2.0 if hippocampus_total else None
        
        return PatientData(
            patient_id=f"Caso_{case_number}_{patient_name.replace(' ', '_')}",
            age=baseline_data.get('age', 0),
            sex=baseline_data.get('sex', 'F'),
            education_years=baseline_data.get('education_years', 16),
            apoe4_copies=apoe4_status,
            mmse_score=baseline_data.get('mmse'),
            cdr_sum=baseline_data.get('cdr', 0),
            adas_cog13=self._parse_numeric_value(baseline_data.get('adas_cog', 'n.d.')),
            csf_abeta42=baseline_data.get('csf_abeta42'),
            csf_abeta40=baseline_data.get('csf_abeta42', 0) / baseline_data.get('csf_abeta42_abeta40_ratio', 1) if baseline_data.get('csf_abeta42_abeta40_ratio') else None,
            csf_ptau181=baseline_data.get('csf_ptau181'),
            csf_total_tau=baseline_data.get('csf_ttau'),
            amyloid_pet_suvr=baseline_data.get('pet_pib_suvr'),
            hippocampus_volume_left=hippocampus_avg,
            hippocampus_volume_right=hippocampus_avg,
            ventricular_volume=None
        )

def main():
    """Test del parser"""
    parser = PatientDataParser("prism_ad/agents/Campione-utenti.md")
    patients = parser.parse_all_patients()
    
    print(f"Parsed {len(patients)} patients:")
    for patient in patients:
        print(f"\nCaso {patient['case_number']}: {patient['patient_name']}")
        print(f"Età: {patient['patient_data'].age}")
        print(f"ApoE4: {patient['patient_data'].apoe4_copies}")
        print(f"Rischio atteso: {patient['expected_risk']['risk_percentage']*100:.1f}% ({patient['expected_risk']['risk_category']})")

if __name__ == "__main__":
    main()
