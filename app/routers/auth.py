# ============================================================
# Router: Autenticazione (registrazione, login, profilo corrente)
# ============================================================
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

# Import dei modelli del database (SQLAlchemy) e Pydantic
from app.database import get_db
from app.db_models import User
from app.models import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserMeResponse,
    UserProfileUpdate,
)

# Librerie per hash password e JWT
from passlib.context import CryptContext
from jose import JWTError, jwt

# ============================================================
# Configurazione JWT
# ============================================================
# 👇 PRIMA: SECRET_KEY era hardcoded qui (brutta abitudine).
# ORA: legge da variabile d'ambiente (se esiste), altrimenti usa
#      un default per sviluppo.
#      In produzione, basta impostare:
#        set SKILLSWAP_SECRET_KEY=la-tua-chiave-sicura
#      (o metterla in un file .env)
SECRET_KEY = os.getenv(
    "SKILLSWAP_SECRET_KEY",
    "skillswap-secret-key-change-in-production-2026"  # fallback per sviluppo
)
ALGORITHM = "HS256"  # Algoritmo di firma
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token valido 24 ore

# ============================================================
# Configurazione hash password
# ============================================================
# Usa bcrypt per hashare le password in modo sicuro
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================
# Router
# ============================================================
router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================
# Funzioni helper
# ============================================================

def hash_password(password: str) -> str:
    """Riceve una password in chiaro e restituisce l'hash bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se la password in chiaro corrisponde all'hash salvato."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT firmato.
    - data: dizionario con i claim (es. {"sub": user_id})
    - expires_delta: durata opzionale del token
    """
    to_encode = data.copy()
    # Imposta la scadenza: ora + delta (o default 24h)
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    # Crea e firma il token JWT
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_id(token: str) -> int:
    """
    Decodifica il token JWT e restituisce l'ID utente.
    Se il token non è valido o è scaduto, solleva eccezione.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide o token scaduto.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica il token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception


# ============================================================
# Helper CONDIVISO: estrae user_id dall'header Authorization
# ============================================================
# Questa funzione è identica in auth.py, skills.py e users.py.
# PRIMA era copiata in ogni file → se cambiavi qualcosa dovevi
# ricordarti di aggiornare TUTTE le copie (e qualche volta te ne
# dimenticavi). Brutto.
# ORA: sta SOLO qui, e gli altri router la importano.
def _get_user_id(authorization: Optional[str]) -> int:
    """
    Prende l'header "Authorization: Bearer <token>"
    e restituisce l'ID utente contenuto nel token JWT.
    Se manca o è invalido → HTTPException 401.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token mancante o formato non valido.",
        )
    token = authorization.split(" ")[1]
    return get_current_user_id(token)


# ============================================================
# Endpoint: POST /auth/register
# ============================================================
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Registra un nuovo utente.
    - Verifica che l'email non sia già registrata
    - Hasha la password
    - Salva l'utente nel database
    - Restituisce un token JWT per login automatico post-registrazione
    """
    # Controlla se esiste già un utente con la stessa email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email già registrata. Prova a effettuare il login.",
        )

    # Crea il nuovo utente con password hashata
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hash_password(user_data.password),
        bio="",
        location="",
    )
    db.add(new_user)
    db.commit()  # Salva nel database
    db.refresh(new_user)  # Aggiorna l'oggetto con l'ID generato

    # Genera il token JWT per l'utente appena registrato
    access_token = create_access_token(data={"sub": new_user.id})

    # Restituisce il token + dati utente
    return TokenResponse(
        access_token=access_token,
        user_id=new_user.id,
        name=new_user.name,
    )


# ============================================================
# Endpoint: POST /auth/login
# ============================================================
@router.post("/login", response_model=TokenResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Effettua il login.
    - Cerca l'utente per email
    - Verifica la password
    - Restituisce un token JWT
    """
    # Cerca l'utente nel database tramite email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali errate. Email non trovata.",
        )

    # Verifica la password
    if not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali errate. Password sbagliata.",
        )

    # Genera il token JWT
    access_token = create_access_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        name=user.name,
    )


# ============================================================
# Endpoint: GET /auth/me (usa Header Authorization)
# ============================================================
@router.get("/me", response_model=UserMeResponse)
def get_my_profile(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Restituisce i dati dell'utente autenticato.
    Legge il token dall'header 'Authorization: Bearer <token>'.
    """
    # 👇 Usa _get_user_id invece di riscrivere la logica ogni volta
    user_id = _get_user_id(authorization)

    # Cerca l'utente nel database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")

    return user


# ============================================================
# Endpoint: PUT /auth/profile (aggiorna bio, location, name)
# ============================================================
@router.put("/profile", response_model=UserMeResponse)
def update_my_profile(
    profile_data: UserProfileUpdate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Aggiorna i dati del profilo dell'utente autenticato.
    Accetta bio, location, name (campi opzionali).
    I campi non inviati non vengono sovrascritti (grazie ai Optional).
    """
    user_id = _get_user_id(authorization)

    # Cerca l'utente
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")

    # Aggiorna solo i campi forniti (non null)
    # 👇 pattern "solo se non è None": se il frontend non manda il campo,
    #    Pydantic lo imposta a None e noi lo ignoriamo.
    if profile_data.bio is not None:
        user.bio = profile_data.bio
    if profile_data.location is not None:
        user.location = profile_data.location
    if profile_data.name is not None:
        user.name = profile_data.name

    db.commit()
    db.refresh(user)
    return user
