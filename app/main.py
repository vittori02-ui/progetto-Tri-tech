from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.db_models import Base
from app.models import StatusResponse, SkillResponse, SkillCreate, UserRegister, UserResponse, UserSkillCreate
from app.routers import auth, skills, users, requests, feedback

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
    return {"status": "ok", "message": "SkillSwap API is running", "version": "0.2.0"}
