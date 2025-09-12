#!/usr/bin/env python3
"""
Table Validator - Estrae tabelle strutturate dall'Anamnesi del Dottore usando OpenAI
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, List
import re

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

from test_plan_parser_v2 import PatientDataParserV2
from prism_ad.agents.prism_agents import PRISMAgentSystem

class TableValidator:
    """Validatore di tabelle che usa OpenAI per estrarre dati strutturati"""
    
    def __init__(self, markdown_file: str = "prism_ad/agents/Campione-utenti.md"):
        self.markdown_file = markdown_file
        self.parser = PatientDataParserV2(markdown_file)
        self.prism_system = None
        
        # Configurazione ambiente
        self.model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
        self.base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")
        
        # Template della tabella
        self.table_variables = [
            "Age",
            "Gender", 
            "Race",
            "Educational level",
            "ApoE4 carrier",
            "CDR",
            "MMSE",
            "ADCS-PACC",
            "RAVLT Trial 1",
            "CSF t-tau (pg/ml)",
            "CSF p-tau181 (pg/ml)",
            "CSF Aβ42 (pg/ml)",
            "CSF Aβ42/Aβ40 ratio",
            "PET PIB SUVR cortex",
            "MRI Hippocampus (ml)"
        ]
    
    async def initialize_system(self):
        """Inizializza il sistema PRISM per accesso a OpenAI"""
        print("Initializing OpenAI system for table extraction...")
        self.prism_system = PRISMAgentSystem(
            model_name=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url
        )
        await self.prism_system.initialize_agents()
        print("System initialized successfully")
    
    async def validate_all_tables(self) -> List[Dict[str, Any]]:
        """Valida tutte le tabelle nel file"""
        print("=" * 80)
        print("TABLE VALIDATOR - ANAMNESI TO STRUCTURED DATA")
        print("=" * 80)
        print()
        
        # Parse dei dati
        print("Step 1: Parsing patient data...")
        patients_data = self.parser.parse_all_patients()
        print(f"Found {len(patients_data)} patients")
        print()
        
        # Inizializza sistema
        await self.initialize_system()
        print()
        
        results = []
        
        # Valida ogni paziente
        for i, patient_info in enumerate(patients_data, 1):
            print(f"Step 2.{i}: Validating table for {patient_info['patient_name']}...")
            result = await self._validate_single_table(patient_info)
            results.append(result)
            print(f"Completed patient {i}/{len(patients_data)}")
            print()
        
        # Chiudi sistema
        await self.prism_system.close()
        
        # Analizza risultati
        self._analyze_validation_results(results)
        
        return results
    
    async def _validate_single_table(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """Valida la tabella di un singolo paziente"""
        anamnesis = patient_info['doctor_anamnesis']
        existing_baseline = patient_info['baseline_data']
        existing_followup = patient_info['followup_data']
        
        print(f"  Patient: {patient_info['patient_name']}")
        print(f"  Anamnesis length: {len(anamnesis)} characters")
        
        # Estrai tabella usando OpenAI
        print("  Extracting structured data from anamnesis...")
        try:
            extracted_table = await self._extract_table_from_anamnesis(anamnesis)
            print("    ✅ Table extraction completed")
        except Exception as e:
            print(f"    ❌ Error extracting table: {e}")
            return {
                'patient_info': patient_info,
                'error': str(e),
                'success': False
            }
        
        # Confronta con tabella esistente
        print("  Comparing with existing table...")
        comparison = self._compare_tables(extracted_table, existing_baseline, existing_followup)
        
        accuracy_score = self._calculate_accuracy(comparison)
        print(f"  Accuracy: {accuracy_score:.1f}%")
        
        return {
            'patient_info': patient_info,
            'extracted_table': extracted_table,
            'existing_baseline': existing_baseline,
            'existing_followup': existing_followup,
            'comparison': comparison,
            'accuracy_score': accuracy_score,
            'success': True
        }
    
    async def _extract_table_from_anamnesis(self, anamnesis: str) -> Dict[str, Any]:
        """Estrae dati strutturati dall'anamnesi usando OpenAI"""
        
        # Crea il prompt per l'estrazione
        prompt = f"""
Analizza la seguente anamnesi clinica e estrai i dati strutturati per creare una tabella con valori baseline e follow-up a 5 anni.

ANAMNESI:
{anamnesis}

Estrai i seguenti dati e restituisci SOLO un JSON valido con questa struttura esatta:

{{
  "baseline": {{
    "Age": [valore numerico],
    "Gender": "[Male/Female]",
    "Race": "[descrizione]",
    "Educational level": [anni di istruzione],
    "ApoE4 carrier": "[Negative/Positive (X allele)]",
    "CDR": [valore numerico],
    "MMSE": [valore numerico],
    "ADCS-PACC": [valore numerico],
    "RAVLT Trial 1": [valore numerico],
    "CSF t-tau (pg/ml)": [valore numerico],
    "CSF p-tau181 (pg/ml)": [valore numerico],
    "CSF Aβ42 (pg/ml)": [valore numerico],
    "CSF Aβ42/Aβ40 ratio": [valore numerico],
    "PET PIB SUVR cortex": [valore numerico],
    "MRI Hippocampus (ml)": [valore numerico]
  }},
  "followup_5y": {{
    "Age": [valore numerico],
    "Gender": "[Male/Female]",
    "Race": "[descrizione]",
    "Educational level": [anni di istruzione],
    "ApoE4 carrier": "[Negative/Positive (X allele)]",
    "CDR": [valore numerico],
    "MMSE": [valore numerico],
    "ADCS-PACC": [valore numerico],
    "RAVLT Trial 1": [valore numerico],
    "CSF t-tau (pg/ml)": [valore numerico],
    "CSF p-tau181 (pg/ml)": [valore numerico],
    "CSF Aβ42 (pg/ml)": [valore numerico],
    "CSF Aβ42/Aβ40 ratio": [valore numerico],
    "PET PIB SUVR cortex": [valore numerico],
    "MRI Hippocampus (ml)": [valore numerico]
  }}
}}

ISTRUZIONI:
- Se un valore non è menzionato, usa null
- Mantieni la precisione dei valori numerici come descritti
- Per PET PIB SUVR usa il formato numerico (es. 1.30, non 1300)
- Restituisci SOLO il JSON, senza testo aggiuntivo

JSON:
"""
        
        # Usa un agente per l'estrazione (usiamo clinician per semplicità)
        result = await self.prism_system.agents["clinician"].run(task=prompt)
        response = result.messages[-1].content if result.messages else ""
        
        # Estrai JSON dalla risposta
        try:
            # Cerca il JSON nella risposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                extracted_data = json.loads(json_str)
                return extracted_data
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}")
    
    def _compare_tables(self, extracted: Dict[str, Any], existing_baseline: Dict[str, Any], 
                       existing_followup: Dict[str, Any]) -> Dict[str, Any]:
        """Confronta tabella estratta con quella esistente"""
        comparison = {
            'baseline_matches': {},
            'followup_matches': {},
            'baseline_differences': {},
            'followup_differences': {}
        }
        
        # Confronta baseline
        if 'baseline' in extracted:
            for variable in self.table_variables:
                extracted_value = extracted['baseline'].get(variable)
                existing_value = existing_baseline.get(variable)
                
                if self._values_match(extracted_value, existing_value):
                    comparison['baseline_matches'][variable] = {
                        'extracted': extracted_value,
                        'existing': existing_value
                    }
                else:
                    comparison['baseline_differences'][variable] = {
                        'extracted': extracted_value,
                        'existing': existing_value
                    }
        
        # Confronta follow-up
        if 'followup_5y' in extracted:
            for variable in self.table_variables:
                extracted_value = extracted['followup_5y'].get(variable)
                existing_value = existing_followup.get(variable)
                
                if self._values_match(extracted_value, existing_value):
                    comparison['followup_matches'][variable] = {
                        'extracted': extracted_value,
                        'existing': existing_value
                    }
                else:
                    comparison['followup_differences'][variable] = {
                        'extracted': extracted_value,
                        'existing': existing_value
                    }
        
        return comparison
    
    def _values_match(self, extracted_value: Any, existing_value: Any) -> bool:
        """Verifica se due valori sono equivalenti"""
        if extracted_value is None and existing_value is None:
            return True
        
        if extracted_value is None or existing_value is None:
            return False
        
        # Confronto numerico con tolleranza
        if isinstance(extracted_value, (int, float)) and isinstance(existing_value, (int, float)):
            return abs(extracted_value - existing_value) < 0.1
        
        # Confronto stringhe (case insensitive)
        if isinstance(extracted_value, str) and isinstance(existing_value, str):
            return extracted_value.lower().strip() == existing_value.lower().strip()
        
        # Confronto booleano
        if isinstance(extracted_value, bool) and isinstance(existing_value, bool):
            return extracted_value == existing_value
        
        return str(extracted_value) == str(existing_value)
    
    def _calculate_accuracy(self, comparison: Dict[str, Any]) -> float:
        """Calcola l'accuratezza della tabella estratta"""
        total_variables = len(self.table_variables) * 2  # baseline + followup
        
        baseline_matches = len(comparison['baseline_matches'])
        followup_matches = len(comparison['followup_matches'])
        total_matches = baseline_matches + followup_matches
        
        accuracy = (total_matches / total_variables) * 100
        return accuracy
    
    def _analyze_validation_results(self, results: List[Dict[str, Any]]):
        """Analizza i risultati della validazione"""
        print("=" * 80)
        print("VALIDATION RESULTS ANALYSIS")
        print("=" * 80)
        
        successful_results = [r for r in results if r.get('success', False)]
        
        if not successful_results:
            print("No successful validations to analyze")
            return
        
        # Calcola accuratezza media
        total_accuracy = sum(r['accuracy_score'] for r in successful_results)
        average_accuracy = total_accuracy / len(successful_results)
        
        print(f"Average Table Accuracy: {average_accuracy:.1f}%")
        print(f"Total Patients Validated: {len(successful_results)}")
        print()
        
        # Dettaglio per paziente
        for result in successful_results:
            patient_name = result['patient_info']['patient_name']
            accuracy = result['accuracy_score']
            status = "✅" if accuracy >= 80 else "⚠️" if accuracy >= 60 else "❌"
            
            print(f"{status} {patient_name}: {accuracy:.1f}% accuracy")
            
            # Mostra differenze principali
            comparison = result['comparison']
            if comparison['baseline_differences'] or comparison['followup_differences']:
                baseline_diffs = len(comparison['baseline_differences'])
                followup_diffs = len(comparison['followup_differences'])
                print(f"   Baseline differences: {baseline_diffs}")
                print(f"   Follow-up differences: {followup_diffs}")
        
        print()
    
    def save_results(self, results: List[Dict[str, Any]], filename: str = "table_validation_results.json"):
        """Salva i risultati della validazione"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"Validation results saved to {filename}")

async def main():
    """Funzione principale per eseguire la validazione tabelle"""
    validator = TableValidator()
    
    try:
        results = await validator.validate_all_tables()
        validator.save_results(results)
        
    except Exception as e:
        print(f"Error during table validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
