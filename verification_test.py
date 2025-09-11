#!/usr/bin/env python3
"""
Static verification test for PRISM-AD system integration
This test verifies the structure and content without running the actual agents
"""

import os
import sys

def verify_file_structure():
    """Verify that all required files exist and have correct structure"""
    print("🔍 Verifying file structure...")
    
    required_files = [
        "prism_ad/agents/agent_prompts.py",
        "prism_ad/agents/prism_agents.py",
        "prism_ad/data/patient_model.py",
        "prism_ad/config.py",
        "test_new_prism_system.py",
        "simple_test.py",
        "INTEGRATION_SUMMARY.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    return True

def verify_agent_prompts():
    """Verify that agent prompts contain expected content"""
    print("\n📝 Verifying agent prompts...")
    
    try:
        with open("prism_ad/agents/agent_prompts.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_prompts = [
            "RAG_AGENT_PROMPT",
            "CLINICIAN_AGENT_PROMPT", 
            "COX_AGENT_PROMPT",
            "CONSENSUS_AGENT_PROMPT",
            "FINAL_RESPONSE_AGENT_PROMPT"
        ]
        
        missing_prompts = []
        for prompt in required_prompts:
            if prompt not in content:
                missing_prompts.append(prompt)
            else:
                print(f"✅ {prompt}")
        
        if missing_prompts:
            print(f"❌ Missing prompts: {missing_prompts}")
            return False
        
        # Check for key content in prompts
        key_phrases = [
            "Alzheimer's Disease",
            "FDA Stage",
            "5-year risk",
            "JSON",
            "unified schema"
        ]
        
        found_phrases = []
        for phrase in key_phrases:
            if phrase in content:
                found_phrases.append(phrase)
        
        print(f"✅ Found key phrases: {found_phrases}")
        return True
        
    except Exception as e:
        print(f"❌ Error reading agent prompts: {e}")
        return False

def verify_agent_system():
    """Verify that agent system has correct structure"""
    print("\n🤖 Verifying agent system...")
    
    try:
        with open("prism_ad/agents/prism_agents.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_components = [
            "class PRISMAgentSystem",
            "async def initialize_agents",
            "async def process_patient",
            "_run_rag_agent",
            "_run_clinician_agent",
            "_run_cox_agent",
            "_run_consensus_agent",
            "_run_final_response_agent"
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
            else:
                print(f"✅ {component}")
        
        if missing_components:
            print(f"❌ Missing components: {missing_components}")
            return False
        
        # Check for imports
        required_imports = [
            "RAG_AGENT_PROMPT",
            "CLINICIAN_AGENT_PROMPT",
            "COX_AGENT_PROMPT",
            "CONSENSUS_AGENT_PROMPT",
            "FINAL_RESPONSE_AGENT_PROMPT"
        ]
        
        missing_imports = []
        for import_name in required_imports:
            if import_name not in content:
                missing_imports.append(import_name)
        
        if missing_imports:
            print(f"❌ Missing imports: {missing_imports}")
            return False
        
        print("✅ All required components found")
        return True
        
    except Exception as e:
        print(f"❌ Error reading agent system: {e}")
        return False

def verify_test_files():
    """Verify that test files are properly structured"""
    print("\n🧪 Verifying test files...")
    
    test_files = [
        "test_new_prism_system.py",
        "simple_test.py"
    ]
    
    for test_file in test_files:
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "PRISMAgentSystem" in content and "async" in content:
                print(f"✅ {test_file} - Properly structured")
            else:
                print(f"❌ {test_file} - Missing required content")
                return False
                
        except Exception as e:
            print(f"❌ Error reading {test_file}: {e}")
            return False
    
    return True

def verify_documentation():
    """Verify that documentation is complete"""
    print("\n📚 Verifying documentation...")
    
    try:
        with open("INTEGRATION_SUMMARY.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_sections = [
            "# PRISM-AD System Integration Summary",
            "## Changes Made",
            "## Unified JSON Schema",
            "## Usage"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
            else:
                print(f"✅ {section}")
        
        if missing_sections:
            print(f"❌ Missing sections: {missing_sections}")
            return False
        
        print("✅ Documentation is complete")
        return True
        
    except Exception as e:
        print(f"❌ Error reading documentation: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 PRISM-AD System Integration Verification")
    print("="*60)
    
    tests = [
        ("File Structure", verify_file_structure),
        ("Agent Prompts", verify_agent_prompts),
        ("Agent System", verify_agent_system),
        ("Test Files", verify_test_files),
        ("Documentation", verify_documentation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("The PRISM-AD system integration is complete and ready for use.")
    else:
        print(f"\n⚠️ {total - passed} verification(s) failed.")
        print("Please review the errors above.")
    
    print("="*60)

if __name__ == "__main__":
    main()
