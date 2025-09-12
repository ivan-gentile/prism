#!/usr/bin/env python3
"""
Sample script to index documents for PRISM-AD RAG system.
This script processes documents from data/collections/alz_guidelines/ 
and creates embeddings in ChromaDB using OpenAI's API.
"""

import os
import sys
import chromadb
import openai
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from prism_ad.config import RAG_COLLECTION_NAME, RAG_CHROMA_PATH, RAG_EMBEDDING_MODEL

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Simple text chunking with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
    return [c for c in chunks if len(c.strip()) > 50]  # Filter very short chunks

def extract_text_from_file(file_path: Path) -> str:
    """Extract text from various file formats."""
    # Ensure the file exists
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return ""
        
    if file_path.suffix.lower() == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error reading text file {file_path.name}: {e}")
            return ""
    elif file_path.suffix.lower() == '.pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page_num, page in enumerate(reader.pages):
                    try:
                        text += page.extract_text() + "\n"
                    except Exception as e:
                        print(f"⚠️ Error extracting page {page_num + 1} from {file_path.name}: {e}")
                        continue
            return text
        except ImportError:
            print("PyPDF2 not installed. Install with: pip install PyPDF2")
            return ""
        except Exception as e:
            print(f"❌ Error reading PDF file {file_path.name}: {e}")
            return ""
    else:
        print(f"Unsupported file format: {file_path.suffix}")
        return ""

def create_embeddings(texts: List[str], model: str = RAG_EMBEDDING_MODEL) -> List[List[float]]:
    """Create embeddings using OpenAI API."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    embeddings = []
    batch_size = 100  # OpenAI's batch limit
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(
            model=model,
            input=batch
        )
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
        print(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} embeddings")
    
    return embeddings

def index_documents():
    """Main indexing function."""
    print("🔍 Starting document indexing for PRISM-AD RAG...")
    
    # Setup paths
    collections_path = Path("collections") / RAG_COLLECTION_NAME
    chroma_path = Path(RAG_CHROMA_PATH)
    
    if not collections_path.exists():
        print(f"❌ Collections directory not found: {collections_path}")
        return
    
    # Find documents
    documents = []
    for ext in ['*.txt', '*.pdf']:
        documents.extend(list(collections_path.glob(ext)))
    
    if not documents:
        print(f"❌ No documents found in {collections_path}")
        print("Place your .txt or .pdf files in the collections directory first.")
        return
    
    print(f"📄 Found {len(documents)} documents")
    
    # Initialize ChromaDB
    chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_path / RAG_COLLECTION_NAME))
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(RAG_COLLECTION_NAME)
        print(f"🗑️ Deleted existing collection: {RAG_COLLECTION_NAME}")
    except:
        pass
    
    collection = client.create_collection(
        name=RAG_COLLECTION_NAME,
        metadata={"description": "Alzheimer's guidelines and research papers"}
    )
    
    # Process documents
    all_chunks = []
    all_metadata = []
    all_ids = []
    
    for doc_idx, doc_path in enumerate(documents):
        print(f"📖 Processing: {doc_path.name}")
        
        # Extract text
        text = extract_text_from_file(doc_path)
        if not text.strip():
            print(f"⚠️ No text extracted from {doc_path.name}")
            continue
        
        # Chunk text
        chunks = chunk_text(text)
        print(f"   Created {len(chunks)} chunks")
        
        # Create metadata
        for chunk_idx, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "doc_title": doc_path.stem,
                "section_title": f"Section {chunk_idx + 1}",
                "year": datetime.now().year,  # You can extract this from document if available
                "type": "text",
                "chunk_id": f"{doc_path.stem}_chunk_{chunk_idx}",
                "source_file": str(doc_path)
            })
            all_ids.append(f"{doc_idx}_{chunk_idx}")
    
    if not all_chunks:
        print("❌ No chunks to index!")
        return
    
    print(f"🔄 Creating embeddings for {len(all_chunks)} chunks...")
    embeddings = create_embeddings(all_chunks)
    
    # Add to ChromaDB
    print("💾 Adding to ChromaDB...")
    collection.add(
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadata,
        ids=all_ids
    )
    
    print(f"✅ Successfully indexed {len(all_chunks)} chunks from {len(documents)} documents")
    print(f"📊 Collection '{RAG_COLLECTION_NAME}' ready for querying!")

if __name__ == "__main__":
    # Change to data directory
    os.chdir(Path(__file__).parent)
    index_documents()
