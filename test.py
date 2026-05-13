#print("hello word")
from app.database import SessionLocal
from app.db_models import Skill

db=SessionLocal()
nuova_skill=Skill(name="Test",description="Test funzionamento") #inserisci dati finti, si chiama hardcoded
"""
verifica che il db funziona con:
sqlAlchemy si connette al db
la tabella skill esiste?
si puo inserire una riga?
riesco a leggere?

in futuro 
utente compila il form
il frontend manda i dati all'API
API li manda al db
"""
db.add(nuova_skill)
db.commit()
skill=db.query(Skill).all()
for s in skill:
    print(f"ID: {s.id} | Nome: {s.name} | Descrizione: {s.description}")

db.close()
