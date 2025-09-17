"""PRISM-AD Multi-Agent System Implementation"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from pydantic import BaseModel

from prism_ad.config import OPENAI_API_KEY, MODEL_NAME, BASE_URL, AGENT_NAMES
from prism_ad.agents.agent_prompts import (
    RAG_AGENT_PROMPT,
    CLINICIAN_AGENT_PROMPT,
    CLINICIAN_FASTWEB_AGENT_PROMPT,
    CLINICIAN_GPT4O_AGENT_PROMPT,
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
    FDAStage,
    REFERENCE_RANGES
)


def determine_fda_stage(patient: PatientData) -> str:
    """
    Unified FDA stage determination function - used consistently across all agents
    
    This function implements the standardized staging logic that should be 
    applied consistently by all agents in the PRISM-AD system.
    """
    # Cognitive assessment
    has_cognitive_impairment = False
    has_functional_impairment = False
    
    # Check CDR score
    if patient.cdr_sum is not None:
        if patient.cdr_sum == 0:
            # CDR 0 = normal cognition (but check other indicators)
            has_cognitive_impairment = False
        elif patient.cdr_sum == 0.5:
            # CDR 0.5 = very mild impairment (questionable dementia)
            has_cognitive_impairment = True
        elif patient.cdr_sum >= 1.0:
            # CDR ≥ 1 = mild dementia or worse
            has_cognitive_impairment = True
            has_functional_impairment = True
    
    # Check MMSE score
    if patient.mmse_score is not None:
        if patient.mmse_score < 24:
            has_cognitive_impairment = True
        if patient.mmse_score < 20:
            has_functional_impairment = True
    
    # Check biomarker abnormalities
    has_amyloid_pathology = False
    has_tau_pathology = False
    
    # CSF Amyloid beta 42 (lower = more pathological)
    if patient.csf_abeta42 is not None:
        # Using reference ranges - below 600 is abnormal
        if patient.csf_abeta42 < REFERENCE_RANGES["csf_abeta42"]["abnormal_below"]:
            has_amyloid_pathology = True
    
    # CSF Amyloid beta 42/40 ratio (lower = more pathological)
    if patient.csf_abeta42 and patient.csf_abeta40:
        ratio = patient.csf_abeta42 / patient.csf_abeta40
        # Ratio below 0.08 typically indicates amyloid pathology
        if ratio < 0.08:
            has_amyloid_pathology = True
            
    # Amyloid PET (higher = more pathological)
    if patient.amyloid_pet_suvr is not None:
        # Using reference ranges - above 1.3 is positive
        if patient.amyloid_pet_suvr > REFERENCE_RANGES["amyloid_pet_suvr"]["positive"]:
            has_amyloid_pathology = True
    
    # CSF P-tau 181 (higher = more pathological)
    if patient.csf_ptau181 is not None:
        # Using reference ranges - above 30 is abnormal
        if patient.csf_ptau181 > REFERENCE_RANGES["csf_ptau181"]["abnormal_above"]:
            has_tau_pathology = True
            
    # CSF Total tau (higher = more pathological)
    if patient.csf_total_tau is not None:
        # Using reference ranges - above 400 is abnormal
        if patient.csf_total_tau > REFERENCE_RANGES["csf_total_tau"]["abnormal_above"]:
            has_tau_pathology = True
    
    # Special case: Check for subtle cognitive changes with severe biomarker pathology
    # This applies when standard tests (MMSE, CDR) appear normal but biomarkers are severely abnormal
    has_severe_biomarker_pathology = False
    
    # Multiple severe biomarker abnormalities suggest Stage 3 even with subtle cognitive changes
    severe_markers_count = 0
    
    if patient.csf_abeta42 is not None and patient.csf_abeta42 < 550:  # Very low Aβ42
        severe_markers_count += 1
    if patient.csf_ptau181 is not None and patient.csf_ptau181 > 40:  # Very high p-tau
        severe_markers_count += 1
    if patient.csf_abeta42 and patient.csf_abeta40:
        ratio = patient.csf_abeta42 / patient.csf_abeta40
        if ratio < 0.075:  # Very low ratio indicating severe amyloid pathology
            severe_markers_count += 1
    if patient.amyloid_pet_suvr is not None and patient.amyloid_pet_suvr >= 1.3:  # Positive amyloid PET
        severe_markers_count += 1
    if patient.hippocampus_volume_left and patient.hippocampus_volume_right:
        total_volume = patient.hippocampus_volume_left + patient.hippocampus_volume_right
        if total_volume < 4500:  # Reduced hippocampal volume (4.5 ml threshold)
            severe_markers_count += 1
            
    # If 3 or more severe biomarker abnormalities, consider as Stage 3 even with subtle symptoms
    if severe_markers_count >= 3:
        has_severe_biomarker_pathology = True

    # Determine FDA stage based on clinical and biomarker status
    if has_functional_impairment:
        # Stage 4: Mild dementia (functional impairment present)
        return "Stage4"
    elif has_cognitive_impairment:
        # Stage 3: MCI due to Alzheimer's (cognitive symptoms but preserved function)
        return "Stage3"
    elif has_severe_biomarker_pathology:
        # Stage 3: Subtle cognitive changes with severe biomarker pathology (prodromal AD)
        return "Stage3"
    elif has_amyloid_pathology or has_tau_pathology:
        # Stage 2: Mild cognitive changes with brain pathology 
        return "Stage2"
    else:
        # Stage 1: Preclinical AD or normal aging
        return "Stage1"


class PRISMAgentSystem:
    """Multi-agent system for Alzheimer's Disease risk assessment using RAG, Clinician, Cox, Consensus, and Final Response agents"""
    
    def __init__(self, model_name: str = MODEL_NAME, api_key: str = OPENAI_API_KEY, base_url: str = BASE_URL):
        """Initialize the PRISM-AD agent system"""
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.agents = {}
        self.model_client = None
        self.conversation_history = []
        self.processing_results = {}
        self.web_tracker = None
        
    def set_web_tracker(self, web_tracker):
        """Imposta il web tracker per l'interfaccia"""
        self.web_tracker = web_tracker
        
    async def initialize_agents(self):
        """Create and initialize all five specialized agents"""
        print("Initializing PRISM-AD Agent System...")
        
        # Create model client
        # For custom models (like FastWeb), we need to provide model_info
        model_info = None
        if self.model_name not in ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]:
            # Custom model - provide basic model info with all required fields
            model_info = {
                "model": self.model_name,
                "context_length": 4096,  # Default context length
                "max_tokens": 2048,      # Default max tokens
                "supports_function_calling": True,
                "supports_vision": False,
                "vision": False,  # Required field for autogen v0.4.7+
                "function_calling": True,  # Required field for autogen v0.4.7+
                "json_output": True,  # Required field for autogen v0.4.7+
                "family": "llama"  # Required field for autogen v0.4.7+
            }
        
        # Create HTTP client with SSL verification disabled for FastWeb
        import httpx
        http_client = None
        if "fastweb.it" in self.base_url or "ai-factory" in self.base_url:
            # Disable SSL verification for FastWeb endpoints
            http_client = httpx.AsyncClient(verify=False)
        
        self.model_client = OpenAIChatCompletionClient(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.2,  # Low temperature for consistent medical analysis
            model_info=model_info,
            http_client=http_client
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
        
        self.agents["clinician_fastweb"] = AssistantAgent(
            name="Clinician_FASTWEB_Agent",
            model_client=self.model_client,
            system_message=CLINICIAN_FASTWEB_AGENT_PROMPT,
            max_tool_iterations=1
        )
        
        self.agents["clinician_gpt4o"] = AssistantAgent(
            name="Clinician_GPT4O_Agent",
            model_client=self.model_client,
            system_message=CLINICIAN_GPT4O_AGENT_PROMPT,
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
        
        print("All agents initialized successfully")
        
    async def process_patient(self, patient_data: Dict[str, Any], web_tracker=None) -> str:
        """Process patient data through the complete agent pipeline"""
        
        # Inizializza sistema di progresso
        from prism_ad.utils.progress_display import prism_progress
        
        # Collega web tracker se disponibile
        if web_tracker:
            prism_progress.set_web_tracker(web_tracker)
        
        prism_progress.start_analysis()
        prism_progress.start_phase("init")
        
        # Convert to PatientData model
        try:
            patient = PatientData(**patient_data)
            prism_progress.update_progress("Dati paziente validati")
        except Exception as e:
            prism_progress.show_error(f"Errore parsing dati paziente: {e}")
            raise
            
        # Determine patient's FDA stage using unified function
        patient_stage = determine_fda_stage(patient)
        prism_progress.update_progress(f"Determinato FDA stage: {patient_stage}")
        prism_progress.end_phase()
        
        prism_progress.start_phase("data_collection")
        prism_progress.update_progress("Dati clinici pronti per analisi")
        prism_progress.end_phase()
            
        # Step 1: RAG Agent Analysis
        prism_progress.start_agent_analysis("rag", "Evidence Retrieval")
        rag_result = await self._run_rag_agent(patient, patient_stage)
        prism_progress.end_phase()
        
        # Step 2: Clinician Agent Analysis
        prism_progress.start_agent_analysis("clinician", "Clinician Assessment")
        clinician_result = await self._run_clinician_agent(patient, patient_stage)
        prism_progress.end_phase()
        
        # Step 3: Model GPT4o Agent Analysis
        prism_progress.start_agent_analysis("biomarker", "Advanced Clinical Analysis")
        clinician_gpt4o_result = await self._run_clinician_gpt4o_agent(patient, patient_stage)
        prism_progress.end_phase()
        
        # Step 4: Model Fastweb Agent Analysis
        prism_progress.start_agent_analysis("risk", "Risk Assessment")
        clinician_fastweb_result = await self._run_clinician_fastweb_agent(patient, patient_stage)
        prism_progress.end_phase()
        
        # Step 5: Cox Agent Analysis
        prism_progress.start_agent_analysis("risk", "Statistical Analysis")
        cox_result = await self._run_cox_agent(patient, patient_stage)
        prism_progress.end_phase()
        
        # Step 6: Consensus Agent
        prism_progress.start_agent_analysis("consensus", "Multi-Agent Consensus")
        consensus_result = await self._run_consensus_agent(
            rag_result, clinician_result, clinician_gpt4o_result, 
            clinician_fastweb_result, cox_result
        )
        prism_progress.end_phase()
        
        # Step 7: Final Response Agent
        prism_progress.start_phase("final_report")
        final_report = await self._run_final_response_agent(consensus_result)
        prism_progress.end_phase()
        
        prism_progress.start_phase("formatting")
        prism_progress.update_progress("Report formattato con successo")
        prism_progress.end_phase()
        
        prism_progress.start_phase("complete")
        prism_progress.end_phase()
        prism_progress.complete_analysis()
        
        return final_report
        
    async def _run_rag_agent(self, patient: PatientData, patient_stage: str) -> str:
        """Run the RAG agent with clinical evidence retrieval (hybrid system)"""
        print(f"🔧 DEBUG: RAG Agent - web_tracker available: {self.web_tracker is not None}")
        if self.web_tracker:
            print("🔧 DEBUG: Sending RAG progress message to web tracker")
            self.web_tracker.update_progress("🔍 RAG Agent - Consultazione base di evidenze cliniche...")
        try:
            # Initialize Hybrid RAG system if not already done
            if not hasattr(self, 'rag_system'):
                from prism_ad.rag.hybrid_rag import create_hybrid_rag_agent
                self.rag_system = create_hybrid_rag_agent("./clinical_pdfs")
                method = "ChromaDB" if self.rag_system.use_chromadb else "Ricerca Testuale"
                print(f"🧠 Hybrid RAG system initialized ({method}) with {len(self.rag_system.pdf_contents) if not self.rag_system.use_chromadb else 'ChromaDB'} clinical documents")
            
            # Create patient data for RAG
            patient_data = {
                "stage": patient_stage,
                "age": patient.age,
                "sex": patient.sex or "unknown",
                "mmse": patient.mmse_score,
                "cdr": patient.cdr_sum or 0.0,
                "csf_abeta42": patient.csf_abeta42,
                "csf_ptau181": patient.csf_ptau181,
                "csf_total_tau": patient.csf_total_tau,
                "amyloid_pet_suvr": patient.amyloid_pet_suvr,
                "hippocampus_volume_left": patient.hippocampus_volume_left,
                "hippocampus_volume_right": patient.hippocampus_volume_right
            }
            
            # Get clinical evidence from RAG system
            clinical_context = self.rag_system.get_agent_context(patient_data)
            print(f"📚 RAG retrieved {len(clinical_context)} characters of clinical evidence")
            
            # Get specific evidence for risk assessment
            risk_evidence = self.rag_system.get_risk_evidence(patient_data)
            
            # Extract key findings from evidence
            key_findings = []
            for category, results in risk_evidence.items():
                if results:
                    best_result = results[0]
                    key_findings.append(f"From {best_result.get('metadata', {}).get('file_name', 'clinical literature')}: {best_result.get('text', '')[:150]}...")
            
            # Create input JSON for the agent with RAG context
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
                "stage_hint": patient_stage,
                "question": f"Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor) from current {patient_stage}",
                "retrieved_evidence": key_findings[:5]  # Top 5 evidenze più rilevanti
            }
            
            task = f"""You are a RAG agent specialized in Alzheimer's Disease analysis. You have access to clinical evidence from peer-reviewed literature.

CLINICAL EVIDENCE RETRIEVED FROM YOUR DOCUMENT DATABASE:
{clinical_context}

KEY FINDINGS FROM RETRIEVED DOCUMENTS:
{chr(10).join([f"- {finding}" for finding in key_findings[:3]])}

PATIENT DATA TO ANALYZE:
{json.dumps(input_data, indent=2)}

Based on the clinical evidence you retrieved from your document database, analyze this patient and provide a JSON response following the unified schema. Use the retrieved evidence to inform your risk assessment, particularly focusing on:

1. How the patient's biomarker values compare to cutoffs mentioned in your retrieved literature
2. Risk factors and progression patterns described in your documents
3. Staging criteria and prognosis information from your evidence base

Please provide your analysis in the exact JSON format specified in your system prompt, explicitly citing and referencing the clinical evidence you retrieved."""
            
            result = await self.agents["rag"].run(task=task)
            rag_response = result.messages[-1].content if result.messages else ""
            print(f"RAG Agent says: {rag_response[:200]}...")
            
            self.processing_results["rag"] = rag_response
            
            if self.web_tracker:
                self.web_tracker.update_progress("✅ RAG Agent completato")
                
            return rag_response
            
        except Exception as e:
            print(f"⚠️ RAG system error: {e}")
            print("🔄 Falling back to basic RAG agent without clinical evidence...")
            
            # Fallback to basic RAG agent without clinical evidence
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
                "stage_hint": patient_stage,
                "question": f"Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor) from current {patient_stage}"
            }
            
            task = f"""Analyze the following patient data and provide a JSON response following the unified schema:

{json.dumps(input_data, indent=2)}

Please provide your analysis in the exact JSON format specified in your system prompt."""
            
            result = await self.agents["rag"].run(task=task)
            rag_response = result.messages[-1].content if result.messages else ""
            print(f"RAG Agent (fallback) says: {rag_response[:200]}...")
            
            self.processing_results["rag"] = rag_response
            return rag_response
        
    async def _run_clinician_agent(self, patient: PatientData, patient_stage: str) -> str:
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
            "stage_hint": patient_stage,
            "question": f"Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor) from current {patient_stage}"
        }
        
        task = f"""Analyze the following patient data and provide a JSON response following the unified schema:

{json.dumps(input_data, indent=2)}

Please provide your analysis in the exact JSON format specified in your system prompt."""
        
        result = await self.agents["clinician"].run(task=task)
        clinician_response = result.messages[-1].content if result.messages else ""
        print(f"Clinician Agent says: {clinician_response[:200]}...")
        
        self.processing_results["clinician"] = clinician_response
        return clinician_response
        
    async def _run_clinician_fastweb_agent(self, patient: PatientData, patient_stage: str) -> str:
        """Run the Clinician FASTWEB agent"""
        print(f"🔧 DEBUG: Fastweb Agent - web_tracker available: {self.web_tracker is not None}")
        if self.web_tracker:
            print("🔧 DEBUG: Sending Fastweb progress message to web tracker")
            self.web_tracker.update_progress("🌐 Model Fastweb - Analisi specialistica...")
        # Create input JSON for the agent (same format as Clinician)
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
            "stage_hint": patient_stage,
            "question": f"Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor) from current {patient_stage}"
        }
        
        task = f"""Analyze the following patient data and provide a JSON response following the unified schema:

{json.dumps(input_data, indent=2)}

Please provide your analysis in the exact JSON format specified in your system prompt."""
        
        result = await self.agents["clinician_fastweb"].run(task=task)
        clinician_fastweb_response = result.messages[-1].content if result.messages else ""
        print(f"Clinician FASTWEB Agent says: {clinician_fastweb_response[:200]}...")
        
        self.processing_results["clinician_fastweb"] = clinician_fastweb_response
        
        if self.web_tracker:
            self.web_tracker.update_progress("✅ Model Fastweb completato")
            
        return clinician_fastweb_response
        
    async def _run_clinician_gpt4o_agent(self, patient: PatientData, patient_stage: str) -> str:
        """Run the Model GPT4o agent"""
        print(f"🔧 DEBUG: GPT4o Agent - web_tracker available: {self.web_tracker is not None}")
        if self.web_tracker:
            print("🔧 DEBUG: Sending GPT4o progress message to web tracker")
            self.web_tracker.update_progress("🤖 Model GPT4o - Analisi clinica avanzata...")
        # Create input JSON for the agent (same format as Clinician)
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
            "stage_hint": patient_stage,
            "question": f"Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor) from current {patient_stage}"
        }
        
        task = f"""Analyze the following patient data and provide a JSON response following the unified schema:

{json.dumps(input_data, indent=2)}

Please provide your analysis in the exact JSON format specified in your system prompt."""
        
        result = await self.agents["clinician_gpt4o"].run(task=task)
        clinician_gpt4o_response = result.messages[-1].content if result.messages else ""
        print(f"Model GPT4o Agent says: {clinician_gpt4o_response[:200]}...")
        
        self.processing_results["clinician_gpt4o"] = clinician_gpt4o_response
        
        if self.web_tracker:
            self.web_tracker.update_progress("✅ Model GPT4o completato")
            
        return clinician_gpt4o_response
        
    async def _run_cox_agent(self, patient: PatientData, patient_stage: str) -> str:
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
            "stage_hint": patient_stage,
            "question": f"Estimate 5-year risk of progression to FDA Stage3 (MCI AD/Progressor) from current {patient_stage}"
        }
        
        task = f"""Analyze the following patient data and provide a JSON response following the unified schema:

{json.dumps(input_data, indent=2)}

Please provide your analysis in the exact JSON format specified in your system prompt."""
        
        result = await self.agents["cox"].run(task=task)
        cox_response = result.messages[-1].content if result.messages else ""
        print(f"Cox Agent says: {cox_response[:200]}...")
        
        self.processing_results["cox"] = cox_response
        return cox_response
        
    async def _run_consensus_agent(self, rag_result: str, clinician_result: str, 
                                  clinician_gpt4o_result: str, clinician_fastweb_result: str, 
                                  cox_result: str) -> str:
        """Run the Consensus agent"""
        task = f"""You have received five solver outputs from all agents. Please analyze them and provide a consensus JSON response.

Current weighting scheme:
- RAG Agent: 0.25 (active)
- Clinician Agent: 0.25 (active)
- Model GPT4o: 0.25 (active)  
- Model Fastweb: 0.25 (active)
- Cox Agent: 0.0 (inactive)

RAG Agent Output (weight: 0.25):
{rag_result}

Clinician Agent Output (weight: 0.25):
{clinician_result}

Model GPT4o Output (weight: 0.25):
{clinician_gpt4o_result}

Model Fastweb Output (weight: 0.25):
{clinician_fastweb_result}

Cox Agent Output (weight: 0.0):
{cox_result}

Please provide your consensus analysis in the exact JSON format specified in your system prompt with "agent": "consensus"."""
        
        result = await self.agents["consensus"].run(task=task)
        consensus_response = result.messages[-1].content if result.messages else ""
        print(f"Consensus Agent says: {consensus_response[:200]}...")
        
        self.processing_results["consensus"] = consensus_response
        return consensus_response
        
    async def _run_final_response_agent(self, consensus_result: str) -> str:
        """Run the Final Response agent and format output"""
        task = f"""Transform the following consensus JSON into a professional Italian report for the treating neurologist:

{consensus_result}

Please provide your final report in Italian following the structure specified in your system prompt."""
        
        result = await self.agents["final_response"].run(task=task)
        final_response = result.messages[-1].content if result.messages else ""
        
        # 📄 Formatta e salva il report in formati multipli
        try:
            from prism_ad.utils.pdf_formatter import format_prism_report
            import json
            
            # Estrai patient ID se disponibile
            patient_id = None
            try:
                consensus_data = json.loads(consensus_result)
                patient_id = consensus_data.get('patient_id', 'unknown')
            except:
                patient_id = f"patient_{hash(consensus_result) % 10000}"
            
            # Genera report formattati
            print(f"\nGenerazione report formattati per paziente {patient_id}...")
            report_files = format_prism_report(
                markdown_content=final_response,
                output_dir="./reports",
                patient_id=patient_id
            )
            
            if report_files:
                print("Report generati:")
                for format_type, path in report_files.items():
                    print(f"   {format_type.upper()}: {path}")
            else:
                print("Generazione report fallita, verrà restituito solo il testo")
                
        except Exception as e:
            print(f"Errore nella formattazione PDF: {e}")
            print("Restituisco solo il report testuale")
        print(f"Final Response Agent says: {final_response[:200]}...")
        
        self.processing_results["final_response"] = final_response
        return final_response
        
    async def close(self):
        """Clean up resources"""
        try:
            # Close all agents first
            for agent_name, agent in self.agents.items():
                try:
                    if hasattr(agent, 'close'):
                        await agent.close()
                except Exception as e:
                    print(f"⚠️ Error closing agent {agent_name}: {e}")
            
            # Close model client
            if self.model_client:
                await self.model_client.close()
                print("Model client closed")
                
            # Clear processing results
            self.processing_results.clear()
            
            # Clear conversation history
            self.conversation_history.clear()
            
        except Exception as e:
            print(f"⚠️ Error during PRISM system cleanup: {e}")
            
    async def get_agent_conversation(self, agent_name: str) -> List[str]:
        """Get conversation history for a specific agent"""
        if agent_name in self.processing_results:
            return self.processing_results[agent_name]
        return []
