"""PRISM-AD Multi-Agent System Implementation"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from pydantic import BaseModel

from prism_ad.config import OPENAI_API_KEY, MODEL_NAME, AGENT_NAMES, FASTWEB_ENABLED
from prism_ad.agents.model_providers import ModelProviderFactory, MultiProviderAgentSystem
from prism_ad.agents.agent_prompts import (
    PARSER_PROMPT,
    INTAKE_VALIDATOR_PROMPT,
    NORMALIZER_PROMPT,  # TO BE REMOVED
    FDA_CLASSIFIER_PROMPT,
    QUANT_MODEL_PROMPT,
    RISK_CALCULATOR_PROMPT,
    REPORT_SYNTHESIZER_PROMPT
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
# Import the quantitative risk calculator tool
from prism_ad.utils.quant_risk_calculator import calculate_alzheimer_risk

# Add imports for rag
from prism_ad.config import (
    RAG_COLLECTION_NAME, RAG_CHROMA_PATH, RAG_EMBEDDING_MODEL,
    RAG_MIN_YEAR, RAG_TOP_K, RAG_FINAL_K, RAG_SCORE_THRESHOLD
)
from prism_ad.rag.risk_rag_memory import RiskRAGMemory, RiskRAGConfig


class PRISMAgentSystem:
    """Multi-agent system for Alzheimer's Disease risk assessment"""
    
    def __init__(self, model_name: str = MODEL_NAME, api_key: str = OPENAI_API_KEY):
        """Initialize the PRISM-AD agent system with multi-provider support"""
        self.model_name = model_name
        self.api_key = api_key
        self.agents = {}
        self.model_client = None  # Legacy support for single client
        self.provider_system = MultiProviderAgentSystem()  # New multi-provider system
        self.conversation_history = []
        self.processing_results = {}
        
    async def initialize_agents(self):
        """Create and initialize all specialized agents with multi-provider support"""
        print("🔧 Initializing PRISM-AD Agent System (Multi-Provider Architecture)...")
        if FASTWEB_ENABLED:
            print("✨ FastWeb integration enabled for selected agents")
        else:
            print("📌 Using OpenAI models for all agents")
        
        # Create default model client for backward compatibility
        self.model_client = OpenAIChatCompletionClient(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.2  # Low temperature for consistent medical analysis
        )
        
        # Create each specialized agent with appropriate provider
        # NEW: Parser agent
        parser_client = self.provider_system.get_or_create_client("parser")
        self.agents["parser"] = AssistantAgent(
            name=AGENT_NAMES["parser"],
            model_client=parser_client,
            system_message=PARSER_PROMPT,
            max_tool_iterations=1
        )
        
        validator_client = self.provider_system.get_or_create_client("validator")
        self.agents["validator"] = AssistantAgent(
            name=AGENT_NAMES["validator"],
            model_client=validator_client,
            system_message=INTAKE_VALIDATOR_PROMPT,
            max_tool_iterations=1
        )

        # Build Risk RAG Memory (patient-aware evidence injected into context)
        self.rag_mem = RiskRAGMemory(
            config=RiskRAGConfig(
                chroma_base_path=RAG_CHROMA_PATH,
                collection_name=RAG_COLLECTION_NAME,
                embedding_model_name=RAG_EMBEDDING_MODEL,
                k_initial=RAG_TOP_K,
                k_final=RAG_FINAL_K,
                min_year=RAG_MIN_YEAR,
                type_filter=None,           # set to "text" or "table" if you want
                score_threshold=RAG_SCORE_THRESHOLD,
            )
        )

        risk_calc_client = self.provider_system.get_or_create_client("risk_calculator")
        self.agents["risk_calculator"] = AssistantAgent(
            name=AGENT_NAMES["risk_calculator"],
            model_client=risk_calc_client,
            system_message=RISK_CALCULATOR_PROMPT,
            max_tool_iterations=1,
            memory=[self.rag_mem],    # <-- inject memory
        )


        classifier_client = self.provider_system.get_or_create_client("classifier")
        self.agents["classifier"] = AssistantAgent(
            name=AGENT_NAMES["classifier"],
            model_client=classifier_client,
            system_message=FDA_CLASSIFIER_PROMPT,
            max_tool_iterations=1
        )
        
        # NEW: Quantitative Model with tool calling (requires OpenAI for tool support)
        quant_client = self.provider_system.get_or_create_client("quant_model")
        self.agents["quant_model"] = AssistantAgent(
            name=AGENT_NAMES["quant_model"],
            model_client=quant_client,
            system_message=QUANT_MODEL_PROMPT,
            tools=[calculate_alzheimer_risk],  # Add the calculator as a tool
            max_tool_iterations=2,  # Allow tool calls
            reflect_on_tool_use=True  # Summarize tool output
        )
        
        reporter_client = self.provider_system.get_or_create_client("reporter")
        self.agents["reporter"] = AssistantAgent(
            name=AGENT_NAMES["reporter"],
            model_client=reporter_client,
            system_message=REPORT_SYNTHESIZER_PROMPT,
            max_tool_iterations=1
        )
        
        print("✅ All agents initialized successfully")
        
        # Print provider summary
        summary = self.provider_system.get_provider_summary()
        if summary["fastweb_enabled"]:
            fastweb_agents = [agent for agent, info in summary["agent_assignments"].items() 
                            if info["provider"] == "FastWeb"]
            if fastweb_agents:
                print(f"🚀 FastWeb agents: {', '.join(fastweb_agents)}")
        
    async def parse_clinical_text(self, clinical_text: str, callback=None) -> Dict[str, Any]:
        """Parse natural language clinical description into structured data"""
        async def emit(msg: str):
            """Helper to emit messages through callback if provided"""
            print(msg)
            if callback:
                await callback(msg)
        
        task = f"""Parse the following clinical description and extract all relevant patient data:
        
        Clinical Text:
        {clinical_text}
        
        Extract all available information including:
        - Demographics (age, sex, education)
        - Genetic markers (ApoE4 status)
        - CSF biomarkers (with units)
        - Imaging results
        - Cognitive scores
        - Clinical observations
        
        For any data not explicitly mentioned, return "not available".
        Provide the extracted data in a structured format."""
        
        result = await self.agents["parser"].run(task=task)
        parser_msg = result.messages[-1].content if result.messages else ""
        
        await emit(f"Parser extracted: {parser_msg}")
        
        # Parse the extracted information into structured format
        # This is simplified - in production would use more robust parsing
        extracted_data = self._parse_extraction(parser_msg)
        
        return extracted_data
    
    def _parse_extraction(self, parser_output: str) -> Dict[str, Any]:
        """Convert parser output to structured dictionary"""
        # Default structure with "not available" for missing fields
        data = {
            "patient_id": f"PT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "age": None,
            "sex": None,
            "education_years": None,
            "apoe4_copies": None,
            "csf_abeta42": None,
            "csf_ptau181": None,
            "csf_total_tau": None,
            "hippocampus_volume_left": None,
            "hippocampus_volume_right": None,
            "amyloid_pet_suvr": None,
            "mmse_score": None,
            "moca_score": None,
            "cdr_sum": None,
            "memory_complaints": None,
            "functional_impairment": None
        }
        
        # Simple extraction logic - would be more sophisticated in production
        import re
        
        # Extract age
        age_match = re.search(r'(\d{2,3})[- ]?(?:year|yo|y\.o)', parser_output.lower())
        if age_match:
            data["age"] = float(age_match.group(1))
        
        # Extract sex
        if 'female' in parser_output.lower() or ' f ' in parser_output.lower():
            data["sex"] = "F"
        elif 'male' in parser_output.lower() or ' m ' in parser_output.lower():
            data["sex"] = "M"
        
        # Extract MMSE
        mmse_match = re.search(r'mmse[:\s]*(\d+)', parser_output.lower())
        if mmse_match:
            data["mmse_score"] = float(mmse_match.group(1))
        
        # Extract ApoE4
        if 'apoe4' in parser_output.lower():
            if 'homozygous' in parser_output.lower() or '2 copies' in parser_output.lower():
                data["apoe4_copies"] = "2"
            elif 'heterozygous' in parser_output.lower() or '1 copy' in parser_output.lower() or 'carrier' in parser_output.lower():
                data["apoe4_copies"] = "1"
            elif 'negative' in parser_output.lower() or '0 copies' in parser_output.lower():
                data["apoe4_copies"] = "0"
        
        # Extract CSF markers
        csf_ab42_match = re.search(r'(?:aβ42|abeta42|ab42)[:\s]*(\d+)', parser_output.lower())
        if csf_ab42_match:
            data["csf_abeta42"] = float(csf_ab42_match.group(1))
        
        ptau_match = re.search(r'p-?tau[:\s]*(\d+)', parser_output.lower())
        if ptau_match:
            data["csf_ptau181"] = float(ptau_match.group(1))
        
        # Extract PET
        pet_match = re.search(r'(?:pet|suvr)[:\s]*(\d+\.?\d*)', parser_output.lower())
        if pet_match:
            data["amyloid_pet_suvr"] = float(pet_match.group(1))
        elif 'positive amyloid' in parser_output.lower():
            data["amyloid_pet_suvr"] = 1.45  # Default positive value
        
        return data
    
    async def process_patient(self, patient_data: Dict[str, Any] | str, callback=None):
        """Process patient data through the complete agent pipeline
        
        Args:
            patient_data: Either structured dict or natural language text description
            callback: Optional callback function to receive progress updates
            
        Yields:
            Progress messages and final report
        """
        def emit(msg: str) -> str:
            """Helper to emit messages through callback if provided"""
            print(msg)
            return msg
            
        yield emit("\n" + "="*60)
        yield emit("🏥 PRISM-AD ASSESSMENT PIPELINE STARTED (NEW ARCHITECTURE)")
        yield emit("="*60)
        yield emit("")
        
        # Check if input is text or structured data
        if isinstance(patient_data, str):
            # Parse natural language input
            yield emit("📝 PARSING CLINICAL TEXT")
            yield emit("-"*40)
            parser_result = await self.parse_clinical_text(patient_data)
            if hasattr(parser_result, 'output'):
                yield emit(parser_result.output)
            patient_data = parser_result
        
        # Convert to PatientData model
        try:
            patient = PatientData(**patient_data)
        except Exception as e:
            error_msg = f"❌ Error parsing patient data: {e}"
            yield emit(error_msg)
            raise
            
        # Step 1: Intake Validation
        yield emit("\n📋 Step 1: INTAKE VALIDATION")
        yield emit("-"*40)
        validation_result = await self._run_validator(patient)
        yield emit(validation_result['validation'])
        
        # Step 2: PARALLEL MODEL EXECUTION (NEW ARCHITECTURE)
        yield emit("\n⚙️ Step 2: PARALLEL MODEL EXECUTION")
        yield emit("-"*40)
        yield emit("Running 3 models in parallel: Quantitative, FDA Classifier, RAG")
        
        # Run three models in parallel
        parallel_results = await asyncio.gather(
            self._run_quant_model(validation_result),
            self._run_classifier_new(validation_result),
            self._run_rag_evidence(validation_result),
            return_exceptions=True
        )
        
        quant_result = parallel_results[0]
        classification_result = parallel_results[1]
        rag_result = parallel_results[2]
        
        # Handle any exceptions from parallel execution
        for i, result in enumerate(parallel_results):
            if isinstance(result, Exception):
                yield emit(f"⚠️ Warning: Model {i} failed: {result}")
                parallel_results[i] = None
                
        # Output model results
        if rag_result:
            yield emit(rag_result['rag_context'])
        if classification_result:
            yield emit(classification_result['classification'])
        if quant_result:
            yield emit(quant_result['quant_assessment'])
        
        # Step 3: Information Aggregation
        yield emit("\n🔄 Step 3: INFORMATION AGGREGATION")
        yield emit("-"*40)
        aggregated_result = await self._run_aggregator(
            validation_result,
            quant_result,
            classification_result,
            rag_result
        )
        yield emit(aggregated_result['aggregated_assessment'])
        
        # Step 4: Report Synthesis
        yield emit("\n📄 Step 4: REPORT SYNTHESIS")
        yield emit("-"*40)
        final_report = await self._run_reporter_new(
            patient,
            validation_result,
            aggregated_result
        )
        
        # Format and yield final report
        # Yield the final report as both a formatted message and a data object
        report_text = f"""
📋 FINAL REPORT PREVIEW (NEW ARCHITECTURE):
----------------------------------------
EXECUTIVE SUMMARY
{final_report.executive_summary}

ASSESSMENT RESULTS
- FDA Stage: {final_report.fda_stage}
- Risk Level: {final_report.risk_level}
- 5-Year Progression Risk: {final_report.progression_risk if hasattr(final_report, 'progression_risk') else '95%'}
- Confidence Score: {final_report.confidence_score}

============================================================
✅ ASSESSMENT COMPLETE"""
        yield emit(report_text)
        
        # Yield the final report as a data object
        yield {'final_report': final_report}
        
    async def _run_validator(self, patient: PatientData, callback=None) -> Dict[str, Any]:
        """Run the Intake Validator agent"""
        async def emit(msg: str):
            """Helper to emit messages through callback if provided"""
            print(msg)
            if callback:
                await callback(msg)
                
        task = f"""Validate the following patient data and identify any concerns:
        
        Patient ID: {patient.patient_id}
        Age: {patient.age}
        Sex: {patient.sex}
        
        Genetic Markers:
        - ApoE4 copies: {patient.apoe4_copies}
        
        CSF Biomarkers:
        - Aβ42: {patient.csf_abeta42} pg/mL
        - p-tau181: {patient.csf_ptau181} pg/mL
        - Total tau: {patient.csf_total_tau} pg/mL
        
        Imaging:
        - Hippocampus volume (L): {patient.hippocampus_volume_left} mm³
        - Hippocampus volume (R): {patient.hippocampus_volume_right} mm³
        - Amyloid PET SUVR: {patient.amyloid_pet_suvr}
        
        Cognitive Scores:
        - MMSE: {patient.mmse_score}
        - MoCA: {patient.moca_score}
        - CDR-SB: {patient.cdr_sum}
        
        Provide a structured validation report including:
        1. Data completeness assessment
        2. Biological plausibility check
        3. Critical missing data
        4. Data quality score (0-1)
        """
        
        result = await self.agents["validator"].run(task=task)
        
        # Extract validation message
        validation_msg = result.messages[-1].content if result.messages else ""
        await emit(f"Validator says: {validation_msg}")
        
        # Store for pipeline context
        self.processing_results["validation"] = validation_msg
        return {"validation": validation_msg, "patient": patient}
        
    # REMOVED: Normalizer is no longer part of the new architecture
    # async def _run_normalizer(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
    #     """Run the Data Normalizer agent - DEPRECATED"""
    #     pass
    
    async def _run_quant_model(self, validation_result: Dict[str, Any], callback=None) -> Dict[str, Any]:
        """Run the Quantitative Risk Model agent with tool calling"""
        async def emit(msg: str):
            """Helper to emit messages through callback if provided"""
            print(msg)
            if callback:
                await callback(msg)
                
        patient = validation_result["patient"]
        
        # Create a task that encourages tool use
        task = f"""Use the calculate_alzheimer_risk tool to compute the quantitative risk score for this patient.
        
        Patient data to pass to the tool:
        - age: {patient.age if patient.age else None}
        - apoe4_copies: {f'"{patient.apoe4_copies}"' if patient.apoe4_copies else None}
        - csf_abeta42: {patient.csf_abeta42 if patient.csf_abeta42 else None}
        - csf_ptau: {patient.csf_ptau181 if patient.csf_ptau181 else None}
        - csf_total_tau: {patient.csf_total_tau if patient.csf_total_tau else None}
        - amyloid_pet: {patient.amyloid_pet_suvr if patient.amyloid_pet_suvr else None}
        - hippocampus_left: {patient.hippocampus_volume_left if patient.hippocampus_volume_left else None}
        - hippocampus_right: {patient.hippocampus_volume_right if patient.hippocampus_volume_right else None}
        - mmse: {patient.mmse_score if patient.mmse_score else None}
        - moca: {patient.moca_score if patient.moca_score else None}
        - cdr_sum: {patient.cdr_sum if patient.cdr_sum else None}
        
        Call the calculate_alzheimer_risk tool with the available parameters, then analyze and summarize the results.
        Focus on:
        1. The calculated risk score and category
        2. The 5-year progression probability
        3. Key risk drivers
        4. Confidence level based on data completeness
        """
        
        try:
            result = await self.agents["quant_model"].run(task=task)
            
            # The agent should have used the tool and provided a summary
            quant_msg = result.messages[-1].content if result.messages else ""
            
            # Look for tool call results in the messages
            tool_result = None
            for msg in result.messages:
                if hasattr(msg, 'content') and 'risk_score' in str(msg.content):
                    tool_result = msg.content
                    break
            
            await emit(f"Quant Model (with tool) calculated: {quant_msg}")
            
            self.processing_results["quant_model"] = quant_msg
            return {
                "quant_assessment": quant_msg,
                "tool_result": tool_result,
                "patient": patient
            }
        except Exception as e:
            await emit(f"⚠️ Quant Model error: {e}")
            return None
    
    async def _run_rag_evidence(self, validation_result: Dict[str, Any], callback=None) -> Dict[str, Any]:
        """Run targeted retrieval to produce a human-readable evidence context block."""
        async def emit(msg: str):
            print(msg)
            if callback:
                await callback(msg)

        patient = validation_result["patient"]

        # Build a short query context from patient data (lightweight; memory.update_context will add more)
        query_bits = []
        if patient.amyloid_pet_suvr is not None:
            query_bits.append(f"amyloid PET SUVR {patient.amyloid_pet_suvr}")
        if patient.csf_abeta42 is not None:
            query_bits.append(f"CSF Aβ42 {patient.csf_abeta42} pg/mL")
        if patient.csf_ptau181 is not None:
            query_bits.append(f"p-tau {patient.csf_ptau181} pg/mL")
        if patient.apoe4_copies is not None:
            query_bits.append(f"ApoE4 {patient.apoe4_copies} copies")
        if patient.mmse_score is not None:
            query_bits.append(f"MMSE {patient.mmse_score}")
        if patient.hippocampus_volume_left and patient.hippocampus_volume_right:
            avg_hip = (patient.hippocampus_volume_left + patient.hippocampus_volume_right) / 2
            query_bits.append(f"hippocampal volume ~{avg_hip:.0f} mm³")

        # One consolidated query string for logging; memory will still expand subqueries
        concise_query = " | ".join(query_bits) if query_bits else "AD risk evidence thresholds and multipliers"
        await emit(f"RAG evidence: querying with context → {concise_query}")

        # Use the RAG memory directly to produce a readable 'rag_context' to show in the console/UI.
        rag_block = "Evidence:\n"
        if hasattr(self, 'rag_mem') and self.rag_mem:
            mem_results = await self.rag_mem.query(concise_query)
            if mem_results:
                for mc in mem_results[:6]:
                    rag_block += f"• {mc.content}\n"
            else:
                rag_block += "• No matching evidence retrieved with current filters.\n"
        else:
            rag_block += "• RAG memory not available.\n"

        return {"rag_context": rag_block, "patient": patient}


    async def _run_classifier_new(self, validation_result: Dict[str, Any], callback=None) -> Dict[str, Any]:
        """Run the FDA Stage Classifier agent (new architecture without normalization)"""
        async def emit(msg: str):
            """Helper to emit messages through callback if provided"""
            print(msg)
            if callback:
                await callback(msg)
                
        patient = validation_result["patient"]
        
        task = f"""Classify the patient into FDA Alzheimer's stages based on:
        
        Validation notes: {validation_result['validation'][:300]}
        
        Key criteria:
        - Amyloid status: PET SUVR {patient.amyloid_pet_suvr}, CSF Aβ42 {patient.csf_abeta42}
        - Tau status: CSF p-tau {patient.csf_ptau181}, total tau {patient.csf_total_tau}
        - Cognitive status: MMSE {patient.mmse_score}, MoCA {patient.moca_score}
        - Functional status: CDR-SB {patient.cdr_sum}
        
        Determine:
        1. FDA stage (1-6 or Normal)
        2. Confidence level (0-1)
        3. Supporting evidence
        4. Alternative possibilities if confidence <0.8
        """
        
        result = await self.agents["classifier"].run(task=task)
        classification_msg = result.messages[-1].content if result.messages else ""
        await emit(f"Classifier says: {classification_msg}")
        
        self.processing_results["classification"] = classification_msg
        return {
            "classification": classification_msg,
            "patient": patient
        }
    
    async def _run_aggregator(self, validation_result, quant_result, classification_result, rag_result, callback=None) -> Dict[str, Any]:
        """Aggregate information from multiple models"""
        async def emit(msg: str):
            """Helper to emit messages through callback if provided"""
            print(msg)
            if callback:
                await callback(msg)
                
        patient = validation_result["patient"]
        
        # Build aggregation task
        task = f"""Aggregate and synthesize the following assessments from three specialized models:
        
        1. QUANTITATIVE MODEL ASSESSMENT:
        {quant_result['quant_assessment'][:600] if quant_result else 'Model failed to run'}
        
        2. FDA CLASSIFICATION:
        {classification_result['classification'][:600] if classification_result else 'Model failed to run'}
        
        3. KNOWLEDGE BASE (RAG) CONTEXT:
        {rag_result['rag_context'][:300] if rag_result else 'RAG not available'}
        
        Synthesize a consensus assessment that:
        1. Reconciles any conflicts between models
        2. Weights evidence appropriately
        3. Provides unified risk score (0-100)
        4. Determines consensus FDA stage
        5. Identifies areas of agreement/disagreement
        6. Calculates overall confidence level
        
        If models disagree significantly, explain the discrepancy and provide a balanced view.
        """
        
        result = await self.agents["risk_calculator"].run(task=task)  # Repurposing risk calculator as aggregator
        aggregated_msg = result.messages[-1].content if result.messages else ""
        await emit(f"Aggregator consensus: {aggregated_msg}")
        
        self.processing_results["aggregation"] = aggregated_msg
        return {
            "aggregated_assessment": aggregated_msg,
            "quant_result": quant_result,
            "classification_result": classification_result,
            "rag_result": rag_result,
            "patient": patient
        }
        
    # DEPRECATED - Now used as Information Aggregator
    async def _run_risk_calculator(
        self, 
        normalization_result: Dict[str, Any],
        classification_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """DEPRECATED - This method is kept for backward compatibility
        Use _run_aggregator instead in new architecture"""
        patient = normalization_result["patient"]
        
        task = f"""Calculate 5-year progression risk based on:
        
        FDA Classification: {classification_result['classification'][:500]}
        Normalized biomarkers: {normalization_result['normalization'][:500]}
        
        Patient factors:
        - Age: {patient.age}
        - ApoE4 status: {patient.apoe4_copies} copies
        - Education: {patient.education_years} years
        
        Biomarker profile:
        - CSF Aβ42/p-tau ratio: {(patient.csf_abeta42 or 1) / (patient.csf_ptau181 or 1) if patient.csf_ptau181 else 'N/A'}
        - Hippocampal atrophy: See normalization
        - Cognitive trajectory: MMSE {patient.mmse_score}
        
        Calculate:
        1. 5-year progression probability (%)
        2. Confidence interval
        3. Major risk factors
        4. Protective factors
        """
        
        result = await self.agents["risk_calculator"].run(task=task)
        risk_msg = result.messages[-1].content if result.messages else ""
        print(f"Risk Calculator says: {risk_msg[:200]}...")
        
        self.processing_results["risk"] = risk_msg
        return {
            **classification_result,
            "risk_assessment": risk_msg
        }
        
    async def _run_reporter(
        self,
        patient: PatientData,
        validation_result: Dict[str, Any],
        normalization_result: Dict[str, Any],
        classification_result: Dict[str, Any],
        risk_result: Dict[str, Any]
    ) -> ClinicalReport:
        """Run the Report Synthesizer agent"""
        
        task = f"""Create a comprehensive clinical report synthesizing all analyses:
        
        PATIENT: {patient.patient_id}, {patient.age}yo {patient.sex or 'Unknown'}
        
        VALIDATION SUMMARY:
        {validation_result['validation'][:400]}
        
        NORMALIZATION FINDINGS:
        {normalization_result['normalization'][:400]}
        
        FDA CLASSIFICATION:
        {classification_result['classification'][:400]}
        
        RISK ASSESSMENT:
        {risk_result['risk_assessment'][:400]}
        
        Generate a clinical report with:
        1. Executive summary (2-3 sentences)
        2. FDA stage and confidence
        3. Risk level (Low/Moderate/High/Very High)
        4. Key findings (top 3-5)
        5. Clinical recommendations (prioritized)
        6. Follow-up timeline
        7. Clinical trial eligibility
        
        Make it clear, actionable, and appropriate for both clinicians and informed patients.
        """
        
        result = await self.agents["reporter"].run(task=task)
        report_msg = result.messages[-1].content if result.messages else ""
        
        # Parse key information from the report (simplified for demo)
        # In production, we'd use structured output or better parsing
        from prism_ad.data.patient_model import FDAStage
        
        # Simple parsing logic to extract stage and risk level
        report_lower = report_msg.lower()
        
        # Determine FDA stage from classification
        fda_stage = FDAStage.UNCERTAIN  # Default
        if "stage 1" in classification_result['classification'].lower():
            fda_stage = FDAStage.STAGE_1
        elif "stage 2" in classification_result['classification'].lower():
            fda_stage = FDAStage.STAGE_2
        elif "stage 3" in classification_result['classification'].lower() or "mci" in classification_result['classification'].lower():
            fda_stage = FDAStage.STAGE_3
        elif "stage 4" in classification_result['classification'].lower() or "mild dementia" in classification_result['classification'].lower():
            fda_stage = FDAStage.STAGE_4
        elif "stage 5" in classification_result['classification'].lower():
            fda_stage = FDAStage.STAGE_5
        elif "stage 6" in classification_result['classification'].lower():
            fda_stage = FDAStage.STAGE_6
        elif "normal" in classification_result['classification'].lower():
            fda_stage = FDAStage.NORMAL
            
        # Determine risk level from risk assessment
        risk_level = "Moderate"  # Default
        if "very high" in risk_result['risk_assessment'].lower():
            risk_level = "Very High"
        elif "high" in risk_result['risk_assessment'].lower():
            risk_level = "High"
        elif "low" in risk_result['risk_assessment'].lower():
            risk_level = "Low"
        
        # Parse key findings from report (simplified)
        key_findings = []
        if "amyloid" in report_lower:
            key_findings.append("Abnormal amyloid biomarkers detected")
        if "tau" in report_lower:
            key_findings.append("Elevated tau proteins indicating neurodegeneration")
        if "cognitive" in report_lower:
            key_findings.append("Cognitive impairment observed")
        if not key_findings:
            key_findings = ["Complete assessment performed", "See detailed report"]
            
        # Parse recommendations (simplified)
        recommendations = []
        if "specialist" in report_lower or "neurologist" in report_lower:
            recommendations.append("Referral to neurologist recommended")
        if "monitor" in report_lower:
            recommendations.append("Regular monitoring advised")
        if "lifestyle" in report_lower:
            recommendations.append("Lifestyle interventions recommended")
        if not recommendations:
            recommendations = ["Follow clinical guidelines", "Schedule follow-up assessment"]
        
        # Create structured report
        report = ClinicalReport(
            patient_id=patient.patient_id,
            assessment_date=datetime.now().isoformat(),
            executive_summary=report_msg[:500] if len(report_msg) > 500 else report_msg,
            fda_stage=fda_stage,
            risk_level=risk_level,
            key_findings=key_findings[:5],  # Limit to 5 findings
            recommendations=recommendations[:5],  # Limit to 5 recommendations
            follow_up_timeline="6 months" if "high" in risk_level.lower() else "12 months",
            clinical_trial_eligibility=[],
            detailed_results={
                "full_report": report_msg,
                "validation": validation_result['validation'],
                "normalization": normalization_result['normalization'],
                "classification": classification_result['classification'],
                "risk": risk_result['risk_assessment']
            }
        )
        
        print(f"\n📋 FINAL REPORT PREVIEW:")
        print("-"*40)
        print(report_msg[:500])
        
        return report
    
    async def _run_reporter_new(self, patient: PatientData, validation_result: Dict[str, Any], aggregated_result: Dict[str, Any], callback=None) -> ClinicalReport:
        """Run the simplified Report Synthesizer agent"""
        async def emit(msg: str):
            """Helper to emit messages through callback if provided"""
            print(msg)
            if callback:
                await callback(msg)
                
        task = f"""Create a clear clinical report based on the assessment results.
        
        PATIENT: {patient.patient_id}, {patient.age}yo {patient.sex or 'Unknown'}
        
        AGGREGATED ASSESSMENT:
        {aggregated_result['aggregated_assessment'][:1000]}
        
        Follow the exact format specified in your instructions.
        Focus on clarity and actionable recommendations.
        """
        
        result = await self.agents["reporter"].run(task=task)
        report_text = result.messages[-1].content if result.messages else ""
        await emit(report_text)
        
        # Parse the plain text report
        from prism_ad.data.patient_model import FDAStage
        import re
        
        # Helper function to extract value after a label
        def extract_value(text, label, default="Unknown"):
            pattern = rf"{label}[:\s]*([^\n]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else default
        
        # Parse FDA stage
        fda_stage_text = extract_value(report_text, "FDA Stage", "").lower()
        fda_stage = FDAStage.UNCERTAIN
        if "stage 1" in fda_stage_text:
            fda_stage = FDAStage.STAGE_1
        elif "stage 2" in fda_stage_text:
            fda_stage = FDAStage.STAGE_2
        elif "stage 3" in fda_stage_text or "mci" in fda_stage_text:
            fda_stage = FDAStage.STAGE_3
        elif "stage 4" in fda_stage_text:
            fda_stage = FDAStage.STAGE_4
        elif "stage 5" in fda_stage_text:
            fda_stage = FDAStage.STAGE_5
        elif "stage 6" in fda_stage_text:
            fda_stage = FDAStage.STAGE_6
        elif "normal" in fda_stage_text:
            fda_stage = FDAStage.NORMAL
        
        # Parse risk level
        risk_level = extract_value(report_text, "Risk Level", "Moderate")
        
        # Parse confidence score
        confidence_score = extract_value(report_text, "Confidence Score", "Moderate")
        
        # Parse follow-up timeline
        follow_up = extract_value(report_text, "Next assessment", "6 months")
        
        # Extract executive summary (first paragraph or section)
        exec_summary_match = re.search(r"EXECUTIVE SUMMARY[:\s]*([^\n]+(?:\n[^\n]+)?)", report_text, re.IGNORECASE)
        executive_summary = exec_summary_match.group(1).strip() if exec_summary_match else report_text[:300]
        
        # Extract key findings (look for bullet points after KEY FINDINGS)
        key_findings = []
        findings_match = re.search(r"KEY FINDINGS[:\s]*\n((?:[•\-\*][^\n]+\n?)+)", report_text, re.IGNORECASE)
        if findings_match:
            findings_text = findings_match.group(1)
            key_findings = [line.strip().lstrip('•-* ') for line in findings_text.split('\n') if line.strip()]
        if not key_findings:
            key_findings = ["Assessment completed", "See full report for details"]
        
        # Extract recommendations
        recommendations = []
        rec_match = re.search(r"CLINICAL RECOMMENDATIONS[:\s]*\n((?:[•\-\*][^\n]+\n?)+)", report_text, re.IGNORECASE)
        if rec_match:
            rec_text = rec_match.group(1)
            recommendations = [line.strip().lstrip('•-* ') for line in rec_text.split('\n') if line.strip()]
        if not recommendations:
            recommendations = ["Follow standard clinical guidelines", "Schedule regular monitoring"]
        
        # Create structured report with all required fields
        report = ClinicalReport(
            patient_id=patient.patient_id,
            assessment_date=datetime.now().isoformat(),
            executive_summary=executive_summary,
            fda_stage=fda_stage,
            risk_level=risk_level,
            key_findings=key_findings[:5],  # Limit to 5
            recommendations=recommendations[:5],  # Limit to 5
            clinical_recommendations=recommendations[:5],  # For infrastructure compatibility
            follow_up_timeline=follow_up,
            confidence_score=confidence_score,
            timestamp=datetime.now(),
            clinical_trial_eligibility=[],
            detailed_results={
                "full_report": report_text,
                "aggregated_assessment": aggregated_result.get('aggregated_assessment', ''),
                "model_outputs": {
                    "quantitative": aggregated_result.get('quant_result', {}).get('quant_assessment', 'N/A'),
                    "fda_classification": aggregated_result.get('classification_result', {}).get('classification', 'N/A'),
                    "rag_context": aggregated_result.get('rag_result', {}).get('rag_context', 'N/A')
                }
            }
        )
        
        print(f"\n📋 FINAL REPORT PREVIEW (NEW ARCHITECTURE):")
        print("-"*40)
        print(report_text[:500])
        
        return report
        
    async def close(self):
        """Clean up resources"""
        # Close multi-provider clients
        await self.provider_system.close_all()
        
        # Close legacy model client if exists
        if self.model_client:
            await self.model_client.close()
            print("🔒 Legacy model client closed")
            
    async def get_agent_conversation(self, agent_name: str) -> List[str]:
        """Get conversation history for a specific agent"""
        if agent_name in self.processing_results:
            return self.processing_results[agent_name]
        return []
