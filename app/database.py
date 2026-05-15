# database.py = COLLEGAMENTO AL DATABASE
# Questo file configura SQLAlchemy per parlare con SQLite.
# Ruolo: dire "come connettersi" e "come creare sessioni".

from sqlalchemy import create_engine
# create_engine: crea la connessione al database (il "ponte" tra Python e il file .db).

from sqlalchemy.orm import sessionmaker, DeclarativeBase
# sessionmaker: fabbrica che crea "sessioni" (le usi per fare query).
# DeclarativeBase: classe base per definire le tabelle del database.


# ============================================================
# URL DEL DATABASE (dove si trova il file .db)
# ============================================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./skillswap.db"
# "sqlite:///./skillswap.db" = il database e' il file "skillswap.db"
# nella cartella del progetto. SQLite salva tutto in un unico file.


# ============================================================
# ENGINE (gestisce la connessione fisica al database)
# ============================================================
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,                    # URL del database
    connect_args={"check_same_thread": False},  # SQLite blocca l'accesso da thread
)                                               # diversi. Noi lo disabilitiamo perche'
                                                # FastAPI usa thread multipli.


# ============================================================
# SESSIONLOCAL (fabbrica di sessioni)
# ============================================================
# Ogni volta che chiami SessionLocal(), crei una nuova sessione.
# La sessione e' come un "blocco note" dove scrivi le operazioni
# da fare sul database. Poi chiami commit() per salvare tutto.
SessionLocal = sessionmaker(
    autocommit=False,   # False = devi chiamare tu manualmente commit()
    autoflush=False,    # False = aspetti tu prima di mandare le query
    bind=engine,        # Collega questa fabbrica al nostro database
)


# ============================================================
# BASE (classe madre per TUTTE le tabelle)
# ============================================================
class Base(DeclarativeBase):
    pass
    # Tutte le tabelle (User, Skill, UserSkill...) ereditano da Base.
    # Base tiene traccia di tutte le tabelle e sa come crearle.


# ============================================================
# GET_DB (la "dependency" di FastAPI per il database)
# ============================================================
# Questa funzione viene chiamata ogni volta che un endpoint ha
# bisogno del database. FastAPI la chiama all'inizio della richiesta
# e chiude la sessione alla fine, anche se c'e' un errore.
def get_db():
    db = SessionLocal()  # Crea una nuova sessione
    try:
        yield db         # Passa la sessione all'endpoint
    finally:
        db.close()       # Alla fine (anche se errore), chiudi la sessione
