 import psycopg2
from config import DATABASE_URL

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def sauvegarder_email(email: dict, analyse: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO emails
        (outlook_id, sujet, expediteur_email, date_reception,
         corps_brut, resume_ia, categorie, score_urgence, reponse_proposee)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (outlook_id) DO NOTHING''',
        (email['id'], email['sujet'], email['expediteur'],
         email['date'], email['corps'], analyse['resume'],
         analyse['categorie'], analyse['urgence'],
         analyse['reponse_proposee']))
    conn.commit()
    conn.close()

def get_emails_dashboard():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT sujet, expediteur_email, categorie, 
               score_urgence, resume_ia, reponse_proposee
        FROM emails
        ORDER BY date_reception DESC
    ''')
    emails = cur.fetchall()
    conn.close()
    return emails
