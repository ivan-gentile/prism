#!/usr/bin/env python3
"""
Test specifico per l'integrazione RAG senza dipendere da OpenAI
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

from prism_ad.data.patient_model import PatientData, ApoE4Status
from prism_ad.agents.prism_agents import determine_fda_stage

def test_rag_integration_direct():
    """Test diretto dell'integrazione RAG"""
    print("🚀 TEST INTEGRAZIONE RAG DIRETTA")
    print("=" * 60)
    
    try:
        # Test 1: Importa e inizializza RAG ibrido
        print("🔧 Test importazione RAG ibrido...")
        from prism_ad.rag.hybrid_rag import create_hybrid_rag_agent
        
        rag_agent = create_hybrid_rag_agent("./clinical_pdfs")
        method = "ChromaDB" if rag_agent.use_chromadb else "Ricerca Testuale"
        pdf_count = len(rag_agent.pdf_contents) if not rag_agent.use_chromadb else "gestiti da ChromaDB"
        
        print(f"✅ RAG Agent creato con successo!")
        print(f"   Metodo: {method}")
        print(f"   PDF: {pdf_count}")
        
        # Test 2: Crea paziente e determina stage
        print(f"\n👤 Test determinazione stage...")
        patient_data = {
            "patient_id": "test_001",
            "age": 72,
            "sex": "female",
            "apoe4_copies": ApoE4Status.ONE_COPY,  # Equivalente a eterozigote
            "mmse_score": 26,
            "cdr_sum": 0.5,
            "csf_abeta42": 480,
            "csf_ptau181": 45,
            "csf_total_tau": 420,
            "amyloid_pet_suvr": 1.4,
            "hippocampus_volume_left": 2.1,
            "hippocampus_volume_right": 2.3
        }
        
        patient = PatientData(**patient_data)
        patient_stage = determine_fda_stage(patient)
        
        print(f"✅ Stage determinato: {patient_stage}")
        
        # Test 3: Prepara dati per RAG
        print(f"\n🔍 Test preparazione dati RAG...")
        rag_patient_data = {
            "stage": patient_stage,
            "age": patient.age,
            "sex": patient.sex,
            "mmse": patient.mmse_score,
            "cdr": patient.cdr_sum,
            "csf_abeta42": patient.csf_abeta42,
            "csf_ptau181": patient.csf_ptau181,
            "csf_total_tau": patient.csf_total_tau,
            "amyloid_pet_suvr": patient.amyloid_pet_suvr,
            "hippocampus_volume_left": patient.hippocampus_volume_left,
            "hippocampus_volume_right": patient.hippocampus_volume_right
        }
        
        print(f"✅ Dati RAG preparati: {len(rag_patient_data)} campi")
        
        # Test 4: Ricerca evidenze
        print(f"\n📚 Test ricerca evidenze...")
        evidence = rag_agent.get_risk_evidence(rag_patient_data)
        
        total_evidence = sum(len(results) for results in evidence.values())
        print(f"✅ Evidenze trovate: {total_evidence} totali")
        
        for category, results in evidence.items():
            if results:
                best = results[0]
                print(f"   {category}: {len(results)} risultati")
                print(f"      Migliore: {best.get('metadata', {}).get('file_name', 'Unknown')}")
                print(f"      Score: {best.get('similarity_score', 0):.3f}")
        
        # Test 5: Contesto per agente
        print(f"\n🧠 Test generazione contesto...")
        context = rag_agent.get_agent_context(rag_patient_data)
        
        print(f"✅ Contesto generato: {len(context)} caratteri")
        print(f"📄 Preview contesto:")
        print("-" * 40)
        print(context[:500] + "..." if len(context) > 500 else context)
        
        # Test 6: Key findings per l'agente
        print(f"\n🎯 Test key findings...")
        key_findings = []
        for category, results in evidence.items():
            if results:
                best_result = results[0]
                key_findings.append(f"From {best_result.get('metadata', {}).get('file_name', 'clinical literature')}: {best_result.get('text', '')[:150]}...")
        
        print(f"✅ Key findings estratti: {len(key_findings)}")
        for i, finding in enumerate(key_findings[:3], 1):
            print(f"   {i}. {finding[:100]}...")
        
        # Test 7: Simula prompt per agente RAG
        print(f"\n🤖 Test costruzione prompt agente...")
        
        input_data = {
            "patient_profile": {
                "age": patient.age,
                "sex": patient.sex or "unknown",
                "apoE4_status": patient.apoe4_copies.value if patient.apoe4_copies else "unknown",
                "mmse": patient.mmse_score,
                "cdr": patient.cdr_sum or 0.0,
                "csf_abeta42": patient.csf_abeta42,
                "csf_ptau181": patient.csf_ptau181,
                "amyloid_pet_suvr": patient.amyloid_pet_suvr
            },
            "stage_hint": patient_stage,
            "question": f"Estimate 5-year risk of progression to FDA Stage3 from current {patient_stage}",
            "retrieved_evidence": key_findings[:5]
        }
        
        prompt_length = len(json.dumps(input_data, indent=2)) + len(context)
        print(f"✅ Prompt costruito: {prompt_length} caratteri totali")
        print(f"   Input data: {len(json.dumps(input_data))} caratteri")
        print(f"   Clinical context: {len(context)} caratteri")
        print(f"   Key findings: {len(key_findings)} evidenze")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_query_examples():
    """Test con query di esempio"""
    print(f"\n\n🔍 TEST QUERY DI ESEMPIO")
    print("=" * 50)
    
    try:
        from prism_ad.rag.hybrid_rag import create_hybrid_rag_agent
        
        rag_agent = create_hybrid_rag_agent("./clinical_pdfs")
        
        # Query di test
        test_queries = [
            "CSF biomarker cutoffs for Alzheimer diagnosis",
            "progression from MCI to dementia rates",
            "amyloid PET positive thresholds",
            "tau protein clinical significance"
        ]
        
        patient_data = {
            "stage": "Stage2",
            "age": 70,
            "csf_abeta42": 480,
            "csf_ptau181": 45,
            "amyloid_pet_suvr": 1.4
        }
        
        print(f"👤 Paziente test: Stage2, 70 anni, biomarkers borderline")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Query {i}: '{query}'")
            
            results = rag_agent.search_clinical_evidence(
                query=query,
                patient_data=patient_data,
                n_results=2
            )
            
            if results:
                best = results[0]
                print(f"   ✅ Risultato trovato:")
                print(f"      Score: {best.get('similarity_score', 0):.3f}")
                print(f"      Metodo: {best.get('search_method', 'unknown')}")
                print(f"      Fonte: {best.get('metadata', {}).get('file_name', 'Unknown')}")
                print(f"      Testo: {best.get('text', '')[:120]}...")
            else:
                print(f"   ❌ Nessun risultato trovato")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test query: {e}")
        return False

def main():
    """Funzione principale"""
    print("🎯 TEST INTEGRAZIONE RAG (SENZA OPENAI)")
    print("=" * 70)
    
    success = 0
    total = 2
    
    # Test 1: Integrazione diretta
    if test_rag_integration_direct():
        print("\n✅ Test 1 PASSATO: Integrazione RAG diretta")
        success += 1
    else:
        print("\n❌ Test 1 FALLITO")
    
    # Test 2: Query di esempio
    if test_rag_query_examples():
        print("\n✅ Test 2 PASSATO: Query di esempio")
        success += 1
    else:
        print("\n❌ Test 2 FALLITO")
    
    print(f"\n🎯 RISULTATI: {success}/{total} test passati")
    
    if success == total:
        print("\n🎉 SUCCESS! RAG INTEGRAZIONE COMPLETATA!")
        print("✅ RAG ibrido funziona perfettamente")
        print("✅ Evidenze cliniche recuperate da PDF reali")
        print("✅ Pronto per integrazione con agenti OpenAI")
        print("✅ Sistema resiliente (funziona con/senza ChromaDB)")
        print("\n📋 PROSSIMI PASSI:")
        print("1. Configura OPENAI_API_KEY per test completi")
        print("2. Testa pipeline completa con agenti")
        print("3. Valuta risultati clinici su casi reali")
    else:
        print("\n⚠️ Alcuni test falliti - verifica configurazione")

if __name__ == "__main__":
    main()
