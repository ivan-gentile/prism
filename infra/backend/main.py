from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from model.simulator import PRISMAlzheimerModel

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

@app.post("/chat")
async def chat(message: Message):
    print(f"Received message: {message.text}")
    response = model.process(message.text)
    return {"response": response}
