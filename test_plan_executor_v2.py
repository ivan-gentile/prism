#!/usr/bin/env python3
"""
Test Plan Executor V2 - Esegue predizioni sui dati baseline e confronta con Outcome
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

from test_plan_parser_v2 import PatientDataParserV2
from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.data.patient_model import PatientData

class TestPlanExecutorV2:
    """Esecutore del test plan V2 con validazione Outcome"""
    
    def __init__(self, markdown_file: str = "prism_ad/agents/Campione-utenti.md"):
        self.markdown_file = markdown_file
        self.parser = PatientDataParserV2(markdown_file)
        self.prism_system = None
        self.results = []
        
        # Configurazione ambiente
        self.model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
        self.base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")
    
    async def initialize_system(self):
        """Inizializza il sistema PRISM"""
        print("Initializing PRISM Agent System...")
        self.prism_system = PRISMAgentSystem(
            model_name=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url
        )
        await self.prism_system.initialize_agents()
        print("PRISM system initialized successfully")
        print(f"Available agents: {list(self.prism_system.agents.keys())}")
    
    async def run_complete_test_plan(self) -> List[Dict[str, Any]]:
        """Esegue il test plan completo con validazione Outcome"""
        print("=" * 80)
        print("PRISM TEST PLAN EXECUTOR V2 - OUTCOME VALIDATION")
        print("=" * 80)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Parse dei dati pazienti
        print("Step 1: Parsing patient data...")
        patients_data = self.parser.parse_all_patients()
        print(f"Parsed {len(patients_data)} patients")
        print()
        
        # 2. Inizializza sistema PRISM
        await self.initialize_system()
        print()
        
        # 3. Esegui predizioni su ogni paziente
        for i, patient_info in enumerate(patients_data, 1):
            print(f"Step 2.{i}: Testing patient {patient_info['patient_name']}...")
            result = await self._test_single_patient(patient_info)
            self.results.append(result)
            print(f"Completed patient {i}/{len(patients_data)}")
            print()
        
        # 4. Chiudi sistema
        await self.prism_system.close()
        
        # 5. Analizza risultati
        accuracy_report = self._analyze_accuracy()
        
        print("=" * 80)
        print("TEST PLAN EXECUTION COMPLETED")
        print("=" * 80)
        
        return self.results
    
    async def _test_single_patient(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue predizione su un singolo paziente e confronta con Outcome"""
        patient_data = patient_info['patient_data']
        expected_outcome = patient_info['outcome']
        
        print(f"  Patient: {patient_info['patient_name']} ({patient_data.age} anni)")
        print(f"  ApoE4: {patient_data.apoe4_copies}, MMSE: {patient_data.mmse_score}")
        print(f"  Expected Outcome: {expected_outcome['diagnosis']} (Progression: {expected_outcome['progression']})")
        
        # Esegui i 3 agenti clinici
        print("  Running clinical agents...")
        
        try:
            # Clinician Agent (GPT-4o-mini)
            clinician_result = await self.prism_system._run_clinician_agent(patient_data)
            clinician_risk = self._extract_risk_from_result(clinician_result)
            print(f"    ✅ Clinician Agent: {clinician_risk*100:.1f}%")
            
            # Clinician GPT4o Agent
            clinician_gpt4o_result = await self.prism_system._run_clinician_gpt4o_agent(patient_data)
            clinician_gpt4o_risk = self._extract_risk_from_result(clinician_gpt4o_result)
            print(f"    ✅ Clinician GPT4o: {clinician_gpt4o_risk*100:.1f}%")
            
            # Clinician FASTWEB Agent
            clinician_fastweb_result = await self.prism_system._run_clinician_fastweb_agent(patient_data)
            clinician_fastweb_risk = self._extract_risk_from_result(clinician_fastweb_result)
            print(f"    ✅ Clinician FASTWEB: {clinician_fastweb_risk*100:.1f}%")
            
        except Exception as e:
            print(f"    ❌ Error running clinical agents: {e}")
            return {
                'patient_info': patient_info,
                'error': str(e),
                'success': False
            }
        
        # Calcola rischio medio
        average_risk = (clinician_risk + clinician_gpt4o_risk + clinician_fastweb_risk) / 3
        print(f"  Average Risk: {average_risk*100:.1f}%")
        
        # Esegui Consensus Agent
        print("  Running consensus agent...")
        try:
            consensus_result = await self._run_consensus_agent(
                clinician_result, clinician_gpt4o_result, clinician_fastweb_result
            )
            print("    ✅ Consensus Agent completed")
        except Exception as e:
            print(f"    ❌ Error running consensus agent: {e}")
            consensus_result = f"Error: {e}"
        
        # Esegui Final Response Agent
        print("  Running final response agent...")
        try:
            final_result = await self._run_final_response_agent(consensus_result, patient_info)
            print("    ✅ Final Response Agent completed")
        except Exception as e:
            print(f"    ❌ Error running final response agent: {e}")
            final_result = f"Error: {e}"
        
        # Valuta accuratezza predizione
        prediction_accuracy = self._evaluate_prediction(average_risk, expected_outcome)
        print(f"  Prediction Accuracy: {prediction_accuracy['accuracy_category']} ({prediction_accuracy['accuracy_score']:.1f}%)")
        
        return {
            'patient_info': patient_info,
            'expected_outcome': expected_outcome,
            'clinical_results': {
                'clinician': {'result': clinician_result, 'risk': clinician_risk},
                'clinician_gpt4o': {'result': clinician_gpt4o_result, 'risk': clinician_gpt4o_risk},
                'clinician_fastweb': {'result': clinician_fastweb_result, 'risk': clinician_fastweb_risk}
            },
            'average_risk': average_risk,
            'consensus_result': consensus_result,
            'final_result': final_result,
            'prediction_accuracy': prediction_accuracy,
            'success': True
        }
    
    def _extract_risk_from_result(self, result: str) -> float:
        """Estrae il valore di rischio dal risultato JSON"""
        try:
            # Cerca il pattern "risk_5y": 0.XX nel JSON
            import re
            risk_match = re.search(r'"risk_5y":\s*([0-9.]+)', result)
            if risk_match:
                return float(risk_match.group(1))
            return 0.0
        except:
            return 0.0
    
    def _evaluate_prediction(self, predicted_risk: float, expected_outcome: Dict[str, Any]) -> Dict[str, Any]:
        """Valuta l'accuratezza della predizione confrontando con l'Outcome"""
        expected_progression = expected_outcome['progression']
        
        # Definisci soglie di rischio
        # Rischio basso: < 20% → no progression expected
        # Rischio alto: >= 20% → progression expected
        risk_threshold = 0.20
        
        predicted_progression = predicted_risk >= risk_threshold
        
        # Calcola accuratezza
        is_correct = predicted_progression == expected_progression
        
        if is_correct:
            accuracy_score = 100.0
            accuracy_category = "CORRECT"
        else:
            # Calcola quanto è distante dalla soglia
            if expected_progression and predicted_risk < risk_threshold:
                # Doveva predire progressione ma ha predetto basso rischio
                distance = risk_threshold - predicted_risk
                accuracy_score = max(0, 100 - (distance * 500))  # Penalizza la sottostima
                accuracy_category = "UNDERESTIMATED"
            elif not expected_progression and predicted_risk >= risk_threshold:
                # Doveva predire no progressione ma ha predetto alto rischio
                distance = predicted_risk - risk_threshold
                accuracy_score = max(0, 100 - (distance * 500))  # Penalizza la sovrastima
                accuracy_category = "OVERESTIMATED"
            else:
                accuracy_score = 0.0
                accuracy_category = "INCORRECT"
        
        return {
            'predicted_risk': predicted_risk,
            'predicted_progression': predicted_progression,
            'expected_progression': expected_progression,
            'is_correct': is_correct,
            'accuracy_score': accuracy_score,
            'accuracy_category': accuracy_category,
            'risk_threshold': risk_threshold
        }
    
    async def _run_consensus_agent(self, clinician_result: str, clinician_gpt4o_result: str, 
                                 clinician_fastweb_result: str) -> str:
        """Esegue il Consensus Agent per valutare i risultati"""
        
        consensus_input = f"""
Analizza i risultati dei tre agenti clinici e fornisci un consenso:

AGENTE 1 (Clinician - GPT-4o-mini):
{clinician_result}

AGENTE 2 (Clinician GPT4o - GPT-4o):
{clinician_gpt4o_result}

AGENTE 3 (Clinician FASTWEB - Llama-3.3-70B):
{clinician_fastweb_result}

Fornisci un'analisi di consenso che includa:
1. Convergenze e divergenze tra i risultati
2. Stima del rischio di consenso
3. Livello di accordo tra gli agenti
4. Giustificazione della scelta del consenso
"""
        
        result = await self.prism_system.agents["consensus"].run(task=consensus_input)
        return result.messages[-1].content if result.messages else ""
    
    async def _run_final_response_agent(self, consensus_result: str, patient_info: Dict[str, Any]) -> str:
        """Esegue il Final Response Agent per la sintesi finale"""
        
        final_input = f"""
Trasforma il risultato del consenso in un report narrativo professionale in italiano per il neurologo curante.

RISULTATO DEL CONSENSO:
{consensus_result}

INFORMAZIONI PAZIENTE:
- Nome: {patient_info['patient_name']}
- Età: {patient_info['patient_data'].age}
- ApoE4: {patient_info['patient_data'].apoe4_copies}
- Anamnesi: {patient_info['doctor_anamnesis'][:200]}...

Crea un report professionale che includa:
1. Analisi clinica del paziente
2. Stima del rischio a 5 anni
3. Raccomandazioni per il monitoraggio
4. Comunicazione per il paziente
"""
        
        result = await self.prism_system.agents["final_response"].run(task=final_input)
        return result.messages[-1].content if result.messages else ""
    
    def _analyze_accuracy(self) -> Dict[str, Any]:
        """Analizza l'accuratezza complessiva del sistema"""
        if not self.results:
            return {}
        
        successful_results = [r for r in self.results if r.get('success', False)]
        
        if not successful_results:
            return {'overall_accuracy': 0.0, 'total_tests': 0}
        
        correct_predictions = sum(1 for r in successful_results 
                                if r['prediction_accuracy']['is_correct'])
        
        total_tests = len(successful_results)
        overall_accuracy = (correct_predictions / total_tests) * 100
        
        # Calcola accuratezza per categoria
        progression_cases = [r for r in successful_results 
                           if r['expected_outcome']['progression']]
        no_progression_cases = [r for r in successful_results 
                              if not r['expected_outcome']['progression']]
        
        progression_accuracy = 0.0
        if progression_cases:
            correct_progression = sum(1 for r in progression_cases 
                                    if r['prediction_accuracy']['is_correct'])
            progression_accuracy = (correct_progression / len(progression_cases)) * 100
        
        no_progression_accuracy = 0.0
        if no_progression_cases:
            correct_no_progression = sum(1 for r in no_progression_cases 
                                       if r['prediction_accuracy']['is_correct'])
            no_progression_accuracy = (correct_no_progression / len(no_progression_cases)) * 100
        
        accuracy_report = {
            'total_tests': total_tests,
            'correct_predictions': correct_predictions,
            'overall_accuracy': overall_accuracy,
            'progression_cases': len(progression_cases),
            'progression_accuracy': progression_accuracy,
            'no_progression_cases': len(no_progression_cases),
            'no_progression_accuracy': no_progression_accuracy
        }
        
        print("\n" + "=" * 80)
        print("ACCURACY ANALYSIS")
        print("=" * 80)
        print(f"Overall Accuracy: {overall_accuracy:.1f}% ({correct_predictions}/{total_tests})")
        print(f"Progression Cases: {progression_accuracy:.1f}% ({len(progression_cases)} cases)")
        print(f"No Progression Cases: {no_progression_accuracy:.1f}% ({len(no_progression_cases)} cases)")
        
        return accuracy_report
    
    def save_results(self, filename: str = "test_plan_results_v2.json"):
        """Salva i risultati in un file JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        print(f"Results saved to {filename}")

async def main():
    """Funzione principale per eseguire il test plan V2"""
    executor = TestPlanExecutorV2()
    
    try:
        results = await executor.run_complete_test_plan()
        
        # Salva risultati
        executor.save_results()
        
        # Stampa dettaglio risultati
        print("\n" + "=" * 80)
        print("DETAILED RESULTS")
        print("=" * 80)
        
        for result in results:
            if result.get('success', False):
                patient_name = result['patient_info']['patient_name']
                expected = result['expected_outcome']
                accuracy = result['prediction_accuracy']
                avg_risk = result['average_risk'] * 100
                
                status = "✅" if accuracy['is_correct'] else "❌"
                print(f"{status} {patient_name}:")
                print(f"   Expected: {expected['diagnosis']} (Progression: {expected['progression']})")
                print(f"   Predicted Risk: {avg_risk:.1f}%")
                print(f"   Accuracy: {accuracy['accuracy_category']} ({accuracy['accuracy_score']:.1f}%)")
                print()
        
    except Exception as e:
        print(f"Error executing test plan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
