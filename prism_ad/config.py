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
