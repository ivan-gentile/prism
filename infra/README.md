# PRISM-AD Clinical Assessment Infrastructure

A web-based interface for the PRISM-AD multi-agent system for Alzheimer's Disease risk assessment. This infrastructure provides a FastAPI backend integrated with the sophisticated PRISM-AD clinical analysis pipeline.

## Features

- **Full PRISM-AD Integration**: Uses the complete multi-agent system for clinical assessment
- **Clinical Text Processing**: Accepts natural language clinical descriptions
- **Comprehensive Analysis**: Provides FDA staging, risk assessment, and clinical recommendations
- **Web Interface**: Simple chat-like interface for clinical interactions

## Setup

1. **Activate the virtual environment** (required):
```bash
# Windows
prism_env\Scripts\activate

# Linux/Mac
source prism_env/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up OpenAI API key** (required for PRISM-AD system):
```bash
# Create .env file in the project root with:
OPENAI_API_KEY=your_api_key_here
```

4. **Run the backend**:
```bash
uvicorn backend.main:app --reload
```

5. **Open the frontend**:
   - Open `frontend/index.html` in your browser
   - Or visit `http://localhost:8000/docs` for API documentation

## Usage

Enter clinical information in the web interface, such as:

```
75-year-old male with memory complaints and cognitive decline over 2 years.
MMSE score: 23/30, showing deficits in recall and orientation.
Patient is ApoE4 positive (1 copy). 
CSF analysis: Aβ42 480 pg/mL (low), p-tau 42 pg/mL (elevated).
Amyloid PET positive with SUVR 1.48.
Patient has difficulty managing finances but still independent in basic activities.
```

The system will provide:
- FDA stage classification
- Risk level assessment
- Clinical recommendations
- Follow-up timeline
- Confidence scores

## Project Structure

- `backend/` - FastAPI backend server with PRISM-AD integration
- `frontend/` - Clinical assessment web interface
- `model/` - PRISM-AD multi-agent system integration

## Architecture

The system integrates the full PRISM-AD pipeline:

1. **Clinical Text Parser** - Extracts structured data from clinical narratives
2. **Data Validator** - Ensures data quality and biological plausibility
3. **Parallel Analysis** - Runs multiple specialized models:
   - Quantitative risk model
   - FDA stage classifier
   - RAG-based analysis (future)
4. **Report Synthesizer** - Generates comprehensive clinical reports

## API Endpoints

- `POST /chat` - Process clinical text and return assessment results
- `GET /docs` - Interactive API documentation
