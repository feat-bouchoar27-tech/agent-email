from ai_processor import analyser_email
from database import init_db, email_existe, sauvegarder_email
from outlook_connector import get_emails_non_lus, marquer_lu
from datetime import datetime
import time

def traiter_emails():
    print("🚀 Démarrage agent (mode réel)...\n")
    init_db()

    emails = get_emails_non_lus(top=10)

    if not emails:
        print("📭 Aucun email trouvé.")
        return

    for email in emails:
        message_id = email["id"]

        if email_existe(message_id):
            print(f"⏭️  Déjà traité : {email['sujet']}")
            continue

        sujet      = email.get("sujet", "(Sans sujet)")
        expediteur = email.get("expediteur", "")
        corps      = email.get("corps", "")
        date       = email.get("date", "")

        print(f"📧 Traitement : {sujet}")
        print(f"   De : {expediteur}")

        try:
            analyse = analyser_email(sujet, corps, expediteur)
        except Exception as e:
            print(f"   ❌ Erreur analyse : {e}")
            continue

        emoji = "🔴" if analyse.get("urgence") == "haute" else "🟡" if analyse.get("urgence") == "moyenne" else "🟢"
        print(f"   📁 Catégorie : {analyse.get('categorie')}")
        print(f"   {emoji} Urgence   : {analyse.get('urgence')}")
        print(f"   💡 Action    : {analyse.get('type_action')}")

        try:
            date_reception = datetime.strptime(
                date[:31].strip(), "%a, %d %b %Y %H:%M:%S %z"
            ) if date else datetime.now()
        except:
            date_reception = datetime.now()

        sauvegarder_email({
            "message_id"      : message_id,
            "expediteur"      : expediteur,
            "sujet"           : sujet,
            "corps"           : corps,
            "date_reception"  : date_reception,
            "resume"          : analyse.get("resume", ""),
            "categorie"       : analyse.get("categorie", "autre"),
            "urgence"         : analyse.get("urgence", "faible"),
            "type_action"     : analyse.get("type_action", "autre"),
            "reponse_proposee": analyse.get("reponse_proposee", "")
        })

        print(f"   ✅ Sauvegardé !\n")
        time.sleep(1)

    print("✅ Traitement terminé !")

if __name__ == "__main__":
    traiter_emails()