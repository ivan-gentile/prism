#!/usr/bin/env python3
"""
Test script to verify PRISM-AD integration with the infra system
"""
import sys
import os
import asyncio

# Add the parent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from model.simulator import PRISMAlzheimerModel


async def test_integration():
    """Test the PRISM-AD integration"""
    print("🧪 Testing PRISM-AD Integration with Infrastructure")
    print("="*60)
    
    # Sample clinical text for testing
    test_cases = [
        {
            "name": "MCI Case",
            "text": """
            75-year-old male with memory complaints and cognitive decline over 2 years.
            MMSE score: 23/30, showing deficits in recall and orientation.
            Patient is ApoE4 positive (1 copy). 
            CSF analysis: Aβ42 480 pg/mL (low), p-tau 42 pg/mL (elevated).
            Amyloid PET positive with SUVR 1.48.
            Patient has difficulty managing finances but still independent in basic activities.
            """
        },
        {
            "name": "High Risk Case",
            "text": """
            82-year-old female with progressive cognitive decline.
            MMSE: 18/30, MoCA: 16/30.
            ApoE4 homozygous (2 copies).
            CSF: Aβ42 320 pg/mL, p-tau 68 pg/mL, total tau 520 pg/mL.
            Hippocampal atrophy evident on MRI.
            Requires assistance with complex activities.
            """
        },
        {
            "name": "Simple Test",
            "text": "70 year old with memory problems, MMSE 24"
        }
    ]
    
    model = PRISMAlzheimerModel()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        print(f"Input: {test_case['text'][:100]}...")
        
        try:
            # Test the async processing
            result = await model.process_async(test_case['text'].strip())
            
            if result["status"] == "success":
                print(f"✅ SUCCESS - Risk Level: {result['risk_level']}")
                print(f"   FDA Stage: {result['fda_stage']}")
                print(f"   Confidence: {result.get('confidence_score', 'N/A')}")
            else:
                print(f"❌ ERROR: {result.get('error_message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
    
    # Test the synchronous wrapper (used by FastAPI)
    print(f"\n🔄 Testing Synchronous Wrapper")
    print("-" * 40)
    
    try:
        sync_response = model.process("65 year old with mild cognitive impairment, MMSE 25")
        print("✅ Synchronous processing successful")
        print(f"Response length: {len(sync_response)} characters")
        print(f"Sample: {sync_response[:200]}...")
    except Exception as e:
        print(f"❌ Synchronous processing failed: {e}")
    
    # Clean up
    await model.close()
    print(f"\n🏁 Integration test completed!")


if __name__ == "__main__":
    asyncio.run(test_integration())
