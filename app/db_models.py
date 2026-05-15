from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base  # engine NON serve più qui (create_all spostato in main.py)


# ============================================================
# Modelli SQLAlchemy (tabelle del database)
# ============================================================

class User(Base):
    """
    Tabella 'users': memorizza i dati degli utenti registrati.
    Corrisponde al modello Pydantic UserMeResponse / UserPublicResponse.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    date =Column(DateTime, default=datetime.now) #crea una colonna per la data e l'ora se non viene passato nulla la mette in automatico
    user_skills = relationship("UserSkill", back_populates="user")
    sent_requests=relationship("SessionRequest",foreign_keys="SessionRequest.sender_id",back_populates="sender")
    received_requests = relationship("SessionRequest", foreign_keys="SessionRequest.receiver_id", back_populates="receiver")

    password = Column(String, nullable=False)  # Hash della password
    bio = Column(String, default="", nullable=True)  # Biografia utente
    location = Column(String, default="", nullable=True)  # Località utente

    # 👇 RINOMINATO: prima si chiamava "date", ma è un nome ambiguo
    # (sembra il tipo "data" generico). "created_at" è lo standard nel 99% dei progetti.
    # 👇 timezone.utc: registra l'istante in UTC, così non importa
    # che fuso orario abbia il server — i dati sono sempre consistenti.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Skill(Base):
    """
    Tabella 'skills': catalogo globale delle skill disponibili.
    name è unico per evitare duplicati.
    Corrisponde al modello Pydantic SkillResponse.
    """
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Nome univoco della skill
    description = Column(String, default="")

    # Relazione: una skill può essere associata a molti utenti
    user_skills = relationship("UserSkill", back_populates="skill")


class UserSkill(Base):
    """
    Tabella 'user_skills': relazione N:N tra utenti e skill.
    Ogni record collega un utente a una skill con un livello.
    """
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    level = Column(String, nullable=False)
    type=Column(String,nullable=False)
    level = Column(String, nullable=False)  # Principiante | Intermedio | Avanzato

    # Relazioni bidirezionali
    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")

class SessionRequest(Base):
    __tablename__ = "session_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    status = Column(String, default="pending")  # Può essere: pending, accepted, rejected
    #message = Column(String, default="")
    date=Column(DateTime,default=datetime.now)
    sender=relationship("User",foreign_keys=[sender_id],back_populates="sent_requests")
    receiver=relationship("User",foreign_keys=[receiver_id],back_populates="received_requests")

Base.metadata.create_all(bind=engine)
    

#repository anche quelle cose che comunicano con il database
# ⚠️ NOTA: create_all() NON è più qui!
# Prima stava a livello di modulo (veniva eseguito all'import).
# Ora è nello "startup" del lifespan in main.py.
# Motivo: con l'auto-reload di FastAPI (--reload) il modulo veniva
# re-importato continuamente, causando potenziali race condition.
# Inoltre è più pulito: la creazione delle tabelle è un'operazione
# di avvio, non un effetto collaterale di un import.

