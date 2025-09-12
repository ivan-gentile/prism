import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Run uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("infra.backend.main:app", host="127.0.0.1", port=8000, reload=True)
