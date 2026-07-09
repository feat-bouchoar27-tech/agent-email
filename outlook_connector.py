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

def connecter():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(IMAP_USER, IMAP_PASSWORD)
    return mail

def decoder_header(valeur):
    if not valeur:
        return ""
    parties = decode_header(valeur)
    resultat = ""
    for partie, encodage in parties:
        if isinstance(partie, bytes):
            resultat += partie.decode(encodage or "utf-8", errors="ignore")
        else:
            resultat += partie
    return resultat

def get_emails_non_lus(top=10):
    mail = connecter()
    mail.select("INBOX")

    # Chercher tous les emails
    _, messages = mail.search(None, "ALL")
    ids = messages[0].split()

    if not ids:
        print("📭 Aucun email trouvé")
        mail.logout()
        return []

    # Prendre les derniers
    ids = ids[-top:]
    emails = []

    for uid in reversed(ids):
        _, msg_data = mail.fetch(uid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        sujet      = decoder_header(msg.get("Subject", ""))
        expediteur = decoder_header(msg.get("From", ""))
        date       = msg.get("Date", "")

        # Identifiant STABLE de l'email : le vrai Message-ID (header RFC 822),
        # jamais le numero de sequence IMAP qui peut changer/se decaler.
        message_id_reel = msg.get("Message-ID", "").strip()
        if not message_id_reel:
            # Filet de securite si un email n'a pas de Message-ID (rare) :
            # on combine expediteur+sujet+date pour rester stable dans le temps,
            # au lieu du numero de sequence IMAP qui n'est pas fiable.
            message_id_reel = f"fallback:{expediteur}:{sujet}:{date}"

        # Extraire le corps
        corps = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    corps = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            corps = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

        emails.append({
            "id"         : message_id_reel,
            "uid_imap"   : uid.decode(),  # gardé si besoin pour marquer_lu()
            "sujet"      : sujet,
            "expediteur" : expediteur,
            "corps"      : corps[:2000],
            "date"       : date
        })

    mail.logout()
    print(f"📬 {len(emails)} email(s) trouvé(s)")
    return emails

def marquer_lu(uid):
    mail = connecter()
    mail.select("INBOX")
    mail.store(uid, "+FLAGS", "\\Seen")
    mail.logout()

if __name__ == "__main__":
    emails = get_emails_non_lus()
    for e in emails:
        print(f"\n📧 Sujet : {e['sujet']}")
        print(f"   ID (Message-ID) : {e['id']}")
        print(f"   De    : {e['expediteur']}")
        print(f"   Date  : {e['date']}")
        print(f"   Corps : {e['corps'][:100]}...")