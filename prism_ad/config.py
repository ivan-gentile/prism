"""Configuration file for PRISM-AD system"""
import os

# API Keys - Store as environment variables in production
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Model Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")  # Default OpenAI endpoint
TEMPERATURE = 0.2  # Lower temperature for more consistent medical analysis

# Agent Names (must be valid Python identifiers - no spaces)
AGENT_NAMES = {
    "validator": "intake_validator",
    "normalizer": "data_normalizer",
    "classifier": "fda_classifier",
    "risk_calculator": "risk_calculator",
    "reporter": "report_synthesizer"
}
