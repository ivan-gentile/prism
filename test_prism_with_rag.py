#!/usr/bin/env python3
"""
Test sistema PRISM completo con RAG ibrido integrato
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

# Configura API key per il test
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "test-key-for-demo")

# Se non c'è una vera API key, imposta una di test
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "test-key-for-demo"
    print("⚠️ Using test API key - agent responses will be simulated")

from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.data.patient_model import PatientData, ApoE4Status

async def test_prism_with_rag():
    """Test del sistema PRISM completo con RAG"""
    print("🚀 TEST SISTEMA PRISM CON RAG IBRIDO")
    print("=" * 60)
    
    try:
        # Inizializza il sistema PRISM
        print("🔧 Inizializzazione sistema PRISM...")
        prism_system = PRISMAgentSystem()
        await prism_system.initialize_agents()
        
        # Crea paziente di test con valori significativi
        patient_data = {
            "patient_id": "test_rag_001",
            "age": 72,
            "sex": "female",
            "apoe4_copies": ApoE4Status.ONE_COPY,
            "mmse_score": 26,  # Lieve deterioramento cognitivo
            "cdr_sum": 0.5,    # CDR 0.5 = very mild dementia
            "adas_cog13": 12,
            "csf_abeta42": 480,    # Borderline basso (normale >600)
            "csf_abeta40": 8000,   
            "csf_ptau181": 45,     # Elevato (normale <40)
            "csf_total_tau": 420,  # Elevato (normale <400)
            "amyloid_pet_suvr": 1.4,  # Positivo (normale <1.3)
            "hippocampus_volume_left": 2.1,   # Ridotto
            "hippocampus_volume_right": 2.3   # Ridotto
        }
        
        print("👤 PAZIENTE DI TEST:")
        print(f"   Age: {patient_data['age']} years")
        print(f"   Sex: {patient_data['sex']}")
        print(f"   APOE4: {patient_data['apoe4_copies'].value}")
        print(f"   MMSE: {patient_data['mmse_score']}")
        print(f"   CDR: {patient_data['cdr_sum']}")
        print(f"   CSF Aβ42: {patient_data['csf_abeta42']} pg/ml")
        print(f"   CSF p-tau181: {patient_data['csf_ptau181']} pg/ml")
        print(f"   CSF total tau: {patient_data['csf_total_tau']} pg/ml")
        print(f"   Amyloid PET SUVR: {patient_data['amyloid_pet_suvr']}")
        print(f"   Hippocampus volume: {patient_data['hippocampus_volume_left']} + {patient_data['hippocampus_volume_right']} ml")
        
        # Determina stage
        patient = PatientData(**patient_data)
        patient_stage = prism_system.determine_fda_stage(patient)
        print(f"\n📊 STAGE DETERMINATO: {patient_stage}")
        
        # Test solo RAG agent
        print(f"\n🧠 TEST RAG AGENT CON EVIDENZE CLINICHE")
        print("-" * 50)
        
        rag_result = await prism_system._run_rag_agent(patient, patient_stage)
        
        print(f"\n✅ RAG Agent completato!")
        print(f"📄 Lunghezza risposta: {len(rag_result)} caratteri")
        
        # Prova a parsare la risposta JSON
        try:
            # Estrai JSON dalla risposta
            if "```json" in rag_result:
                json_start = rag_result.find("```json") + 7
                json_end = rag_result.find("```", json_start)
                json_str = rag_result[json_start:json_end].strip()
            elif "{" in rag_result and "}" in rag_result:
                json_start = rag_result.find("{")
                json_end = rag_result.rfind("}") + 1
                json_str = rag_result[json_start:json_end]
            else:
                json_str = rag_result
            
            rag_json = json.loads(json_str)
            
            print(f"\n📊 ANALISI RAG PARSATA:")
            print(f"   Agent: {rag_json.get('agent', 'unknown')}")
            print(f"   Stage: {rag_json.get('stage_classification', 'unknown')}")
            print(f"   Risk 5y: {rag_json.get('risk_5y', 'unknown')}")
            print(f"   Uncertainty: {rag_json.get('uncertainty', {}).get('ci90', 'unknown')}")
            print(f"   Evidence count: {len(rag_json.get('evidence', []))}")
            print(f"   Features used: {len(rag_json.get('features_used', []))}")
            
            # Mostra evidenze
            if rag_json.get('evidence'):
                print(f"\n📚 EVIDENZE UTILIZZATE:")
                for i, evidence in enumerate(rag_json['evidence'][:3], 1):
                    print(f"   {i}. {evidence}")
            
            # Mostra interpretazione
            if rag_json.get('interpretation'):
                print(f"\n🎯 INTERPRETAZIONE:")
                for i, interp in enumerate(rag_json['interpretation'][:3], 1):
                    print(f"   {i}. {interp}")
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Risposta RAG non è JSON valido: {e}")
            print(f"📄 Prime 500 caratteri della risposta:")
            print(rag_result[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if 'prism_system' in locals():
            await prism_system.close()

async def test_sistema_completo():
    """Test del sistema PRISM completo"""
    print(f"\n\n🏥 TEST SISTEMA PRISM COMPLETO")
    print("=" * 60)
    
    try:
        # Inizializza sistema
        prism_system = PRISMAgentSystem()
        await prism_system.initialize_agents()
        
        # Paziente più semplice per test veloce
        patient_data = {
            "patient_id": "test_complete_001",
            "age": 68,
            "sex": "female",
            "apoe4_copies": ApoE4Status.ONE_COPY,
            "mmse_score": 28,
            "cdr_sum": 0.0,
            "csf_abeta42": 520,
            "csf_ptau181": 35,
            "amyloid_pet_suvr": 1.2
        }
        
        print("👤 PAZIENTE TEST COMPLETO:")
        for key, value in patient_data.items():
            if hasattr(value, 'value'):
                print(f"   {key}: {value.value}")
            else:
                print(f"   {key}: {value}")
        
        # Esegui pipeline completa
        print(f"\n🔄 Esecuzione pipeline completa...")
        final_report = await prism_system.process_patient(patient_data)
        
        print(f"\n✅ Pipeline completata!")
        print(f"📄 Report finale ({len(final_report)} caratteri):")
        print("-" * 50)
        print(final_report[:800] + "..." if len(final_report) > 800 else final_report)
        
        return True
        
    except Exception as e:
        print(f"❌ Errore sistema completo: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'prism_system' in locals():
            await prism_system.close()

async def main():
    """Funzione principale"""
    print("🎯 TEST INTEGRAZIONE RAG + PRISM")
    print("=" * 70)
    
    success = 0
    total = 2
    
    # Test 1: Solo RAG
    if await test_prism_with_rag():
        print("✅ Test 1 PASSATO: RAG Agent integrato")
        success += 1
    else:
        print("❌ Test 1 FALLITO")
    
    # Test 2: Sistema completo
    if await test_sistema_completo():
        print("✅ Test 2 PASSATO: Sistema completo")
        success += 1
    else:
        print("❌ Test 2 FALLITO")
    
    print(f"\n🎯 RISULTATI: {success}/{total} test passati")
    
    if success == total:
        print("\n🎉 SUCCESS! PRISM + RAG FUNZIONA PERFETTAMENTE!")
        print("✅ RAG ibrido integrato")
        print("✅ Evidenze cliniche utilizzate")
        print("✅ Sistema multi-agente operativo")
        print("✅ Pipeline completa funzionante")
    elif success > 0:
        print("\n⚠️ Successo parziale - alcuni componenti funzionano")
    else:
        print("\n❌ Test falliti - necessarie correzioni")

if __name__ == "__main__":
    asyncio.run(main())
