#!/usr/bin/env python3
"""
Demo del sistema RAG - Mostra contenuto PDF e testa con prompt semplice
"""

import os
import sys
from pathlib import Path

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

def show_pdf_contents():
    """Mostra il contenuto dei PDF clinici disponibili"""
    print("📚 CONTENUTO PDF CLINICI DISPONIBILI")
    print("=" * 60)
    
    pdf_dir = Path("./clinical_pdfs")
    if not pdf_dir.exists():
        print("❌ Directory clinical_pdfs non trovata")
        return
    
    # Cerca PDF in tutte le sottodirectory
    pdf_files = []
    for subdir in ["studies", "guidelines", "reviews", "other"]:
        subdir_path = pdf_dir / subdir
        if subdir_path.exists():
            pdfs = list(subdir_path.glob("*.pdf"))
            pdf_files.extend(pdfs)
            print(f"\n📁 {subdir.upper()}:")
            for pdf in pdfs:
                print(f"   📄 {pdf.name}")
    
    if not pdf_files:
        print("❌ Nessun PDF trovato")
        return
    
    # Mostra contenuto del primo PDF
    if pdf_files:
        first_pdf = pdf_files[0]
        print(f"\n🔍 ANALISI DETTAGLIATA DEL PRIMO PDF:")
        print(f"📄 File: {first_pdf.name}")
        print("-" * 50)
        
        try:
            from prism_ad.rag.vector_store import ClinicalVectorStore
            
            # Crea vector store temporaneo
            vector_store = ClinicalVectorStore(
                persist_directory="./temp_demo_db",
                collection_name="demo_documents"
            )
            
            # Estrai testo dal PDF
            pdf_data = vector_store.extract_text_from_pdf(str(first_pdf))
            
            print(f"📊 Statistiche:")
            print(f"   - Caratteri totali: {len(pdf_data['full_text'])}")
            print(f"   - Pagine: {pdf_data['num_pages']}")
            print(f"   - Chunk creati: {len(vector_store.chunk_text(pdf_data['full_text']))}")
            
            print(f"\n📝 PRIME 500 CARATTERI:")
            print("-" * 30)
            print(pdf_data['full_text'][:500])
            print("...")
            
            print(f"\n📝 ULTIMI 300 CARATTERI:")
            print("-" * 30)
            print("..." + pdf_data['full_text'][-300:])
            
            # Mostra metadati
            print(f"\n📋 METADATI PDF:")
            print("-" * 20)
            for key, value in pdf_data['metadata'].items():
                if value:
                    print(f"   {key}: {value}")
            
            return pdf_data
            
        except Exception as e:
            print(f"❌ Errore nell'analisi PDF: {e}")
            return None

def test_rag_with_simple_prompt():
    """Testa il RAG con un prompt semplice"""
    print("\n\n🧠 TEST RAG CON PROMPT SEMPLICE")
    print("=" * 60)
    
    try:
        from prism_ad.rag.rag_agent import create_clinical_rag_agent
        
        print("🔧 Inizializzazione RAG Agent...")
        rag_agent = create_clinical_rag_agent(
            pdf_directory="./clinical_pdfs",
            persist_directory="./simple_chroma_db",
            collection_name="clinical_documents"
        )
        print("✅ RAG Agent inizializzato")
        
        # Dati paziente di test
        patient_data = {
            "stage": "Stage2",
            "age": 68,
            "sex": "female",
            "mmse": 28,
            "cdr": 0.0,
            "csf_abeta42": 520,
            "csf_ptau181": 35,
            "csf_total_tau": 380,
            "amyloid_pet_suvr": 1.2,
            "hippocampus_volume_left": 2.4,
            "hippocampus_volume_right": 2.5
        }
        
        print(f"\n👤 Dati paziente di test:")
        for key, value in patient_data.items():
            print(f"   {key}: {value}")
        
        # Test 1: Ricerca semplice
        print(f"\n🔍 TEST 1: Ricerca 'Alzheimer risk progression'")
        print("-" * 50)
        
        results = rag_agent.search_clinical_evidence(
            query="Alzheimer risk progression",
            patient_data=patient_data,
            n_results=3
        )
        
        print(f"📊 Trovati {len(results)} risultati:")
        for i, result in enumerate(results, 1):
            print(f"\n   {i}. Score: {result.get('similarity_score', 0):.3f}")
            print(f"      Fonte: {result.get('metadata', {}).get('file_name', 'Unknown')}")
            print(f"      Testo: {result.get('text', '')[:200]}...")
        
        # Test 2: Ricerca biomarcatori
        print(f"\n🔍 TEST 2: Ricerca 'CSF biomarkers normal values'")
        print("-" * 50)
        
        results2 = rag_agent.search_clinical_evidence(
            query="CSF biomarkers normal values",
            patient_data=patient_data,
            n_results=2
        )
        
        print(f"📊 Trovati {len(results2)} risultati:")
        for i, result in enumerate(results2, 1):
            print(f"\n   {i}. Score: {result.get('similarity_score', 0):.3f}")
            print(f"      Fonte: {result.get('metadata', {}).get('file_name', 'Unknown')}")
            print(f"      Testo: {result.get('text', '')[:200]}...")
        
        # Test 3: Contesto completo per agente
        print(f"\n🔍 TEST 3: Contesto completo per agente")
        print("-" * 50)
        
        context = rag_agent.get_agent_context(patient_data)
        print(f"📄 Contesto generato ({len(context)} caratteri):")
        print("-" * 30)
        print(context[:800] + "..." if len(context) > 800 else context)
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_queries():
    """Testa query semplici per dimostrare le capacità"""
    print("\n\n🎯 TEST QUERY SEMPLICI")
    print("=" * 60)
    
    try:
        from prism_ad.rag.rag_agent import create_clinical_rag_agent
        
        rag_agent = create_clinical_rag_agent(
            pdf_directory="./clinical_pdfs",
            persist_directory="./simple_chroma_db",
            collection_name="clinical_documents"
        )
        
        # Query di test
        test_queries = [
            "What is the normal range for CSF Aβ42?",
            "How to interpret amyloid PET results?",
            "What are the FDA staging criteria?",
            "Risk factors for Alzheimer progression",
            "Biomarker cutoffs for diagnosis"
        ]
        
        patient_data = {"stage": "Stage2", "age": 70}
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 QUERY {i}: {query}")
            print("-" * 40)
            
            results = rag_agent.search_clinical_evidence(
                query=query,
                patient_data=patient_data,
                n_results=2
            )
            
            if results:
                best_result = results[0]
                print(f"✅ Miglior risultato (Score: {best_result.get('similarity_score', 0):.3f}):")
                print(f"   Fonte: {best_result.get('metadata', {}).get('file_name', 'Unknown')}")
                print(f"   Testo: {best_result.get('text', '')[:150]}...")
            else:
                print("❌ Nessun risultato trovato")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nei test query: {e}")
        return False

def main():
    """Funzione principale"""
    print("🚀 DEMO SISTEMA RAG PRISM-AD")
    print("=" * 60)
    
    # 1. Mostra contenuto PDF
    pdf_data = show_pdf_contents()
    
    if pdf_data:
        # 2. Test RAG con prompt semplice
        if test_rag_with_simple_prompt():
            print("\n✅ Test RAG completato con successo!")
        
        # 3. Test query semplici
        if test_simple_queries():
            print("\n✅ Test query semplici completato!")
        
        print("\n🎉 DEMO COMPLETATA!")
        print("\n📋 Il sistema RAG è funzionante e può:")
        print("   - Estrarre testo da PDF clinici")
        print("   - Creare chunk per la ricerca")
        print("   - Trovare evidenze cliniche rilevanti")
        print("   - Fornire contesto agli agenti")
    else:
        print("❌ Demo fallita - problemi con i PDF")

if __name__ == "__main__":
    main()
