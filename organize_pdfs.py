#!/usr/bin/env python3
"""
Script per organizzare automaticamente i PDF clinici in categorie
"""

import os
import shutil
from pathlib import Path
import re

def categorize_pdf(filename: str) -> str:
    """
    Categorizza un PDF basandosi sul nome del file
    
    Args:
        filename: Nome del file PDF
        
    Returns:
        Categoria: 'guidelines', 'studies', 'reviews', o 'other'
    """
    filename_lower = filename.lower()
    
    # Keywords per linee guida
    guideline_keywords = [
        'guideline', 'criteria', 'consensus', 'recommendation', 
        'nia-aa', 'iwg', 'fda', 'clinical practice', 'diagnostic',
        'staging', 'classification', 'framework', 'protocol'
    ]
    
    # Keywords per studi
    study_keywords = [
        'study', 'cohort', 'longitudinal', 'clinical trial', 'adni', 
        'aibl', 'biomarker', 'validation', 'prospective', 'retrospective',
        'population', 'sample', 'participants', 'follow-up'
    ]
    
    # Keywords per review
    review_keywords = [
        'review', 'meta-analysis', 'systematic', 'literature', 
        'overview', 'summary', 'expert opinion', 'consensus paper',
        'state of the art', 'current knowledge'
    ]
    
    # Conta matches per categoria
    guideline_score = sum(1 for keyword in guideline_keywords if keyword in filename_lower)
    study_score = sum(1 for keyword in study_keywords if keyword in filename_lower)
    review_score = sum(1 for keyword in review_keywords if keyword in filename_lower)
    
    # Determina categoria con score più alto
    if guideline_score > study_score and guideline_score > review_score:
        return 'guidelines'
    elif study_score > review_score:
        return 'studies'
    elif review_score > 0:
        return 'reviews'
    else:
        return 'other'

def organize_pdfs(source_dir: str, target_base_dir: str = "./clinical_pdfs"):
    """
    Organizza i PDF dalla directory sorgente nelle categorie appropriate
    
    Args:
        source_dir: Directory con tutti i PDF
        target_base_dir: Directory base per l'organizzazione
    """
    source_path = Path(source_dir)
    target_path = Path(target_base_dir)
    
    if not source_path.exists():
        print(f"❌ Directory sorgente non trovata: {source_dir}")
        return
    
    # Crea directory target se non esistono
    categories = ['guidelines', 'studies', 'reviews', 'other']
    for category in categories:
        (target_path / category).mkdir(parents=True, exist_ok=True)
    
    # Trova tutti i PDF
    pdf_files = list(source_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  Nessun file PDF trovato in: {source_dir}")
        return
    
    print(f"📁 Trovati {len(pdf_files)} file PDF in: {source_dir}")
    print("🔄 Organizzando i file...")
    
    # Statistiche
    stats = {category: 0 for category in categories}
    
    for pdf_file in pdf_files:
        try:
            # Determina categoria
            category = categorize_pdf(pdf_file.name)
            
            # Percorso di destinazione
            target_file = target_path / category / pdf_file.name
            
            # Copia il file (non sposta per sicurezza)
            shutil.copy2(pdf_file, target_file)
            
            stats[category] += 1
            print(f"  📄 {pdf_file.name} → {category}/")
            
        except Exception as e:
            print(f"  ❌ Errore con {pdf_file.name}: {e}")
    
    # Mostra statistiche finali
    print(f"\n📊 Organizzazione completata:")
    for category, count in stats.items():
        if count > 0:
            print(f"  {category}: {count} file")
    
    print(f"\n📂 File organizzati in: {target_path}")
    print("✅ I PDF sono ora pronti per il sistema RAG!")

def main():
    """Funzione principale"""
    print("📚 Organizzatore PDF Clinici per PRISM-AD")
    print("=" * 50)
    
    # Chiedi directory sorgente
    source_dir = input("📁 Inserisci il percorso della directory con i PDF: ").strip()
    
    if not source_dir:
        # Usa directory corrente se non specificata
        source_dir = "."
        print(f"📁 Usando directory corrente: {os.getcwd()}")
    
    # Organizza i PDF
    organize_pdfs(source_dir)

if __name__ == "__main__":
    main()
