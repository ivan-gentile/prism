#!/usr/bin/env python3
"""
Test completo per l'integrazione del RAG agent con il sistema PRISM-AD
"""

import asyncio
import json
import sys
from pathlib import Path

# Aggiungi il path per importare i moduli PRISM
sys.path.append('.')

from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.data.patient_model import PatientData, ApoE4Status

async def test_rag_integration():
    """Test dell'integrazione RAG agent"""
    print("🧪 Testing RAG Agent Integration")
    print("=" * 50)
    
    try:
        # Inizializza il sistema PRISM
        print("🚀 Initializing PRISM Agent System...")
        prism_system = PRISMAgentSystem()
        await prism_system.initialize_agents()
        
        # Crea dati paziente di test
        patient_data = {
            "age": 72,
            "sex": "female",
            "apoe4_copies": ApoE4Status.HETEROZYGOUS,
            "mmse_score": 26,
            "cdr_sum": 0.5,
            "adas_cog13": 12,
            "csf_abeta42": 480,
            "csf_abeta40": 8000,
            "csf_ptau181": 45,
            "csf_total_tau": 420,
            "amyloid_pet_suvr": 1.4,
            "hippocampus_volume_left": 2.1,
            "hippocampus_volume_right": 2.3
        }
        
        print("👤 Patient data created:")
        print(f"   Age: {patient_data['age']}")
        print(f"   MMSE: {patient_data['mmse_score']}")
        print(f"   CDR: {patient_data['cdr_sum']}")
        print(f"   CSF Aβ42: {patient_data['csf_abeta42']}")
        print(f"   CSF p-tau181: {patient_data['csf_ptau181']}")
        print(f"   Amyloid PET SUVR: {patient_data['amyloid_pet_suvr']}")
        
        # Test solo RAG agent
        print("\n🔍 Testing RAG Agent specifically...")
        patient = PatientData(**patient_data)
        patient_stage = prism_system.determine_fda_stage(patient)
        print(f"📊 Determined stage: {patient_stage}")
        
        # Esegui solo RAG agent
        rag_result = await prism_system._run_rag_agent(patient, patient_stage)
        print(f"✅ RAG Agent completed")
        print(f"📄 RAG Response length: {len(rag_result)} characters")
        
        # Prova a parsare la risposta JSON
        try:
            # Estrai JSON dalla risposta
            if "```json" in rag_result:
                json_start = rag_result.find("```json") + 7
                json_end = rag_result.find("```", json_start)
                json_str = rag_result[json_start:json_end].strip()
            elif "{" in rag_result and "}" in rag_result:
                json_start = rag_result.find("{")
                json_end = rag_result.rfind("}") + 1
                json_str = rag_result[json_start:json_end]
            else:
                json_str = rag_result
            
            rag_json = json.loads(json_str)
            print("✅ RAG response is valid JSON")
            print(f"   Agent: {rag_json.get('agent', 'unknown')}")
            print(f"   Stage: {rag_json.get('stage_classification', 'unknown')}")
            print(f"   Risk 5y: {rag_json.get('risk_5y', 'unknown')}")
            print(f"   Evidence count: {len(rag_json.get('evidence', []))}")
            
        except json.JSONDecodeError as e:
            print(f"⚠️ RAG response is not valid JSON: {e}")
            print(f"📄 Raw response: {rag_result[:500]}...")
        
        # Test sistema completo con RAG
        print("\n🏥 Testing complete PRISM system with RAG...")
        full_result = await prism_system.process_patient(patient_data)
        print(f"✅ Complete system test completed")
        print(f"📄 Final report length: {len(full_result)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in RAG integration test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if 'prism_system' in locals():
            await prism_system.close()

async def test_rag_system_only():
    """Test solo del sistema RAG senza agenti"""
    print("\n🧠 Testing RAG System Only")
    print("=" * 30)
    
    try:
        from prism_ad.rag.rag_agent import create_clinical_rag_agent
        
        # Crea RAG agent
        print("🔧 Creating RAG agent...")
        rag_agent = create_clinical_rag_agent(
            pdf_directory="./clinical_pdfs",
            persist_directory="./simple_chroma_db",
            collection_name="clinical_documents"
        )
        
        # Dati paziente di test
        patient_data = {
            "stage": "Stage2",
            "age": 68,
            "sex": "female",
            "mmse": 28,
            "cdr": 0.0,
            "csf_abeta42": 520,
            "csf_ptau181": 35,
            "csf_total_tau": 380,
            "amyloid_pet_suvr": 1.2,
            "hippocampus_volume_left": 2.4,
            "hippocampus_volume_right": 2.5
        }
        
        print("👤 Testing with patient data:")
        for key, value in patient_data.items():
            print(f"   {key}: {value}")
        
        # Test ricerca evidenze
        print("\n🔍 Testing evidence retrieval...")
        evidence = rag_agent.get_risk_evidence(patient_data)
        print(f"📚 Evidence categories: {list(evidence.keys())}")
        
        for category, results in evidence.items():
            if results:
                print(f"   {category}: {len(results)} results")
                for i, result in enumerate(results[:2], 1):
                    print(f"     {i}. Score: {result.get('similarity_score', 0):.3f}")
                    print(f"        Text: {result.get('text', '')[:100]}...")
        
        # Test contesto per agente
        print("\n📄 Testing agent context generation...")
        context = rag_agent.get_agent_context(patient_data)
        print(f"📄 Context length: {len(context)} characters")
        print(f"📄 Context preview:")
        print(context[:300] + "..." if len(context) > 300 else context)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in RAG system test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Funzione principale"""
    print("🚀 PRISM-AD RAG Integration Test")
    print("=" * 60)
    
    # Test 1: Solo sistema RAG
    if await test_rag_system_only():
        print("✅ RAG System test passed")
    else:
        print("❌ RAG System test failed")
        return
    
    # Test 2: Integrazione completa
    if await test_rag_integration():
        print("✅ RAG Integration test passed")
    else:
        print("❌ RAG Integration test failed")
        return
    
    print("\n🎉 All RAG tests completed successfully!")
    print("\n📋 RAG Agent is now integrated and ready for use!")

if __name__ == "__main__":
    asyncio.run(main())
