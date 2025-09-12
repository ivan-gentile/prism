from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator, Callable
import asyncio
import json

from ..model.simulator import PRISMAlzheimerModel

app = FastAPI()

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
