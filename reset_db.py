from database import get_connection

conn = get_connection()
cur = conn.cursor()

# Supprimer l'ancienne table
cur.execute("DROP TABLE IF EXISTS emails;")

# Recréer avec la bonne structure
cur.execute("""
    CREATE TABLE emails (
        id              SERIAL PRIMARY KEY,
        message_id      TEXT UNIQUE,
        expediteur      TEXT,
        sujet           TEXT,
        corps           TEXT,
        date_reception  TIMESTAMP,
        resume          TEXT,
        categorie       TEXT,
        urgence         TEXT,
        type_action     TEXT,
        reponse_proposee TEXT,
        traite          BOOLEAN DEFAULT FALSE,
        date_traitement TIMESTAMP,
        created_at      TIMESTAMP DEFAULT NOW()
    )
""")

conn.commit()
cur.close()
conn.close()
print("✅ Table emails recréée proprement !")