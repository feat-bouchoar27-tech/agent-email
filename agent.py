from ai_processor import analyser_email
from database import init_db, email_existe, sauvegarder_email
from datetime import datetime
import time

def traiter_emails_reels(token=None):
    """Mode réel avec Outlook"""
    print("🚀 Démarrage agent (mode réel)...\n")
    init_db()

    from outlook_connector import get_emails_non_lus, marquer_lu
    emails = get_emails_non_lus(token, top=10)

    if not emails:
        print("📭 Aucun email non lu trouvé.")
        return

    for email in emails:
        message_id = email["id"]

        if email_existe(message_id):
            print(f"⏭️  Déjà traité : {email['subject']}")
            continue

        sujet      = email.get("subject", "(Sans sujet)")
        expediteur = email["from"]["emailAddress"]["address"]
        corps      = email.get("body", {}).get("content", "")[:2000]
        date_str   = email.get("receivedDateTime", "")

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
            date_reception = datetime.fromisoformat(
                date_str.replace("Z", "+00:00")
            ) if date_str else datetime.now()
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

        marquer_lu(token, message_id)
        print(f"   ✅ Sauvegardé !\n")
        time.sleep(1)

    print("✅ Traitement terminé !")

def traiter_emails_demo():
    """Mode démo sans Outlook"""
    print("🚀 Démarrage agent (mode démo)...\n")
    init_db()

    emails_test = [
        {
            "id": "demo-001",
            "sujet": "Relance facture impayée #2024-089",
            "expediteur": "ahmed.client@gmail.com",
            "corps": "Bonjour, je relance pour ma facture de 4500 EUR toujours impayée.",
            "date": "2024-01-15T10:30:00"
        },
        {
            "id": "demo-002",
            "sujet": "Congé annuel - Demande validation",
            "expediteur": "sara.rh@famasser.ma",
            "corps": "Bonjour, je souhaite poser mes congés du 20 au 30 janvier.",
            "date": "2024-01-15T11:00:00"
        },
        {
            "id": "demo-003",
            "sujet": "Nouveau contrat fournisseur informatique",
            "expediteur": "commercial@fournisseur.ma",
            "corps": "Veuillez trouver ci-joint notre nouvelle offre de contrat.",
            "date": "2024-01-15T09:00:00"
        },
        {
            "id": "demo-004",
            "sujet": "URGENT - Facture 15000 EUR menace juridique",
            "expediteur": "avocat@cabinet.ma",
            "corps": "Sans paiement sous 24h nous engageons une procédure juridique.",
            "date": "2024-01-15T08:00:00"
        }
    ]

    for email in emails_test:
        if email_existe(email["id"]):
            print(f"⏭️  Déjà traité : {email['sujet']}")
            continue

        print(f"📧 Traitement : {email['sujet']}")
        analyse = analyser_email(email["sujet"], email["corps"], email["expediteur"])

        emoji = "🔴" if analyse.get("urgence") == "haute" else "🟡" if analyse.get("urgence") == "moyenne" else "🟢"
        print(f"   📁 Catégorie : {analyse.get('categorie')}")
        print(f"   {emoji} Urgence   : {analyse.get('urgence')}")
        print(f"   💡 Action    : {analyse.get('type_action')}")

        sauvegarder_email({
            "message_id"      : email["id"],
            "expediteur"      : email["expediteur"],
            "sujet"           : email["sujet"],
            "corps"           : email["corps"],
            "date_reception"  : datetime.fromisoformat(email["date"]),
            "resume"          : analyse.get("resume", ""),
            "categorie"       : analyse.get("categorie", "autre"),
            "urgence"         : analyse.get("urgence", "faible"),
            "type_action"     : analyse.get("type_action", "autre"),
            "reponse_proposee": analyse.get("reponse_proposee", "")
        })
        print(f"   ✅ Sauvegardé !\n")
        time.sleep(1)

    print("✅ Pipeline complet fonctionnel !")

if __name__ == "__main__":
    # Mode démo par défaut — changera en mode réel après Azure
    traiter_emails_demo()