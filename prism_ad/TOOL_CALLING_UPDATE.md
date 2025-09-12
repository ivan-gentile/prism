# PRISM-AD Tool Calling Update

## Overview
This update enhances the PRISM-AD system with AutoGen's tool calling capabilities and simplifies the Reporter agent for better infrastructure integration.

## Key Changes

### 1. Quantitative Risk Calculator Tool
- **Location**: `prism_ad/utils/quant_risk_calculator.py`
- **Purpose**: Standalone Python script that calculates AD risk scores transparently
- **Features**:
  - Age-based risk multipliers
  - Genetic risk factors (ApoE4)
  - Biomarker scoring (0-100 points)
  - Risk categories (Low/Moderate/High/Very High)
  - Confidence intervals based on data completeness
  - Transparent calculation breakdown

### 2. Tool Calling Integration
The Quantitative Model agent now uses the `calculate_alzheimer_risk` tool:

```python
# The agent is configured with the tool
self.agents["quant_model"] = AssistantAgent(
    name=AGENT_NAMES["quant_model"],
    model_client=self.model_client,
    system_message=QUANT_MODEL_PROMPT,
    tools=[calculate_alzheimer_risk],  # Tool provided here
    max_tool_iterations=2,
    reflect_on_tool_use=True
)
```

**Benefits**:
- Consistent calculations across all assessments
- Transparent, auditable risk scoring
- Works with partial data (handles missing values gracefully)
- Returns structured JSON with detailed breakdowns

### 3. Simplified Reporter Agent
The Reporter agent now produces clean, plain text output that's easier to parse:

**Output Format**:
```
EXECUTIVE SUMMARY
[2-3 sentence summary]

ASSESSMENT RESULTS
- FDA Stage: [Stage X]
- Risk Level: [Low/Moderate/High/Very High]
- 5-Year Progression Risk: [X%]
- Confidence Score: [High/Moderate/Low]

KEY FINDINGS
• [Finding 1]
• [Finding 2]
• [Finding 3]

CLINICAL RECOMMENDATIONS
• [Recommendation 1]
• [Recommendation 2]
• [Recommendation 3]

FOLLOW-UP TIMELINE
- Next assessment: [timeframe]
- Monitoring frequency: [schedule]
```

### 4. Infrastructure Compatibility
Updated `ClinicalReport` model includes:
- `clinical_recommendations` field (for infra compatibility)
- `confidence_score` field
- `timestamp` field
- Backward compatibility with existing `recommendations` field

## Testing

### Run Tool Calling Tests
```bash
python prism_ad/test_tool_calling.py
```

This tests:
1. Direct tool calls
2. Agent-mediated tool calls
3. Partial data handling
4. Confidence intervals

### Run Full Pipeline Test
```bash
python prism_ad/test_new_architecture.py
```

### Run Integration Test
```bash
python infra/test_integration.py
```

## Tool Parameters

The `calculate_alzheimer_risk` tool accepts:
- `age`: Patient age in years
- `apoe4_copies`: "0", "1", or "2" (as string)
- `csf_abeta42`: CSF Aβ42 (pg/mL)
- `csf_ptau`: CSF p-tau (pg/mL)
- `csf_total_tau`: CSF total tau (pg/mL)
- `amyloid_pet`: PET SUVR value
- `hippocampus_left`: Left hippocampus volume (mm³)
- `hippocampus_right`: Right hippocampus volume (mm³)
- `mmse`: MMSE score (0-30)
- `moca`: MoCA score (0-30)
- `cdr_sum`: CDR sum of boxes

All parameters are optional - the tool adapts to available data.

## Example Usage

### Direct Tool Call
```python
from prism_ad.utils.quant_risk_calculator import calculate_alzheimer_risk

result = await calculate_alzheimer_risk(
    age=75,
    apoe4_copies="1",
    csf_abeta42=480,
    mmse=23
)
```

### Through Agent System
```python
clinical_text = """
75-year-old male with MMSE 23, ApoE4 positive (1 copy).
CSF Aβ42: 480 pg/mL, p-tau: 42 pg/mL.
"""

report = await system.process_patient(clinical_text)
```

## Architecture Benefits

1. **Transparency**: All calculations are explicit and auditable
2. **Consistency**: Same calculator used across all assessments
3. **Flexibility**: Works with any amount of available data
4. **Integration**: Clean text output integrates easily with existing infrastructure
5. **AutoGen Native**: Leverages AutoGen's tool calling framework properly

## Next Steps

1. Add more sophisticated tools (e.g., trajectory modeling)
2. Implement real RAG component with medical knowledge base
3. Add visualization tools for risk trajectories
4. Create tools for clinical trial matching
5. Develop tools for intervention recommendations
