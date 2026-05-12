from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
#è l'entry point del programma delle API
from app.models import StatusResponse, SkillResponse
from app.database import get_db
from app.db_models import Skill

app = FastAPI(title="SkillSwap API", version="0.1.0")


@app.get("/", response_model=StatusResponse)
def root():
    """
    Health-check endpoint returning the API status.
    """
    return StatusResponse(status="ok", message="SkillSwap API is running")


@app.get("/skills", response_model=list[SkillResponse])
def get_skills(db: Session = Depends(get_db)):
    """
    Returns all skills stored in the database.
    No authentication required.
    """
    skills = db.query(Skill).all()
    return skills
