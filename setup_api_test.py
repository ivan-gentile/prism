#!/usr/bin/env python3
"""
Setup script to test PRISM Clinician Agent with OpenAI API
"""

import os
import sys

def setup_api_key():
    """Setup OpenAI API key for testing"""
    
    print("=" * 60)
    print("PRISM CLINICIAN AGENT - API SETUP")
    print("=" * 60)
    print()
    
    # Check if API key is already set
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        print(f"OpenAI API key is already set: {api_key[:10]}...")
        return True
    
    print("OpenAI API key not found in environment variables.")
    print()
    print("To set your API key, you can:")
    print("1. Set it as an environment variable:")
    print("   PowerShell: $env:OPENAI_API_KEY='your-api-key-here'")
    print("   CMD: set OPENAI_API_KEY=your-api-key-here")
    print()
    print("2. Or create a .env file in the project root with:")
    print("   OPENAI_API_KEY=your-api-key-here")
    print()
    
    # Try to read from .env file
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"Found {env_file} file, checking for API key...")
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        key = line.split('=', 1)[1].strip()
                        os.environ['OPENAI_API_KEY'] = key
                        print(f"API key loaded from {env_file}: {key[:10]}...")
                        return True
        except Exception as e:
            print(f"Error reading {env_file}: {e}")
    
    print("No API key found. Please set your OpenAI API key to continue.")
    return False

def main():
    """Main setup function"""
    if setup_api_key():
        print("\nAPI key is ready! You can now run the clinician agent test.")
        print("Run: python test_clinician_with_api.py")
    else:
        print("\nPlease set your OpenAI API key and try again.")
        print("You can get an API key from: https://platform.openai.com/api-keys")

if __name__ == "__main__":
    main()
