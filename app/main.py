from app import db_models
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
#è l'entry point del programma delle API
from app.models import StatusResponse, SkillResponse, UserCreate, UserResponse, UserSkillCreate
from app.database import get_db, engine
from app.db_models import Skill
from app.models import StatusResponse, SkillResponse, SkillCreate, UserCreate, UserResponse, UserSkillCreate
# ============================================================
# main.py - Entry point dell'applicazione FastAPI
# ============================================================

# main.py = PUNTO DI PARTENZA DEL BACKEND
# Quando fai girare "uvicorn app.main:app --reload", FastAPI parte da qui.


from contextlib import asynccontextmanager
# asynccontextmanager: trasforma una funzione normale in una funzione
# che puo' eseguire codice all'avvio e allo spegnimento del server.

from fastapi import FastAPI
# FastAPI: il framework che crea il server web e gestisce le richieste HTTP.

from fastapi.middleware.cors import CORSMiddleware

# Import del database e modelli (engine serve per create_all)
# CORSMiddleware: permette al frontend (es. http://localhost:5173) di
# parlare con questo backend (http://localhost:8000). Senza, il browser blocca tutto.
from app.database import engine
# engine: la connessione al database SQLite (file skillswap.db).

from app.db_models import Base

# Import dei router
from app.routers import auth, skills, users
from fastapi.middleware.cors import CORSMiddleware

# Base: la classe madre di tutte le tabelle del database.

from app.routers import auth, skills, users, requests, feedback
# router: endpoint divisi in file separati per ordine.
#   auth = registrazione/login
#   skills = gestione competenze
#   users = profili e ricerca
#   requests = richieste di sessione
#   feedback = valutazioni post-sessione

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# LIFESPAN: COSA FARE ALL'AVVIO DEL SERVER
# ============================================================
# "lifespan" e' il metodo moderno di FastAPI (quello vecchio era deprecato).
# Il codice prima di "yield" gira all'avvio, dopo "yield" gira allo spegnimento.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # All'avvio del server, crea tutte le tabelle del database
    # (se non esistono gia'). create_all() e' intelligente: controlla
    # se la tabella esiste gia' e crea solo quelle nuove.
    Base.metadata.create_all(bind=engine)

    yield  # Qui il server rimane in esecuzione finche' non lo spegni

    # (Opzionale) Qui potresti chiudere connessioni, cancellare file temporanei, ecc.


# ============================================================
# CREAZIONE DELL'APP FASTAPI
# ============================================================
app = FastAPI(
    title="SkillSwap API",
    version="0.2.0",
    description="API per lo scambio di competenze tra utenti",
    lifespan=lifespan,  # Collega la funzione lifespan all'app
)

# ============================================================
# CORS MIDDLEWARE (permette al frontend di chiamare il backend)
# ============================================================
# CORS = Cross-Origin Resource Sharing.
# Problema: frontend su porta 5173, backend su porta 8000.
# Per il browser sono "origini diverse" -> blocca la richiesta.
# Soluzione: questo middleware dice al browser "lascia passare!".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # ["*"] = permetti TUTTI (solo in sviluppo!)
    allow_credentials=False,    # False perche' usiamo ["*"]
    allow_methods=["*"],        # Permetti GET, POST, PUT, DELETE...
    allow_headers=["*"],        # Permetti Authorization, Content-Type...
)

# ============================================================
# INCLUSIONE DEI ROUTER (collega gli endpoint all'app)
# ============================================================
app.include_router(auth.router)     # /auth/register, /auth/login, /auth/me, /auth/profile
app.include_router(skills.router)   # /skills/ (catalogo) e /skills/my (skill personali)
app.include_router(users.router)    # /users/public/{id}, /users/search, /users/stats
app.include_router(requests.router) # /requests/ (richieste di sessione tra utenti)
app.include_router(feedback.router) # /feedback/ (valutazioni post-sessione)


# ============================================================
# ENDPOINT: GET /  (Health Check - controllo che il server sia vivo)
# ============================================================
@app.get("/", response_model=dict)
def root():
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
"""
    Endpoint di health check.
    Restituisce lo stato del server per verificare che sia in esecuzione.
    
=======
>>>>>>> mura
    return {
        "status": "ok",                  # "ok" = tutto funziona
        "message": "SkillSwap API is running",
        "version": "0.2.0",
    }

"""
