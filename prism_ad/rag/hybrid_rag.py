"""
Hybrid RAG Agent - Fallback da ChromaDB a ricerca testuale
"""

import os
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from pathlib import Path
import re

class HybridRAGAgent:
    """RAG Agent ibrido con fallback testuale"""
    
    def __init__(self, pdf_directory: str = "./clinical_pdfs"):
        """
        Inizializza RAG Agent con ricerca testuale (ChromaDB disabilitato)
        
        Args:
            pdf_directory: Directory con PDF clinici
        """
        self.pdf_directory = pdf_directory
        self.logger = logging.getLogger(__name__)
        self.use_chromadb = False  # Forza l'uso della ricerca testuale
        self.vector_store = None
        self.pdf_contents = {}  # Cache dei contenuti PDF
        
        # ChromaDB disabilitato - usa solo ricerca testuale
        self.logger.info("🔍 ChromaDB disabilitato - usando ricerca testuale affidabile")
        
        # Carica PDF in memoria per ricerca testuale
        self._load_pdfs_to_memory()
        
        self.logger.info(f"🧠 HybridRAGAgent initialized (Text Search Mode)")
    
    
    def _load_pdfs_to_memory(self):
        """Carica PDF in memoria per ricerca testuale"""
        try:
            from prism_ad.rag.vector_store import ClinicalVectorStore
            
            # Usa solo le funzioni di estrazione testo
            temp_vs = ClinicalVectorStore("./temp", "temp")
            
            pdf_dir = Path(self.pdf_directory)
            pdf_files = []
            
            # Trova tutti i PDF
            for subdir in ["studies", "guidelines", "reviews", "other"]:
                subdir_path = pdf_dir / subdir
                if subdir_path.exists():
                    pdf_files.extend(list(subdir_path.glob("*.pdf")))
            
            self.logger.info(f"📚 Loading {len(pdf_files)} PDFs to memory...")
            
            for pdf_file in pdf_files:
                try:
                    # Estrai solo il testo, senza ChromaDB
                    pdf_data = temp_vs.extract_text_from_pdf(str(pdf_file))
                    chunks = temp_vs.chunk_text(pdf_data['full_text'])
                    
                    self.pdf_contents[pdf_file.name] = {
                        'full_text': pdf_data['full_text'],
                        'chunks': chunks,
                        'metadata': pdf_data['metadata'],
                        'file_path': str(pdf_file)
                    }
                    
                    self.logger.info(f"✅ Loaded: {pdf_file.name} ({len(chunks)} chunks)")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to load {pdf_file.name}: {e}")
            
            self.logger.info(f"📚 Loaded {len(self.pdf_contents)} PDFs to memory")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load PDFs to memory: {e}")
    
    def search_clinical_evidence(self, 
                                query: str,
                                patient_data: Dict[str, Any],
                                n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Cerca evidenze cliniche usando ricerca testuale veloce (ridotta a 3 risultati)
        """
        return self._search_with_text(query, patient_data, n_results)
    
    
    def _search_with_text(self, query: str, patient_data: Dict[str, Any], n_results: int) -> List[Dict[str, Any]]:
        """Ricerca testuale semplice"""
        try:
            results = []
            query_terms = query.lower().split()
            
            # Aggiungi termini dal paziente
            patient_terms = []
            if patient_data.get('csf_abeta42'):
                patient_terms.extend(['abeta', 'amyloid'])
            if patient_data.get('csf_ptau181'):
                patient_terms.extend(['tau', 'ptau'])
            if patient_data.get('mmse'):
                patient_terms.append('mmse')
            if patient_data.get('cdr'):
                patient_terms.append('cdr')
            
            all_terms = query_terms + patient_terms
            
            for pdf_name, pdf_data in self.pdf_contents.items():
                for chunk_idx, chunk in enumerate(pdf_data['chunks']):
                    chunk_text = chunk['text'].lower()
                    
                    # Calcola score di rilevanza
                    score = 0
                    for term in all_terms:
                        count = chunk_text.count(term)
                        if count > 0:
                            score += count * (2 if term in query_terms else 1)
                    
                    if score > 0:
                        # Calcola similarity_score normalizzato
                        similarity_score = min(score / (len(chunk_text) / 100), 1.0)
                        
                        results.append({
                            'text': chunk['text'],
                            'similarity_score': similarity_score,
                            'relevance': 'high' if similarity_score > 0.7 else 'medium' if similarity_score > 0.4 else 'low',
                            'metadata': {
                                'file_name': pdf_name,
                                'chunk_index': chunk_idx,
                                'score': score
                            },
                            'search_method': 'text',
                            'rank': 0  # Sarà assegnato dopo ordinamento
                        })
            
            # Ordina per score
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Assegna rank
            for i, result in enumerate(results[:n_results]):
                result['rank'] = i + 1
            
            return results[:n_results]
            
        except Exception as e:
            self.logger.error(f"❌ Text search failed: {e}")
            return []
    
    def get_risk_evidence(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ottiene evidenze per rischio di progressione"""
        try:
            current_stage = patient_data.get("stage", "Stage1")
            
            # Query ridotte per velocità (solo 2 query essenziali)
            queries = [
                f"risk progression {current_stage} Alzheimer",
                "biomarker progression prediction"
            ]
            
            evidence = {
                "risk_evidence": [],
                "biomarker_evidence": [],
                "staging_evidence": [],
                "prognosis_evidence": []
            }
            
            # Cerca per ogni query
            for query in queries:
                results = self.search_clinical_evidence(
                    query=query,
                    patient_data=patient_data,
                    n_results=1  # Solo 1 risultato per query per velocità
                )
                
                if "risk" in query:
                    evidence["risk_evidence"].extend(results)
                elif "biomarker" in query:
                    evidence["biomarker_evidence"].extend(results)
                elif "staging" in query:
                    evidence["staging_evidence"].extend(results)
                else:
                    evidence["prognosis_evidence"].extend(results)
            
            return evidence
            
        except Exception as e:
            self.logger.error(f"❌ Error getting risk evidence: {e}")
            return {}
    
    def get_agent_context(self, patient_data: Dict[str, Any]) -> str:
        """Genera contesto per agente clinico"""
        try:
            evidence = self.get_risk_evidence(patient_data)
            
            context = "## EVIDENZE CLINICHE RILEVANTI\n\n"
            context += f"**Metodo di ricerca**: Ricerca testuale affidabile\n\n"
            
            # Evidenze di rischio
            if evidence.get("risk_evidence"):
                context += "### Rischio di Progressione:\n"
                for i, result in enumerate(evidence["risk_evidence"][:3], 1):
                    context += f"{i}. **Score: {result.get('similarity_score', 0):.3f}**\n"
                    context += f"   Fonte: {result.get('metadata', {}).get('file_name', 'Unknown')}\n"
                    context += f"   {result.get('text', '')[:200]}...\n\n"
            
            # Evidenze biomarcatori
            if evidence.get("biomarker_evidence"):
                context += "### Biomarcatori:\n"
                for i, result in enumerate(evidence["biomarker_evidence"][:2], 1):
                    context += f"{i}. **Score: {result.get('similarity_score', 0):.3f}**\n"
                    context += f"   Fonte: {result.get('metadata', {}).get('file_name', 'Unknown')}\n"
                    context += f"   {result.get('text', '')[:200]}...\n\n"
            
            # Statistiche database testuale
            context += f"### Database Clinico (Ricerca Testuale):\n"
            context += f"- Documenti caricati: {len(self.pdf_contents)}\n"
            total_chunks = sum(len(pdf['chunks']) for pdf in self.pdf_contents.values())
            context += f"- Chunk totali: {total_chunks}\n"
            context += f"- Metodo: Analisi testuale diretta senza dipendenze esterne\n"
            
            return context
            
        except Exception as e:
            self.logger.error(f"❌ Error generating agent context: {e}")
            return "Errore nel generare contesto clinico."

def create_hybrid_rag_agent(pdf_directory: str = "./clinical_pdfs") -> HybridRAGAgent:
    """
    Crea RAG agent ibrido che funziona sempre
    
    Args:
        pdf_directory: Directory con PDF clinici
        
    Returns:
        RAG agent ibrido funzionante
    """
    try:
        rag_agent = HybridRAGAgent(pdf_directory)
        logging.info("✅ Hybrid RAG Agent created successfully")
        return rag_agent
    except Exception as e:
        logging.error(f"❌ Error creating hybrid RAG agent: {e}")
        raise
