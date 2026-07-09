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
            created_at      TIMESTAMP DEFAULT NOW(),
            langue          TEXT,
            raison_urgence  TEXT,
            score_similarite FLOAT DEFAULT 0
        )
    """)
    for col, typ in [("langue", "TEXT"), ("raison_urgence", "TEXT"), ("score_similarite", "FLOAT DEFAULT 0")]:
        try:
            cur.execute(f"ALTER TABLE emails ADD COLUMN {col} {typ}")
        except Exception:
            conn.rollback()
            cur = conn.cursor()

    # Table pour le suivi reel de la consommation de tokens Groq (par appel API).
    # Necessaire car agent.py tourne dans un processus separe de api.py :
    # un compteur en memoire dans api.py ne peut jamais etre mis a jour par agent.py.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tokens_usage (
            id                SERIAL PRIMARY KEY,
            jour              DATE DEFAULT CURRENT_DATE,
            prompt_tokens     INT DEFAULT 0,
            completion_tokens INT DEFAULT 0,
            total_tokens      INT DEFAULT 0,
            created_at        TIMESTAMP DEFAULT NOW()
        )
    """)

    # Table pour l'historique des emails reellement envoyes via SMTP (/repondre).
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emails_envoyes (
            id            SERIAL PRIMARY KEY,
            destinataire  TEXT,
            sujet         TEXT,
            corps         TEXT,
            email_id      INT,
            date_envoi    TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Base de données initialisée")

def email_existe(message_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM emails WHERE message_id = %s", (message_id,))
    existe = cur.fetchone() is not None
    cur.close()
    conn.close()
    return existe

def chercher_email_similaire(sujet: str, categorie: str, seuil: float = 0.4) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    mots = [m.lower() for m in sujet.split() if len(m) > 3]
    if not mots:
        cur.close()
        conn.close()
        return None
    cur.execute("""
        SELECT id, sujet, reponse_proposee, urgence, raison_urgence
        FROM emails
        WHERE categorie = %s
          AND reponse_proposee IS NOT NULL
          AND reponse_proposee != ''
          AND traite = TRUE
        ORDER BY date_reception DESC
        LIMIT 20
    """, (categorie,))
    emails = cur.fetchall()
    cur.close()
    conn.close()
    if not emails:
        return None
    meilleur = None
    meilleur_score = 0
    for email in emails:
        sujet_hist = (email[1] or "").lower()
        mots_hist = [m for m in sujet_hist.split() if len(m) > 3]
        communs = set(mots) & set(mots_hist)
        total = max(len(set(mots) | set(mots_hist)), 1)
        score = len(communs) / total
        if score > meilleur_score:
            meilleur_score = score
            meilleur = {
                "id": email[0],
                "sujet": email[1],
                "reponse": email[2],
                "urgence": email[3],
                "raison_urgence": email[4],
                "score": round(score, 2)
            }
    if meilleur and meilleur_score >= seuil:
        return meilleur
    return None

def sauvegarder_email(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO emails 
            (message_id, expediteur, sujet, corps, date_reception,
             resume, categorie, urgence, type_action, reponse_proposee,
             langue, raison_urgence)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        data["reponse_proposee"],
        data.get("langue", "fr"),
        data.get("raison_urgence", "")
    ))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Email sauvegardé : {data['sujet'][:50]}")

def get_tous_emails():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, expediteur, sujet, corps, date_reception,
               resume, categorie, urgence, type_action,
               reponse_proposee, traite, created_at,
               langue, raison_urgence, date_traitement
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

def log_tokens(prompt_tokens: int, completion_tokens: int):
    """Enregistre la consommation de tokens d'un appel Groq.
    Appelé depuis ai_processor.py, dans le processus agent.py."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        total = (prompt_tokens or 0) + (completion_tokens or 0)
        cur.execute("""
            INSERT INTO tokens_usage (jour, prompt_tokens, completion_tokens, total_tokens)
            VALUES (CURRENT_DATE, %s, %s, %s)
        """, (prompt_tokens or 0, completion_tokens or 0, total))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        # On ne bloque jamais le traitement d'un email a cause d'un souci
        # de log des tokens : on affiche juste un avertissement.
        print(f"⚠️  Impossible de logger les tokens : {e}")

def get_tokens_today() -> dict:
    """Retourne la somme des tokens consommes aujourd'hui (jour calendaire serveur)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(prompt_tokens), 0),
               COALESCE(SUM(completion_tokens), 0),
               COALESCE(SUM(total_tokens), 0)
        FROM tokens_usage
        WHERE jour = CURRENT_DATE
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {"prompt": row[0], "completion": row[1], "total": row[2]}

def log_envoi(destinataire: str, sujet: str, corps: str, email_id: int = None):
    """Enregistre un email reellement envoye via SMTP (/repondre)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO emails_envoyes (destinataire, sujet, corps, email_id)
        VALUES (%s, %s, %s, %s)
    """, (destinataire, sujet, corps, email_id))
    conn.commit()
    cur.close()
    conn.close()

def get_envois():
    """Retourne l'historique des emails envoyes (100 derniers), du plus recent au plus ancien."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, destinataire, sujet, corps, date_envoi, email_id
        FROM emails_envoyes
        ORDER BY date_envoi DESC
        LIMIT 100
    """)
    colonnes = [desc[0] for desc in cur.description]
    rows = [dict(zip(colonnes, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("Connexion PostgreSQL OK")
