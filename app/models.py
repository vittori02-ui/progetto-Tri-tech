from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional

# ============================================================
# Modelli Pydantic (struttura dati per request/response API)
# ============================================================

# --- Modelli di stato generici ---
class StatusResponse(BaseModel):
    """Modello per risposta di stato generica (es. health check)."""
    status: str
    message: str


# --- Modelli per le Skill ---
class SkillResponse(BaseModel):
    """
    Modello per restituire una skill al frontend.
    Il campo 'name' corrisponde a db_models.Skill.name
    """
    id: int
    name: str  # Corrisponde a 'name' nel db_models.Skill
    description: str | None = "Inserisci qualcosa"
    model_config = ConfigDict(from_attributes=True)  # Dati da SQLAlchemy, non da dict


class SkillCreate(BaseModel):
    """Modello per creare una nuova skill."""
    name: str
<<<<<<< Updated upstream
    description: str|None="Inserisci qualcosa"
    model_config = ConfigDict(from_attributes=True) #riga importante dice a pydantic
                                                    #dice questi dati non vengono  da un dizionario
                                                    #ma da sqlAlchemy se non da errore
                                                    #fare una cartella dove ci sono i controller per far vedere i get al frontend

class UserCreate(BaseModel):
=======
    description: Optional[str] = ""


# --- Modelli per UserSkill (relazione utente-skill) ---
class UserSkillResponse(BaseModel):
    """
    Modello per restituire una skill associata a un utente.
    Contiene i dati della skill + il livello.
    """
    id: int
    skill_id: int
    skill_name: str  # Nome della skill (popolato dalla relazione)
    level: str  # Principiante, Intermedio, Avanzato
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class UserSkillCreate(BaseModel):
    """
    Modello per associare una skill a un utente (POST/PUT).

    ⚠️ NOTA: level viene validato automaticamente da `validate_level()` sotto.
    Se mandi "pro" invece di "Principiante" ottieni un errore 422 chiaro.
    """
    skill_name: str  # Nome della skill (se non esiste, viene creata)
    level: str  # Principiante | Intermedio | Avanzato

    # 👇 Validatore automatico: Pydantic lo chiama DOPO aver creato l'oggetto
    # Se il valore non è tra quelli permessi, restituisce errore 422
    @field_validator("level")
    @classmethod
    def validate_level(cls, v):
        """
        Controlla che level sia uno dei 3 valori permessi.
        Se non lo è, Pydantic restituisce automaticamente errore 422
        senza che noi dobbiamo scrivere codice nell'endpoint.
        """
        allowed = {"Principiante", "Intermedio", "Avanzato"}
        if v not in allowed:
            raise ValueError(
                f"'{v}' non è un livello valido. Usa uno di: {', '.join(sorted(allowed))}"
            )
        return v


# --- Modelli per l'Autenticazione ---
class UserRegister(BaseModel):
    """Modello per la registrazione di un nuovo utente."""
>>>>>>> Stashed changes
    name: str
    email: str
    password: str

<<<<<<< Updated upstream
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: str

class UserSkillCreate(BaseModel):
    user_id: int
    skill_id: int
    level: str # Es: "Principiante", "Intermedio", "Avanzato"
    type: str

class SessionRequestCreate(BaseModel):
    sender_id: int
    receiver_id: int
    skill_id: int
    message: str | None = None

class SessionRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender_id: int
    receiver_id: int
    skill_id: int
    status: str
    message: str

class SkillCreate(BaseModel):
    name: str
    description: str | None = None
=======
    # 👇 Validatori base per evitare dati assurdi
    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        """Controllo base: l'email deve contenere @ (es. pinco@pallo.it)."""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Inserisci un'email valida (es. nome@dominio.com)")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Almeno 6 caratteri — non è super sicuro ma evita errori banali."""
        if len(v) < 6:
            raise ValueError("La password deve avere almeno 6 caratteri")
        return v


class UserLogin(BaseModel):
    """Modello per il login di un utente esistente."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Modello che restituisce il token JWT dopo login/registrazione."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str


class UserMeResponse(BaseModel):
    """Modello per la risposta dell'endpoint /auth/me (profilo corrente)."""
    id: int
    name: str
    email: str
    bio: Optional[str] = ""
    location: Optional[str] = ""
    model_config = ConfigDict(from_attributes=True)


class UserPublicResponse(BaseModel):
    """
    Modello per il profilo PUBBLICO di un utente.

    🔐 NOTA: NON include email! Un utente malintenzionato potrebbe
    usare l'email per spam o phishing. Il profilo pubblico mostra
    solo nome, bio e città — roba che l'utente ha scelto di condividere.
    L'email la vede solo l'utente stesso tramite /auth/me (protetto da login).
    """
    id: int
    name: str
    bio: Optional[str] = ""
    location: Optional[str] = ""
    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Modello per aggiornare il profilo utente (bio, location, name)."""
    bio: Optional[str] = None
    location: Optional[str] = None
    name: Optional[str] = None


# --- Modelli per la Ricerca ---
class UserSearchResponse(BaseModel):
    """
    Modello per i risultati della ricerca utenti.

    🔐 NOTA: stesso discorso di UserPublicResponse — niente email.
    La ricerca è pubblica (non serve login), quindi l'email non deve uscire.
    """
    id: int
    name: str
    bio: Optional[str] = ""
    location: Optional[str] = ""
    offered_skills: list[UserSkillResponse] = []
    wanted_skills: list[UserSkillResponse] = []
    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    """Modello per le statistiche della dashboard/home."""
    total_users: int
    total_skills: int
    total_matches: int
>>>>>>> Stashed changes
