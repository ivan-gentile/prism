# PRISM-AD Data Directory

This directory contains all data assets for the PRISM-AD RAG system.

## Directory Structure

```
data/
├── chromadb/              # ChromaDB persistent storage
│   └── alz_guidelines/    # Collection for Alzheimer's guidelines
├── collections/           # Raw documents for indexing
│   └── alz_guidelines/    # Source documents (PDFs, texts, etc.)
├── embeddings/           # Pre-computed embeddings (optional)
└── processed/            # Processed/chunked documents
```

## Data Placement Guidelines

### 1. Raw Documents (`collections/alz_guidelines/`)
Place your source documents here:
- PDF files of Alzheimer's guidelines
- Research papers
- Clinical protocols
- Text files with medical knowledge

### 2. ChromaDB Storage (`chromadb/alz_guidelines/`)
This directory is automatically created by ChromaDB. Do not modify manually.

### 3. Processing Pipeline
1. Place raw documents in `collections/alz_guidelines/`
2. Run indexing scripts to process and embed documents
3. ChromaDB will store embeddings in `chromadb/alz_guidelines/`

## Usage Notes

- The RAG system expects the ChromaDB collection to be pre-populated
- Use consistent embedding models between indexing and querying
- Current configuration uses OpenAI's `text-embedding-3-small` model
