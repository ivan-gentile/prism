#!/usr/bin/env python3
"""
Demo semplice del RAG - senza problemi SSL
"""

import os
import sys
import ssl
from pathlib import Path

# Disabilita SSL completamente
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'false'
ssl._create_default_https_context = ssl._create_unverified_context

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

def show_pdf_contents():
    """Mostra il contenuto dei PDF senza usare ChromaDB"""
    print("📚 CONTENUTO PDF CLINICI DISPONIBILI")
    print("=" * 60)
    
    try:
        from prism_ad.rag.vector_store import ClinicalVectorStore
        
        # Lista PDF disponibili
        pdf_dir = Path("./clinical_pdfs")
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
            return None
        
        # Analizza il primo PDF
        first_pdf = pdf_files[0]
        print(f"\n🔍 ANALISI DETTAGLIATA: {first_pdf.name}")
        print("-" * 50)
        
        # Crea vector store temporaneo
        vector_store = ClinicalVectorStore(
            persist_directory="./temp_demo",
            collection_name="demo"
        )
        
        # Estrai testo dal PDF
        pdf_data = vector_store.extract_text_from_pdf(str(first_pdf))
        
        print(f"📊 STATISTICHE:")
        print(f"   - File: {pdf_data['file_name']}")
        print(f"   - Caratteri totali: {len(pdf_data['full_text']):,}")
        print(f"   - Pagine: {pdf_data['num_pages']}")
        print(f"   - Hash file: {pdf_data['file_hash'][:8]}...")
        
        # Crea chunk
        chunks = vector_store.chunk_text(pdf_data['full_text'])
        print(f"   - Chunk creati: {len(chunks)}")
        
        print(f"\n📝 PRIME 400 CARATTERI DEL DOCUMENTO:")
        print("-" * 40)
        print(pdf_data['full_text'][:400])
        print("...")
        
        print(f"\n📝 ESEMPIO DI CHUNK (primo):")
        print("-" * 30)
        if chunks:
            print(f"Chunk 1 (parole: {chunks[0]['word_count']}):")
            print(chunks[0]['text'][:300] + "...")
        
        print(f"\n📋 METADATI PDF:")
        print("-" * 20)
        for key, value in pdf_data['metadata'].items():
            if value and str(value).strip():
                print(f"   {key}: {value}")
        
        return pdf_data, chunks
        
    except Exception as e:
        print(f"❌ Errore nell'analisi PDF: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_text_search():
    """Testa la ricerca testuale senza ChromaDB"""
    print("\n\n🔍 TEST RICERCA TESTUALE SENZA SSL")
    print("=" * 60)
    
    try:
        pdf_data, chunks = show_pdf_contents()
        if not pdf_data or not chunks:
            print("❌ Nessun dato PDF disponibile")
            return
        
        # Test ricerca semplice nel testo
        search_terms = [
            "Alzheimer",
            "biomarker",
            "progression",
            "CSF",
            "amyloid",
            "tau",
            "risk"
        ]
        
        print(f"\n🎯 RICERCA TERMINI NEL DOCUMENTO:")
        print("-" * 40)
        
        full_text = pdf_data['full_text'].lower()
        
        for term in search_terms:
            count = full_text.count(term.lower())
            print(f"   '{term}': {count} occorrenze")
            
            if count > 0:
                # Trova prima occorrenza con contesto
                pos = full_text.find(term.lower())
                start = max(0, pos - 50)
                end = min(len(full_text), pos + len(term) + 50)
                context = pdf_data['full_text'][start:end]
                print(f"      Contesto: ...{context}...")
        
        print(f"\n📊 CHUNK CHE CONTENGONO 'ALZHEIMER':")
        print("-" * 40)
        
        alzheimer_chunks = []
        for i, chunk in enumerate(chunks):
            if 'alzheimer' in chunk['text'].lower():
                alzheimer_chunks.append((i, chunk))
        
        print(f"   Trovati {len(alzheimer_chunks)} chunk con 'Alzheimer'")
        
        for i, (chunk_idx, chunk) in enumerate(alzheimer_chunks[:3]):
            print(f"\n   Chunk {chunk_idx + 1}:")
            print(f"   {chunk['text'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test ricerca: {e}")
        return False

def test_manual_rag():
    """Testa funzionalità RAG manualmente"""
    print("\n\n🧠 TEST RAG MANUALE (senza ChromaDB)")
    print("=" * 60)
    
    try:
        # Simula paziente
        patient_data = {
            "age": 70,
            "mmse": 26,
            "cdr": 0.5,
            "csf_abeta42": 480,
            "csf_ptau181": 45,
            "amyloid_pet_suvr": 1.4
        }
        
        print(f"👤 PAZIENTE DI TEST:")
        for key, value in patient_data.items():
            print(f"   {key}: {value}")
        
        # Analizza PDF per contenuto rilevante
        pdf_data, chunks = show_pdf_contents()
        if not chunks:
            return False
        
        # Cerca chunk rilevanti per i valori del paziente
        print(f"\n🔍 RICERCA CHUNK RILEVANTI:")
        print("-" * 40)
        
        relevant_terms = [
            f"abeta42",
            f"p-tau",
            f"amyloid",
            f"MMSE",
            f"CDR",
            f"progression"
        ]
        
        relevant_chunks = []
        for chunk in chunks:
            chunk_text = chunk['text'].lower()
            relevance_score = sum(1 for term in relevant_terms if term.lower() in chunk_text)
            if relevance_score > 0:
                relevant_chunks.append((chunk, relevance_score))
        
        # Ordina per rilevanza
        relevant_chunks.sort(key=lambda x: x[1], reverse=True)
        
        print(f"   Trovati {len(relevant_chunks)} chunk rilevanti")
        
        for i, (chunk, score) in enumerate(relevant_chunks[:3]):
            print(f"\n   📄 Chunk {i+1} (Score: {score}):")
            print(f"   {chunk['text'][:250]}...")
        
        # Simula risposta RAG
        print(f"\n🎯 SIMULAZIONE RISPOSTA RAG:")
        print("-" * 40)
        
        if relevant_chunks:
            best_chunk = relevant_chunks[0][0]
            print(f"Basandomi sul documento clinico, per un paziente con:")
            print(f"- MMSE: {patient_data['mmse']}")
            print(f"- CDR: {patient_data['cdr']}")
            print(f"- CSF Aβ42: {patient_data['csf_abeta42']}")
            print(f"- Amyloid PET: {patient_data['amyloid_pet_suvr']}")
            print(f"\nEvidenza trovata nel documento:")
            print(f"'{best_chunk['text'][:300]}...'")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test RAG manuale: {e}")
        return False

def main():
    """Funzione principale"""
    print("🚀 DEMO RAG SEMPLICE (senza problemi SSL)")
    print("=" * 70)
    
    # Test 1: Mostra contenuto PDF
    pdf_data, chunks = show_pdf_contents()
    
    if pdf_data and chunks:
        print("✅ Estrazione PDF completata con successo!")
        
        # Test 2: Ricerca testuale
        if test_text_search():
            print("\n✅ Test ricerca testuale completato!")
        
        # Test 3: RAG manuale
        if test_manual_rag():
            print("\n✅ Test RAG manuale completato!")
        
        print("\n🎉 DEMO COMPLETATA!")
        print("\n📋 DIMOSTRAZIONE:")
        print("   ✅ Il sistema può estrarre testo dai PDF clinici")
        print("   ✅ Il sistema può creare chunk per la ricerca")
        print("   ✅ Il sistema può trovare contenuto rilevante")
        print("   ✅ Il sistema può fornire contesto clinico")
        print("\n🔧 Prossimo passo: Risolvere problemi SSL per ChromaDB")
    else:
        print("❌ Demo fallita - problemi con i PDF")

if __name__ == "__main__":
    main()
