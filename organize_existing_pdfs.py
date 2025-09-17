#!/usr/bin/env python3
"""
🗂️  PRISM-AD PDF Organization Tool
Organizza i PDF clinici in categorie appropriate per il sistema RAG
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import datetime
import re

def auto_categorize_pdf(filename: str) -> str:
    """
    🤖 Categorizza automaticamente un PDF basandosi sul nome
    
    Args:
        filename: Nome del file PDF
        
    Returns:
        Categoria suggerita: 'studies', 'guidelines', 'reviews', 'other'
    """
    filename_lower = filename.lower()
    
    # Keywords per identificare studi clinici
    study_keywords = [
        'predict', 'cox', 'lasso', 'longitudinal', 'longit', 'model',
        'biomarker', 'biom', 'imaging', 'cognitive', 'cogn', 'risk',
        'preclinical', 'preclin', 'mci', 'alzheimer', 'ad'
    ]
    
    # Keywords per linee guida
    guideline_keywords = [
        'guideline', 'criteria', 'diagnostic', 'suppl', 'supplement',
        'data', 'reference', 'standard'
    ]
    
    # Keywords per review
    review_keywords = [
        'review', 'systematic', 'meta-analysis', 'meta', 'overview'
    ]
    
    # Controlla il tipo basandosi sui keywords
    if any(keyword in filename_lower for keyword in review_keywords):
        return 'reviews'
    elif any(keyword in filename_lower for keyword in guideline_keywords):
        return 'guidelines'
    elif any(keyword in filename_lower for keyword in study_keywords):
        return 'studies'
    else:
        return 'other'

def scan_and_categorize_pdfs(base_dir: Path) -> Dict[str, List[str]]:
    """
    🔍 Scansiona tutti i PDF e li categorizza automaticamente
    
    Args:
        base_dir: Directory base da scansionare
        
    Returns:
        Dizionario con categorie e liste di file
    """
    categorization = {
        'studies': [],
        'guidelines': [],
        'reviews': [],
        'other': []
    }
    
    # Trova tutti i PDF nella directory base (non nelle sottodirectory)
    pdf_files = list(base_dir.glob("*.pdf"))
    
    for pdf_file in pdf_files:
        category = auto_categorize_pdf(pdf_file.name)
        categorization[category].append(pdf_file.name)
    
    return categorization

def organize_existing_pdfs():
    """
    📚 Organizza i PDF esistenti in clinical_pdfs nelle categorie appropriate
    
    Categorie supportate:
    - studies: Studi clinici e ricerche predittive
    - guidelines: Linee guida e criteri diagnostici  
    - reviews: Review sistematiche e meta-analisi
    - other: Altri documenti non categorizzati
    """
    
    base_dir = Path("./clinical_pdfs")
    
    # Assicurati che la directory base esista
    base_dir.mkdir(exist_ok=True)
    
    # 🤖 Categorizzazione automatica dei PDF
    print("🔍 SCANSIONE AUTOMATICA DEI PDF...")
    auto_categorization = scan_and_categorize_pdfs(base_dir)
    
    # 📋 Categorizzazione manuale (override per casi specifici)
    manual_overrides = {
        # Forza alcuni file in categorie specifiche se necessario
        "Guam 2025suppl MCI AD risk biom data.pdf": "guidelines",
        # Aggiungi qui altri override se necessario
    }
    
    # Applica gli override manuali
    pdf_categorization = auto_categorization.copy()
    for filename, forced_category in manual_overrides.items():
        # Rimuovi il file dalle altre categorie
        for category, files in pdf_categorization.items():
            if filename in files:
                files.remove(filename)
        
        # Aggiungilo alla categoria forzata
        if filename in [pdf.name for pdf in base_dir.glob("*.pdf")]:
            pdf_categorization[forced_category].append(filename)
    
    # 📊 Mostra categorizzazione automatica
    print("🤖 CATEGORIZZAZIONE AUTOMATICA:")
    for category, files in pdf_categorization.items():
        if files:
            print(f"   📁 {category.upper()}: {len(files)} PDF")
            for filename in files:
                print(f"      • {filename}")
    print()
    
    print("=" * 60)
    print("🗂️  PRISM-AD PDF ORGANIZATION TOOL")
    print("=" * 60)
    print(f"📁 Base directory: {base_dir.absolute()}")
    print(f"🕐 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 📊 Statistiche iniziali
    print("📊 ANALISI INIZIALE:")
    total_pdfs_found = 0
    all_pdfs = list(base_dir.glob("**/*.pdf"))
    
    print(f"   📄 PDF totali trovati: {len(all_pdfs)}")
    for pdf in all_pdfs:
        rel_path = pdf.relative_to(base_dir)
        print(f"      • {rel_path}")
    print()
    
    print("🔄 ORGANIZZAZIONE IN CORSO...")
    print("-" * 40)
    
    # Crea directory per ogni categoria
    categories_created = []
    for category in pdf_categorization.keys():
        target_dir = base_dir / category
        if not target_dir.exists():
            target_dir.mkdir(exist_ok=True)
            categories_created.append(category)
            print(f"   📁 Created directory: {category}/")
    
    if categories_created:
        print()
    
    # Sposta i file nelle categorie appropriate
    moved_count = 0
    error_count = 0
    
    for category, files in pdf_categorization.items():
        target_dir = base_dir / category
        
        if not files:  # Skip empty categories
            continue
            
        print(f"📂 Categoria: {category.upper()}")
        
        for filename in files:
            source_file = base_dir / filename
            target_file = target_dir / filename
            
            if source_file.exists():
                try:
                    # Controlla se il file è già nella posizione corretta
                    if source_file.parent.name == category:
                        print(f"   ✓ {filename} (già in posizione)")
                        continue
                        
                    shutil.move(str(source_file), str(target_file))
                    print(f"   ➜ {filename} → {category}/")
                    moved_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Errore spostando {filename}: {e}")
                    error_count += 1
            else:
                print(f"   ⚠️  File non trovato: {filename}")
                error_count += 1
        
        print()  # Linea vuota tra categorie
    
    # 📊 Report finale dettagliato
    print("=" * 60)
    print("📊 REPORT FINALE")
    print("=" * 60)
    
    total_organized = 0
    for category in pdf_categorization.keys():
        category_dir = base_dir / category
        if category_dir.exists():
            pdf_files = list(category_dir.glob("*.pdf"))
            pdf_count = len(pdf_files)
            
            if pdf_count > 0:
                print(f"📁 {category.upper()}: {pdf_count} PDF")
                for pdf in sorted(pdf_files):
                    print(f"   • {pdf.name}")
                total_organized += pdf_count
                print()
    
    # Verifica PDF non categorizzati
    uncategorized = []
    for pdf in base_dir.glob("*.pdf"):
        if pdf.name not in [f for files in pdf_categorization.values() for f in files]:
            uncategorized.append(pdf.name)
    
    if uncategorized:
        print("⚠️  PDF NON CATEGORIZZATI:")
        for pdf in uncategorized:
            print(f"   • {pdf}")
        print()
    
    # Statistiche finali
    print("-" * 40)
    print(f"📈 STATISTICHE:")
    print(f"   📄 PDF organizzati: {total_organized}")
    print(f"   ✅ Spostamenti riusciti: {moved_count}")
    print(f"   ❌ Errori: {error_count}")
    print(f"   ⚠️  Non categorizzati: {len(uncategorized)}")
    print(f"   📁 Directory: {base_dir.absolute()}")
    print(f"   🕐 Completato: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 60)
    if error_count == 0 and len(uncategorized) == 0:
        print("✅ ORGANIZZAZIONE COMPLETATA CON SUCCESSO!")
    else:
        print("⚠️  ORGANIZZAZIONE COMPLETATA CON AVVISI")
    print("🎯 PDF pronti per il sistema RAG PRISM-AD!")
    print("=" * 60)

if __name__ == "__main__":
    organize_existing_pdfs()
