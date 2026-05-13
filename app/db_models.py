from sqlalchemy import Column, Integer, String, ForeignKey,  DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base, engine


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    date =Column(DateTime, default=datetime.now) #crea una colonna per la data e l'ora se non viene passato nulla la mette in automatico
    user_skills = relationship("UserSkill", back_populates="user")
    sent_requests=relationship("SessionRequest",foreign_keys="SessionRequest.sender_id",back_populates="sender")
    eceived_requests = relationship("SessionRequest", foreign_keys="SessionRequest.receiver_id", back_populates="sender")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String,nullable=False)
    description = Column(String, default="")
    user_skills = relationship("UserSkill", back_populates="skill")


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    level = Column(String, nullable=False)
    type=Column(String,nullable=False)
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
    sender=relationship("User",foreign_keys=[sender_id],back_populates="sender")
    receiver=relationship("User",foreign_keys=[receiver_id],back_populates="receiver")

Base.metadata.create_all(bind=engine)
