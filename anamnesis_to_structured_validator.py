#!/usr/bin/env python3
"""
Anamnesis to Structured Data Validator
Sistema di validazione per l'estrazione di dati strutturati dall'anamnesi del dottore
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, List
import re
from datetime import datetime

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

from test_plan_parser_v2 import PatientDataParserV2
from prism_ad.agents.prism_agents import PRISMAgentSystem

class AnamnesisTaxtructuredValidator:
    """
    Validatore per l'estrazione di dati strutturati dall'anamnesi del dottore.
    
    Questo sistema:
    1. Legge l'anamnesi narrativa del dottore
    2. Usa OpenAI per estrarre dati strutturati in formato tabellare
    3. Confronta con le tabelle esistenti nel file
    4. Calcola l'accuratezza dell'estrazione
    5. Identifica inconsistenze tra testo narrativo e dati strutturati
    """
    
    def __init__(self, markdown_file: str = "prism_ad/agents/Campione-utenti.md"):
        self.markdown_file = markdown_file
        self.parser = PatientDataParserV2(markdown_file)
        self.prism_system = None
        
        # Configurazione ambiente
        self.model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
        self.base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")
        
        # Template della tabella standard
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
        
        # Soglie di accuratezza
        self.accuracy_thresholds = {
            'excellent': 90.0,
            'good': 80.0,
            'acceptable': 70.0,
            'poor': 50.0
        }
    
    async def initialize_system(self):
        """Inizializza il sistema PRISM per accesso a OpenAI"""
        print("🔧 Initializing OpenAI system for anamnesis extraction...")
        self.prism_system = PRISMAgentSystem(
            model_name=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url
        )
        await self.prism_system.initialize_agents()
        print("✅ System initialized successfully")
    
    async def validate_all_anamnesis(self) -> List[Dict[str, Any]]:
        """Valida l'estrazione di dati strutturati da tutte le anamnesi"""
        print("=" * 80)
        print("🏥 ANAMNESIS TO STRUCTURED DATA VALIDATOR")
        print("=" * 80)
        print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Parse dei dati
        print("📋 Step 1: Parsing patient data from markdown...")
        patients_data = self.parser.parse_all_patients()
        print(f"   Found {len(patients_data)} patients")
        print()
        
        # Inizializza sistema
        await self.initialize_system()
        print()
        
        results = []
        
        # Valida ogni paziente
        for i, patient_info in enumerate(patients_data, 1):
            print(f"🧑‍⚕️ Step 2.{i}: Validating anamnesis for {patient_info['patient_name']}...")
            result = await self._validate_single_anamnesis(patient_info)
            results.append(result)
            print(f"   ✅ Completed patient {i}/{len(patients_data)}")
            print()
        
        # Chiudi sistema
        await self.prism_system.close()
        
        # Analizza risultati
        overall_analysis = self._analyze_validation_results(results)
        
        print("=" * 80)
        print("🎯 VALIDATION COMPLETED")
        print("=" * 80)
        
        return results, overall_analysis
    
    async def _validate_single_anamnesis(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """Valida l'estrazione di dati strutturati da una singola anamnesi"""
        anamnesis = patient_info['doctor_anamnesis']
        existing_baseline = patient_info['baseline_data']
        existing_followup = patient_info['followup_data']
        
        print(f"   📝 Patient: {patient_info['patient_name']}")
        print(f"   📏 Anamnesis length: {len(anamnesis)} characters")
        
        # Estrai tabella usando OpenAI
        print("   🤖 Extracting structured data from narrative anamnesis...")
        try:
            extracted_table = await self._extract_structured_data_from_anamnesis(anamnesis)
            print("      ✅ Extraction completed successfully")
        except Exception as e:
            print(f"      ❌ Extraction failed: {e}")
            return {
                'patient_info': patient_info,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
        
        # Confronta con tabelle esistenti
        print("   📊 Comparing extracted data with existing tables...")
        comparison = self._compare_extracted_vs_existing(extracted_table, existing_baseline, existing_followup)
        
        # Calcola metriche di accuratezza
        accuracy_metrics = self._calculate_accuracy_metrics(comparison)
        accuracy_category = self._categorize_accuracy(accuracy_metrics['overall_accuracy'])
        
        print(f"   📈 Overall Accuracy: {accuracy_metrics['overall_accuracy']:.1f}% ({accuracy_category})")
        print(f"   📊 Baseline Accuracy: {accuracy_metrics['baseline_accuracy']:.1f}%")
        print(f"   📊 Follow-up Accuracy: {accuracy_metrics['followup_accuracy']:.1f}%")
        
        return {
            'patient_info': patient_info,
            'extracted_table': extracted_table,
            'existing_baseline': existing_baseline,
            'existing_followup': existing_followup,
            'comparison': comparison,
            'accuracy_metrics': accuracy_metrics,
            'accuracy_category': accuracy_category,
            'success': True,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _extract_structured_data_from_anamnesis(self, anamnesis: str) -> Dict[str, Any]:
        """Estrae dati strutturati dall'anamnesi usando OpenAI con prompt ottimizzato"""
        
        # Prompt ottimizzato per l'estrazione
        extraction_prompt = f"""
Sei un esperto in estrazione di dati clinici. Analizza attentamente la seguente anamnesi neurologica e estrai TUTTI i dati strutturati menzionati.

ANAMNESI CLINICA:
{anamnesis}

Estrai i dati per baseline e follow-up a 5 anni e restituisci ESCLUSIVAMENTE un JSON valido con questa struttura:

{{
  "baseline": {{
    "Age": [età baseline come numero],
    "Gender": "[Male/Female]",
    "Race": "[razza esatta come scritta]",
    "Educational level": [anni di istruzione come numero],
    "ApoE4 carrier": "[Negative/Positive (1 allele)/Positive (2 alleli)]",
    "CDR": [valore CDR come numero],
    "MMSE": [punteggio MMSE come numero],
    "ADCS-PACC": [valore ADCS-PACC come numero],
    "RAVLT Trial 1": [punteggio RAVLT come numero],
    "CSF t-tau (pg/ml)": [valore tau totale come numero],
    "CSF p-tau181 (pg/ml)": [valore p-tau181 come numero],
    "CSF Aβ42 (pg/ml)": [valore Aβ42 come numero],
    "CSF Aβ42/Aβ40 ratio": [rapporto come numero decimale],
    "PET PIB SUVR cortex": [valore SUVR come numero decimale],
    "MRI Hippocampus (ml)": [volume ippocampale come numero decimale]
  }},
  "followup_5y": {{
    "Age": [età a 5 anni come numero],
    "Gender": "[Male/Female]",
    "Race": "[razza esatta come scritta]",
    "Educational level": [anni di istruzione come numero],
    "ApoE4 carrier": "[Negative/Positive (1 allele)/Positive (2 alleli)]",
    "CDR": [valore CDR come numero],
    "MMSE": [punteggio MMSE come numero],
    "ADCS-PACC": [valore ADCS-PACC come numero],
    "RAVLT Trial 1": [punteggio RAVLT come numero],
    "CSF t-tau (pg/ml)": [valore tau totale come numero],
    "CSF p-tau181 (pg/ml)": [valore p-tau181 come numero],
    "CSF Aβ42 (pg/ml)": [valore Aβ42 come numero],
    "CSF Aβ42/Aβ40 ratio": [rapporto come numero decimale],
    "PET PIB SUVR cortex": [valore SUVR come numero decimale],
    "MRI Hippocampus (ml)": [volume ippocampale come numero decimale]
  }}
}}

REGOLE CRITICHE:
- Usa null solo se il valore NON è menzionato nell'anamnesi
- Mantieni la precisione esatta dei numeri (es. 1.30, non 1300)
- Per ApoE4: "Negative" se negativo, "Positive (1 allele)" se eterozigote
- Estrai TUTTI i valori numerici menzionati con precisione
- Restituisci SOLO il JSON, nessun testo aggiuntivo

JSON:
"""
        
        # Usa l'agente clinician per l'estrazione
        result = await self.prism_system.agents["clinician"].run(task=extraction_prompt)
        response = result.messages[-1].content if result.messages else ""
        
        # Estrai e valida il JSON
        try:
            # Cerca il JSON nella risposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                extracted_data = json.loads(json_str)
                
                # Valida la struttura
                if 'baseline' not in extracted_data or 'followup_5y' not in extracted_data:
                    raise ValueError("Missing baseline or followup_5y sections")
                
                return extracted_data
            else:
                raise ValueError("No valid JSON found in response")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def _compare_extracted_vs_existing(self, extracted: Dict[str, Any], 
                                     existing_baseline: Dict[str, Any], 
                                     existing_followup: Dict[str, Any]) -> Dict[str, Any]:
        """Confronta dati estratti con quelli esistenti nelle tabelle"""
        comparison = {
            'baseline': {'matches': {}, 'differences': {}},
            'followup': {'matches': {}, 'differences': {}}
        }
        
        # Confronta baseline
        if 'baseline' in extracted:
            for variable in self.table_variables:
                extracted_value = extracted['baseline'].get(variable)
                existing_value = existing_baseline.get(variable)
                
                if self._values_are_equivalent(extracted_value, existing_value):
                    comparison['baseline']['matches'][variable] = {
                        'extracted': extracted_value,
                        'existing': existing_value
                    }
                else:
                    comparison['baseline']['differences'][variable] = {
                        'extracted': extracted_value,
                        'existing': existing_value,
                        'type': self._classify_difference_type(extracted_value, existing_value)
                    }
        
        # Confronta follow-up
        if 'followup_5y' in extracted:
            for variable in self.table_variables:
                extracted_value = extracted['followup_5y'].get(variable)
                existing_value = existing_followup.get(variable)
                
                if self._values_are_equivalent(extracted_value, existing_value):
                    comparison['followup']['matches'][variable] = {
                        'extracted': extracted_value,
                        'existing': existing_value
                    }
                else:
                    comparison['followup']['differences'][variable] = {
                        'extracted': extracted_value,
                        'existing': existing_value,
                        'type': self._classify_difference_type(extracted_value, existing_value)
                    }
        
        return comparison
    
    def _values_are_equivalent(self, extracted_value: Any, existing_value: Any) -> bool:
        """Verifica equivalenza tra valori estratti ed esistenti con tolleranze appropriate"""
        # Entrambi None/null
        if extracted_value is None and existing_value is None:
            return True
        
        # Uno None, l'altro no
        if extracted_value is None or existing_value is None:
            return False
        
        # Confronto numerico con tolleranza appropriata
        if isinstance(extracted_value, (int, float)) and isinstance(existing_value, (int, float)):
            # Tolleranza relativa per valori grandi, assoluta per piccoli
            if abs(existing_value) > 1:
                tolerance = abs(existing_value) * 0.05  # 5% di tolleranza relativa
            else:
                tolerance = 0.1  # Tolleranza assoluta per valori piccoli
            return abs(extracted_value - existing_value) <= tolerance
        
        # Confronto stringhe (normalizzate)
        if isinstance(extracted_value, str) and isinstance(existing_value, str):
            extracted_norm = extracted_value.lower().strip()
            existing_norm = existing_value.lower().strip()
            
            # Gestisci casi speciali
            if extracted_norm == "negative" and existing_norm == "false":
                return True
            if "positive" in extracted_norm and existing_norm == "true":
                return True
            if "caucasian" in extracted_norm and "caucasian" in existing_norm:
                return True
                
            return extracted_norm == existing_norm
        
        # Confronto booleano
        if isinstance(extracted_value, bool) and isinstance(existing_value, bool):
            return extracted_value == existing_value
        
        # Fallback: confronto stringa
        return str(extracted_value).lower() == str(existing_value).lower()
    
    def _classify_difference_type(self, extracted_value: Any, existing_value: Any) -> str:
        """Classifica il tipo di differenza tra valori"""
        if extracted_value is None:
            return "missing_extraction"
        if existing_value is None:
            return "extra_extraction"
        if isinstance(extracted_value, (int, float)) and isinstance(existing_value, (int, float)):
            return "numerical_difference"
        if isinstance(extracted_value, str) and isinstance(existing_value, str):
            return "format_difference"
        return "type_mismatch"
    
    def _calculate_accuracy_metrics(self, comparison: Dict[str, Any]) -> Dict[str, float]:
        """Calcola metriche dettagliate di accuratezza"""
        total_variables = len(self.table_variables)
        
        # Accuratezza baseline
        baseline_matches = len(comparison['baseline']['matches'])
        baseline_accuracy = (baseline_matches / total_variables) * 100
        
        # Accuratezza follow-up
        followup_matches = len(comparison['followup']['matches'])
        followup_accuracy = (followup_matches / total_variables) * 100
        
        # Accuratezza complessiva
        total_matches = baseline_matches + followup_matches
        total_possible = total_variables * 2
        overall_accuracy = (total_matches / total_possible) * 100
        
        return {
            'baseline_accuracy': baseline_accuracy,
            'followup_accuracy': followup_accuracy,
            'overall_accuracy': overall_accuracy,
            'baseline_matches': baseline_matches,
            'followup_matches': followup_matches,
            'total_matches': total_matches,
            'total_possible': total_possible
        }
    
    def _categorize_accuracy(self, accuracy: float) -> str:
        """Categorizza l'accuratezza in base alle soglie definite"""
        if accuracy >= self.accuracy_thresholds['excellent']:
            return "EXCELLENT"
        elif accuracy >= self.accuracy_thresholds['good']:
            return "GOOD"
        elif accuracy >= self.accuracy_thresholds['acceptable']:
            return "ACCEPTABLE"
        elif accuracy >= self.accuracy_thresholds['poor']:
            return "POOR"
        else:
            return "VERY_POOR"
    
    def _analyze_validation_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizza i risultati complessivi della validazione"""
        print("=" * 80)
        print("📈 COMPREHENSIVE VALIDATION ANALYSIS")
        print("=" * 80)
        
        successful_results = [r for r in results if r.get('success', False)]
        
        if not successful_results:
            print("❌ No successful validations to analyze")
            return {'success': False, 'message': 'No successful validations'}
        
        # Calcola statistiche aggregate
        accuracies = [r['accuracy_metrics']['overall_accuracy'] for r in successful_results]
        baseline_accuracies = [r['accuracy_metrics']['baseline_accuracy'] for r in successful_results]
        followup_accuracies = [r['accuracy_metrics']['followup_accuracy'] for r in successful_results]
        
        average_accuracy = sum(accuracies) / len(accuracies)
        average_baseline = sum(baseline_accuracies) / len(baseline_accuracies)
        average_followup = sum(followup_accuracies) / len(followup_accuracies)
        
        # Conta le categorie di accuratezza
        categories = [r['accuracy_category'] for r in successful_results]
        category_counts = {cat: categories.count(cat) for cat in set(categories)}
        
        print(f"📊 Average Overall Accuracy: {average_accuracy:.1f}%")
        print(f"📊 Average Baseline Accuracy: {average_baseline:.1f}%")
        print(f"📊 Average Follow-up Accuracy: {average_followup:.1f}%")
        print(f"📊 Total Patients Validated: {len(successful_results)}")
        print()
        
        print("🏆 Accuracy Categories:")
        for category, count in category_counts.items():
            print(f"   {category}: {count} patients")
        print()
        
        # Dettaglio per paziente
        print("👥 Patient Details:")
        for result in successful_results:
            patient_name = result['patient_info']['patient_name']
            accuracy = result['accuracy_metrics']['overall_accuracy']
            category = result['accuracy_category']
            
            status_emoji = {
                'EXCELLENT': '🌟',
                'GOOD': '✅',
                'ACCEPTABLE': '⚠️',
                'POOR': '❌',
                'VERY_POOR': '💀'
            }.get(category, '❓')
            
            print(f"   {status_emoji} {patient_name}: {accuracy:.1f}% ({category})")
            
            # Mostra principali differenze
            baseline_diffs = len(result['comparison']['baseline']['differences'])
            followup_diffs = len(result['comparison']['followup']['differences'])
            if baseline_diffs > 0 or followup_diffs > 0:
                print(f"      📉 Differences: Baseline={baseline_diffs}, Follow-up={followup_diffs}")
        
        analysis_summary = {
            'success': True,
            'total_patients': len(successful_results),
            'average_accuracy': average_accuracy,
            'average_baseline_accuracy': average_baseline,
            'average_followup_accuracy': average_followup,
            'category_distribution': category_counts,
            'validation_quality': self._categorize_accuracy(average_accuracy)
        }
        
        print()
        print(f"🎯 Overall Validation Quality: {analysis_summary['validation_quality']}")
        print()
        
        return analysis_summary
    
    def save_validation_results(self, results: List[Dict[str, Any]], analysis: Dict[str, Any], 
                              filename: str = "anamnesis_validation_results.json"):
        """Salva i risultati completi della validazione"""
        output_data = {
            'metadata': {
                'validator_version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'model_used': self.model_name,
                'total_variables_per_timepoint': len(self.table_variables),
                'accuracy_thresholds': self.accuracy_thresholds
            },
            'analysis_summary': analysis,
            'detailed_results': results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Complete validation results saved to: {filename}")
        return filename

async def main():
    """Funzione principale per eseguire la validazione completa anamnesi→strutturati"""
    validator = AnamnesisTaxtructuredValidator()
    
    try:
        print("🚀 Starting Anamnesis to Structured Data Validation...")
        print()
        
        # Esegui validazione completa
        results, analysis = await validator.validate_all_anamnesis()
        
        # Salva risultati
        output_file = validator.save_validation_results(results, analysis)
        
        print("=" * 80)
        print("🎉 VALIDATION PROCESS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"📁 Results saved to: {output_file}")
        print(f"🎯 Validation Quality: {analysis.get('validation_quality', 'Unknown')}")
        print(f"📊 Average Accuracy: {analysis.get('average_accuracy', 0):.1f}%")
        
        return results, analysis
        
    except Exception as e:
        print(f"💥 Critical error during validation: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    asyncio.run(main())
