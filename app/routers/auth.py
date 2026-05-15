# auth.py = ROTTE PER REGISTRAZIONE E LOGIN
# Tutti gli endpoint iniziano con /auth

import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import User
from app.models import (
    UserRegister, UserLogin, TokenResponse,
    UserMeResponse, UserProfileUpdate,
)

import bcrypt


# ============================================================
# CONFIGURAZIONE JWT (COMMENTATO - NON ATTIVO)
# ============================================================
# COSA E' UN JWT (JSON Web Token)?
# --------------------------------
# Un JWT e' come un "badge digitale" che il server ti da dopo il login.
# Contiene informazioni su di te (es. il tuo ID utente) ed e' firmato
# digitalmente dal server con una chiave segreta (SECRET_KEY).
#
# COME FUNZIONA IL FLUSSO JWT:
# 1. Tu fai login con email + password
# 2. Il server verifica le credenziali
# 3. Il server crea un JWT: prende il tuo ID, lo mette in un JSON,
#    lo codifica in base64 e lo FIRMA con la SECRET_KEY
# 4. Il JWT ha una scadenza (exp) - dopo 24 ore non vale piu'
# 5. Tu salvi il JWT nel localStorage del browser
# 6. Ogni richiesta successiva manda il JWT nell'header:
#    "Authorization: Bearer <token>"
# 7. Il server verifica la firma: se e' valida e non scaduta,
#    estrae il tuo ID e ti fa accedere
#
# PERCHE' E' SICURO?
# - La firma impedisce di falsificare il token
# - La scadenza impedisce di usarlo per sempre
# - Il server NON deve salvare nulla in memoria (stateless)
#
# STRUTTURA DI UN JWT (3 parti separate da punti):
#   Header.Algorithm.Signature
#   es: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc123...
#
# PER ORA NON LO USIAMO: usiamo invece un semplice hash della password
# come "chiave" di autenticazione. Il frontend salva l'hash e lo manda
# come header per identificarsi.

# SECRET_KEY = os.getenv(
#     "SKILLSWAP_SECRET_KEY",
#     "skillswap-secret-key-change-in-production-2026"
# )
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# ============================================================
# CREAZIONE DEL ROUTER
# ============================================================
router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    """Prende una password in chiaro e restituisce l'hash bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Controlla se la password corrisponde all'hash salvato nel database."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ============================================================
# FUNZIONI JWT (COMMENTATE - NON ATTIVE)
# ============================================================
# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
#     """Crea un token JWT firmato con la SECRET_KEY.
#     Il token contiene i dati (es. user_id) e una scadenza."""
#     to_encode = data.copy()
#     expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#
#
# def get_current_user_id(token: str) -> int:
#     """Decodifica il JWT e verifica la firma.
#     Se la firma e' valida e il token non e' scaduto,
#     restituisce l'ID utente dal campo 'sub'."""
#     cred_exc = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Credenziali non valide o token scaduto.",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = int(payload.get("sub"))
#         if user_id is None:
#             raise cred_exc
#         return user_id
#     except JWTError:
#         raise cred_exc


def get_user_id_from_hash(auth_hash: str, db: Session) -> int:
    """Trova l'utente confrontando l'hash ricevuto con quello nel database.
    Se l'hash corrisponde, restituisce l'ID utente."""
    user = db.query(User).filter(User.password == auth_hash).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hash non valido. Utente non trovato.",
        )
    return user.id


def _get_user_id(authorization: Optional[str], db: Session) -> int:
    """Prende l'header 'Authorization: Bearer <hash>' e restituisce l'ID utente
    confrontando l'hash con quello salvato nel database."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token mancante o formato non valido. Usa: 'Authorization: Bearer <tuo_hash>'",
        )
    auth_hash = authorization.split(" ")[1]
    return get_user_id_from_hash(auth_hash, db)


# ============================================================
# ENDPOINT: POST /auth/register  (REGISTRAZIONE)
# ============================================================
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Crea un nuovo account. Hasha la password, salva l'utente e restituisce l'hash."""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email gia' registrata.")

    password_hash = hash_password(user_data.password)

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=password_hash,
        bio="",
        location="",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return TokenResponse(access_token=password_hash, user_id=new_user.id, name=new_user.name)


# ============================================================
# ENDPOINT: POST /auth/login  (LOGIN)
# ============================================================
@router.post("/login", response_model=TokenResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Controlla email e password. Se corrette, restituisce l'hash salvato nel DB."""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email non trovata.")

    if not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password sbagliata.")

    return TokenResponse(access_token=user.password, user_id=user.id, name=user.name)


# ============================================================
# ENDPOINT: GET /auth/me  (PROFILO PERSONALE)
# ============================================================
@router.get("/me", response_model=UserMeResponse)
def get_my_profile(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Restituisce i dati dell'utente loggato (nome, email, bio, ecc.)."""
    user_id = _get_user_id(authorization, db)
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
    user_id = _get_user_id(authorization, db)
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
