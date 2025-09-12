"""Quantitative Risk Calculator for Alzheimer's Disease Assessment

This module provides a simple, transparent risk scoring system for AD risk assessment.
It can be called as a tool by the Quantitative Model agent.
"""

from typing import Dict, Any, Optional, Tuple
import json


class AlzheimerRiskCalculator:
    """Quantitative risk calculator for Alzheimer's disease progression"""
    
    def __init__(self):
        """Initialize the risk calculator with scoring parameters"""
        # Age-based risk multipliers
        self.age_multipliers = {
            "under_60": 1.0,
            "60_70": 1.5,
            "70_80": 2.5,
            "over_80": 4.0
        }
        
        # Genetic risk multipliers
        self.apoe4_multipliers = {
            "0": 0.7,   # Protective
            "1": 2.5,   # Moderate risk
            "2": 10.0   # High risk
        }
        
        # Biomarker thresholds and points
        self.biomarker_scoring = {
            "csf_abeta42": {"threshold": 600, "operator": "<", "points": 25},
            "csf_ptau": {"threshold": 30, "operator": ">", "points": 20},
            "csf_total_tau": {"threshold": 400, "operator": ">", "points": 15},
            "amyloid_pet": {"threshold": 1.3, "operator": ">", "points": 30},
            "hippocampus_atrophy": {"threshold": -2.0, "operator": "<", "points": 20},  # Z-score
            "mmse_mild": {"threshold": 27, "operator": "<", "points": 10},
            "mmse_moderate": {"threshold": 24, "operator": "<", "points": 25},
            "moca_impaired": {"threshold": 26, "operator": "<", "points": 15}
        }
        
        # Risk categories
        self.risk_categories = {
            "low": {"range": (0, 20), "progression": (5, 10)},
            "moderate": {"range": (21, 40), "progression": (15, 30)},
            "high": {"range": (41, 60), "progression": (35, 55)},
            "very_high": {"range": (61, 100), "progression": (60, 85)}
        }
    
    def calculate_age_multiplier(self, age: Optional[float]) -> Tuple[float, str]:
        """Calculate age-based risk multiplier"""
        if age is None:
            return 1.5, "Age unknown - using moderate baseline"
        
        if age < 60:
            return self.age_multipliers["under_60"], f"Age {age}: baseline risk"
        elif age <= 70:
            return self.age_multipliers["60_70"], f"Age {age}: 1.5x risk"
        elif age <= 80:
            return self.age_multipliers["70_80"], f"Age {age}: 2.5x risk"
        else:
            return self.age_multipliers["over_80"], f"Age {age}: 4x risk"
    
    def calculate_genetic_multiplier(self, apoe4_copies: Optional[str]) -> Tuple[float, str]:
        """Calculate genetic risk multiplier"""
        if apoe4_copies is None:
            return 1.0, "ApoE4 status unknown - using neutral baseline"
        
        copies = str(apoe4_copies)
        if copies in self.apoe4_multipliers:
            multiplier = self.apoe4_multipliers[copies]
            if copies == "0":
                return multiplier, f"ApoE4 negative: 0.7x risk (protective)"
            elif copies == "1":
                return multiplier, f"ApoE4 heterozygous: 2.5x risk"
            else:
                return multiplier, f"ApoE4 homozygous: 10x risk"
        return 1.0, "ApoE4 status unclear - using neutral baseline"
    
    def calculate_biomarker_score(self, biomarkers: Dict[str, Any]) -> Tuple[int, list]:
        """Calculate biomarker-based risk score"""
        total_score = 0
        contributing_factors = []
        
        # CSF markers
        if biomarkers.get("csf_abeta42") is not None:
            value = biomarkers["csf_abeta42"]
            if value < self.biomarker_scoring["csf_abeta42"]["threshold"]:
                points = self.biomarker_scoring["csf_abeta42"]["points"]
                total_score += points
                contributing_factors.append(f"Low CSF Aβ42 ({value} pg/mL): +{points} points")
        
        if biomarkers.get("csf_ptau") is not None:
            value = biomarkers["csf_ptau"]
            if value > self.biomarker_scoring["csf_ptau"]["threshold"]:
                points = self.biomarker_scoring["csf_ptau"]["points"]
                total_score += points
                contributing_factors.append(f"Elevated CSF p-tau ({value} pg/mL): +{points} points")
        
        if biomarkers.get("csf_total_tau") is not None:
            value = biomarkers["csf_total_tau"]
            if value > self.biomarker_scoring["csf_total_tau"]["threshold"]:
                points = self.biomarker_scoring["csf_total_tau"]["points"]
                total_score += points
                contributing_factors.append(f"Elevated CSF total tau ({value} pg/mL): +{points} points")
        
        # Imaging markers
        if biomarkers.get("amyloid_pet") is not None:
            value = biomarkers["amyloid_pet"]
            if value > self.biomarker_scoring["amyloid_pet"]["threshold"]:
                points = self.biomarker_scoring["amyloid_pet"]["points"]
                total_score += points
                contributing_factors.append(f"Positive amyloid PET (SUVR {value}): +{points} points")
        
        # Hippocampal atrophy (simplified - would need actual Z-score calculation)
        if biomarkers.get("hippocampus_left") is not None and biomarkers.get("hippocampus_right") is not None:
            avg_volume = (biomarkers["hippocampus_left"] + biomarkers["hippocampus_right"]) / 2
            if avg_volume < 3000:  # Simplified threshold
                points = self.biomarker_scoring["hippocampus_atrophy"]["points"]
                total_score += points
                contributing_factors.append(f"Hippocampal atrophy ({avg_volume:.0f} mm³): +{points} points")
        
        # Cognitive scores
        if biomarkers.get("mmse") is not None:
            value = biomarkers["mmse"]
            if value < self.biomarker_scoring["mmse_moderate"]["threshold"]:
                points = self.biomarker_scoring["mmse_moderate"]["points"]
                total_score += points
                contributing_factors.append(f"MMSE impairment ({value}/30): +{points} points")
            elif value < self.biomarker_scoring["mmse_mild"]["threshold"]:
                points = self.biomarker_scoring["mmse_mild"]["points"]
                total_score += points
                contributing_factors.append(f"Mild MMSE decline ({value}/30): +{points} points")
        
        if biomarkers.get("moca") is not None:
            value = biomarkers["moca"]
            if value < self.biomarker_scoring["moca_impaired"]["threshold"]:
                points = self.biomarker_scoring["moca_impaired"]["points"]
                total_score += points
                contributing_factors.append(f"MoCA impairment ({value}/30): +{points} points")
        
        return total_score, contributing_factors
    
    def determine_risk_category(self, score: int) -> Tuple[str, Tuple[int, int]]:
        """Determine risk category based on total score"""
        for category, info in self.risk_categories.items():
            if info["range"][0] <= score <= info["range"][1]:
                return category, info["progression"]
        return "very_high", (60, 85)  # Default to very high if score > 100
    
    def calculate_confidence_interval(self, data_completeness: float) -> int:
        """Calculate confidence interval based on data completeness"""
        if data_completeness >= 0.8:
            return 10  # ±10% for complete data
        elif data_completeness >= 0.5:
            return 20  # ±20% for partial data
        else:
            return 30  # ±30% for minimal data
    
    def calculate_risk(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to calculate comprehensive risk assessment
        
        Args:
            patient_data: Dictionary containing patient information
                - age: float
                - apoe4_copies: str ("0", "1", "2")
                - csf_abeta42: float
                - csf_ptau: float
                - csf_total_tau: float
                - amyloid_pet: float
                - hippocampus_left: float
                - hippocampus_right: float
                - mmse: float
                - moca: float
        
        Returns:
            Dictionary containing risk assessment results
        """
        # Calculate age multiplier
        age_multiplier, age_explanation = self.calculate_age_multiplier(patient_data.get("age"))
        
        # Calculate genetic multiplier
        genetic_multiplier, genetic_explanation = self.calculate_genetic_multiplier(
            patient_data.get("apoe4_copies")
        )
        
        # Calculate biomarker score
        biomarker_score, contributing_factors = self.calculate_biomarker_score(patient_data)
        
        # Determine base risk category
        risk_category, progression_range = self.determine_risk_category(biomarker_score)
        
        # Calculate adjusted risk
        base_risk = sum(progression_range) / 2  # Mid-point of range
        adjusted_risk = base_risk * age_multiplier * genetic_multiplier
        adjusted_risk = min(95, max(5, adjusted_risk))  # Cap between 5-95%
        
        # Calculate data completeness
        expected_fields = ["age", "apoe4_copies", "csf_abeta42", "csf_ptau", 
                          "amyloid_pet", "mmse", "moca"]
        available_fields = sum(1 for field in expected_fields if patient_data.get(field) is not None)
        data_completeness = available_fields / len(expected_fields)
        
        # Calculate confidence interval
        confidence_interval = self.calculate_confidence_interval(data_completeness)
        
        # Identify top risk drivers
        risk_drivers = []
        if genetic_multiplier > 2:
            risk_drivers.append(genetic_explanation)
        if age_multiplier > 2:
            risk_drivers.append(age_explanation)
        risk_drivers.extend(contributing_factors[:3])  # Top 3 biomarker factors
        
        # Create detailed calculation breakdown
        calculation_details = {
            "raw_biomarker_score": biomarker_score,
            "age_multiplier": age_multiplier,
            "genetic_multiplier": genetic_multiplier,
            "base_risk_percentage": base_risk,
            "adjusted_risk_percentage": adjusted_risk,
            "calculation_formula": f"{base_risk:.1f}% × {age_multiplier} × {genetic_multiplier} = {adjusted_risk:.1f}%"
        }
        
        return {
            "risk_score": biomarker_score,
            "risk_category": risk_category.replace("_", " ").title(),
            "five_year_progression": f"{adjusted_risk:.1f}%",
            "confidence_interval": f"±{confidence_interval}%",
            "confidence_range": (
                max(5, adjusted_risk - confidence_interval),
                min(95, adjusted_risk + confidence_interval)
            ),
            "data_completeness": f"{data_completeness*100:.0f}%",
            "risk_drivers": risk_drivers[:5],  # Top 5 risk drivers
            "contributing_factors": contributing_factors,
            "age_explanation": age_explanation,
            "genetic_explanation": genetic_explanation,
            "calculation_details": calculation_details
        }


# Standalone function that can be called as a tool
async def calculate_alzheimer_risk(
    age: Optional[float] = None,
    apoe4_copies: Optional[str] = None,
    csf_abeta42: Optional[float] = None,
    csf_ptau: Optional[float] = None,
    csf_total_tau: Optional[float] = None,
    amyloid_pet: Optional[float] = None,
    hippocampus_left: Optional[float] = None,
    hippocampus_right: Optional[float] = None,
    mmse: Optional[float] = None,
    moca: Optional[float] = None,
    cdr_sum: Optional[float] = None
) -> str:
    """
    Calculate Alzheimer's disease risk score using quantitative model
    
    This tool performs transparent risk calculation based on biomarkers and demographics.
    All parameters are optional - the calculator will work with available data.
    
    Args:
        age: Patient age in years
        apoe4_copies: Number of ApoE4 alleles ("0", "1", or "2")
        csf_abeta42: CSF Amyloid-beta 42 levels (pg/mL)
        csf_ptau: CSF Phosphorylated tau (pg/mL)
        csf_total_tau: CSF Total tau (pg/mL)
        amyloid_pet: Amyloid PET SUVR value
        hippocampus_left: Left hippocampus volume (mm³)
        hippocampus_right: Right hippocampus volume (mm³)
        mmse: Mini-Mental State Examination score (0-30)
        moca: Montreal Cognitive Assessment score (0-30)
        cdr_sum: Clinical Dementia Rating sum of boxes
    
    Returns:
        JSON string with detailed risk assessment
    """
    # Create patient data dictionary
    patient_data = {
        "age": age,
        "apoe4_copies": apoe4_copies,
        "csf_abeta42": csf_abeta42,
        "csf_ptau": csf_ptau,
        "csf_total_tau": csf_total_tau,
        "amyloid_pet": amyloid_pet,
        "hippocampus_left": hippocampus_left,
        "hippocampus_right": hippocampus_right,
        "mmse": mmse,
        "moca": moca,
        "cdr_sum": cdr_sum
    }
    
    # Remove None values
    patient_data = {k: v for k, v in patient_data.items() if v is not None}
    
    # Calculate risk
    calculator = AlzheimerRiskCalculator()
    risk_assessment = calculator.calculate_risk(patient_data)
    
    # Format result as readable JSON
    return json.dumps(risk_assessment, indent=2)


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test with complete data
        result = await calculate_alzheimer_risk(
            age=75,
            apoe4_copies="1",
            csf_abeta42=480,
            csf_ptau=42,
            amyloid_pet=1.48,
            mmse=23
        )
        print("Test Result:")
        print(result)
    
    asyncio.run(test())
