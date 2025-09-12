# Alzheimer Risk Assessment System

A simple chat interface for interacting with an AI model that assesses Alzheimer's risk based on patient prompts.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the backend:
```bash
uvicorn backend.main:app --reload
```

3. Open `frontend/index.html` in your browser

## Project Structure

- `backend/` - FastAPI backend server
- `frontend/` - Simple HTML/JS frontend
- `model/` - AI model simulator
