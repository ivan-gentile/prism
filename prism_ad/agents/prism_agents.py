"""PRISM-AD Multi-Agent System Implementation"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from pydantic import BaseModel

from prism_ad.config import OPENAI_API_KEY, MODEL_NAME, AGENT_NAMES
from prism_ad.agents.agent_prompts import (
    RAG_AGENT_PROMPT,
    CLINICIAN_AGENT_PROMPT,
    COX_AGENT_PROMPT,
    CONSENSUS_AGENT_PROMPT,
    FINAL_RESPONSE_AGENT_PROMPT
)
from prism_ad.data.patient_model import (
    PatientData, 
    ValidationResult,
    NormalizationResult,
    ClassificationResult,
    RiskAssessment,
    ClinicalReport,
    REFERENCE_RANGES
)


class PRISMAgentSystem:
    """Multi-agent system for Alzheimer's Disease risk assessment using RAG, Clinician, Cox, Consensus, and Final Response agents"""
    
    def __init__(self, model_name: str = MODEL_NAME, api_key: str = OPENAI_API_KEY):
        """Initialize the PRISM-AD agent system"""
        self.model_name = model_name
        self.api_key = api_key
        self.agents = {}
        self.model_client = None
        self.conversation_history = []
        self.processing_results = {}
        
    async def initialize_agents(self):
        """Create and initialize all five specialized agents"""
        print("🔧 Initializing PRISM-AD Agent System...")
        
        # Create model client
        self.model_client = OpenAIChatCompletionClient(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.2  # Low temperature for consistent medical analysis
        )
        
        # Create each specialized agent
        self.agents["rag"] = AssistantAgent(
            name="RAG_Agent",
            model_client=self.model_client,
            system_message=RAG_AGENT_PROMPT,
            max_tool_iterations=1
        )
        
        self.agents["clinician"] = AssistantAgent(
            name="Clinician_Agent",
            model_client=self.model_client,
            system_message=CLINICIAN_AGENT_PROMPT,
            max_tool_iterations=1
        )
        
        self.agents["cox"] = AssistantAgent(
            name="Cox_Agent",
            model_client=self.model_client,
            system_message=COX_AGENT_PROMPT,
            max_tool_iterations=1
        )
        
        self.agents["consensus"] = AssistantAgent(
            name="Consensus_Agent",
            model_client=self.model_client,
            system_message=CONSENSUS_AGENT_PROMPT,
            max_tool_iterations=1
        )
        
        self.agents["final_response"] = AssistantAgent(
            name="Final_Response_Agent",
            model_client=self.model_client,
            system_message=FINAL_RESPONSE_AGENT_PROMPT,
            max_tool_iterations=1
        )
        
        print("✅ All agents initialized successfully")
        
    async def process_patient(self, patient_data: Dict[str, Any]) -> str:
        """Process patient data through the complete agent pipeline"""
        print("\n" + "="*60)
        print("🏥 PRISM-AD ASSESSMENT PIPELINE STARTED")
        print("="*60)
        
        # Convert to PatientData model
        try:
            patient = PatientData(**patient_data)
        except Exception as e:
            print(f"❌ Error parsing patient data: {e}")
            raise
            
        # Step 1: RAG Agent Analysis
        print("\n🔍 Step 1: RAG AGENT ANALYSIS")
        print("-"*40)
        rag_result = await self._run_rag_agent(patient)
        
        # Step 2: Clinician Agent Analysis
        print("\n👨‍⚕️ Step 2: CLINICIAN AGENT ANALYSIS")
        print("-"*40)
        clinician_result = await self._run_clinician_agent(patient)
        
        # Step 3: Cox Agent Analysis
        print("\n📊 Step 3: COX AGENT ANALYSIS")
        print("-"*40)
        cox_result = await self._run_cox_agent(patient)
        
        # Step 4: Consensus Agent
        print("\n🤝 Step 4: CONSENSUS AGENT")
        print("-"*40)
        consensus_result = await self._run_consensus_agent(rag_result, clinician_result, cox_result)
        
        # Step 5: Final Response Agent
        print("\n📄 Step 5: FINAL RESPONSE AGENT")
        print("-"*40)
        final_report = await self._run_final_response_agent(consensus_result)
        
        print("\n" + "="*60)
        print("✅ ASSESSMENT COMPLETE")
        print("="*60)
        
        return final_report
        
    async def _run_rag_agent(self, patient: PatientData) -> str:
        """Run the RAG agent"""
        # Create input JSON for the agent
        input_data = {
            "patient_profile": {
                "age": patient.age,
                "sex": patient.sex or "unknown",
                "apoE4_status": patient.apoe4_copies.value if patient.apoe4_copies else "unknown",
                "mmse": patient.mmse_score,
                "cdr": patient.cdr_sum or 0.0,
                "adas13": patient.adas_cog13,
                "adcs_pacc": "not_available",
                "ravlt_total": 45,  # Default value
                "csf_abeta42": patient.csf_abeta42,
                "csf_abeta42_abeta40_ratio": (patient.csf_abeta42 / patient.csf_abeta40) if patient.csf_abeta42 and patient.csf_abeta40 else "not_available",
                "csf_ptau181": patient.csf_ptau181,
                "csf_ttau": patient.csf_total_tau,
                "pet_piB_centiloids": patient.amyloid_pet_suvr,
                "mri_hippocampal_volume": (patient.hippocampus_volume_left + patient.hippocampus_volume_right) / 2 if patient.hippocampus_volume_left and patient.hippocampus_volume_right else "not_available",
                "mri_ventricular_volume": "not_available"
            },
            "normative_refs": [
                "ADNI_norms_IF>5_2020",
                "DOI:10.1000/xyz123 (2021)"
            ],
            "stage_hint": "Stage1",
            "question": "Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor)"
        }
        
        task = f"""Analyze the following patient data and provide a JSON response following the unified schema:

{json.dumps(input_data, indent=2)}

Please provide your analysis in the exact JSON format specified in your system prompt."""
        
        result = await self.agents["rag"].run(task=task)
        rag_response = result.messages[-1].content if result.messages else ""
        print(f"RAG Agent says: {rag_response[:200]}...")
        
        self.processing_results["rag"] = rag_response
        return rag_response
        
    async def _run_clinician_agent(self, patient: PatientData) -> str:
        """Run the Clinician agent"""
        # Create input JSON for the agent (same format as RAG)
        input_data = {
            "patient_profile": {
                "age": patient.age,
                "sex": patient.sex or "unknown",
                "apoE4_status": patient.apoe4_copies.value if patient.apoe4_copies else "unknown",
                "mmse": patient.mmse_score,
                "cdr": patient.cdr_sum or 0.0,
                "adas13": patient.adas_cog13,
                "adcs_pacc": "not_available",
                "ravlt_total": 45,  # Default value
                "csf_abeta42": patient.csf_abeta42,
                "csf_abeta42_abeta40_ratio": (patient.csf_abeta42 / patient.csf_abeta40) if patient.csf_abeta42 and patient.csf_abeta40 else "not_available",
                "csf_ptau181": patient.csf_ptau181,
                "csf_ttau": patient.csf_total_tau,
                "pet_piB_centiloids": patient.amyloid_pet_suvr,
                "mri_hippocampal_volume": (patient.hippocampus_volume_left + patient.hippocampus_volume_right) / 2 if patient.hippocampus_volume_left and patient.hippocampus_volume_right else "not_available",
                "mri_ventricular_volume": "not_available"
            },
            "normative_refs": [
                "ADNI_norms_IF>5_2020",
                "DOI:10.1000/xyz123 (2021)"
            ],
            "stage_hint": "Stage1",
            "question": "Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor)"
        }
        
        task = f"""Analyze the following patient data and provide a JSON response following the unified schema:

{json.dumps(input_data, indent=2)}

Please provide your analysis in the exact JSON format specified in your system prompt."""
        
        result = await self.agents["clinician"].run(task=task)
        clinician_response = result.messages[-1].content if result.messages else ""
        print(f"Clinician Agent says: {clinician_response[:200]}...")
        
        self.processing_results["clinician"] = clinician_response
        return clinician_response
        
    async def _run_cox_agent(self, patient: PatientData) -> str:
        """Run the Cox agent"""
        # Create input JSON for the agent (same format as RAG)
        input_data = {
            "patient_profile": {
                "age": patient.age,
                "sex": patient.sex or "unknown",
                "apoE4_status": patient.apoe4_copies.value if patient.apoe4_copies else "unknown",
                "mmse": patient.mmse_score,
                "cdr": patient.cdr_sum or 0.0,
                "adas13": patient.adas_cog13,
                "adcs_pacc": "not_available",
                "ravlt_total": 45,  # Default value
                "csf_abeta42": patient.csf_abeta42,
                "csf_abeta42_abeta40_ratio": (patient.csf_abeta42 / patient.csf_abeta40) if patient.csf_abeta42 and patient.csf_abeta40 else "not_available",
                "csf_ptau181": patient.csf_ptau181,
                "csf_ttau": patient.csf_total_tau,
                "pet_piB_centiloids": patient.amyloid_pet_suvr,
                "mri_hippocampal_volume": (patient.hippocampus_volume_left + patient.hippocampus_volume_right) / 2 if patient.hippocampus_volume_left and patient.hippocampus_volume_right else "not_available",
                "mri_ventricular_volume": "not_available"
            },
            "normative_refs": [
                "ADNI_norms_IF>5_2020",
                "DOI:10.1000/xyz123 (2021)"
            ],
            "stage_hint": "Stage1",
            "question": "Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor)"
        }
        
        task = f"""Analyze the following patient data and provide a JSON response following the unified schema:

{json.dumps(input_data, indent=2)}

Please provide your analysis in the exact JSON format specified in your system prompt."""
        
        result = await self.agents["cox"].run(task=task)
        cox_response = result.messages[-1].content if result.messages else ""
        print(f"Cox Agent says: {cox_response[:200]}...")
        
        self.processing_results["cox"] = cox_response
        return cox_response
        
    async def _run_consensus_agent(self, rag_result: str, clinician_result: str, cox_result: str) -> str:
        """Run the Consensus agent"""
        task = f"""You have received three solver outputs from RAG, Clinician, and Cox agents. Please analyze them and provide a consensus JSON response.

RAG Agent Output:
{rag_result}

Clinician Agent Output:
{clinician_result}

Cox Agent Output:
{cox_result}

Please provide your consensus analysis in the exact JSON format specified in your system prompt with "agent": "consensus"."""
        
        result = await self.agents["consensus"].run(task=task)
        consensus_response = result.messages[-1].content if result.messages else ""
        print(f"Consensus Agent says: {consensus_response[:200]}...")
        
        self.processing_results["consensus"] = consensus_response
        return consensus_response
        
    async def _run_final_response_agent(self, consensus_result: str) -> str:
        """Run the Final Response agent"""
        task = f"""Transform the following consensus JSON into a professional Italian report for the treating neurologist:

{consensus_result}

Please provide your final report in Italian following the structure specified in your system prompt."""
        
        result = await self.agents["final_response"].run(task=task)
        final_response = result.messages[-1].content if result.messages else ""
        print(f"Final Response Agent says: {final_response[:200]}...")
        
        self.processing_results["final_response"] = final_response
        return final_response
        
    async def close(self):
        """Clean up resources"""
        if self.model_client:
            await self.model_client.close()
            print("🔒 Model client closed")
            
    async def get_agent_conversation(self, agent_name: str) -> List[str]:
        """Get conversation history for a specific agent"""
        if agent_name in self.processing_results:
            return self.processing_results[agent_name]
        return []
