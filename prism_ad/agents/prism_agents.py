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


class PRISMAgentSystem:
    """Multi-agent system for Alzheimer's Disease risk assessment"""
    
    def __init__(self, model_name: str = MODEL_NAME, api_key: str = OPENAI_API_KEY):
        """Initialize the PRISM-AD agent system"""
        self.model_name = model_name
        self.api_key = api_key
        self.agents = {}
        self.model_client = None
        self.conversation_history = []
        self.processing_results = {}
        
    async def initialize_agents(self):
        """Create and initialize all specialized agents"""
        print("🔧 Initializing PRISM-AD Agent System (New Architecture)...")
        
        # Create model client
        self.model_client = OpenAIChatCompletionClient(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.2  # Low temperature for consistent medical analysis
        )
        
        # Create each specialized agent
        # NEW: Parser agent
        self.agents["parser"] = AssistantAgent(
            name=AGENT_NAMES["parser"],
            model_client=self.model_client,
            system_message=PARSER_PROMPT,
            max_tool_iterations=1
        )
        
        self.agents["validator"] = AssistantAgent(
            name=AGENT_NAMES["validator"],
            model_client=self.model_client,
            system_message=INTAKE_VALIDATOR_PROMPT,
            max_tool_iterations=1
        )
        
        # TO BE REMOVED - keeping temporarily for backward compatibility
        # self.agents["normalizer"] = AssistantAgent(
        #     name=AGENT_NAMES["normalizer"],
        #     model_client=self.model_client,
        #     system_message=NORMALIZER_PROMPT,
        #     max_tool_iterations=1
        # )
        
        self.agents["classifier"] = AssistantAgent(
            name=AGENT_NAMES["classifier"],
            model_client=self.model_client,
            system_message=FDA_CLASSIFIER_PROMPT,
            max_tool_iterations=1
        )
        
        # NEW: Quantitative Model
        self.agents["quant_model"] = AssistantAgent(
            name=AGENT_NAMES["quant_model"],
            model_client=self.model_client,
            system_message=QUANT_MODEL_PROMPT,
            max_tool_iterations=1
        )
        
        # Will become Information Aggregator
        self.agents["risk_calculator"] = AssistantAgent(
            name=AGENT_NAMES["risk_calculator"],
            model_client=self.model_client,
            system_message=RISK_CALCULATOR_PROMPT,
            max_tool_iterations=1
        )
        
        self.agents["reporter"] = AssistantAgent(
            name=AGENT_NAMES["reporter"],
            model_client=self.model_client,
            system_message=REPORT_SYNTHESIZER_PROMPT,
            max_tool_iterations=1
        )
        
        print("✅ All agents initialized successfully")
        
    async def parse_clinical_text(self, clinical_text: str) -> Dict[str, Any]:
        """Parse natural language clinical description into structured data"""
        print("\n📝 PARSING CLINICAL TEXT")
        print("-"*40)
        
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
        
        print(f"Parser extracted: {parser_msg[:300]}...")
        
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
    
    async def process_patient(self, patient_data: Dict[str, Any] | str) -> ClinicalReport:
        """Process patient data through the complete agent pipeline
        
        Args:
            patient_data: Either structured dict or natural language text description
        """
        print("\n" + "="*60)
        print("🏥 PRISM-AD ASSESSMENT PIPELINE STARTED (NEW ARCHITECTURE)")
        print("="*60)
        
        # Check if input is text or structured data
        if isinstance(patient_data, str):
            # Parse natural language input
            patient_data = await self.parse_clinical_text(patient_data)
        
        # Convert to PatientData model
        try:
            patient = PatientData(**patient_data)
        except Exception as e:
            print(f"❌ Error parsing patient data: {e}")
            raise
            
        # Step 1: Intake Validation
        print("\n📋 Step 1: INTAKE VALIDATION")
        print("-"*40)
        validation_result = await self._run_validator(patient)
        
        # Step 2: PARALLEL MODEL EXECUTION (NEW ARCHITECTURE)
        print("\n⚙️ Step 2: PARALLEL MODEL EXECUTION")
        print("-"*40)
        print("Running 3 models in parallel: Quantitative, FDA Classifier, RAG (placeholder)")
        
        # Run three models in parallel
        import asyncio
        parallel_results = await asyncio.gather(
            self._run_quant_model(validation_result),
            self._run_classifier_new(validation_result),
            self._run_rag_placeholder(validation_result),  # RAG to be implemented
            return_exceptions=True
        )
        
        quant_result = parallel_results[0]
        classification_result = parallel_results[1]
        rag_result = parallel_results[2]
        
        # Handle any exceptions from parallel execution
        for i, result in enumerate(parallel_results):
            if isinstance(result, Exception):
                print(f"⚠️ Warning: Model {i} failed: {result}")
                parallel_results[i] = None
        
        # Step 3: Information Aggregation
        print("\n🔄 Step 3: INFORMATION AGGREGATION")
        print("-"*40)
        aggregated_result = await self._run_aggregator(
            validation_result,
            quant_result,
            classification_result,
            rag_result
        )
        
        # Step 4: Report Synthesis
        print("\n📄 Step 4: REPORT SYNTHESIS")
        print("-"*40)
        final_report = await self._run_reporter_new(
            patient,
            validation_result,
            aggregated_result
        )
        
        print("\n" + "="*60)
        print("✅ ASSESSMENT COMPLETE")
        print("="*60)
        
        return final_report
        
    async def _run_validator(self, patient: PatientData) -> Dict[str, Any]:
        """Run the Intake Validator agent"""
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
        print(f"Validator says: {validation_msg[:200]}...")
        
        # Store for pipeline context
        self.processing_results["validation"] = validation_msg
        return {"validation": validation_msg, "patient": patient}
        
    # REMOVED: Normalizer is no longer part of the new architecture
    # async def _run_normalizer(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
    #     """Run the Data Normalizer agent - DEPRECATED"""
    #     pass
    
    async def _run_quant_model(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Quantitative Risk Model agent"""
        patient = validation_result["patient"]
        
        task = f"""Calculate quantitative risk score for the following patient:
        
        Demographics:
        - Age: {patient.age if patient.age else 'Not available'}
        - Sex: {patient.sex if patient.sex else 'Not available'}
        - ApoE4 copies: {patient.apoe4_copies if patient.apoe4_copies else 'Not available'}
        
        Biomarkers:
        - CSF Aβ42: {patient.csf_abeta42 if patient.csf_abeta42 else 'Not available'} pg/mL
        - CSF p-tau181: {patient.csf_ptau181 if patient.csf_ptau181 else 'Not available'} pg/mL
        - CSF total tau: {patient.csf_total_tau if patient.csf_total_tau else 'Not available'} pg/mL
        - Amyloid PET SUVR: {patient.amyloid_pet_suvr if patient.amyloid_pet_suvr else 'Not available'}
        - Hippocampus volume (avg): {((patient.hippocampus_volume_left or 0) + (patient.hippocampus_volume_right or 0)) / 2 if patient.hippocampus_volume_left else 'Not available'} mm³
        
        Cognitive:
        - MMSE: {patient.mmse_score if patient.mmse_score else 'Not available'}
        - MoCA: {patient.moca_score if patient.moca_score else 'Not available'}
        - CDR-SB: {patient.cdr_sum if patient.cdr_sum else 'Not available'}
        
        Calculate:
        1. Raw biomarker score (0-100)
        2. Age/genetics adjusted risk
        3. 5-year progression probability
        4. Confidence interval based on data completeness
        5. Top risk drivers
        
        Show your calculations for transparency.
        """
        
        try:
            result = await self.agents["quant_model"].run(task=task)
            quant_msg = result.messages[-1].content if result.messages else ""
            print(f"Quant Model calculated: {quant_msg[:200]}...")
            
            self.processing_results["quant_model"] = quant_msg
            return {
                "quant_assessment": quant_msg,
                "patient": patient
            }
        except Exception as e:
            print(f"⚠️ Quant Model error: {e}")
            return None
    
    async def _run_rag_placeholder(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for RAG component - to be implemented"""
        print("RAG component: Using mock knowledge base...")
        
        # Mock RAG output
        rag_output = """Based on latest clinical guidelines:
        - Recent studies show ApoE4 impact varies by age
        - New biomarker thresholds from 2024 consensus
        - Consider enrollment in AHEAD 3-45 trial if eligible
        - Lifestyle interventions show 30% risk reduction
        """
        
        return {
            "rag_context": rag_output,
            "patient": validation_result["patient"]
        }
        
    async def _run_classifier_new(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run the FDA Stage Classifier agent (new architecture without normalization)"""
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
        print(f"Classifier says: {classification_msg[:200]}...")
        
        self.processing_results["classification"] = classification_msg
        return {
            "classification": classification_msg,
            "patient": patient
        }
    
    async def _run_aggregator(self, validation_result, quant_result, classification_result, rag_result) -> Dict[str, Any]:
        """Aggregate information from multiple models"""
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
        print(f"Aggregator consensus: {aggregated_msg[:200]}...")
        
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
    
    async def _run_reporter_new(self, patient: PatientData, validation_result: Dict[str, Any], aggregated_result: Dict[str, Any]) -> ClinicalReport:
        """Run the Report Synthesizer agent (new architecture)"""
        
        task = f"""Create a comprehensive clinical report based on the aggregated assessment:
        
        PATIENT: {patient.patient_id}, {patient.age}yo {patient.sex or 'Unknown'}
        
        VALIDATION SUMMARY:
        {validation_result['validation'][:300]}
        
        AGGREGATED ASSESSMENT:
        {aggregated_result['aggregated_assessment'][:800]}
        
        Generate a clinical report with:
        1. Executive summary (2-3 sentences)
        2. Consensus FDA stage and confidence
        3. Unified risk level (Low/Moderate/High/Very High)
        4. Key findings from all models (top 3-5)
        5. Clinical recommendations (prioritized)
        6. Follow-up timeline
        7. Model agreement/disagreement notes
        
        Format the output to be clear, actionable, and suitable for both clinicians and informed patients.
        Include areas where the models agreed or disagreed for transparency.
        """
        
        result = await self.agents["reporter"].run(task=task)
        report_msg = result.messages[-1].content if result.messages else ""
        
        # Parse and structure the report (simplified)
        from prism_ad.data.patient_model import FDAStage
        
        # Extract stage and risk from aggregated assessment
        report_lower = aggregated_result['aggregated_assessment'].lower()
        
        # Determine FDA stage
        fda_stage = FDAStage.UNCERTAIN
        if "stage 1" in report_lower:
            fda_stage = FDAStage.STAGE_1
        elif "stage 2" in report_lower:
            fda_stage = FDAStage.STAGE_2
        elif "stage 3" in report_lower or "mci" in report_lower:
            fda_stage = FDAStage.STAGE_3
        elif "stage 4" in report_lower:
            fda_stage = FDAStage.STAGE_4
        elif "normal" in report_lower:
            fda_stage = FDAStage.NORMAL
            
        # Determine risk level
        risk_level = "Moderate"
        if "very high" in report_lower:
            risk_level = "Very High"
        elif "high risk" in report_lower or "high (" in report_lower:
            risk_level = "High"
        elif "low risk" in report_lower or "low (" in report_lower:
            risk_level = "Low"
        
        # Extract key findings
        key_findings = [
            "Multi-model consensus assessment completed",
            "See detailed report for model-specific insights"
        ]
        
        # Extract recommendations
        recommendations = [
            "Follow clinical guidelines based on consensus",
            "Consider multi-disciplinary evaluation"
        ]
        
        # Create structured report
        report = ClinicalReport(
            patient_id=patient.patient_id,
            assessment_date=datetime.now().isoformat(),
            executive_summary=report_msg[:500] if len(report_msg) > 500 else report_msg,
            fda_stage=fda_stage,
            risk_level=risk_level,
            key_findings=key_findings,
            recommendations=recommendations,
            follow_up_timeline="6 months" if "high" in risk_level.lower() else "12 months",
            clinical_trial_eligibility=[],
            detailed_results={
                "full_report": report_msg,
                "validation": validation_result['validation'],
                "aggregated_assessment": aggregated_result['aggregated_assessment'],
                "model_outputs": {
                    "quantitative": aggregated_result.get('quant_result', {}).get('quant_assessment', 'N/A'),
                    "fda_classification": aggregated_result.get('classification_result', {}).get('classification', 'N/A'),
                    "rag_context": aggregated_result.get('rag_result', {}).get('rag_context', 'N/A')
                }
            }
        )
        
        print(f"\n📋 FINAL REPORT PREVIEW (NEW ARCHITECTURE):")
        print("-"*40)
        print(report_msg[:500])
        
        return report
        
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
