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
# Correct URL for basepod1 environment (bpod1 is short for basepod1)
FASTWEB_BASE_URL = os.getenv("FASTWEB_BASE_URL", "https://bpod1.ai-factory.fastweb.it/v1")

# FastWeb models with their JWT tokens
# Use the exact model name that matches the JWT token keys
FASTWEB_MODEL = os.getenv("FASTWEB_MODEL", "Fastweb/FastwebMIIA-7B")

# JWT tokens for each FastWeb model (model-specific authentication)
# These are the hackathon JWT tokens for basepod1 environment
FASTWEB_TOKENS = {
    "Fastweb/FastwebMIIA-7B": os.getenv("FASTWEB_TOKEN_MIIA", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjAwMDEifQ.eyJpc3MiOiJodHRwczovL2FpLWZhY3RvcnkuZmFzdHdlYi5pdCIsInN1YiI6ImhhY2thdGhvbiIsInRlbmFudCI6ImJhc2Vwb2QxIiwibmFtZXNwYWNlIjoibmltLW1paWEiLCJpYXQiOjE3NTY0NTU4MjksImV4cCI6MTc4OTI1NzYwMH0.ZmFudGFzdGljand0"),
    "meta/llama-3-3-70b-instruct": os.getenv("FASTWEB_TOKEN_LLAMA", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjAwMDEifQ.eyJpc3MiOiJodHRwczovL2FpLWZhY3RvcnkuZmFzdHdlYi5pdCIsInN1YiI6ImhhY2thdGhvbiIsInRlbmFudCI6ImJhc2Vwb2QxIiwibmFtZXNwYWNlIjoibmltLWxsYW1hLTMtMy03MGItZnA4IiwiaWF0IjoxNzU2NDU1OTk4LCJleHAiOjE3NTc3MjE2MDB9.ZmFudGFzdGljand0"),
    "openai/whisper-large-v3-turbo": os.getenv("FASTWEB_TOKEN_WHISPER", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjAwMDEifQ.eyJpc3MiOiJodHRwczovL2FpLWZhY3RvcnkuZmFzdHdlYi5pdCIsInN1YiI6ImhhY2thdGhvbiIsInRlbmFudCI6ImJhc2Vwb2QxIiwibmFtZXNwYWNlIjoiY29lLXNwZWVjaDJ0ZXh0IiwiaWF0IjoxNzU2NDU2MDE5LCJleHAiOjE3NTc3MjE2MDB9.ZmFudGFzdGljand0"),
    "jinaai/jina-embeddings-v3": os.getenv("FASTWEB_TOKEN_JINA", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjAwMDEifQ.eyJpc3MiOiJodHRwczovL2FpLWZhY3RvcnkuZmFzdHdlYi5pdCIsInN1YiI6ImhhY2thdGhvbiIsInRlbmFudCI6ImJhc2Vwb2QxIiwibmFtZXNwYWNlIjoiY29lLWppbmEtZW1iZWRkaW5ncy12MyIsImlhdCI6MTc1NjQ1NjAzNSwiZXhwIjoxNzU3NzIxNjAwfQ.ZmFudGFzdGljand0"),
    "google/gemma-3-27b-it": os.getenv("FASTWEB_TOKEN_GEMMA", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjAwMDEifQ.eyJpc3MiOiJodHRwczovL2FpLWZhY3RvcnkuZmFzdHdlYi5pdCIsInN1YiI6ImhhY2thdGhvbiIsInRlbmFudCI6ImJhc2Vwb2QxIiwibmFtZXNwYWNlIjoiY29lLXZpc2lvbi1jYXB0aW9uaW5nIiwiaWF0IjoxNzU2NDU2MTY3LCJleHAiOjE3NTc3MjE2MDB9.ZmFudGFzdGljand0")
}

# Get the JWT token for the selected model
FASTWEB_API_KEY = FASTWEB_TOKENS.get(FASTWEB_MODEL)

# Debug output for FastWeb configuration
if FASTWEB_ENABLED:
    print(f"🔧 FastWeb Debug Info:")
    print(f"   Model: {FASTWEB_MODEL}")
    print(f"   Token configured: {bool(FASTWEB_API_KEY)}")
    print(f"   Base URL: {FASTWEB_BASE_URL}")
    if not FASTWEB_API_KEY:
        print(f"   ⚠️ No JWT token found for model: {FASTWEB_MODEL}")
        print(f"   Available models: {list(FASTWEB_TOKENS.keys())}")

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

# Optional: Override FastWeb model for specific agents
AGENT_FASTWEB_MODEL_OVERRIDE = {
    # Example: "classifier": "google/gemma-3-27b-it",
    # Example: "risk_calculator": "Fastweb/FastwebMIIA-7B",
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
