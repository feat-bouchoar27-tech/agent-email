import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emails (
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
    print("✅ Base de données initialisée")

def email_existe(message_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM emails WHERE message_id = %s", (message_id,))
    existe = cur.fetchone() is not None
    cur.close()
    conn.close()
    return existe

def sauvegarder_email(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO emails 
            (message_id, expediteur, sujet, corps, date_reception,
             resume, categorie, urgence, type_action, reponse_proposee)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (message_id) DO NOTHING
    """, (
        data["message_id"],
        data["expediteur"],
        data["sujet"],
        data["corps"],
        data["date_reception"],
        data["resume"],
        data["categorie"],
        data["urgence"],
        data["type_action"],
        data["reponse_proposee"]
    ))
    conn.commit()
    cur.close()
    conn.close()
    print(f"💾 Email sauvegardé : {data['sujet'][:50]}")

def get_tous_emails():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, expediteur, sujet, date_reception,
               resume, categorie, urgence, type_action,
               reponse_proposee, traite, created_at
        FROM emails
        ORDER BY date_reception DESC
    """)
    colonnes = [desc[0] for desc in cur.description]
    rows = [dict(zip(colonnes, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

def marquer_traite(email_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE emails 
        SET traite = TRUE, date_traitement = %s 
        WHERE id = %s
    """, (datetime.now(), email_id))
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Connexion PostgreSQL OK")