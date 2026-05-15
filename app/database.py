from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Stringa di connessione al database SQLite
# "./skillswap.db" indica che il file si trova nella directory corrente
# SQLite è un database leggero che salva tutto in un singolo file
SQLALCHEMY_DATABASE_URL = "sqlite:///./skillswap.db"

# Crea l'engine che gestisce la connessione al database
# connect_args={"check_same_thread": False} è necessario per SQLite con FastAPI
# poiché più richieste potrebbero accedere al database contemporaneamente
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SessionLocal è una fabbrica di sessioni
# Ogni volta che chiamiamo SessionLocal(), otteniamo una nuova sessione di database
# autocommit=False: dobbiamo chiamare explícitamente commit() per salvare le modifiche
# autoflush=False: controlliamo manualmente quando fare il flush delle modifiche
# bind=engine: associa questa session factory all'engine creato sopra
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base è la classe base per tutti i nostri modelli SQLAlchemy
# DeclarativeBase è la versione moderna di SQLAlchemy per definire i modelli
# Tutte le classi che ereditano da Base diventano tabelle nel database
class Base(DeclarativeBase):
    pass


def get_db():
    """
    Dependency che fornisce una sessione di database per ogni richiesta HTTP.
    Questa funzione viene utilizzata da FastAPI con Depends() per:
    1. Creare una nuova sessione quando inizia la richiesta
    2. Fornire quella sessione alla funzione dell'endpoint
    3. Chiudere automaticamente la sessione quando la richiesta termina
    
    Lo pattern try/finally assicura che la sessione venga sempre chiusa,
    anche se si verifica un'eccezione durante il processing della richiesta.
    """
    db = SessionLocal()
    try:
        yield db  # Fornisce la sessione alla funzione che l'ha richiesta
    finally:
        db.close()  # Assicura che la sessione venga chiusa dopo l'uso
