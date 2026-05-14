<<<<<<< Updated upstream
from app import db_models
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
#è l'entry point del programma delle API
from app.models import StatusResponse, SkillResponse, UserCreate, UserResponse, UserSkillCreate
from app.database import get_db, engine
from app.db_models import Skill
from app.models import StatusResponse, SkillResponse, SkillCreate, UserCreate, UserResponse, UserSkillCreate
=======
# ============================================================
# main.py - Entry point dell'applicazione FastAPI
# ============================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
>>>>>>> Stashed changes

# Import del database e modelli (engine serve per create_all)
from app.database import engine
from app.db_models import Base

# Import dei router
from app.routers import auth, skills, users


# ============================================================
# Lifespan: codice eseguito all'avvio e allo spegnimento
# ============================================================
# "lifespan" è il metodo MODERNO di FastAPI per gestire startup/shutdown.
# Prima si usava @app.on_event("startup") / @app.on_event("shutdown"),
# ma quel metodo è deprecato dalla versione 0.95+.
#
# asynccontextmanager trasforma una funzione in un "gestore di contesto"
# asincrono. Il codice PRIMA di "yield" gira all'avvio,
# il codice DOPO "yield" gira allo spegnimento.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ============================================================
    # STARTUP: crea le tabelle del database se non esistono
    # ============================================================
    # ⚠️ PRIMA era in db_models.py a livello di modulo.
    #    Ogni volta che importavi db_models, partiva create_all().
    #    Con --reload (modalità sviluppo) veniva chiamato decine di volte.
    # ORA: viene chiamato UNA SOLA VOLTA quando l'app parte.
    Base.metadata.create_all(bind=engine)
    yield
    # ============================================================
    # SHUTDOWN: (libero per pulizia connessioni, file temporanei, ecc.)
    # ============================================================


# ============================================================
# Inizializzazione app FastAPI
# ============================================================
app = FastAPI(
    title="SkillSwap API",
    version="0.2.0",
    description="API per lo scambio di competenze tra utenti",
    lifespan=lifespan,  # 👈 Collega il lifespan all'app
)

# ============================================================
# CORS Middleware
# ============================================================
# CORS = Cross-Origin Resource Sharing
# 
# 🔍 COS'È IL PROBLEMA?
# Il browser blocca le richieste del frontend al backend se vengono
# da ORIGINI DIVERSE (dominio, protocollo o porta diversi).
# Esempio: il frontend su http://localhost:5173 chiama
# il backend su http://localhost:8000 → ORIGINI DIVERSE! Bloccato.
#
# 🛠️ COSA FA QUESTO MIDDLEWARE?
# Dice al browser: "Ehi, queste origini qui sotto sono autorizzate
# a parlare con la mia API, non bloccare le richieste!"
#
# ⚠️ NOTA SU allow_origins=["*"]:
# Con "*" PERMETTI TUTTE le origini. Va bene per sviluppo / demo
# ma NON in produzione perché chiunque può chiamare la tua API.
# In produzione usa una lista di origini specifiche.
# ============================================================
app.add_middleware(
    CORSMiddleware,
    # ["*"] = permetti richieste DA OVUNQUE (qualsiasi origine)
    allow_origins=["*"],
    # ⚠️ NOTA: se usi true toglierà il commento a allow_origins=["http://localhost:5173"]
    # perché ["*"] e credentials=True non possono coesistere (errore).
    allow_credentials=False,
    # ["*"] = permetti TUTTI i metodi HTTP (GET, POST, PUT, DELETE, PATCH, ecc.)
    allow_methods=["*"],
    # ["*"] = permetti TUTTI gli header (Content-Type, Authorization, ecc.)
    allow_headers=["*"],
)

# ============================================================
# Inclusione dei router
# Ogni router gestisce un dominio specifico dell'applicazione
# ============================================================
app.include_router(auth.router)   # /auth/register, /auth/login, /auth/me, /auth/profile
app.include_router(skills.router) # /skills/, /skills/my
app.include_router(users.router)  # /users/public/{id}, /users/search, /users/stats


# ============================================================
# Endpoint: GET / (health check)
# ============================================================
@app.get("/", response_model=dict)
def root():
<<<<<<< Updated upstream
    #ritorna lo stato se il server è acceso e funzionante
    return StatusResponse(status="ok", message="SkillSwap API is running")


@app.get("/skills", response_model=list[SkillResponse])#quando qualcuno chiama questo url con get e ritorna una lista secondo lo schema SkillResponse
def get_skills(db: Session = Depends(get_db)):#passa la connesione del db
    skills = db.query(Skill).all() #va nel db e prende le righe di skill e le restituisce
    return skills

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Controlliamo se l'email esiste già per evitare errori nel DB
    db_user = db.query(db_models.User).filter(db_models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    # 2. Trasformiamo i dati di Pydantic in un oggetto SQLAlchemy
    new_user = db_models.User(
        name=user.name,
        email=user.email,
        password=user.password # Ricorda: nel db_models si chiama 'password'
    )
    
    # 3. Salvataggio nel database
    db.add(new_user)      # Aggiunge alla "lista d'attesa"
    db.commit()           # Scrive fisicamente sul file .db
    db.refresh(new_user)  # Recupera l'ID generato dal database
    
    return new_user

@app.post("/users/skills")
def add_skill_to_user(data: UserSkillCreate, db: Session = Depends(get_db)):
    
    # 1. Controlla che l'utente esista
    user = db.query(db_models.User).filter(db_models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")  #messaggio di errore
    
    # 2. Controlla che la skill esista
    skill = db.query(db_models.Skill).filter(db_models.Skill.id == data.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill non trovata")  #messaggio di errore
    
    # 3. Controlla che l'associazione non esista già
    exists = db.query(db_models.UserSkill).filter(
        db_models.UserSkill.user_id == data.user_id,
        db_models.UserSkill.skill_id == data.skill_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Skill già associata a questo utente") #altro messaggio

    # 4. Crea il collegamento
    new_association = db_models.UserSkill(
        user_id=data.user_id,
        skill_id=data.skill_id,
        level=data.level,
        type=data.type
    )
    db.add(new_association)
    db.commit()
    return {"message": "Skill associata correttamente"}


@app.post("/skills", response_model=SkillResponse)
def create_skill(skill: SkillCreate, db: Session = Depends(get_db)):
    # controlla se esiste già
    exists = db.query(db_models.Skill).filter(
        db_models.Skill.name == skill.name
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Skill già esistente")
    
    nuova_skill = db_models.Skill(
        name=skill.name,
        description=skill.description
    )
    db.add(nuova_skill)
    db.commit()
    db.refresh(nuova_skill)
    return nuova_skill
"""
@app.post("/skills/seed")
def seed_skills(db: Session = Depends(get_db)):
    initial_skills = [
        {"name": "Java", "description": "Linguaggio di programmazione ad oggetti"},
        {"name": "PHP", "description": "Linguaggio per lo sviluppo web lato server"},
        {"name": "Android Studio", "description": "IDE per lo sviluppo di app mobile"},
        {"name": "Python", "description": "Linguaggio versatile per AI e Backend"},
        {"name": "Figma", "description": "Strumento per il design di interfacce"}
    ]
    
    for s in initial_skills:
        # Controlliamo se la skill esiste già per non creare duplicati
        exists = db.query(db_models.Skill).filter(db_models.Skill.name == s["name"]).first()
        if not exists:
            new_skill = db_models.Skill(name=s["name"], description=s["description"])
            db.add(new_skill)
    
    db.commit()
    return {"message": "Database popolato con le skill iniziali"}
"""
=======
    """
    Endpoint di health check.
    Restituisce lo stato del server per verificare che sia in esecuzione.
    """
    return {
        "status": "ok",
        "message": "SkillSwap API is running",
        "version": "0.2.0",
    }
>>>>>>> Stashed changes
