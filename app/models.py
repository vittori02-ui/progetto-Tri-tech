# models.py = SCHEMI DEI DATI CHE ENTRANO ED ESCONO DALLE API
# Pydantic serve a validare i dati: se il frontend manda dati sbagliati
# (es. "email senza @"), Pydantic blocca tutto con un errore 422.
#
# CONFRONTO: models.py vs db_models.py:
#   db_models.py = le tabelle nel database
#   models.py    = come devono essere i dati che arrivano/partono dalle API

from pydantic import BaseModel, ConfigDict, field_validator
# BaseModel = classe base per creare schemi di dati
# ConfigDict = configurazione (es. from_attributes=True per leggere da SQLAlchemy)
# field_validator = funzione che controlla se un campo e' valido

from typing import Optional  # Optional[str] = str | None (il campo puo' mancare)
from datetime import datetime  # Per le date


# ============================================================
# MODELLI GENERICI (stato, health check)
# ============================================================
class StatusResponse(BaseModel):
    status: str    # "ok" o "error"
    message: str   # Messaggio di testo


# ============================================================
# MODELLI PER LE SKILL (catalogo globale)
# ============================================================
class SkillResponse(BaseModel):
    """Risposta: una skill del catalogo."""
    id: int                          # ID della skill
    name: str                        # Nome (es. "Python")
    description: str | None = "Inserisci qualcosa"  # Descrizione
    model_config = ConfigDict(from_attributes=True)  # Permette di crearlo da un oggetto SQLAlchemy


class SkillCreate(BaseModel):
    """Richiesta: creare una nuova skill."""
    name: str                        # Nome obbligatorio
    description: Optional[str] = ""  # Descrizione opzionale


# ============================================================
# MODELLI PER UserSkill (skill associate a un utente)
# ============================================================
class UserSkillResponse(BaseModel):
    """Risposta: una skill associata a un utente."""
    id: int
    skill_id: int
    skill_name: str                  # Nome della skill (es. "Python")
    level: str                       # Principiante | Intermedio | Avanzato
    user_id: int
    type: str = "offered"            # offered (offro) | wanted (cerco)
    model_config = ConfigDict(from_attributes=True)


class UserSkillCreate(BaseModel):
    """Richiesta: aggiungere/aggiornare una skill per l'utente."""
    skill_name: str                  # Nome della skill
    level: str                       # Livello scelto
    type: str = "offered"            # offered o wanted

    @field_validator("level")
    @classmethod
    def validate_level(cls, v):
        """Controlla che il livello sia tra quelli permessi."""
        if v not in {"Principiante", "Intermedio", "Avanzato"}:
            raise ValueError(f"'{v}' non e' valido. Scegli: Principiante, Intermedio, Avanzato")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        """Controlla che il tipo sia offered o wanted."""
        if v not in {"offered", "wanted"}:
            raise ValueError("Il tipo deve essere 'offered' o 'wanted'")
        return v


# ============================================================
# MODELLI PER L'AUTENTICAZIONE (registrazione, login, token)
# ============================================================
class UserRegister(BaseModel):
    """Richiesta: registrare un nuovo utente."""
    name: str
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        """Controllo base: l'email deve avere @ e un dominio valido."""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Inserisci un'email valida (es. nome@dominio.com)")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Almeno 6 caratteri per sicurezza."""
        if len(v) < 6:
            raise ValueError("La password deve avere almeno 6 caratteri")
        return v


class UserLogin(BaseModel):
    """Richiesta: login di un utente esistente."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Risposta: token JWT dopo login/registrazione."""
    access_token: str                # Il token da salvare nel localStorage
    token_type: str = "bearer"       # Tipo di token (standard: "bearer")
    user_id: int                     # ID dell'utente
    name: str                        # Nome dell'utente


class UserMeResponse(BaseModel):
    """Risposta: profilo PRIVATO dell'utente (include email)."""
    id: int
    name: str
    email: str                       # Solo qui si vede l'email!
    bio: Optional[str] = ""
    location: Optional[str] = ""
    model_config = ConfigDict(from_attributes=True)


class UserPublicResponse(BaseModel):
    """Risposta: profilo PUBBLICO di un altro utente (NO email per privacy)."""
    id: int
    name: str
    bio: Optional[str] = ""
    location: Optional[str] = ""
    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Richiesta: aggiornare il profilo. Solo i campi inviati vengono modificati."""
    bio: Optional[str] = None
    location: Optional[str] = None
    name: Optional[str] = None


# ============================================================
# MODELLI PER LA RICERCA
# ============================================================
class UserSearchResponse(BaseModel):
    """Risultato della ricerca utenti."""
    id: int
    name: str
    bio: Optional[str] = ""
    location: Optional[str] = ""
    offered_skills: list[UserSkillResponse] = []  # Skill che l'utente offre
    wanted_skills: list[UserSkillResponse] = []   # Skill che l'utente cerca
    is_match: bool = False  # True = c'e' match reciproco (io offro quello che tu cerchi E viceversa)
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MODELLI PER LE RICHIESTE DI SESSIONE
# ============================================================
class SessionRequestCreate(BaseModel):
    """Richiesta: inviare una richiesta di sessione a un altro utente."""
    receiver_id: int              # ID del destinatario
    skill_id: int                 # Skill su cui fare la sessione
    message: Optional[str] = ""   # Messaggio opzionale
    proposed_date: Optional[datetime] = None  # Data proposta
    mode: str = "remoto"          # "in_presenza" o "remoto"

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        if v not in {"in_presenza", "remoto"}:
            raise ValueError("Scegli 'in_presenza' o 'remoto'")
        return v


class SessionRequestResponse(BaseModel):
    """Risposta: dati di una richiesta di sessione."""
    id: int
    sender_id: int
    sender_name: str = ""                # Nome del mittente (popolato dal router)
    receiver_id: int
    receiver_name: str = ""              # Nome del destinatario
    skill_id: int
    skill_name: str = ""                 # Nome della skill
    status: str                          # pending | accepted | rejected | completed | cancelled
    message: Optional[str] = ""
    proposed_date: Optional[datetime] = None
    mode: str = "remoto"
    sender_confirmed: bool = False       # Mittente ha confermato completamento?
    receiver_confirmed: bool = False     # Destinatario ha confermato?
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class SessionRequestAction(BaseModel):
    """Richiesta: eseguire un'azione su una richiesta."""
    action: str  # accept | reject | cancel | confirm_completion

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v not in {"accept", "reject", "cancel", "confirm_completion"}:
            raise ValueError("Azione non valida. Usa: accept, reject, cancel, confirm_completion")
        return v


# ============================================================
# MODELLI PER IL FEEDBACK
# ============================================================
class FeedbackCreate(BaseModel):
    """Richiesta: lasciare un feedback dopo una sessione."""
    session_request_id: int   # ID della sessione completata
    rating: float             # Voto da 1.0 a 5.0
    comment: Optional[str] = ""

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if v < 1.0 or v > 5.0:
            raise ValueError("Il rating deve essere tra 1.0 e 5.0")
        return v


class FeedbackResponse(BaseModel):
    """Risposta: dati di un feedback."""
    id: int
    session_request_id: int
    reviewer_id: int
    reviewer_name: str = ""      # Nome di chi ha lasciato il feedback
    rating: float
    comment: Optional[str] = ""
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# MODELLI PER LA DASHBOARD (statistiche globali)
# ============================================================
class DashboardStats(BaseModel):
    """Statistiche globali dell'app."""
    total_users: int    # Quanti utenti registrati
    total_skills: int   # Quante skill nel catalogo
    total_matches: int  # Quante associazioni utente-skill
