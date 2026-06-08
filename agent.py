from ai_processor import analyser_email
from database import init_db, email_existe, sauvegarder_email
from datetime import datetime
import time

def traiter_emails_demo():
    """Mode demo sans Outlook — pour tester le pipeline complet"""
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
        }
    ]

    for email in emails_test:
        if email_existe(email["id"]):
            print(f"⏭️  Déjà traité : {email['sujet']}")
            continue

        print(f"📧 Traitement : {email['sujet']}")

        analyse = analyser_email(email["sujet"], email["corps"], email["expediteur"])

        print(f"   📁 Catégorie : {analyse.get('categorie')}")
        print(f"   🚨 Urgence   : {analyse.get('urgence')}")
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

        print(f"   ✅ Sauvegardé en base !\n")
        time.sleep(1)

    print("✅ Pipeline complet fonctionnel !")

if __name__ == "__main__":
    traiter_emails_demo()