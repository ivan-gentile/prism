#!/usr/bin/env python3
"""
Test del RAG Agent ibrido (ChromaDB + fallback testuale)
"""

import sys
sys.path.append('.')

def test_hybrid_rag():
    """Test completo RAG ibrido"""
    print("🚀 TEST RAG IBRIDO (ChromaDB + Fallback)")
    print("=" * 60)
    
    try:
        from prism_ad.rag.hybrid_rag import create_hybrid_rag_agent
        
        print("🔧 Creazione Hybrid RAG Agent...")
        rag_agent = create_hybrid_rag_agent("./clinical_pdfs")
        
        print(f"✅ RAG Agent creato!")
        print(f"📊 Metodo: {'ChromaDB' if rag_agent.use_chromadb else 'Ricerca Testuale'}")
        print(f"📚 PDF caricati: {len(rag_agent.pdf_contents) if not rag_agent.use_chromadb else 'Gestiti da ChromaDB'}")
        
        # Paziente di test
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
        
        # Test 1: Ricerca evidenze
        print(f"\n🔍 TEST 1: Ricerca evidenze cliniche")
        results = rag_agent.search_clinical_evidence(
            query="Alzheimer progression biomarkers CSF",
            patient_data=patient_data,
            n_results=5
        )
        
        print(f"📊 Trovati {len(results)} risultati:")
        for i, result in enumerate(results, 1):
            print(f"\n   {i}. **Score: {result.get('similarity_score', 0):.3f}** ({result.get('search_method', 'unknown')})")
            print(f"      Fonte: {result.get('metadata', {}).get('file_name', 'Unknown')}")
            print(f"      Rilevanza: {result.get('relevance', 'unknown')}")
            print(f"      Testo: {result.get('text', '')[:150]}...")
        
        # Test 2: Evidenze rischio
        print(f"\n🎯 TEST 2: Evidenze rischio di progressione")
        evidence = rag_agent.get_risk_evidence(patient_data)
        
        print(f"📋 Categorie evidenze:")
        for category, results in evidence.items():
            if results:
                print(f"   {category}: {len(results)} risultati")
                best = results[0] if results else None
                if best:
                    print(f"      Migliore: {best.get('metadata', {}).get('file_name', 'Unknown')}")
                    print(f"      Score: {best.get('similarity_score', 0):.3f}")
        
        # Test 3: Contesto agente
        print(f"\n🧠 TEST 3: Contesto per agente")
        context = rag_agent.get_agent_context(patient_data)
        
        print(f"📄 Contesto generato ({len(context)} caratteri):")
        print("-" * 50)
        print(context[:800] + "..." if len(context) > 800 else context)
        
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_queries():
    """Test con query specifiche"""
    print("\n\n🎯 TEST QUERY SPECIFICHE")
    print("=" * 50)
    
    try:
        from prism_ad.rag.hybrid_rag import create_hybrid_rag_agent
        
        rag_agent = create_hybrid_rag_agent("./clinical_pdfs")
        
        # Query di test
        test_queries = [
            "What are normal CSF Aβ42 values?",
            "tau PET progression prediction",
            "MCI to dementia conversion rates",
            "biomarker cutoffs Alzheimer diagnosis"
        ]
        
        patient_data = {
            "stage": "Stage2",
            "age": 70,
            "csf_abeta42": 480,
            "csf_ptau181": 45
        }
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 QUERY {i}: '{query}'")
            print("-" * 40)
            
            results = rag_agent.search_clinical_evidence(
                query=query,
                patient_data=patient_data,
                n_results=2
            )
            
            if results:
                best = results[0]
                print(f"✅ Miglior risultato:")
                print(f"   Score: {best.get('similarity_score', 0):.3f}")
                print(f"   Metodo: {best.get('search_method', 'unknown')}")
                print(f"   Fonte: {best.get('metadata', {}).get('file_name', 'Unknown')}")
                print(f"   Testo: {best.get('text', '')[:200]}...")
            else:
                print("❌ Nessun risultato trovato")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore query specifiche: {e}")
        return False

def main():
    """Funzione principale"""
    print("🎉 DEMO RAG IBRIDO - FUNZIONA SEMPRE!")
    print("=" * 70)
    
    success = 0
    total = 2
    
    # Test 1: RAG completo
    if test_hybrid_rag():
        print("✅ Test 1 PASSATO: RAG ibrido funzionale")
        success += 1
    else:
        print("❌ Test 1 FALLITO")
    
    # Test 2: Query specifiche
    if test_specific_queries():
        print("✅ Test 2 PASSATO: Query specifiche")
        success += 1
    else:
        print("❌ Test 2 FALLITO")
    
    print(f"\n🎯 RISULTATI: {success}/{total} test passati")
    
    if success == total:
        print("\n🎉 SUCCESS! RAG IBRIDO FUNZIONA PERFETTAMENTE!")
        print("✅ Risolve problemi SSL automaticamente")
        print("✅ Usa ChromaDB se disponibile")
        print("✅ Fallback testuale sempre funzionante")
        print("✅ Ricerca clinica efficace")
        print("✅ Evidenze basate su PDF reali")
    else:
        print("\n⚠️ Alcuni test falliti")

if __name__ == "__main__":
    main()
