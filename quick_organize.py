#!/usr/bin/env python3
"""
Script rapido per organizzare PDF clinici
"""

import os
import shutil
from pathlib import Path

def quick_organize():
    """Organizza PDF dalla directory corrente"""
    
    # Directory target
    target_dir = Path("./clinical_pdfs")
    target_dir.mkdir(exist_ok=True)
    
    # Crea sottodirectory
    for category in ['guidelines', 'studies', 'reviews', 'other']:
        (target_dir / category).mkdir(exist_ok=True)
    
    # Trova PDF nella directory corrente
    pdf_files = list(Path(".").glob("*.pdf"))
    
    if not pdf_files:
        print("❌ Nessun PDF trovato nella directory corrente")
        return
    
    print(f"📁 Trovati {len(pdf_files)} PDF")
    
    # Organizza tutti i PDF in 'other' per ora
    for pdf_file in pdf_files:
        target_file = target_dir / "other" / pdf_file.name
        shutil.copy2(pdf_file, target_file)
        print(f"  📄 {pdf_file.name} → other/")
    
    print(f"\n✅ PDF copiati in: {target_dir}/other/")
    print("📝 Puoi ora spostarli manualmente nelle categorie appropriate:")
    print("   - guidelines/ : Linee guida e criteri")
    print("   - studies/ : Studi clinici e ricerche") 
    print("   - reviews/ : Review e meta-analisi")

if __name__ == "__main__":
    quick_organize()
