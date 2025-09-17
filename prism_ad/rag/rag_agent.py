"""
RAG Agent per PRISM-AD - Integrazione Vector Store con agenti clinici
"""

import os
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from .vector_store import ClinicalVectorStore

class ClinicalRAGAgent:
    """RAG Agent specializzato per analisi clinica Alzheimer"""
    
    def __init__(self, vector_store: ClinicalVectorStore):
        """
        Inizializza il RAG Agent
        
        Args:
            vector_store: Istanza del vector store configurato
        """
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
        
        # Query templates per ricerca clinica
        self.query_templates = {
            "risk_assessment": [
                "risk progression Alzheimer {stage}",
                "biomarker {biomarker} progression risk",
                "clinical staging {stage} prognosis",
                "5-year risk {stage} to {target_stage}"
            ],
            "biomarker_analysis": [
                "CSF {biomarker} normal values",
                "{biomarker} cutoff values Alzheimer",
                "biomarker {biomarker} clinical significance",
                "{biomarker} progression marker"
            ],
            "staging_criteria": [
                "FDA staging criteria {stage}",
                "clinical criteria {stage} Alzheimer",
                "diagnostic criteria {stage}",
                "staging guidelines {stage}"
            ],
            "prognosis": [
                "prognosis {stage} Alzheimer",
                "outcome {stage} progression",
                "survival {stage} dementia",
                "clinical course {stage}"
            ]
        }
        
        self.logger.info("🧠 ClinicalRAGAgent initialized")
    
    def enhance_query(self, 
                     original_query: str, 
                     patient_data: Dict[str, Any],
                     query_type: str = "risk_assessment") -> List[str]:
        """
        Migliora la query originale con informazioni del paziente
        
        Args:
            original_query: Query originale
            patient_data: Dati del paziente
            query_type: Tipo di query per template
            
        Returns:
            Lista di query migliorate
        """
        enhanced_queries = [original_query]
        
        # Estrai informazioni chiave dal paziente
        stage = patient_data.get("stage", "unknown")
        age = patient_data.get("age", "")
        biomarkers = []
        
        # Identifica biomarcatori disponibili
        for key in ["csf_abeta42", "csf_ptau181", "csf_total_tau", "amyloid_pet_suvr"]:
            if patient_data.get(key) is not None:
                biomarkers.append(key)
        
        # Genera query specifiche usando template
        if query_type in self.query_templates:
            for template in self.query_templates[query_type]:
                try:
                    # Sostituisci placeholder
                    enhanced_query = template.format(
                        stage=stage,
                        target_stage="Stage3" if stage != "Stage3" else "Stage4",
                        biomarker=", ".join(biomarkers) if biomarkers else "CSF",
                        age=age
                    )
                    enhanced_queries.append(enhanced_query)
                except KeyError:
                    # Se template non supporta tutti i placeholder, salta
                    continue
        
        # Aggiungi query specifiche per biomarcatori
        for biomarker in biomarkers:
            enhanced_queries.extend([
                f"{biomarker} clinical significance",
                f"{biomarker} normal values Alzheimer",
                f"{biomarker} progression marker"
            ])
        
        return list(set(enhanced_queries))  # Rimuovi duplicati
    
    def search_clinical_evidence(self, 
                                query: str,
                                patient_data: Dict[str, Any],
                                n_results: int = 5,
                                document_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Cerca evidenze cliniche rilevanti
        
        Args:
            query: Query di ricerca
            patient_data: Dati del paziente per contesto
            n_results: Numero di risultati
            document_types: Tipi di documento da cercare
            
        Returns:
            Lista di evidenze cliniche
        """
        try:
            # Migliora la query
            enhanced_queries = self.enhance_query(query, patient_data)
            
            all_results = []
            seen_texts = set()
            
            # Cerca per ogni query migliorata
            for enhanced_query in enhanced_queries:
                results = self.vector_store.search_documents(
                    query=enhanced_query,
                    n_results=n_results,
                    document_types=document_types
                )
                
                # Aggiungi risultati unici
                for result in results:
                    if result["text"] not in seen_texts:
                        result["source_query"] = enhanced_query
                        all_results.append(result)
                        seen_texts.add(result["text"])
            
            # Ordina per score di similarità
            all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Limita risultati finali
            return all_results[:n_results * 2]  # Più risultati per diversità
            
        except Exception as e:
            self.logger.error(f"❌ Error searching clinical evidence: {e}")
            return []
    
    def get_risk_evidence(self, 
                         patient_data: Dict[str, Any],
                         target_stage: str = "Stage3") -> Dict[str, Any]:
        """
        Ottiene evidenze per stima del rischio
        
        Args:
            patient_data: Dati del paziente
            target_stage: Stage target per progressione
            
        Returns:
            Evidenze cliniche strutturate
        """
        try:
            current_stage = patient_data.get("stage", "Stage1")
            
            # Query per rischio di progressione
            risk_queries = [
                f"risk progression {current_stage} to {target_stage}",
                f"5-year risk {current_stage} Alzheimer",
                f"prognosis {current_stage} progression",
                f"clinical course {current_stage} dementia"
            ]
            
            evidence = {
                "risk_evidence": [],
                "biomarker_evidence": [],
                "staging_evidence": [],
                "prognosis_evidence": []
            }
            
            # Cerca evidenze per ogni categoria
            for query in risk_queries:
                results = self.search_clinical_evidence(
                    query=query,
                    patient_data=patient_data,
                    n_results=3,
                    document_types=["clinical_guideline", "study", "meta_analysis"]
                )
                evidence["risk_evidence"].extend(results)
            
            # Cerca evidenze specifiche per biomarcatori
            biomarkers = ["csf_abeta42", "csf_ptau181", "csf_total_tau", "amyloid_pet_suvr"]
            for biomarker in biomarkers:
                if patient_data.get(biomarker) is not None:
                    biomarker_results = self.search_clinical_evidence(
                        query=f"{biomarker} progression risk Alzheimer",
                        patient_data=patient_data,
                        n_results=2
                    )
                    evidence["biomarker_evidence"].extend(biomarker_results)
            
            # Cerca evidenze per staging
            staging_results = self.search_clinical_evidence(
                query=f"FDA staging criteria {current_stage}",
                patient_data=patient_data,
                n_results=2
            )
            evidence["staging_evidence"].extend(staging_results)
            
            return evidence
            
        except Exception as e:
            self.logger.error(f"❌ Error getting risk evidence: {e}")
            return {}
    
    def format_evidence_for_agent(self, evidence: Dict[str, Any]) -> str:
        """
        Formatta le evidenze per l'agente clinico
        
        Args:
            evidence: Evidenze cliniche strutturate
            
        Returns:
            Testo formattato per l'agente
        """
        try:
            formatted_text = "## EVIDENZE CLINICHE RILEVANTI\n\n"
            
            # Evidenze di rischio
            if evidence.get("risk_evidence"):
                formatted_text += "### Rischio di Progressione:\n"
                for i, result in enumerate(evidence["risk_evidence"][:3], 1):
                    formatted_text += f"{i}. {result['text'][:300]}...\n"
                    formatted_text += f"   Fonte: {result['metadata'].get('file_name', 'Unknown')}\n"
                    formatted_text += f"   Rilevanza: {result['relevance']}\n\n"
            
            # Evidenze biomarcatori
            if evidence.get("biomarker_evidence"):
                formatted_text += "### Evidenze Biomarcatori:\n"
                for i, result in enumerate(evidence["biomarker_evidence"][:2], 1):
                    formatted_text += f"{i}. {result['text'][:300]}...\n"
                    formatted_text += f"   Fonte: {result['metadata'].get('file_name', 'Unknown')}\n\n"
            
            # Evidenze staging
            if evidence.get("staging_evidence"):
                formatted_text += "### Criteri di Staging:\n"
                for i, result in enumerate(evidence["staging_evidence"][:2], 1):
                    formatted_text += f"{i}. {result['text'][:300]}...\n"
                    formatted_text += f"   Fonte: {result['metadata'].get('file_name', 'Unknown')}\n\n"
            
            return formatted_text
            
        except Exception as e:
            self.logger.error(f"❌ Error formatting evidence: {e}")
            return "Errore nel formattare le evidenze cliniche."
    
    def get_agent_context(self, 
                         patient_data: Dict[str, Any],
                         analysis_type: str = "risk_assessment") -> str:
        """
        Ottiene il contesto completo per l'agente clinico
        
        Args:
            patient_data: Dati del paziente
            analysis_type: Tipo di analisi richiesta
            
        Returns:
            Contesto formattato per l'agente
        """
        try:
            # Ottieni evidenze cliniche
            evidence = self.get_risk_evidence(patient_data)
            
            # Formatta per l'agente
            context = self.format_evidence_for_agent(evidence)
            
            # Aggiungi statistiche del vector store
            stats = self.vector_store.get_document_stats()
            context += f"\n### Database Clinico:\n"
            context += f"- Documenti disponibili: {stats.get('unique_documents', 0)}\n"
            context += f"- Chunk totali: {stats.get('total_chunks', 0)}\n"
            context += f"- Tipi di documento: {', '.join(stats.get('document_types', {}).keys())}\n"
            
            return context
            
        except Exception as e:
            self.logger.error(f"❌ Error getting agent context: {e}")
            return "Errore nel recuperare il contesto clinico."

# Funzione di utilità per inizializzare RAG Agent
def create_clinical_rag_agent(pdf_directory: str = None,
                            persist_directory: str = "./chroma_db",
                            collection_name: str = "clinical_documents") -> ClinicalRAGAgent:
    """
    Crea e inizializza un RAG Agent clinico
    
    Args:
        pdf_directory: Directory con PDF clinici da caricare
        persist_directory: Directory per persistenza ChromaDB
        collection_name: Nome della collezione
        
    Returns:
        Istanza configurata del RAG Agent
    """
    try:
        # Crea vector store
        vector_store = ClinicalVectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        
        # Carica PDF se directory specificata
        if pdf_directory:
            from .vector_store import load_pdfs_from_directory
            
            # Carica diversi tipi di documenti
            document_types = {
                "guidelines": "clinical_guideline",
                "studies": "study", 
                "reviews": "meta_analysis"
            }
            
            for folder, doc_type in document_types.items():
                folder_path = os.path.join(pdf_directory, folder)
                if os.path.exists(folder_path):
                    load_pdfs_from_directory(
                        vector_store=vector_store,
                        directory_path=folder_path,
                        document_type=doc_type,
                        tags=[folder]
                    )
        
        # Crea RAG agent
        rag_agent = ClinicalRAGAgent(vector_store)
        
        logging.info("✅ Clinical RAG Agent created and initialized")
        return rag_agent
        
    except Exception as e:
        logging.error(f"❌ Error creating RAG agent: {e}")
        raise
