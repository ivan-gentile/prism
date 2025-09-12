#!/usr/bin/env python3
"""
Test script for PRISM-AD RAG system.
Run this after indexing documents to verify the RAG is working correctly.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from prism_ad.rag.risk_rag_memory import RiskRAGMemory, RiskRAGConfig
from prism_ad.config import (
    RAG_COLLECTION_NAME, RAG_CHROMA_PATH, RAG_EMBEDDING_MODEL,
    RAG_MIN_YEAR, RAG_TOP_K, RAG_FINAL_K, RAG_SCORE_THRESHOLD
)

async def test_rag_query():
    """Test the RAG system with sample queries."""
    print("🧪 Testing PRISM-AD RAG System...")
    
    # Initialize RAG memory
    config = RiskRAGConfig(
        chroma_base_path=RAG_CHROMA_PATH,
        collection_name=RAG_COLLECTION_NAME,
        embedding_model_name=RAG_EMBEDDING_MODEL,
        k_initial=RAG_TOP_K,
        k_final=RAG_FINAL_K,
        min_year=RAG_MIN_YEAR,
        score_threshold=RAG_SCORE_THRESHOLD,
    )
    
    try:
        rag_memory = RiskRAGMemory(config)
        print("✅ RAG memory initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize RAG memory: {e}")
        return
    
    # Test queries
    test_queries = [
        "What are the CSF biomarker thresholds for Alzheimer's progression?",
        "Amyloid PET SUVR cutoff values for MCI to dementia conversion",
        "ApoE4 risk factors for cognitive decline",
        "Hippocampal atrophy progression rates"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        try:
            results = await rag_memory.query(query)
            if results:
                print(f"   ✅ Found {len(results)} relevant chunks")
                for j, result in enumerate(results[:2], 1):  # Show first 2 results
                    meta = result.metadata or {}
                    print(f"   📄 Result {j}: {meta.get('doc_title', 'Unknown')} (score: {meta.get('score', 'N/A')})")
                    # Show snippet
                    content_preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
                    print(f"      {content_preview}")
            else:
                print("   ⚠️ No results found")
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
    
    print("\n🎉 RAG testing completed!")

if __name__ == "__main__":
    # Change to data directory
    import os
    os.chdir(Path(__file__).parent)
    asyncio.run(test_rag_query())
