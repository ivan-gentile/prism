from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import AsyncGenerator, Callable
import asyncio
import json
import os
from pathlib import Path

from ..model.simulator import PRISMAlzheimerModel

app = FastAPI(title="PRISM-AD API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    text: str

# Initialize PRISM-AD Alzheimer's assessment model
model = PRISMAlzheimerModel()

async def progress_callback(message: str):
    """Callback function to handle progress updates"""
    return {
        "event": "progress",
        "data": message
    }

async def stream_process(message: str, callback: Callable) -> AsyncGenerator[str, None]:
    """Stream the processing results"""
    try:
        # Process the message and get updates
        async for update in model.process_stream(message, callback):
            if isinstance(update, dict):
                yield f"data: {json.dumps(update)}\n\n"
            else:
                yield f"data: {json.dumps({'event': 'progress', 'data': str(update)})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'event': 'error', 'data': str(e)})}\n\n"
    finally:
        yield f"data: {json.dumps({'event': 'complete'})}\n\n"

@app.post("/chat")
async def chat(message: Message):
    """Legacy endpoint for non-streaming responses"""
    print(f"Received message: {message.text}")
    response = model.process(message.text)
    return {"response": response}

@app.post("/chat/stream")
async def chat_stream(message: Message):
    """Stream updates during processing"""
    return StreamingResponse(
        stream_process(message.text, progress_callback),
        media_type="text/event-stream"
    )

# Serve the frontend
frontend_path = Path(__file__).parent.parent / "frontend"

# Mount static files
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    @app.get("/")
    async def serve_frontend():
        """Serve the main frontend page"""
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"message": "Frontend not found. Please ensure index.html exists in infra/frontend/"}
else:
    @app.get("/")
    async def root():
        return {"message": "PRISM-AD API is running. Frontend files not found."}
