# PRISM-AD: Multi-Agent System for Alzheimer's Disease Risk Assessment

## 🧠 Overview

PRISM-AD is a demonstration system that shows how AI agents can collaborate to assess Alzheimer's Disease risk. The system uses **AutoGen** to orchestrate 5 specialized agents that process patient biomarker data through a transparent, step-by-step risk assessment following FDA guidelines.

## 🎯 Key Features

- **Multi-Agent Architecture**: 5 specialized agents working sequentially
- **FDA Compliance**: Following official FDA staging criteria for Alzheimer's Disease
- **Transparent Processing**: Each agent explains its reasoning
- **Comprehensive Assessment**: From data validation to clinical report generation
- **Real Biomarkers**: Uses actual AD biomarkers (CSF proteins, imaging, genetics)

## 🏗️ Architecture

### The Five-Agent Pipeline

1. **📋 Intake Validator**
   - Validates data quality and completeness
   - Checks biological plausibility
   - Identifies missing critical data

2. **📊 Data Normalizer**
   - Compares values to age/sex-matched references
   - Calculates Z-scores and percentiles
   - Flags abnormal biomarkers

3. **🏷️ FDA Stage Classifier**
   - Applies official FDA staging criteria
   - Stages 1-6 from preclinical to severe dementia
   - Provides confidence levels

4. **⚠️ Risk Calculator**
   - Estimates 5-year progression probability
   - Combines multiple risk factors
   - Calculates confidence intervals

5. **📄 Report Synthesizer**
   - Creates human-readable clinical summary
   - Provides actionable recommendations
   - Identifies clinical trial eligibility

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key (currently configured for `gpt-4o-mini`)

### Installation

1. Clone the repository:
```bash
git clone <your-repo>
cd prism
```

2. Create and activate virtual environment:
```bash
python -m venv prism_env

# Windows
.\prism_env\Scripts\Activate.ps1

# Linux/Mac
source prism_env/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the System

Test with sample patients:
```bash
python prism_ad/test_prism_system.py
```

Choose from:
1. Single patient test (MCI case)
2. Multiple patients comparison
3. Quick validation test

## 📊 Sample Output

```
🏥 PRISM-AD ASSESSMENT PIPELINE STARTED
============================================================

📋 Step 1: INTAKE VALIDATION
✓ Data validated, quality score: 0.85

📊 Step 2: DATA NORMALIZATION
✓ CSF Aβ42: -2.1 SD (5th percentile) - ABNORMAL
✓ Hippocampus: -1.8 SD (8th percentile) - ABNORMAL

🏷️ Step 3: FDA STAGE CLASSIFICATION
✓ Stage 3: MCI due to Alzheimer's (Confidence: 0.85)

⚠️ Step 4: RISK CALCULATION
✓ 5-year progression risk: 55% (CI: 45-65%)

📄 Step 5: REPORT SYNTHESIS
✓ Clinical report generated with recommendations
```

## 🧬 Biomarkers Used

### Genetic
- **ApoE4**: Risk gene (0, 1, or 2 copies)

### CSF (Cerebrospinal Fluid)
- **Aβ42**: Amyloid-beta (lower = worse)
- **p-tau181**: Phosphorylated tau (higher = worse)
- **Total tau**: Neurodegeneration marker

### Imaging
- **Hippocampus volume**: Memory region size
- **Amyloid PET SUVR**: Brain amyloid burden
- **FDG-PET**: Brain metabolism

### Cognitive
- **MMSE**: Mini-Mental State Exam (0-30)
- **MoCA**: Montreal Cognitive Assessment
- **CDR-SB**: Clinical Dementia Rating

## 🔧 Configuration

Edit `prism_ad/config.py`:
```python
MODEL_NAME = "gpt-4o-mini"  # Can use other OpenAI models
TEMPERATURE = 0.2  # Lower for consistent medical analysis
```

## 📁 Project Structure

```
prism/
├── prism_ad/
│   ├── agents/
│   │   ├── agent_prompts.py    # System prompts for each agent
│   │   └── prism_agents.py     # Main orchestration logic
│   ├── data/
│   │   └── patient_model.py    # Data models and validation
│   ├── config.py               # Configuration settings
│   └── test_prism_system.py    # Test harness
├── requirements.txt
└── README.md
```

## 🎓 Medical Background

### FDA Stages of Alzheimer's

1. **Stage 1**: Brain changes visible, no symptoms
2. **Stage 2**: Brain changes + subtle memory issues
3. **Stage 3**: MCI (Mild Cognitive Impairment)
4. **Stage 4**: Early dementia
5. **Stage 5**: Moderate dementia
6. **Stage 6**: Severe dementia

### Risk Factors

- **High Risk**: ApoE4 (2 copies), Low CSF Aβ42, High tau
- **Moderate Risk**: Age >70, ApoE4 (1 copy), Hippocampal atrophy
- **Protective**: Higher education, Normal metabolism, No ApoE4

## 🔬 For Developers

### Adding New Agents

1. Define system prompt in `agent_prompts.py`
2. Create agent in `prism_agents.py`
3. Add to processing pipeline
4. Update data flow

### Customizing Biomarkers

Edit `REFERENCE_RANGES` in `patient_model.py`:
```python
REFERENCE_RANGES = {
    "csf_abeta42": {"mean": 900, "std": 200, "abnormal_below": 600},
    # Add your biomarker...
}
```

## ⚠️ Disclaimer

This is a **demonstration system** for educational purposes. Not for clinical use. Always consult qualified healthcare professionals for medical decisions.

## 🤝 Hackathon Notes

Built for 8-hour hackathon sprint demonstrating:
- Multi-agent collaboration with AutoGen
- Medical AI transparency
- FDA guideline implementation
- Sequential processing with feedback

## 📜 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- AutoGen framework by Microsoft
- FDA Alzheimer's staging guidelines
- OpenAI GPT models

---

**Remember**: This is a demo showing AI agent collaboration in healthcare. Real clinical systems require extensive validation, regulatory approval, and professional oversight.
