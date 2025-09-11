"""Patient data model for PRISM-AD system"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum


class ApoE4Status(str, Enum):
    """ApoE4 gene variant status"""
    ZERO_COPIES = "0"
    ONE_COPY = "1"
    TWO_COPIES = "2"
    UNKNOWN = "unknown"


class FDAStage(str, Enum):
    """FDA stages of Alzheimer's Disease"""
    STAGE_1 = "Stage 1: Preclinical AD - Brain changes without symptoms"
    STAGE_2 = "Stage 2: Mild cognitive changes with brain pathology"
    STAGE_3 = "Stage 3: MCI due to Alzheimer's"
    STAGE_4 = "Stage 4: Mild dementia"
    STAGE_5 = "Stage 5: Moderate dementia"
    STAGE_6 = "Stage 6: Severe dementia"
    NORMAL = "Normal aging - No significant pathology"
    UNCERTAIN = "Uncertain - Requires additional testing"


class PatientData(BaseModel):
    """Patient biomarker and clinical data"""
    # Demographics
    patient_id: str = Field(..., description="Unique patient identifier")
    age: float = Field(..., ge=0, le=120, description="Patient age in years")
    sex: Optional[str] = Field(None, description="Biological sex (M/F)")
    education_years: Optional[float] = Field(None, ge=0, le=30, description="Years of education")
    
    # Genetic markers
    apoe4_copies: Optional[ApoE4Status] = Field(None, description="Number of ApoE4 alleles (0, 1, or 2)")
    
    # CSF Biomarkers (pg/mL)
    csf_abeta42: Optional[float] = Field(None, gt=0, description="CSF Amyloid-beta 42 levels")
    csf_abeta40: Optional[float] = Field(None, gt=0, description="CSF Amyloid-beta 40 levels")
    csf_ptau181: Optional[float] = Field(None, gt=0, description="CSF Phosphorylated tau 181")
    csf_total_tau: Optional[float] = Field(None, gt=0, description="CSF Total tau")
    
    # Imaging markers
    hippocampus_volume_left: Optional[float] = Field(None, gt=0, description="Left hippocampus volume (mm³)")
    hippocampus_volume_right: Optional[float] = Field(None, gt=0, description="Right hippocampus volume (mm³)")
    amyloid_pet_suvr: Optional[float] = Field(None, gt=0, description="Amyloid PET SUVR (standardized uptake value ratio)")
    fdg_pet_metaroi: Optional[float] = Field(None, gt=0, description="FDG-PET metabolic ROI average")
    
    # Cognitive scores
    mmse_score: Optional[float] = Field(None, ge=0, le=30, description="Mini-Mental State Examination score")
    moca_score: Optional[float] = Field(None, ge=0, le=30, description="Montreal Cognitive Assessment score")
    cdr_sum: Optional[float] = Field(None, ge=0, le=18, description="Clinical Dementia Rating sum of boxes")
    adas_cog13: Optional[float] = Field(None, ge=0, le=85, description="ADAS-Cog 13 score")
    
    # Clinical observations
    memory_complaints: Optional[bool] = Field(None, description="Self-reported memory complaints")
    functional_impairment: Optional[bool] = Field(None, description="Impairment in daily activities")
    
    @field_validator('sex')
    @classmethod
    def validate_sex(cls, v):
        if v and v.upper() not in ['M', 'F', 'MALE', 'FEMALE']:
            raise ValueError('Sex must be M/F or Male/Female')
        return v.upper()[0] if v else None


class ValidationResult(BaseModel):
    """Result from the Intake Validator agent"""
    is_valid: bool
    cleaned_data: PatientData
    missing_critical: List[str] = Field(default_factory=list)
    missing_optional: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    data_quality_score: float = Field(..., ge=0, le=1)


class NormalizationResult(BaseModel):
    """Result from the Normalizer agent"""
    patient_data: PatientData
    z_scores: Dict[str, float] = Field(default_factory=dict)
    percentiles: Dict[str, float] = Field(default_factory=dict)
    abnormal_markers: List[str] = Field(default_factory=list)
    interpretation: Dict[str, str] = Field(default_factory=dict)


class ClassificationResult(BaseModel):
    """Result from the FDA Stage Classifier agent"""
    fda_stage: FDAStage
    confidence: float = Field(..., ge=0, le=1)
    evidence: List[str] = Field(default_factory=list)
    alternative_stages: List[tuple[FDAStage, float]] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Result from the Risk Calculator agent"""
    risk_score: float = Field(..., ge=0, le=1, description="5-year progression risk")
    confidence_interval: tuple[float, float]
    risk_factors: Dict[str, float] = Field(default_factory=dict)
    protective_factors: Dict[str, float] = Field(default_factory=dict)
    risk_trajectory: List[Dict[str, Any]] = Field(default_factory=list)


class ClinicalReport(BaseModel):
    """Final report from the Report Synthesizer agent"""
    patient_id: str
    assessment_date: str
    executive_summary: str
    fda_stage: FDAStage
    risk_level: str  # Low, Moderate, High, Very High
    key_findings: List[str]
    recommendations: List[str]
    follow_up_timeline: str
    clinical_trial_eligibility: List[str] = Field(default_factory=list)
    detailed_results: Dict[str, Any] = Field(default_factory=dict)


# Reference ranges for normalization (simplified for demo)
REFERENCE_RANGES = {
    "csf_abeta42": {"mean": 900, "std": 200, "abnormal_below": 600},
    "csf_ptau181": {"mean": 20, "std": 8, "abnormal_above": 30},
    "csf_total_tau": {"mean": 250, "std": 100, "abnormal_above": 400},
    "hippocampus_volume": {
        "age_70": {"mean": 3500, "std": 400},
        "age_80": {"mean": 3200, "std": 450}
    },
    "mmse_score": {"normal": 27, "mci": 24, "dementia": 20},
    "amyloid_pet_suvr": {"negative": 1.1, "positive": 1.3}
}
