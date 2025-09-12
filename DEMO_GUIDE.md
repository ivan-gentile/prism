# 🏥 PRISM-AD Demo Guide

## 🚀 Quick Start

Your beautiful new PRISM-AD demo is now ready! The server is running in the background.

### Access the Demo

1. **Open your browser** and navigate to: **http://127.0.0.1:8000**
2. You'll see the modern PRISM-AD interface with a medical theme

### Alternative Ways to Start the Server

#### Option 1: Use the Batch File (Windows)
```bash
# Just double-click or run:
start_demo.bat
```

#### Option 2: Manual Start
```bash
# Activate virtual environment
.\prism_env\Scripts\activate  # Windows
source prism_env/bin/activate  # Linux/Mac

# Run the server
python run_server.py
```

## 🎯 How to Use the Demo

### 1. Quick Example Cases
The UI includes pre-loaded example cases. Click on any of these buttons:
- **Mild Cognitive Impairment** - Early stage case
- **Moderate Risk Case** - Mid-stage progression
- **High Risk Case** - Advanced symptoms
- **Comprehensive Assessment** - Full biomarker panel

### 2. Enter Your Own Clinical Data
Type or paste clinical information in the text area. Include details like:
- Patient demographics (age, gender)
- Cognitive test scores (MMSE, MoCA)
- Biomarker data (CSF proteins, PET scans)
- Genetic factors (ApoE4 status)
- Clinical observations

### 3. Run Assessment
Click the **"Perform Assessment"** button to:
- Process data through 6 specialized AI agents
- See real-time progress updates
- Get comprehensive risk assessment

### 4. Review Results
The system provides:
- **Risk Level** (Low/Moderate/High/Very High)
- **FDA Stage** (1-6 classification)
- **Confidence Score**
- **Executive Summary**
- **Key Clinical Findings**
- **Recommendations**
- **Follow-up Timeline**

### 5. Export Results
Click **"Download Report"** to save the assessment as JSON

## 🎨 UI Features

### Modern Medical Design
- **Clean Interface**: Professional healthcare aesthetic
- **Color-Coded Risk Levels**: Visual risk indicators
- **Responsive Layout**: Works on desktop and mobile
- **Real-time Updates**: Live progress during processing

### Interactive Elements
- **Example Cases**: One-click demo scenarios
- **Progress Tracking**: See each agent's processing
- **Agent Status**: Visual confirmation of multi-agent consensus
- **Smooth Animations**: Professional transitions

## 🔧 Technical Features

### Multi-Agent Architecture
The system uses 6 specialized agents:
1. **Parser Agent** - Extracts clinical data
2. **Validator Agent** - Ensures data quality
3. **FDA Classifier** - Applies staging criteria
4. **Quantitative Risk** - Calculates probabilities
5. **RAG Knowledge** - Retrieves guidelines
6. **Report Generator** - Creates summaries

### Streaming Architecture
- Real-time progress updates via Server-Sent Events
- Async processing for responsive UI
- Fallback to standard endpoints if needed

### API Endpoints
- `GET /` - Main UI interface
- `POST /chat` - Standard assessment endpoint
- `POST /chat/stream` - Streaming assessment with progress
- `GET /docs` - Interactive API documentation

## 📊 Example Input Format

```
75-year-old male with memory complaints and cognitive decline over 2 years.
MMSE score: 23/30, showing deficits in recall and orientation.
Patient is ApoE4 positive (1 copy).
CSF analysis: Aβ42 480 pg/mL (low), p-tau 42 pg/mL (elevated).
Amyloid PET positive with SUVR 1.48.
Patient has difficulty managing finances but still independent in basic activities.
```

## 🛠️ Troubleshooting

### If the UI doesn't load:
1. Ensure the server is running (check console for errors)
2. Verify you're using http://127.0.0.1:8000 (not https)
3. Check that port 8000 is not blocked

### If assessments fail:
1. Ensure OpenAI API key is set in `.env` file
2. Check internet connection for API calls
3. Verify input contains clinical information

### To stop the server:
- Press `Ctrl+C` in the terminal
- Or close the terminal window

## 🎯 Demo Talking Points

When demonstrating PRISM-AD, highlight:

1. **Early Detection**: 5-year prediction window
2. **Multi-Agent Consensus**: Reduces bias and errors
3. **FDA Compliance**: Follows official staging guidelines
4. **Comprehensive Analysis**: 15+ biomarkers considered
5. **Clinical Utility**: Actionable recommendations
6. **Speed**: < 3 seconds for complete assessment
7. **Transparency**: Explainable AI with confidence scores

## 🔗 Additional Resources

- **API Documentation**: http://127.0.0.1:8000/docs
- **Main README**: See README.md for technical details
- **Architecture**: See HACKATHON_SUMMARY.md for system design

---

**Your demo is ready!** Open http://127.0.0.1:8000 in your browser to see the beautiful new interface.
