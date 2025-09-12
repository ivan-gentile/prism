"""Configuration file for PRISM-AD system"""
import os
from dotenv import load_dotenv
load_dotenv()
# API Keys - Store as environment variables in production
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Model Configuration
MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.2  # Lower temperature for more consistent medical analysis

# Agent Names (must be valid Python identifiers - no spaces)
AGENT_NAMES = {
    "parser": "clinical_parser",
    "validator": "intake_validator",
    "normalizer": "data_normalizer",  # TO BE REMOVED
    "classifier": "fda_classifier",
    "quant_model": "quantitative_model",
    "risk_calculator": "risk_calculator",  # Will become aggregator
    "reporter": "report_synthesizer"
}
# --- RAG Settings ---
RAG_COLLECTION_NAME = "alz_guidelines"   # folder under data/collections, embeddings, chromadb
RAG_CHROMA_PATH = "data/chromadb"        # base path holding per-collection Chroma stores
RAG_EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI's default embedding model
RAG_MIN_YEAR = 2018
RAG_TOP_K = 18       # initial recall from Chroma before rerank
RAG_FINAL_K = 8      # after cross-encoder rerank
RAG_SCORE_THRESHOLD = 0.35
