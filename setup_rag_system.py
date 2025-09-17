#!/usr/bin/env python3
"""
Script per configurare e testare il sistema RAG per PRISM-AD
"""

import os
import sys
import logging
from pathlib import Path

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

try:
    from prism_ad.rag.vector_store import ClinicalVectorStore, load_pdfs_from_directory
    from prism_ad.rag.rag_agent import ClinicalRAGAgent, create_clinical_rag_agent
except ImportError as e:
    print(f"❌ Error importing RAG modules: {e}")
    print("🔧 Make sure to install dependencies: pip install chromadb sentence-transformers pypdf2")
    sys.exit(1)

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_sample_pdf_directory():
    """Crea una directory di esempio con PDF clinici"""
    sample_dir = Path("./clinical_pdfs")
    sample_dir.mkdir(exist_ok=True)
    
    # Crea sottodirectory per diversi tipi di documenti
    (sample_dir / "guidelines").mkdir(exist_ok=True)
    (sample_dir / "studies").mkdir(exist_ok=True)
    (sample_dir / "reviews").mkdir(exist_ok=True)
    
    print(f"📁 Created sample directory: {sample_dir}")
    print("📄 Add your clinical PDFs to the appropriate subdirectories:")
    print(f"   - Guidelines: {sample_dir / 'guidelines'}")
    print(f"   - Studies: {sample_dir / 'studies'}")
    print(f"   - Reviews: {sample_dir / 'reviews'}")
    
    return sample_dir

def test_vector_store():
    """Testa il vector store con dati di esempio"""
    print("\n🧪 Testing Vector Store...")
    
    try:
        # Crea vector store
        vector_store = ClinicalVectorStore(
            persist_directory="./test_chroma_db",
            collection_name="test_clinical_docs"
        )
        
        # Test con testo di esempio
        sample_text = """
        Alzheimer's Disease Risk Assessment Guidelines
        
        The National Institute on Aging-Alzheimer's Association (NIA-AA) criteria 
        define three stages of Alzheimer's disease:
        
        1. Preclinical AD (Stage 1): Biomarker evidence of AD pathology without 
           cognitive symptoms. Risk of progression to MCI within 5 years: 5-15%.
        
        2. MCI due to AD (Stage 2): Mild cognitive impairment with biomarker 
           evidence. Risk of progression to dementia within 5 years: 20-40%.
        
        3. Dementia due to AD (Stage 3): Clear cognitive and functional impairment.
        
        CSF biomarkers:
        - Aβ42 < 550 pg/ml indicates amyloid pathology
        - p-tau181 > 40 pg/ml indicates tau pathology
        - Aβ42/Aβ40 ratio < 0.075 is highly predictive
        
        Amyloid PET SUVR > 1.3 indicates positive amyloid burden.
        Hippocampal volume < 4.5 ml total indicates atrophy.
        """
        
        # Aggiungi documento di test
        test_file = "./test_document.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(sample_text)
        
        # Simula aggiunta di documento (in realtà dovrebbe essere PDF)
        chunks = vector_store.chunk_text(sample_text)
        
        if chunks:
            # Aggiungi chunk al vector store
            ids = [f"test_chunk_{i}" for i in range(len(chunks))]
            documents = [chunk["text"] for chunk in chunks]
            metadatas = [{
                "file_name": "test_guidelines.txt",
                "document_type": "clinical_guideline",
                "chunk_index": i,
                "source": "test"
            } for i in range(len(chunks))]
            
            vector_store.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            print(f"✅ Added {len(chunks)} test chunks to vector store")
            
            # Test ricerca
            results = vector_store.search_documents(
                query="Alzheimer risk progression biomarkers",
                n_results=3
            )
            
            print(f"🔍 Search results: {len(results)} found")
            for i, result in enumerate(results, 1):
                print(f"  {i}. Score: {result['similarity_score']:.3f}")
                print(f"     Text: {result['text'][:100]}...")
            
            # Statistiche
            stats = vector_store.get_document_stats()
            print(f"📊 Vector Store Stats: {stats}")
            
            return True
        else:
            print("❌ No chunks created from sample text")
            return False
            
    except Exception as e:
        print(f"❌ Error testing vector store: {e}")
        return False

def test_rag_agent():
    """Testa il RAG agent"""
    print("\n🧠 Testing RAG Agent...")
    
    try:
        # Crea RAG agent
        vector_store = ClinicalVectorStore(
            persist_directory="./test_chroma_db",
            collection_name="test_clinical_docs"
        )
        
        rag_agent = ClinicalRAGAgent(vector_store)
        
        # Dati paziente di test
        patient_data = {
            "stage": "Stage1",
            "age": 68,
            "csf_abeta42": 1200,
            "csf_ptau181": 25,
            "mmse": 28,
            "cdr": 0
        }
        
        # Test ricerca evidenze
        evidence = rag_agent.get_risk_evidence(patient_data)
        print(f"📚 Found evidence categories: {list(evidence.keys())}")
        
        # Test contesto per agente
        context = rag_agent.get_agent_context(patient_data)
        print(f"📄 Generated context length: {len(context)} characters")
        print(f"📄 Context preview: {context[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing RAG agent: {e}")
        return False

def main():
    """Funzione principale"""
    print("🚀 PRISM-AD RAG System Setup")
    print("=" * 50)
    
    # Crea directory di esempio
    sample_dir = create_sample_pdf_directory()
    
    # Test vector store
    if test_vector_store():
        print("✅ Vector Store test passed")
    else:
        print("❌ Vector Store test failed")
        return
    
    # Test RAG agent
    if test_rag_agent():
        print("✅ RAG Agent test passed")
    else:
        print("❌ RAG Agent test failed")
        return
    
    print("\n🎉 RAG System setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Add your clinical PDFs to the appropriate directories")
    print("2. Run the system with real PDFs:")
    print("   python -c \"from prism_ad.rag.rag_agent import create_clinical_rag_agent; agent = create_clinical_rag_agent('./clinical_pdfs')\"")
    print("3. Integrate with PRISM agents in prism_agents.py")

if __name__ == "__main__":
    main()
