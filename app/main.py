from fastapi import FastAPI
#è l'entry point del programma delle API
from app.models import StatusResponse

app = FastAPI(title="SkillSwap API", version="0.1.0")

@app.get("/", response_model=StatusResponse)
def root():
    """
    Health-check endpoint returning the API status.
    """
    return StatusResponse(status="ok", message="SkillSwap API is running")
