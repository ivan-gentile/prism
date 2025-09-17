#!/usr/bin/env python3
"""
📄 PDF Formatter per PRISM-AD
Converte report Markdown in PDF professionali ben formattati
"""

import os
import datetime
from pathlib import Path
from typing import Optional
import markdown
import pdfkit
from jinja2 import Template

class PrismPDFFormatter:
    """
    🎨 Formatter professionale per report PRISM-AD
    Converte Markdown in PDF con styling medico professionale
    """
    
    def __init__(self):
        self.css_template = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20mm;
            background: #ffffff;
        }
        
        /* Header styling */
        h1 {
            color: #1e3a8a;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 10px;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 30px;
        }
        
        h2 {
            color: #1e40af;
            font-size: 22px;
            font-weight: 600;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #3b82f6;
            padding-left: 15px;
        }
        
        h3 {
            color: #1e40af;
            font-size: 18px;
            font-weight: 500;
            margin-top: 25px;
            margin-bottom: 12px;
        }
        
        h4 {
            color: #374151;
            font-size: 16px;
            font-weight: 500;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        /* Separatori */
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(to right, #3b82f6, #60a5fa, #3b82f6);
            margin: 25px 0;
        }
        
        /* Tabelle */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        th {
            background: #1e40af;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 14px;
        }
        
        tr:nth-child(even) {
            background: #f8fafc;
        }
        
        tr:hover {
            background: #f1f5f9;
        }
        
        /* Codice e valori */
        code {
            background: #f1f5f9;
            color: #1e40af;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-weight: 600;
            font-size: 14px;
        }
        
        /* Liste */
        ul, ol {
            margin: 15px 0;
            padding-left: 25px;
        }
        
        li {
            margin: 8px 0;
            line-height: 1.5;
        }
        
        /* Indicatori di rischio professionale */
        .risk-low { 
            color: #059669; 
            font-weight: 600; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .risk-medium { 
            color: #d97706; 
            font-weight: 600; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .risk-high { 
            color: #dc2626; 
            font-weight: 600; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Box informativi */
        .info-box {
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        
        .warning-box {
            background: #fefce8;
            border: 1px solid #eab308;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        
        .danger-box {
            background: #fef2f2;
            border: 1px solid #ef4444;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        
        /* Footer professionale */
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e5e7eb;
            font-size: 11px;
            color: #6b7280;
            text-align: center;
            font-style: italic;
        }
        
        /* Print styles */
        @media print {
            body { margin: 0; padding: 15mm; }
            h1 { page-break-after: avoid; }
            h2, h3, h4 { page-break-after: avoid; }
            table { page-break-inside: avoid; }
            .page-break { page-break-before: always; }
        }
        
        /* Responsiveness */
        @media (max-width: 768px) {
            body { padding: 15px; }
            h1 { font-size: 24px; }
            h2 { font-size: 20px; }
            table { font-size: 12px; }
        }
        </style>
        """
    
    def format_markdown_to_html(self, markdown_content: str) -> str:
        """
        Converte Markdown in HTML ben formattato
        
        Args:
            markdown_content: Contenuto in formato Markdown
            
        Returns:
            HTML formattato con CSS professionale
        """
        
        # Converte Markdown in HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'toc']
        )
        
        # Template HTML completo
        html_template = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PRISM-AD Report</title>
            {self.css_template}
        </head>
        <body>
            {html_content}
            
            <div class="footer">
                <p>Report generato da PRISM-AD v2.0 - Sistema di Intelligenza Artificiale per la Valutazione del Rischio Alzheimer</p>
                <p>Generato il {datetime.datetime.now().strftime('%d/%m/%Y alle %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def convert_to_pdf(self, 
                      markdown_content: str, 
                      output_path: str,
                      patient_id: Optional[str] = None) -> bool:
        """
        Converte Markdown in PDF professionale
        
        Args:
            markdown_content: Contenuto del report in Markdown
            output_path: Percorso del file PDF di output
            patient_id: ID del paziente (opzionale)
            
        Returns:
            True se la conversione è riuscita, False altrimenti
        """
        
        try:
            # Converte in HTML
            html_content = self.format_markdown_to_html(markdown_content)
            
            # Opzioni per PDF
            options = {
                'page-size': 'A4',
                'margin-top': '1in',
                'margin-right': '0.75in',
                'margin-bottom': '1in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'print-media-type': None,
                'disable-smart-shrinking': None,
            }
            
            # Aggiungi header se c'è un patient ID
            if patient_id:
                options['header-html'] = f"""
                <div style="font-size: 10px; color: #6b7280; text-align: center; padding: 10px;">
                    PRISM-AD Report - Paziente {patient_id} - {datetime.datetime.now().strftime('%d/%m/%Y')}
                </div>
                """
                options['header-spacing'] = '10'
            
            # Genera PDF
            pdfkit.from_string(html_content, output_path, options=options)
            
            print(f"PDF generato con successo: {output_path}")
            return True
            
        except Exception as e:
            print(f"Errore durante la generazione del PDF: {e}")
            return False
    
    def save_formatted_report(self, 
                            markdown_content: str,
                            base_filename: str = "prism_ad_report",
                            output_dir: str = "./reports") -> dict:
        """
        Salva il report in formati multipli (MD, HTML, PDF)
        
        Args:
            markdown_content: Contenuto del report
            base_filename: Nome base del file
            output_dir: Directory di output
            
        Returns:
            Dizionario con i percorsi dei file generati
        """
        
        # Crea directory se non esiste
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{base_filename}_{timestamp}"
        
        results = {}
        
        try:
            # Salva Markdown
            md_path = output_path / f"{base_name}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            results['markdown'] = str(md_path)
            print(f"Markdown salvato: {md_path}")
            
            # Salva HTML
            html_content = self.format_markdown_to_html(markdown_content)
            html_path = output_path / f"{base_name}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            results['html'] = str(html_path)
            print(f"HTML salvato: {html_path}")
            
            # Salva PDF (se wkhtmltopdf è disponibile)
            try:
                pdf_path = output_path / f"{base_name}.pdf"
                if self.convert_to_pdf(markdown_content, str(pdf_path)):
                    results['pdf'] = str(pdf_path)
            except Exception as e:
                print(f"PDF non disponibile (installare wkhtmltopdf): {e}")
            
            return results
            
        except Exception as e:
            print(f"Errore durante il salvataggio: {e}")
            return {}

# Funzione di utilità per uso semplice
def format_prism_report(markdown_content: str, 
                       output_dir: str = "./reports",
                       patient_id: Optional[str] = None) -> dict:
    """
    Funzione di utilità per formattare rapidamente un report PRISM-AD
    
    Args:
        markdown_content: Contenuto del report in Markdown
        output_dir: Directory dove salvare i file
        patient_id: ID del paziente (opzionale)
        
    Returns:
        Dizionario con i percorsi dei file generati
    """
    
    formatter = PrismPDFFormatter()
    
    base_filename = "prism_ad_report"
    if patient_id:
        base_filename = f"prism_ad_report_paziente_{patient_id}"
    
    return formatter.save_formatted_report(
        markdown_content=markdown_content,
        base_filename=base_filename,
        output_dir=output_dir
    )

if __name__ == "__main__":
    # Test del formatter
    test_markdown = """
# PRISM-AD - Report di Valutazione del Rischio Alzheimer

---

**INFORMAZIONI GENERALI**
- **Data di analisi:** 12/09/2025
- **Identificativo paziente:** TEST_001
- **Sistema:** PRISM-AD v2.0
- **Metodologia:** Consensus Multi-Agent con Evidenze Cliniche

---

## SINTESI CLINICA PER IL MEDICO CURANTE

### **VALUTAZIONE DEL RISCHIO PRIMARIO**
**Rischio di conversione ad Alzheimer a 5 anni:** `25.3%` (IC90: 18.1% - 32.5%)

**Classificazione FDA:** Stage 2 - Mild Cognitive Impairment

**Categoria di rischio:** MODERATO

### **PROFILO CLINICO DEL PAZIENTE**

#### **Fattori di Rischio Identificati:**
- Età avanzata (75 anni)
- Presenza di APOE4 eterozigote
- Declino cognitivo lieve documentato
- Atrofia ippocampale bilaterale

#### **Fattori Protettivi:**
- Elevato livello di istruzione
- Attività fisica regolare
- Buon controllo cardiovascolare

### **PROFILO BIOMARCATORI**

| Parametro | Valore Osservato | Range di Riferimento | Interpretazione Clinica |
|-----------|------------------|----------------------|------------------------|
| Aβ42/Aβ40 | 0.052 | >0.067 | Ridotto |
| p-Tau181 | 28.4 pg/mL | <22.0 | Elevato |
| MMSE | 26/30 | ≥27 | Lievemente ridotto |

---

## COMUNICAZIONE AL PAZIENTE

### **Significato dei Risultati**

I suoi esami mostrano alcuni cambiamenti che potrebbero indicare un rischio moderato di sviluppare problemi di memoria più significativi nei prossimi 5 anni.

### **Interpretazione del Livello di Rischio**

Il rischio stimato è del 25%, il che significa che la maggior parte delle persone con il suo profilo (circa 3 su 4) non svilupperà problemi significativi.

---

## APPENDICE METODOLOGICA

### **Algoritmo di Consenso**
- **Metodologia:** Meta-analisi bayesiana multi-agente
- **Agenti computazionali consultati:** 6 specialisti virtuali
- **Gestione dell'eterogeneità:** Modello random-effects

### **Base di Evidenze Cliniche**
- **Numero di studi inclusi:** 15 studi longitudinali
- **Riferimenti bibliografici principali:**
  - Groot et al. 2024 (DOI: 10.1000/xxx)
  - Li et al. 2019 (DOI: 10.1000/yyy)
  - Ossenkoppele et al. 2022 (DOI: 10.1000/zzz)

---

**DISCLAIMER MEDICO-LEGALE**

Questo report è generato da un sistema di intelligenza artificiale sviluppato per il supporto alle decisioni cliniche.
    """
    
    print("Test del formatter PDF professionale...")
    results = format_prism_report(test_markdown, "./test_reports", "TEST_001")
    
    if results:
        print("Test completato con successo!")
        for format_type, path in results.items():
            print(f"   {format_type.upper()}: {path}")
    else:
        print("Test fallito")
