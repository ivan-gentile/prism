#!/usr/bin/env python
"""Quick script to check FastWeb JWT token configuration and status"""
import os
import json
import base64
from datetime import datetime
from prism_ad.config import FASTWEB_TOKENS, FASTWEB_MODEL, FASTWEB_ENABLED

def decode_jwt_payload(token):
    """Decode JWT payload to check expiry and other details"""
    try:
        # JWT structure: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (add padding if needed)
        payload = parts[1]
        padding = 4 - (len(payload) % 4)
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        return None

def check_token_status(token_name, token):
    """Check the status of a JWT token"""
    if not token:
        return "❌ Not configured"
    
    if token.startswith("your_") or token == "":
        return "❌ Placeholder value"
    
    payload = decode_jwt_payload(token)
    if not payload:
        return "⚠️ Invalid JWT format"
    
    # Check expiry
    if 'exp' in payload:
        exp_timestamp = payload['exp']
        exp_date = datetime.fromtimestamp(exp_timestamp)
        now = datetime.now()
        
        if now > exp_date:
            return f"❌ Expired on {exp_date.strftime('%Y-%m-%d %H:%M')}"
        else:
            days_left = (exp_date - now).days
            return f"✅ Valid until {exp_date.strftime('%Y-%m-%d')} ({days_left} days left)"
    
    return "✅ Valid (no expiry date)"

def main():
    print("\n" + "="*60)
    print("🔐 FastWeb JWT Token Configuration Check")
    print("="*60)
    
    print(f"\n📋 FastWeb Status:")
    print(f"  • FastWeb Enabled: {FASTWEB_ENABLED}")
    print(f"  • Default Model: {FASTWEB_MODEL}")
    
    print("\n🔑 JWT Token Status:")
    print("-" * 40)
    
    for model_name, token in FASTWEB_TOKENS.items():
        status = check_token_status(model_name, token)
        is_default = " (DEFAULT)" if model_name == FASTWEB_MODEL else ""
        print(f"\n{model_name}{is_default}:")
        print(f"  Status: {status}")
        
        if token and not token.startswith("your_"):
            payload = decode_jwt_payload(token)
            if payload:
                print(f"  Environment: {payload.get('tenant', 'Unknown')}")
                print(f"  Application: {payload.get('sub', 'Unknown')}")
                print(f"  Namespace: {payload.get('namespace', 'Unknown')}")
    
    # Check current token for default model
    print("\n" + "="*60)
    current_token = FASTWEB_TOKENS.get(FASTWEB_MODEL)
    if current_token and not current_token.startswith("your_"):
        print(f"✅ JWT token configured for default model: {FASTWEB_MODEL}")
    else:
        print(f"❌ No valid JWT token for default model: {FASTWEB_MODEL}")
        print("   Please configure the appropriate token in your .env file")
    
    # Show environment variable names for configuration
    print("\n📝 To configure tokens, set these environment variables:")
    print("  • FASTWEB_TOKEN_MIIA     → Fastweb/FastwebMIIA-7B")
    print("  • FASTWEB_TOKEN_LLAMA    → meta/llama-3-3-70b-instruct")
    print("  • FASTWEB_TOKEN_GEMMA    → google/gemma-3-27b-it")
    print("  • FASTWEB_TOKEN_JINA     → jinaai/jina-embeddings-v3")
    print("  • FASTWEB_TOKEN_WHISPER  → openai/whisper-large-v3-turbo")
    
    print("\n💡 Tip: Copy env.example to .env and update with your tokens")
    print("="*60)

if __name__ == "__main__":
    main()
