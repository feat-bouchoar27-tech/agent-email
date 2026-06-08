from database import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("ALTER TABLE emails ADD COLUMN IF NOT EXISTS message_id TEXT UNIQUE;")
conn.commit()
cur.close()
conn.close()
print("✅ Colonne message_id ajoutée !")