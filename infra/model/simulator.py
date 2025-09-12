import sys
import os
import asyncio
from typing import Dict, Any

# Add the parent directory to Python path to import prism_ad
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from prism_ad.agents.prism_agents import PRISMAgentSystem
from prism_ad.data.patient_model import ClinicalReport


class PRISMAlzheimerModel:
    """Integration of the full PRISM-AD multi-agent system for Alzheimer's risk assessment"""
    
    def __init__(self):
        """Initialize the PRISM-AD system"""
        self.prism_system = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the PRISM-AD agent system"""
        if not self.is_initialized:
            print("🔧 Initializing PRISM-AD Multi-Agent System...")
            self.prism_system = PRISMAgentSystem()
            await self.prism_system.initialize_agents()
            self.is_initialized = True
            print("✅ PRISM-AD System initialized successfully")
    
    async def process_async(self, text: str) -> Dict[str, Any]:
        """
        Process clinical text through the full PRISM-AD pipeline
        
        Args:
            text: Clinical description or patient data
            
        Returns:
            Dict containing the clinical assessment results
        """
        try:
            # Ensure system is initialized
            await self.initialize()
            
            print(f"🏥 Processing clinical text through PRISM-AD pipeline...")
            print(f"Input: {text[:100]}..." if len(text) > 100 else f"Input: {text}")
            
            # Process through the full PRISM-AD pipeline
            clinical_report: ClinicalReport = await self.prism_system.process_patient(text)
            
            # Convert to dictionary for API response
            result = {
                "status": "success",
                "assessment_type": "PRISM-AD Alzheimer's Risk Assessment",
                "patient_id": clinical_report.patient_id,
                "fda_stage": clinical_report.fda_stage,
                "risk_level": clinical_report.risk_level,
                "executive_summary": clinical_report.executive_summary,
                "key_findings": clinical_report.key_findings,
                "clinical_recommendations": clinical_report.clinical_recommendations,
                "follow_up_timeline": clinical_report.follow_up_timeline,
                "confidence_score": clinical_report.confidence_score,
                "processing_timestamp": clinical_report.timestamp.isoformat() if clinical_report.timestamp else None
            }
            
            print(f"✅ Assessment completed - Risk Level: {clinical_report.risk_level}")
            return result
            
        except Exception as e:
            print(f"❌ Error processing clinical text: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "assessment_type": "PRISM-AD Alzheimer's Risk Assessment",
                "fallback_response": "Unable to complete full assessment. Please ensure the input contains relevant clinical information such as age, cognitive scores, biomarker data, or clinical observations."
            }
    
    async def process_stream(self, text: str, callback) -> Dict[str, Any]:
        """
        Process clinical text through the full PRISM-AD pipeline with streaming updates
        
        Args:
            text: Clinical description or patient data
            callback: Async callback function for progress updates
            
        Yields:
            Progress updates and final results
        """
        try:
            # Ensure system is initialized
            if not self.is_initialized:
                yield "🔧 Initializing PRISM-AD Multi-Agent System..."
                yield "🔧 Initializing PRISM-AD Agent System (New Architecture)..."
                await self.initialize()
                yield "✅ All agents initialized successfully"
                yield "✅ PRISM-AD System initialized successfully"
                yield ""

            yield "============================================================"
            yield "🏥 PRISM-AD ASSESSMENT PIPELINE STARTED (NEW ARCHITECTURE)"
            yield "============================================================"
            yield ""

            # Process through the full PRISM-AD pipeline with progress updates
            clinical_report = None
            async for item in self.prism_system.process_patient(text):
                if isinstance(item, str):
                    # It's a progress message
                    yield item
                else:
                    # It's the final report
                    clinical_report = item

            # Convert to dictionary for API response
            result = {
                "status": "success",
                "assessment_type": "PRISM-AD Alzheimer's Risk Assessment",
                "patient_id": clinical_report.patient_id,
                "fda_stage": clinical_report.fda_stage,
                "risk_level": clinical_report.risk_level,
                "executive_summary": clinical_report.executive_summary,
                "key_findings": clinical_report.key_findings,
                "clinical_recommendations": clinical_report.clinical_recommendations,
                "follow_up_timeline": clinical_report.follow_up_timeline,
                "confidence_score": clinical_report.confidence_score,
                "processing_timestamp": clinical_report.timestamp.isoformat() if clinical_report.timestamp else None
            }
            
            yield result
            
        except Exception as e:
            print(f"❌ Error processing clinical text: {e}")
            yield {
                "status": "error",
                "error_message": str(e),
                "assessment_type": "PRISM-AD Alzheimer's Risk Assessment",
                "fallback_response": "Unable to complete full assessment. Please ensure the input contains relevant clinical information such as age, cognitive scores, biomarker data, or clinical observations."
            }
    
    def process(self, text: str) -> str:
        """
        Synchronous wrapper for the async processing method
        This is called by the FastAPI endpoint
        """
        try:
            # Check if there's already a running event loop
            try:
                loop = asyncio.get_running_loop()
                # If there's already a loop, we need to run in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_async_in_thread, text)
                    result = future.result(timeout=60)  # 60 second timeout
            except RuntimeError:
                # No running loop, we can create our own
                result = asyncio.run(self.process_async(text))
                
            # Format the response for the chat interface
            if result["status"] == "success":
                response = f"""🏥 **PRISM-AD Alzheimer's Risk Assessment**

**Risk Level:** {result['risk_level']}
**FDA Stage:** {result['fda_stage']}

**Executive Summary:**
{result['executive_summary']}

**Key Findings:**
{chr(10).join(['• ' + finding for finding in result['key_findings'][:3]])}

**Clinical Recommendations:**
{chr(10).join(['• ' + rec for rec in result['clinical_recommendations'][:3]])}

**Follow-up:** {result['follow_up_timeline']}
**Confidence:** {result.get('confidence_score', 'N/A')}

---
*This assessment was generated using the PRISM-AD multi-agent system for Alzheimer's disease risk evaluation.*"""
            else:
                response = f"""❌ **Assessment Error**

{result.get('fallback_response', result.get('error_message', 'Unknown error occurred'))}

Please provide clinical information such as:
• Patient age and demographics
• Cognitive test scores (MMSE, MoCA)
• Biomarker data (CSF, PET, genetic)
• Clinical observations and symptoms"""
            
            return response
                
        except Exception as e:
            print(f"Exception in process: {e}")
            return f"❌ **System Error**: Unable to process request - {str(e)}"
    
    def _run_async_in_thread(self, text: str) -> Dict[str, Any]:
        """Helper method to run async code in a separate thread"""
        return asyncio.run(self.process_async(text))
    
    async def close(self):
        """Clean up resources"""
        if self.prism_system:
            await self.prism_system.close()
