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
    INTAKE_VALIDATOR_PROMPT,
    NORMALIZER_PROMPT,
    FDA_CLASSIFIER_PROMPT,
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
        """Create and initialize all five specialized agents"""
        print("🔧 Initializing PRISM-AD Agent System...")
        
        # Create model client
        self.model_client = OpenAIChatCompletionClient(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.2  # Low temperature for consistent medical analysis
        )
        
        # Create each specialized agent
        self.agents["validator"] = AssistantAgent(
            name=AGENT_NAMES["validator"],
            model_client=self.model_client,
            system_message=INTAKE_VALIDATOR_PROMPT,
            max_tool_iterations=1
        )
        
        self.agents["normalizer"] = AssistantAgent(
            name=AGENT_NAMES["normalizer"],
            model_client=self.model_client,
            system_message=NORMALIZER_PROMPT,
            max_tool_iterations=1
        )
        
        self.agents["classifier"] = AssistantAgent(
            name=AGENT_NAMES["classifier"],
            model_client=self.model_client,
            system_message=FDA_CLASSIFIER_PROMPT,
            max_tool_iterations=1
        )
        
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
        
    async def process_patient(self, patient_data: Dict[str, Any]) -> ClinicalReport:
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
            
        # Step 1: Intake Validation
        print("\n📋 Step 1: INTAKE VALIDATION")
        print("-"*40)
        validation_result = await self._run_validator(patient)
        
        # Step 2: Data Normalization
        print("\n📊 Step 2: DATA NORMALIZATION")
        print("-"*40)
        normalization_result = await self._run_normalizer(validation_result)
        
        # Step 3: FDA Stage Classification
        print("\n🏷️ Step 3: FDA STAGE CLASSIFICATION")
        print("-"*40)
        classification_result = await self._run_classifier(normalization_result)
        
        # Step 4: Risk Calculation
        print("\n⚠️ Step 4: RISK CALCULATION")
        print("-"*40)
        risk_result = await self._run_risk_calculator(
            normalization_result, 
            classification_result
        )
        
        # Step 5: Report Synthesis
        print("\n📄 Step 5: REPORT SYNTHESIS")
        print("-"*40)
        final_report = await self._run_reporter(
            patient,
            validation_result,
            normalization_result,
            classification_result,
            risk_result
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
        
    async def _run_normalizer(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Data Normalizer agent"""
        patient = validation_result["patient"]
        
        task = f"""Normalize the following validated patient data against age/sex-matched references:
        
        Previous validation: {validation_result['validation'][:500]}
        
        Patient: {patient.age} year old {patient.sex or 'Unknown sex'}
        
        Key biomarkers to normalize:
        - CSF Aβ42: {patient.csf_abeta42} pg/mL (reference mean: 900, abnormal <600)
        - CSF p-tau181: {patient.csf_ptau181} pg/mL (reference mean: 20, abnormal >30)
        - Hippocampus volume: {(patient.hippocampus_volume_left or 0) + (patient.hippocampus_volume_right or 0) / 2} mm³
        - MMSE: {patient.mmse_score} (adjust for education: {patient.education_years} years)
        - Amyloid PET: {patient.amyloid_pet_suvr} (positive >1.3)
        
        Calculate Z-scores and identify abnormal markers (>1.5 SD from normal).
        """
        
        result = await self.agents["normalizer"].run(task=task)
        normalization_msg = result.messages[-1].content if result.messages else ""
        print(f"Normalizer says: {normalization_msg[:200]}...")
        
        self.processing_results["normalization"] = normalization_msg
        return {
            "normalization": normalization_msg,
            "patient": patient,
            "validation": validation_result["validation"]
        }
        
    async def _run_classifier(self, normalization_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run the FDA Stage Classifier agent"""
        patient = normalization_result["patient"]
        
        task = f"""Classify the patient into FDA Alzheimer's stages based on:
        
        Normalization analysis: {normalization_result['normalization'][:500]}
        
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
            **normalization_result,
            "classification": classification_msg
        }
        
    async def _run_risk_calculator(
        self, 
        normalization_result: Dict[str, Any],
        classification_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the Risk Calculator agent"""
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
