"""
seed_skills.py — Popola il database con skill preimpostate.
Esegui una volta sola: python seed_skills.py
Se la skill esiste già (nome univoco), la salta.
"""
from app.database import SessionLocal
from app.db_models import Skill

SKILLS = [
    # --- Linguaggi di programmazione ---
    {"name": "Python", "description": "Linguaggio di programmazione versatile, usato per backend, AI e automazione."},
    {"name": "JavaScript", "description": "Linguaggio di scripting lato client, fondamentale per lo sviluppo web."},
    {"name": "TypeScript", "description": "Superset tipizzato di JavaScript, per progetti frontend e backend scalabili."},
    {"name": "Java", "description": "Linguaggio robusto e portabile, punto di riferimento per applicazioni enterprise."},
    {"name": "C#", "description": "Linguaggio Microsoft per applicazioni .NET, videogiochi con Unity e app Windows."},
    {"name": "C++", "description": "Linguaggio ad alte prestazioni per sistemi, motori grafici e software real-time."},
    {"name": "Go", "description": "Linguaggio performante e concorrente creato da Google, ideale per microservizi."},
    {"name": "Rust", "description": "Linguaggio moderno focalizzato su sicurezza e performance, alternativa a C++."},
    {"name": "Kotlin", "description": "Linguaggio moderno per JVM, scelta primaria per sviluppo Android nativo."},
    {"name": "Swift", "description": "Linguaggio Apple per sviluppare app iOS e macOS."},
    {"name": "PHP", "description": "Linguaggio lato server ampiamente usato per CMS come WordPress."},
    {"name": "Ruby", "description": "Linguaggio elegante e produttivo, reso celebre dal framework Ruby on Rails."},

    # --- Framework & Librerie Frontend ---
    {"name": "React", "description": "Libreria JS/TS di Meta per costruire interfacce utente reattive e component-based."},
    {"name": "Angular", "description": "Framework TypeScript completo di Google per single-page application enterprise."},
    {"name": "Vue.js", "description": "Framework progressivo JS, facile da integrare e con curva di apprendimento dolce."},
    {"name": "Next.js", "description": "Framework React con SSR/SSG, routing automatico e ottimizzazioni built-in."},
    {"name": "Svelte", "description": "Framework reattivo che compila a vanilla JS, senza virtual DOM, molto performante."},

    # --- Framework & Librerie Backend ---
    {"name": "Django", "description": "Framework Python completo con ORM, admin panel e sistema di autenticazione."},
    {"name": "FastAPI", "description": "Framework Python moderno e veloce, basato su type hint e standard OpenAPI."},
    {"name": "Flask", "description": "Micro-framework Python semplice e flessibile, ideale per API leggere e microservizi."},
    {"name": "Spring Boot", "description": "Framework Java per creare applicazioni enterprise con convenzioni e auto-configurazione."},
    {"name": "Express.js", "description": "Framework Node.js minimalista e veloce per API REST e backend web."},

    # --- Database ---
    {"name": "SQL", "description": "Linguaggio standard per interrogare e gestire database relazionali."},
    {"name": "PostgreSQL", "description": "RDBMS open-source avanzato, supporta JSON, ricerca full-text e stored procedure."},
    {"name": "MongoDB", "description": "Database NoSQL orientato ai documenti JSON, ideale per dati flessibili e non strutturati."},
    {"name": "MySQL", "description": "RDBMS open-source popolare, usato in stack LAMP e da milioni di piattaforme web."},
    {"name": "SQLite", "description": "RDBMS leggero incorporato, non richiede server: perfetto per app embedded e prototipi."},

    # --- DevOps & Cloud ---
    {"name": "Docker", "description": "Piattaforma di containerizzazione per impacchettare e distribuire applicazioni in modo isolato."},
    {"name": "AWS", "description": "Piattaforma cloud di Amazon con servizi di computing, storage, AI e networking."},
    {"name": "Linux", "description": "Sistema operativo open-source, dominante su server e ambienti di sviluppo backend."},
    {"name": "Git", "description": "Sistema di versionamento distribuito, standard de facto per collaborare sul codice."},
    {"name": "CI/CD", "description": "Pipeline di Continuous Integration e Delivery per automatizzare test e deploy."},

    # --- Data Science & AI ---
    {"name": "Machine Learning", "description": "Tecniche per addestrare modelli predittivi su dati, base dell'AI moderna."},
    {"name": "TensorFlow", "description": "Framework Google per deep learning, con supporto a GPU e modelli distribuiti."},
    {"name": "Pandas", "description": "Libreria Python per manipolazione e analisi dati, fulcro del data science workflow."},

    # --- Altro ---
    {"name": "HTML/CSS", "description": "Fondamenta del web: HTML per strutturare le pagine, CSS per stilizzarle."},
    {"name": "Node.js", "description": "Runtime JS lato server basato sul motore V8, per backend con un solo linguaggio."},
    {"name": "REST API", "description": "Stile architetturale per API web basate su HTTP e risorse standardizzate."},
    {"name": "GraphQL", "description": "Query language per API di Facebook, permette al client di richiedere esattamente i dati necessari."},
]

db = SessionLocal()

added = 0
skipped = 0

for s in SKILLS:
    existing = db.query(Skill).filter(Skill.name == s["name"]).first()
    if existing:
        print(f"  [SKIP] Gia' presente: {s['name']}")
        skipped += 1
    else:
        skill = Skill(name=s["name"], description=s["description"])
        db.add(skill)
        print(f"  [OK] Aggiunta: {s['name']}")
        added += 1

db.commit()

print(f"\n---------------------------------------")
print(f"  [OK] Aggiunte:       {added}")
print(f"  [SKIP] Gia' presenti: {skipped}")
print(f"  Totale catalogo:    {added + skipped} skill")
print(f"---------------------------------------")

db.close()
