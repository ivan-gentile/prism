"""
Vector Store per PRISM-AD - Gestione PDF clinici con ChromaDB
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import hashlib
from datetime import datetime
import ssl
import urllib3

# Disabilita warning SSL per ChromaDB
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurazione SSL globale aggressiva
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = 'false'
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Disabilita SSL completamente
ssl._create_default_https_context = ssl._create_unverified_context

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    import PyPDF2
    from PyPDF2 import PdfReader
except ImportError as e:
    print(f"⚠️  RAG dependencies not available: {e}")
    print("🔧 Install with: pip install chromadb sentence-transformers pypdf2")

class ClinicalVectorStore:
    """Vector Store specializzato per documenti clinici PDF"""
    
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 collection_name: str = "clinical_documents",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Inizializza il Vector Store per documenti clinici
        
        Args:
            persist_directory: Directory per persistenza ChromaDB
            collection_name: Nome della collezione
            embedding_model: Modello per embeddings (medical-specialized)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        # Crea directory se non esiste
        os.makedirs(persist_directory, exist_ok=True)
        
        # Inizializza ChromaDB
        self._init_chromadb()
        
        # Inizializza embedding model
        self._init_embedding_model()
        
        logging.info(f"✅ ClinicalVectorStore initialized: {collection_name}")
    
    def _init_chromadb(self):
        """Inizializza ChromaDB client e collezione"""
        try:
            # Configura SSL per evitare errori di certificato
            os.environ['CURL_CA_BUNDLE'] = ''
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            os.environ['SSL_VERIFY'] = 'false'
            
            # Disabilita verifiche SSL per ChromaDB
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            
            self.chroma_client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    # Configura per evitare problemi SSL
                    chroma_server_ssl_enabled=False
                )
            )
            
            # Ottieni o crea collezione
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.collection_name
                )
                logging.info(f"📚 Loaded existing collection: {self.collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Clinical documents for PRISM-AD RAG"}
                )
                logging.info(f"📚 Created new collection: {self.collection_name}")
                
        except Exception as e:
            logging.error(f"❌ Error initializing ChromaDB: {e}")
            raise
    
    def _init_embedding_model(self):
        """Inizializza il modello di embedding"""
        try:
            # Configura SSL per SentenceTransformers
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            
            # Usa un modello medical-specialized se disponibile
            # Fallback a modello generale per ora
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logging.info(f"🧠 Embedding model loaded: {self.embedding_model_name}")
        except Exception as e:
            logging.error(f"❌ Error loading embedding model: {e}")
            # Prova con un modello più semplice
            try:
                logging.info("🔄 Trying fallback embedding model...")
                self.embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
                logging.info("✅ Fallback embedding model loaded")
            except Exception as e2:
                logging.error(f"❌ Error loading fallback model: {e2}")
                raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Estrae testo da PDF clinico con metadati
        
        Args:
            pdf_path: Percorso del file PDF
            
        Returns:
            Dict con testo estratto e metadati
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                # Metadati del PDF
                metadata = pdf_reader.metadata or {}
                
                # Estrai testo da tutte le pagine
                full_text = ""
                page_texts = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        full_text += page_text + "\n"
                        page_texts.append({
                            "page": page_num + 1,
                            "text": page_text.strip()
                        })
                
                # Calcola hash del file per identificazione univoca
                file_hash = hashlib.md5(open(pdf_path, 'rb').read()).hexdigest()
                
                return {
                    "file_path": pdf_path,
                    "file_name": os.path.basename(pdf_path),
                    "file_hash": file_hash,
                    "full_text": full_text.strip(),
                    "page_texts": page_texts,
                    "num_pages": len(pdf_reader.pages),
                    "metadata": {
                        "title": metadata.get("Title", ""),
                        "author": metadata.get("Author", ""),
                        "subject": metadata.get("Subject", ""),
                        "creator": metadata.get("Creator", ""),
                        "creation_date": str(metadata.get("CreationDate", "")),
                        "modification_date": str(metadata.get("ModDate", ""))
                    },
                    "extraction_date": datetime.now().isoformat()
                }
                
        except Exception as e:
            logging.error(f"❌ Error extracting PDF {pdf_path}: {e}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Divide il testo in chunk per il vector store
        
        Args:
            text: Testo da dividere
            chunk_size: Dimensione massima di ogni chunk
            overlap: Sovrapposizione tra chunk
            
        Returns:
            Lista di chunk con metadati
        """
        if not text.strip():
            return []
        
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text.strip(),
                    "chunk_index": len(chunks),
                    "start_word": i,
                    "end_word": min(i + chunk_size, len(words)),
                    "word_count": len(chunk_words)
                })
        
        return chunks
    
    def add_pdf_document(self, pdf_path: str, 
                        document_type: str = "clinical_guideline",
                        tags: List[str] = None) -> bool:
        """
        Aggiunge un documento PDF al vector store
        
        Args:
            pdf_path: Percorso del PDF
            document_type: Tipo di documento (clinical_guideline, study, etc.)
            tags: Tag per categorizzazione
            
        Returns:
            True se aggiunto con successo
        """
        try:
            # Estrai testo dal PDF
            pdf_data = self.extract_text_from_pdf(pdf_path)
            
            # Verifica se documento già esistente
            existing = self.collection.get(
                where={"file_hash": pdf_data["file_hash"]}
            )
            
            if existing["ids"]:
                logging.info(f"📄 Document already exists: {pdf_data['file_name']}")
                return True
            
            # Crea chunk dal testo
            chunks = self.chunk_text(pdf_data["full_text"])
            
            if not chunks:
                logging.warning(f"⚠️  No text extracted from: {pdf_path}")
                return False
            
            # Prepara dati per ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for chunk in chunks:
                chunk_id = f"{pdf_data['file_hash']}_chunk_{chunk['chunk_index']}"
                
                ids.append(chunk_id)
                documents.append(chunk["text"])
                
                metadata = {
                    "file_name": pdf_data["file_name"],
                    "file_path": pdf_path,
                    "file_hash": pdf_data["file_hash"],
                    "document_type": document_type,
                    "chunk_index": chunk["chunk_index"],
                    "start_word": chunk["start_word"],
                    "end_word": chunk["end_word"],
                    "word_count": chunk["word_count"],
                    "num_pages": pdf_data["num_pages"],
                    "extraction_date": pdf_data["extraction_date"]
                }
                
                # Aggiungi metadati PDF se disponibili
                metadata.update(pdf_data["metadata"])
                
                # Aggiungi tag
                if tags:
                    metadata["tags"] = ",".join(tags)
                
                metadatas.append(metadata)
            
            # Disabilita SSL per questa operazione
            import ssl
            old_context = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context
            
            try:
                # Aggiungi al vector store
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            finally:
                # Ripristina il contesto SSL
                ssl._create_default_https_context = old_context
            
            logging.info(f"✅ Added {len(chunks)} chunks from: {pdf_data['file_name']}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error adding PDF {pdf_path}: {e}")
            return False
    
    def search_documents(self, 
                        query: str, 
                        n_results: int = 5,
                        document_types: List[str] = None,
                        filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Cerca documenti rilevanti per la query
        
        Args:
            query: Query di ricerca
            n_results: Numero di risultati da restituire
            document_types: Filtra per tipi di documento
            filters: Filtri aggiuntivi per metadati
            
        Returns:
            Lista di documenti rilevanti con score
        """
        try:
            # Costruisci filtri
            where_clause = {}
            if document_types:
                where_clause["document_type"] = {"$in": document_types}
            if filters:
                where_clause.update(filters)
            
            # Disabilita SSL per la ricerca
            import ssl
            old_context = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context
            
            try:
                # Esegui ricerca
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_clause if where_clause else None
                )
            finally:
                # Ripristina il contesto SSL
                ssl._create_default_https_context = old_context
            
            # Formatta risultati
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                formatted_results.append({
                    "rank": i + 1,
                    "text": doc,
                    "metadata": metadata,
                    "similarity_score": 1 - distance,  # Converti distanza in score
                    "relevance": self._calculate_relevance(distance)
                })
            
            return formatted_results
            
        except Exception as e:
            logging.error(f"❌ Error searching documents: {e}")
            return []
    
    def _calculate_relevance(self, distance: float) -> str:
        """Calcola livello di rilevanza basato sulla distanza"""
        if distance < 0.3:
            return "high"
        elif distance < 0.6:
            return "medium"
        else:
            return "low"
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche del vector store"""
        try:
            count = self.collection.count()
            
            # Ottieni metadati per analisi
            all_docs = self.collection.get()
            
            # Analizza tipi di documento
            doc_types = {}
            file_names = set()
            
            for metadata in all_docs["metadatas"]:
                doc_type = metadata.get("document_type", "unknown")
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                file_names.add(metadata.get("file_name", "unknown"))
            
            return {
                "total_chunks": count,
                "unique_documents": len(file_names),
                "document_types": doc_types,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model_name
            }
            
        except Exception as e:
            logging.error(f"❌ Error getting stats: {e}")
            return {}
    
    def delete_document(self, file_hash: str) -> bool:
        """Elimina un documento dal vector store"""
        try:
            # Trova tutti i chunk del documento
            results = self.collection.get(where={"file_hash": file_hash})
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logging.info(f"🗑️  Deleted document with hash: {file_hash}")
                return True
            else:
                logging.warning(f"⚠️  Document not found: {file_hash}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error deleting document: {e}")
            return False

# Funzione di utilità per caricare PDF da directory
def load_pdfs_from_directory(vector_store: ClinicalVectorStore, 
                           directory_path: str,
                           document_type: str = "clinical_guideline",
                           tags: List[str] = None) -> Dict[str, int]:
    """
    Carica tutti i PDF da una directory nel vector store
    
    Args:
        vector_store: Istanza del vector store
        directory_path: Percorso della directory
        document_type: Tipo di documento per tutti i PDF
        tags: Tag comuni per tutti i PDF
        
    Returns:
        Dict con statistiche di caricamento
    """
    directory = Path(directory_path)
    if not directory.exists():
        logging.error(f"❌ Directory not found: {directory_path}")
        return {"success": 0, "failed": 0}
    
    pdf_files = list(directory.glob("*.pdf"))
    if not pdf_files:
        logging.warning(f"⚠️  No PDF files found in: {directory_path}")
        return {"success": 0, "failed": 0}
    
    success_count = 0
    failed_count = 0
    
    for pdf_file in pdf_files:
        try:
            if vector_store.add_pdf_document(
                str(pdf_file), 
                document_type=document_type,
                tags=tags
            ):
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logging.error(f"❌ Failed to load {pdf_file}: {e}")
            failed_count += 1
    
    logging.info(f"📚 Loaded {success_count} PDFs, {failed_count} failed")
    return {"success": success_count, "failed": failed_count}
