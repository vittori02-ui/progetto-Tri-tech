# db_models.py = STRUTTURA DEL DATABASE (le tabelle)
# Qui definiamo COME sono fatte le tabelle del database.
# Ogni classe = una tabella. Ogni attributo = una colonna.
#
# CONFRONTO: db_models.py vs models.py:
#   db_models.py = come sono fatte le tabelle NEL DATABASE
#   models.py    = come sono fatti i dati CHE VIAGGIANO NELLE API

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
)
# Column = una colonna della tabella
# Integer, String, Boolean, Float, DateTime, Text = tipi di dato
# ForeignKey = collegamento tra tabelle ("questa colonna punta a quell'altra tabella")

from sqlalchemy.orm import relationship
# relationship = collegamento "virtuale" tra due tabelle.
# Esempio: user.user_skills mi da TUTTE le skill di un utente

from datetime import datetime, timezone
# datetime = per registrare data e ora

from app.database import Base
# Base = la classe madre (da database.py). Ogni tabella eredita da Base.


# ============================================================
# TABELLA: users  (gli utenti dell'app)
# ============================================================
class User(Base):
    __tablename__ = "users"  # Nome della tabella nel database

    id = Column(Integer, primary_key=True, index=True)       # ID univoco dell'utente (auto-generato)
    name = Column(String, nullable=False)                    # Nome completo
    email = Column(String, unique=True, nullable=False)      # Email (deve essere unica!)
    password = Column(String, nullable=False)                # Password (hashata con bcrypt, mai in chiaro)
    bio = Column(String, default="", nullable=True)          # Biografia personale (es. "Sviluppatore Python")
    location = Column(String, default="", nullable=True)     # Citta' (es. "Milano")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Data di registrazione

    # "Relazioni": non sono colonne vere, ma collegamenti comodi.
    # Esempio: user.user_skills mi da tutte le skill di quell'utente.
    user_skills = relationship("UserSkill", back_populates="user")
    sent_requests = relationship("SessionRequest", foreign_keys="SessionRequest.sender_id", back_populates="sender")
    received_requests = relationship("SessionRequest", foreign_keys="SessionRequest.receiver_id", back_populates="receiver")


# ============================================================
# TABELLA: skills  (catalogo delle competenze)
# ============================================================
class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)       # Nome skill (es. "Python", unico!)
    description = Column(String, default="")                 # Breve descrizione

    user_skills = relationship("UserSkill", back_populates="skill")


# ============================================================
# TABELLA: user_skills  (chi ha quale skill e con che livello)
# ============================================================
# Questa e' una tabella "ponte": collega User e Skill.
# Un utente puo' avere molte skill, una skill puo' appartenere a molti utenti.
class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)    # ID dell'utente
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)  # ID della skill
    level = Column(String, nullable=False)                               # Principiante | Intermedio | Avanzato
    type = Column(String, nullable=False, default="offered")             # offered (offro) | wanted (cerco)

    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")


# ============================================================
# TABELLA: session_requests  (richieste di sessione tra utenti)
# ============================================================
# Quando Alice vuole imparare Java da Bob, crea una SessionRequest.
class SessionRequest(Base):
    __tablename__ = "session_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)    # Chi ha inviato la richiesta
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Chi riceve la richiesta
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)    # Skill oggetto della sessione

    # Stato della richiesta (solo uno alla volta):
    #   pending   = in attesa di risposta
    #   accepted  = il ricevente ha accettato
    #   rejected  = il ricevente ha rifiutato
    #   completed = entrambi hanno confermato il completamento
    #   cancelled = il mittente ha annullato
    status = Column(String, nullable=False, default="pending")

    message = Column(Text, default="", nullable=True)                     # Messaggio opzionale
    proposed_date = Column(DateTime, nullable=True)                       # Data proposta per la sessione
    mode = Column(String, default="remoto")                               # "in_presenza" o "remoto"

    # Doppia conferma: entrambi devono dire "sì, la sessione e' finita"
    sender_confirmed = Column(Boolean, default=False)     # Mittente ha confermato?
    receiver_confirmed = Column(Boolean, default=False)   # Ricevente ha confermato?

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_requests")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_requests")
    skill = relationship("Skill")


# ============================================================
# TABELLA: feedback  (valutazioni dopo la sessione)
# ============================================================
# Dopo che una sessione e' completata, i partecipanti lasciano un feedback.
class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    session_request_id = Column(Integer, ForeignKey("session_requests.id"), unique=True, nullable=False)  # Solo UN feedback per sessione
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)   # Chi lascia il feedback
    rating = Column(Float, nullable=False)                                  # Voto da 1.0 a 5.0
    comment = Column(Text, default="", nullable=True)                       # Commento opzionale
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session_request = relationship("SessionRequest")
    reviewer = relationship("User")
