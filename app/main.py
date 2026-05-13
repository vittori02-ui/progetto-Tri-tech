from app import db_models
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
#è l'entry point del programma delle API
from app.models import StatusResponse, SkillResponse
from app.database import get_db,engine
from app.db_models import Skill

app = FastAPI(title="SkillSwap API", version="0.1.0")
"""
Import
Depends=dice a fast API che una funzione dipende da 
qualcosa in questo caso il database(db)

Session=è il tipo della connesione del database

get_db= la funzione che abbiamo gia in database.py che apre e chiude la connesione

db_model=importa le tabelle che ho creato in db_model
"""
db_models.Base.metadata.create_all(bind=engine) # serve a crearele tabelle se non ci sono si altrimenti no

@app.get("/", response_model=StatusResponse)
def root():
    #ritorna lo stato se il server è acceso e funzionante
    return StatusResponse(status="ok", message="SkillSwap API is running")


@app.get("/skills", response_model=list[SkillResponse])#quando qualcuno chiama questo url con get e ritorna una lista secondo lo schema SkillResponse
def get_skills(db: Session = Depends(get_db)):#passa la connesione del db
    skills = db.query(Skill).all() #va nel db e prende le righe di skill e le restituisce
    return skills
