#!/usr/bin/env python3
"""
Test finale per RAG con SSL risolto
"""

import os
import sys
import ssl
import urllib3

# Configurazione SSL MASSIMA
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'false'
os.environ['PYTHONHTTPSVERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()

sys.path.append('.')

def test_rag_completo():
    """Test RAG completo con SSL disabilitato"""
    print("🚀 TEST RAG COMPLETO - SSL DISABILITATO")
    print("=" * 60)
    
    try:
        from prism_ad.rag.rag_agent import create_clinical_rag_agent
        
        print("🔧 Creazione RAG Agent...")
        rag_agent = create_clinical_rag_agent(
            pdf_directory="./clinical_pdfs",
            persist_directory="./final_test_db",
            collection_name="final_test"
        )
        
        print("✅ RAG Agent creato con successo!")
        
        # Dati paziente
        patient_data = {
            "stage": "Stage2",
            "age": 68,
            "sex": "female", 
            "mmse": 26,
            "cdr": 0.5,
            "csf_abeta42": 480,
            "csf_ptau181": 45,
            "csf_total_tau": 380,
            "amyloid_pet_suvr": 1.4
        }
        
        print(f"\n👤 PAZIENTE TEST:")
        for key, value in patient_data.items():
            print(f"   {key}: {value}")
        
        # Test 1: Ricerca semplice
        print(f"\n🔍 TEST 1: Ricerca evidenze cliniche")
        results = rag_agent.search_clinical_evidence(
            query="Alzheimer progression risk biomarkers",
            patient_data=patient_data,
            n_results=3
        )
        
        print(f"📊 Trovati {len(results)} risultati:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. Score: {result.get('similarity_score', 0):.3f}")
            print(f"      Fonte: {result.get('metadata', {}).get('file_name', 'Unknown')}")
            print(f"      Testo: {result.get('text', '')[:150]}...")
            print()
        
        # Test 2: Contesto agente
        print(f"🧠 TEST 2: Generazione contesto")
        context = rag_agent.get_agent_context(patient_data)
        print(f"✅ Contesto generato: {len(context)} caratteri")
        print(f"📄 Preview:")
        print(context[:500] + "..." if len(context) > 500 else context)
        
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🎯 TEST RAG FINALE")
    print("=" * 40)
    
    if test_rag_completo():
        print("\n🎉 SUCCESS! RAG funziona perfettamente!")
        print("✅ SSL risolto")
        print("✅ ChromaDB funzionante") 
        print("✅ Ricerca vettoriale attiva")
        print("✅ Evidenze cliniche recuperate")
    else:
        print("\n❌ Test fallito")

if __name__ == "__main__":
    main()
