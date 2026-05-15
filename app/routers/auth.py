# auth.py = ROTTE PER REGISTRAZIONE E LOGIN
# Tutti gli endpoint iniziano con /auth

import os                                   # Per leggere variabili d'ambiente
from datetime import datetime, timedelta, timezone  # Per gestire date e scadenze
from typing import Optional                 # Optional = il valore puo' essere None

from fastapi import APIRouter, Depends, HTTPException, Header, status
# APIRouter = gruppo di endpoint con prefisso comune (/auth)
# Depends = per iniettare il database negli endpoint
# HTTPException = per restituire errori HTTP (401, 404, 409...)
# Header = per leggere l'header Authorization della richiesta
# status = codici HTTP (200=OK, 201=Creato, 401=Non autorizzato, ecc.)

from sqlalchemy.orm import Session         # Il tipo "sessione del database"

from app.database import get_db             # Funzione per ottenere una sessione DB
from app.db_models import User              # Modello della tabella users
from app.models import (
    UserRegister, UserLogin, TokenResponse,
    UserMeResponse, UserProfileUpdate,
)

from passlib.context import CryptContext    # Per hashare le password con bcrypt
from jose import JWTError, jwt              # Per creare e verificare token JWT


# ============================================================
# CONFIGURAZIONE JWT (il "timbro" che identifica l'utente)
# ============================================================
# JWT = JSON Web Token. E' come un "badge digitale" che dice "questo utente e' loggato".
# Il token viene creato al login e scade dopo 24 ore.
SECRET_KEY = os.getenv(
    "SKILLSWAP_SECRET_KEY",
    "skillswap-secret-key-change-in-production-2026"  # Chiave per firmare i token (in produzione cambiala!)
)
ALGORITHM = "HS256"                               # Algoritmo di sicurezza
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24             # Token valido 24 ore


# ============================================================
# CONFIGURAZIONE HASH PASSWORD
# ============================================================
# bcrypt trasforma la password in un codice segreto (hash).
# Anche se qualcuno ruba il database, non puo' leggere le password.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# CREAZIONE DEL ROUTER
# ============================================================
# prefix="/auth" significa che TUTTI gli endpoint qui dentro
# avranno il percorso /auth/... (es. /auth/register)
router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================
# FUNZIONI DI SUPPORTO (helper)
# ============================================================

def hash_password(password: str) -> str:
    """Prende una password in chiaro e restituisce l'hash (codice segreto)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Controlla se la password corrisponde all'hash salvato nel database."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT (badge digitale). Il token contiene i dati dell'utente e scade dopo un po'."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})   # Aggiunge la data di scadenza
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_id(token: str) -> int:
    """Legge il token JWT e restituisce l'ID dell'utente a cui appartiene.
    Se il token e' falso o scaduto, da' errore 401 (non autorizzato)."""
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide o token scaduto.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))   # "sub" = subject = ID utente
        if user_id is None:
            raise cred_exc
        return user_id
    except JWTError:
        raise cred_exc


# ============================================================
# Helper CONDIVISO (usato anche da altri router: skills, users, ecc.)
# ============================================================
def _get_user_id(authorization: Optional[str]) -> int:
    """Prende l'header 'Authorization: Bearer <token>' e restituisce l'ID utente."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token mancante o formato non valido.",
        )
    token = authorization.split(" ")[1]   # Prende il token dopo "Bearer "
    return get_current_user_id(token)


# ============================================================
# ENDPOINT: POST /auth/register  (REGISTRAZIONE)
# ============================================================
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Crea un nuovo account. Hasha la password, salva l'utente e restituisce un token JWT."""
    # Controlla se l'email e' gia' usata da qualcun altro
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email gia' registrata.")

    # Crea l'utente con password hashata (mai in chiaro!)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hash_password(user_data.password),
        bio="",
        location="",
    )
    db.add(new_user)      # Prepara l'inserimento
    db.commit()           # Scrive nel database
    db.refresh(new_user)  # Aggiorna l'oggetto con l'ID generato

    # Crea il token per fare subito il login
    access_token = create_access_token(data={"sub": str(new_user.id)})

    return TokenResponse(access_token=access_token, user_id=new_user.id, name=new_user.name)


# ============================================================
# ENDPOINT: POST /auth/login  (LOGIN)
# ============================================================
@router.post("/login", response_model=TokenResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Controlla email e password, se giuste restituisce un token JWT."""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email non trovata.")

    if not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password sbagliata.")

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, user_id=user.id, name=user.name)


# ============================================================
# ENDPOINT: GET /auth/me  (PROFILO PERSONALE)
# ============================================================
@router.get("/me", response_model=UserMeResponse)
def get_my_profile(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Restituisce i dati dell'utente loggato (nome, email, bio, ecc.)."""
    user_id = _get_user_id(authorization)       # Legge il token e ottiene l'ID
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")
    return user


# ============================================================
# ENDPOINT: PUT /auth/profile  (MODIFICA PROFILO)
# ============================================================
@router.put("/profile", response_model=UserMeResponse)
def update_my_profile(profile_data: UserProfileUpdate, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Modifica bio, citta' o nome. Solo i campi inviati vengono cambiati."""
    user_id = _get_user_id(authorization)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")

    if profile_data.bio is not None:
        user.bio = profile_data.bio
    if profile_data.location is not None:
        user.location = profile_data.location
    if profile_data.name is not None:
        user.name = profile_data.name

    db.commit()
    db.refresh(user)
    return user
