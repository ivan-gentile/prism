"""Configuration file for PRISM-AD system - Enhanced with FastWeb support"""
import os
from dotenv import load_dotenv
load_dotenv()

# Primary API configuration (OpenAI)
PRIMARY_PROVIDER = os.getenv("PRIMARY_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PRIMARY_API_KEY = OPENAI_API_KEY  # Keep backward compatibility
PRIMARY_BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")
PRIMARY_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")

# FastWeb configuration for specific agents
FASTWEB_ENABLED = os.getenv("FASTWEB_ENABLED", "false").lower() == "true"
FASTWEB_API_KEY = os.getenv("FASTWEB_API_KEY")
FASTWEB_BASE_URL = os.getenv("FASTWEB_BASE_URL", "https://api.ai-fastweb.it/v1")
FASTWEB_MODEL = os.getenv("FASTWEB_MODEL", "Llama-3.3-70B-Instruct")

# Legacy support - keep these for backward compatibility
MODEL_NAME = PRIMARY_MODEL
TEMPERATURE = 0.2  # Lower temperature for more consistent medical analysis

# Agent-specific model mapping
# Determines which provider each agent uses
AGENT_MODEL_MAP = {
    "parser": "primary",  # Uses OpenAI
    "validator": "primary",  # Uses OpenAI
    "classifier": "fastweb" if FASTWEB_ENABLED else "primary",  # Can use FastWeb
    "quant_model": "primary",  # Needs tool support, stays with OpenAI
    "risk_calculator": "fastweb" if FASTWEB_ENABLED else "primary",  # Can use FastWeb
    "aggregator": "fastweb" if FASTWEB_ENABLED else "primary",  # Future aggregator
    "reporter": "primary"  # Uses OpenAI
}

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

# Provider configurations
PROVIDER_CONFIGS = {
    "primary": {
        "api_key": PRIMARY_API_KEY,
        "base_url": PRIMARY_BASE_URL,
        "model": PRIMARY_MODEL,
        "temperature": TEMPERATURE
    },
    "fastweb": {
        "api_key": FASTWEB_API_KEY,
        "base_url": FASTWEB_BASE_URL,
        "model": FASTWEB_MODEL,
        "temperature": TEMPERATURE
    }
}
