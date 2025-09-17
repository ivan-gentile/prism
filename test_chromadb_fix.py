#!/usr/bin/env python3
"""
Test per risolvere problemi SSL con ChromaDB
"""

import os
import sys
import ssl
from pathlib import Path

# Configurazione SSL globale
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'false'
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Disabilita SSL completamente
ssl._create_default_https_context = ssl._create_unverified_context

# Disabilita warning SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

def test_chromadb_simple():
    """Test ChromaDB semplice"""
    print("🧪 TEST CHROMADB CON SSL DISABILITATO")
    print("=" * 50)
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        print("✅ ChromaDB importato correttamente")
        
        # Crea client ChromaDB con configurazione semplice
        client = chromadb.PersistentClient(
            path="./test_ssl_fix_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        print("✅ Client ChromaDB creato")
        
        # Crea collezione di test
        collection = client.create_collection(
            name="test_ssl_collection",
            metadata={"description": "Test SSL fix"}
        )
        
        print("✅ Collezione creata")
        
        # Aggiungi documenti di test
        collection.add(
            documents=["Alzheimer disease is a neurodegenerative condition", 
                      "CSF biomarkers include amyloid beta and tau proteins"],
            metadatas=[{"source": "test1"}, {"source": "test2"}],
            ids=["doc1", "doc2"]
        )
        
        print("✅ Documenti aggiunti")
        
        # Test query
        results = collection.query(
            query_texts=["Alzheimer biomarkers"],
            n_results=2
        )
        
        print("✅ Query eseguita con successo!")
        print(f"📊 Risultati: {len(results['documents'][0])}")
        for i, doc in enumerate(results['documents'][0]):
            print(f"   {i+1}. {doc}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sentence_transformers():
    """Test SentenceTransformers con SSL disabilitato"""
    print("\n🧪 TEST SENTENCE TRANSFORMERS")
    print("=" * 50)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        print("✅ SentenceTransformers importato")
        
        # Prova modello semplice
        model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        print("✅ Modello caricato")
        
        # Test embedding
        texts = ["Alzheimer disease", "tau protein"]
        embeddings = model.encode(texts)
        
        print(f"✅ Embeddings creati: {embeddings.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore SentenceTransformers: {e}")
        return False

def test_vector_store():
    """Test del nostro vector store"""
    print("\n🧪 TEST VECTOR STORE PERSONALIZZATO")
    print("=" * 50)
    
    try:
        from prism_ad.rag.vector_store import ClinicalVectorStore
        
        print("✅ ClinicalVectorStore importato")
        
        # Crea vector store con configurazione SSL
        vs = ClinicalVectorStore(
            persist_directory="./test_ssl_vs",
            collection_name="test_ssl",
            embedding_model="paraphrase-MiniLM-L6-v2"
        )
        
        print("✅ Vector store inizializzato")
        
        # Test con PDF
        pdf_dir = Path("./clinical_pdfs/studies")
        if pdf_dir.exists():
            pdfs = list(pdf_dir.glob("*.pdf"))
            if pdfs:
                first_pdf = pdfs[0]
                print(f"📄 Test con: {first_pdf.name}")
                
                success = vs.add_pdf_document(
                    str(first_pdf),
                    document_type="study",
                    tags=["test"]
                )
                
                if success:
                    print("✅ PDF aggiunto al vector store")
                    
                    # Test ricerca
                    results = vs.search_documents(
                        query="Alzheimer progression",
                        n_results=2
                    )
                    
                    print(f"✅ Ricerca completata: {len(results)} risultati")
                    for i, result in enumerate(results, 1):
                        print(f"   {i}. Score: {result['similarity_score']:.3f}")
                        print(f"      Testo: {result['text'][:100]}...")
                    
                    return True
                else:
                    print("❌ Errore aggiunta PDF")
                    return False
            else:
                print("❌ Nessun PDF trovato")
                return False
        else:
            print("❌ Directory PDF non trovata")
            return False
        
    except Exception as e:
        print(f"❌ Errore Vector Store: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_agent():
    """Test RAG agent completo"""
    print("\n🧪 TEST RAG AGENT COMPLETO")
    print("=" * 50)
    
    try:
        from prism_ad.rag.rag_agent import create_clinical_rag_agent
        
        print("✅ RAG Agent importato")
        
        # Crea RAG agent
        rag_agent = create_clinical_rag_agent(
            pdf_directory="./clinical_pdfs",
            persist_directory="./test_ssl_rag",
            collection_name="test_ssl_rag"
        )
        
        print("✅ RAG Agent creato")
        
        # Test con paziente
        patient_data = {
            "stage": "Stage2",
            "age": 68,
            "mmse": 26,
            "cdr": 0.5,
            "csf_abeta42": 480,
            "csf_ptau181": 45
        }
        
        print("👤 Test con paziente:")
        for key, value in patient_data.items():
            print(f"   {key}: {value}")
        
        # Test ricerca evidenze
        evidence = rag_agent.get_risk_evidence(patient_data)
        
        print("✅ Evidenze ottenute:")
        for category, results in evidence.items():
            if results:
                print(f"   {category}: {len(results)} risultati")
        
        # Test contesto
        context = rag_agent.get_agent_context(patient_data)
        print(f"✅ Contesto generato: {len(context)} caratteri")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore RAG Agent: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Funzione principale"""
    print("🚀 TEST RISOLUZIONE PROBLEMI SSL CHROMADB")
    print("=" * 60)
    
    success_count = 0
    total_tests = 4
    
    # Test 1: ChromaDB base
    if test_chromadb_simple():
        print("✅ Test 1 PASSATO: ChromaDB base")
        success_count += 1
    else:
        print("❌ Test 1 FALLITO: ChromaDB base")
    
    # Test 2: SentenceTransformers
    if test_sentence_transformers():
        print("✅ Test 2 PASSATO: SentenceTransformers")
        success_count += 1
    else:
        print("❌ Test 2 FALLITO: SentenceTransformers")
    
    # Test 3: Vector Store
    if test_vector_store():
        print("✅ Test 3 PASSATO: Vector Store")
        success_count += 1
    else:
        print("❌ Test 3 FALLITO: Vector Store")
    
    # Test 4: RAG Agent
    if test_rag_agent():
        print("✅ Test 4 PASSATO: RAG Agent")
        success_count += 1
    else:
        print("❌ Test 4 FALLITO: RAG Agent")
    
    print(f"\n🎯 RISULTATI FINALI: {success_count}/{total_tests} test passati")
    
    if success_count == total_tests:
        print("🎉 TUTTI I TEST PASSATI! ChromaDB funziona correttamente!")
    else:
        print("⚠️ Alcuni test falliti. ChromaDB potrebbe avere problemi SSL.")

if __name__ == "__main__":
    main()
