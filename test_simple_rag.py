#!/usr/bin/env python3
"""
Test semplificato del sistema RAG senza ChromaDB
"""

import os
import sys
from pathlib import Path

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

def test_pdf_processing():
    """Testa l'elaborazione dei PDF senza vector store"""
    print("🧪 Testing PDF Processing...")
    
    try:
        from prism_ad.rag.vector_store import ClinicalVectorStore
        
        # Crea vector store
        vector_store = ClinicalVectorStore(
            persist_directory="./simple_chroma_db",
            collection_name="simple_clinical_docs"
        )
        
        # Test con un PDF reale
        pdf_dir = Path("./clinical_pdfs/studies")
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if pdf_files:
            test_pdf = pdf_files[0]
            print(f"📄 Testing with: {test_pdf.name}")
            
            # Estrai testo dal PDF
            pdf_data = vector_store.extract_text_from_pdf(str(test_pdf))
            
            if pdf_data["full_text"]:
                print(f"✅ Text extracted: {len(pdf_data['full_text'])} characters")
                print(f"📊 Pages: {pdf_data['num_pages']}")
                print(f"📝 Preview: {pdf_data['full_text'][:200]}...")
                
                # Test chunking
                chunks = vector_store.chunk_text(pdf_data["full_text"])
                print(f"🔪 Created {len(chunks)} chunks")
                
                return True
            else:
                print("❌ No text extracted from PDF")
                return False
        else:
            print("❌ No PDF files found in studies directory")
            return False
            
    except Exception as e:
        print(f"❌ Error in PDF processing: {e}")
        return False

def main():
    """Test principale"""
    print("🚀 Simple RAG Test")
    print("=" * 30)
    
    if test_pdf_processing():
        print("✅ PDF processing test passed")
    else:
        print("❌ PDF processing test failed")

if __name__ == "__main__":
    main()
