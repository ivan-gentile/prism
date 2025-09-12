#!/usr/bin/env python
"""Debug config values directly"""
import os
import sys

# Set FASTWEB_ENABLED to true for testing
os.environ["FASTWEB_ENABLED"] = "true"

# Import everything fresh
if 'prism_ad.config' in sys.modules:
    del sys.modules['prism_ad.config']

print("Environment variables before import:")
print(f"  FASTWEB_MODEL={os.getenv('FASTWEB_MODEL', 'Not set')}")
print(f"  FASTWEB_BASE_URL={os.getenv('FASTWEB_BASE_URL', 'Not set')}")

# Import config
from prism_ad import config

print("\nValues from config.py:")
print(f"  config.FASTWEB_MODEL={config.FASTWEB_MODEL}")
print(f"  config.FASTWEB_BASE_URL={config.FASTWEB_BASE_URL}")
print(f"  config.FASTWEB_API_KEY={'Set' if config.FASTWEB_API_KEY else 'Not set'}")

print("\nProvider configs:")
print(f"  fastweb config: {config.PROVIDER_CONFIGS.get('fastweb', {})}")
