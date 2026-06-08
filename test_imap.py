import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER   = os.getenv("IMAP_SERVER")
IMAP_PORT     = int(os.getenv("IMAP_PORT", 993))
IMAP_USER     = os.getenv("IMAP_USER")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")

mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(IMAP_USER, IMAP_PASSWORD)
mail.select("INBOX")

# Chercher TOUS les emails
_, messages = mail.search(None, "ALL")
ids = messages[0].split()
print(f"📬 Total emails dans la boîte : {len(ids)}")

# Afficher les 5 derniers
for uid in ids[-5:]:
    _, msg_data = mail.fetch(uid, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])
    sujet = decode_header(msg.get("Subject", ""))[0][0]
    if isinstance(sujet, bytes):
        sujet