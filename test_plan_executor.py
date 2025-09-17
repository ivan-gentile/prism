#!/usr/bin/env python3
"""
Test Plan Executor - Esegue il test plan completo su tutti i pazienti
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

from test_plan_parser import PatientDataParser
from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.data.patient_model import PatientData

class TestPlanExecutor:
    """Esecutore principale del test plan"""
    
    def __init__(self, markdown_file: str = "prism_ad/agents/Campione-utenti.md"):
        self.markdown_file = markdown_file
        self.parser = PatientDataParser(markdown_file)
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
        """Esegue il test plan completo su tutti i pazienti"""
        print("=" * 80)
        print("PRISM TEST PLAN EXECUTOR")
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
        
        # 3. Esegui test su ogni paziente
        for i, patient_info in enumerate(patients_data, 1):
            print(f"Step 2.{i}: Testing patient {patient_info['patient_name']}...")
            result = await self._test_single_patient(patient_info)
            self.results.append(result)
            print(f"Completed patient {i}/{len(patients_data)}")
            print()
        
        # 4. Chiudi sistema
        await self.prism_system.close()
        
        print("=" * 80)
        print("TEST PLAN EXECUTION COMPLETED")
        print("=" * 80)
        
        return self.results
    
    async def _test_single_patient(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue il test su un singolo paziente"""
        patient_data = patient_info['patient_data']
        expected_risk = patient_info['expected_risk']
        
        print(f"  Patient: {patient_info['patient_name']}")
        print(f"  Age: {patient_data.age}, ApoE4: {patient_data.apoe4_copies}")
        print(f"  Expected Risk: {expected_risk['risk_percentage']*100:.1f}% ({expected_risk['risk_category']})")
        
        # Esegui i 3 agenti clinici
        print("  Running clinical agents...")
        
        try:
            # Clinician Agent (GPT-4o-mini)
            clinician_result = await self.prism_system._run_clinician_agent(patient_data)
            print("    ✅ Clinician Agent completed")
            
            # Model GPT4o Agent
            clinician_gpt4o_result = await self.prism_system._run_clinician_gpt4o_agent(patient_data)
            print("    ✅ Model GPT4o Agent completed")
            
            # Clinician FASTWEB Agent
            clinician_fastweb_result = await self.prism_system._run_clinician_fastweb_agent(patient_data)
            print("    ✅ Clinician FASTWEB Agent completed")
            
        except Exception as e:
            print(f"    ❌ Error running clinical agents: {e}")
            return {
                'patient_info': patient_info,
                'error': str(e),
                'success': False
            }
        
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
        
        return {
            'patient_info': patient_info,
            'expected_risk': expected_risk,
            'clinical_results': {
                'clinician': clinician_result,
                'clinician_gpt4o': clinician_gpt4o_result,
                'clinician_fastweb': clinician_fastweb_result
            },
            'consensus_result': consensus_result,
            'final_result': final_result,
            'success': True
        }
    
    async def _run_consensus_agent(self, clinician_result: str, clinician_gpt4o_result: str, 
                                 clinician_fastweb_result: str) -> str:
        """Esegue il Consensus Agent per valutare i risultati"""
        
        # Crea input per il consensus agent
        consensus_input = f"""
Analizza i risultati dei tre agenti clinici e fornisci un consenso:

AGENTE 1 (Clinician - GPT-4o-mini):
{clinician_result}

AGENTE 2 (Model GPT4o - GPT-4o):
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
        
        # Crea input per il final response agent
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
    
    def save_results(self, filename: str = "test_plan_results.json"):
        """Salva i risultati in un file JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        print(f"Results saved to {filename}")

async def main():
    """Funzione principale per eseguire il test plan"""
    executor = TestPlanExecutor()
    
    try:
        results = await executor.run_complete_test_plan()
        
        # Salva risultati
        executor.save_results()
        
        # Stampa sommario
        print("\n" + "=" * 80)
        print("TEST PLAN SUMMARY")
        print("=" * 80)
        
        successful_tests = sum(1 for r in results if r.get('success', False))
        total_tests = len(results)
        
        print(f"Total patients tested: {total_tests}")
        print(f"Successful tests: {successful_tests}")
        print(f"Failed tests: {total_tests - successful_tests}")
        print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
        
        if successful_tests > 0:
            print("\nPatient Results:")
            for result in results:
                if result.get('success', False):
                    patient_name = result['patient_info']['patient_name']
                    expected_risk = result['expected_risk']['risk_percentage'] * 100
                    print(f"  ✅ {patient_name}: Expected {expected_risk:.1f}%")
                else:
                    patient_name = result['patient_info']['patient_name']
                    print(f"  ❌ {patient_name}: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"Error executing test plan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
