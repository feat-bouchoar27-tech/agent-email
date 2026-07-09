"""
Bot Telegram interactif pour l'agent email Famasser.
Tourne en parallele de agent.py (processus separe), en mode "polling" :
interroge regulierement l'API Telegram pour voir si de nouveaux messages/
commandes sont arrives, et y repond.

Commandes disponibles :
    /urgences  -> liste les emails urgence haute non traites
    /stats     -> statistiques du jour (emails traites, tokens consommes)
    /aide      -> rappel des commandes disponibles

Lancement : python telegram_bot.py
"""

import os
import time
import requests
from dotenv import load_dotenv
from database import get_tous_emails, get_tokens_today

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def envoyer_message(texte: str, chat_id: str = None):
    """Envoie un message texte au chat donne (ou au chat par defaut du .env)."""
    cible = chat_id or TELEGRAM_CHAT_ID
    try:
        requests.post(f"{API_URL}/sendMessage", data={"chat_id": cible, "text": texte}, timeout=10)
    except Exception as e:
        print(f"⚠️  Erreur envoi message : {e}")


def commande_urgences(chat_id: str):
    """Liste les emails d'urgence haute non traites."""
    emails = get_tous_emails()
    urgents = [e for e in emails if e.get("urgence") == "haute" and not e.get("traite")]

    if not urgents:
        envoyer_message("✅ Aucune urgence haute en attente.", chat_id)
        return

    lignes = [f"🔴 {len(urgents)} urgence(s) haute(s) en attente :\n"]
    for e in urgents[:10]:  # limite a 10 pour ne pas depasser la taille max d'un message Telegram
        lignes.append(f"• {e['sujet'][:60]}\n  De : {e['expediteur'][:50]}\n  {e.get('raison_urgence','')}")
    if len(urgents) > 10:
        lignes.append(f"\n... et {len(urgents) - 10} de plus.")

    envoyer_message("\n\n".join(lignes), chat_id)


def commande_stats(chat_id: str):
    """Statistiques du jour : emails traites/non traites, tokens consommes."""
    emails = get_tous_emails()
    total = len(emails)
    traites = len([e for e in emails if e.get("traite")])
    urgences_hautes = len([e for e in emails if e.get("urgence") == "haute"])

    try:
        tokens = get_tokens_today()
        texte_tokens = f"{tokens['total']} tokens utilises aujourd'hui"
    except Exception:
        texte_tokens = "Tokens : indisponible"

    message = (
        f"📊 Statistiques\n\n"
        f"Total emails : {total}\n"
        f"Traites : {traites}\n"
        f"Non traites : {total - traites}\n"
        f"Urgences hautes (total) : {urgences_hautes}\n"
        f"{texte_tokens}"
    )
    envoyer_message(message, chat_id)


def commande_aide(chat_id: str):
    envoyer_message(
        "🤖 Commandes disponibles :\n\n"
        "/urgences - emails urgents non traites\n"
        "/stats - statistiques du jour\n"
        "/aide - affiche ce message",
        chat_id
    )


COMMANDES = {
    "/urgences": commande_urgences,
    "/stats": commande_stats,
    "/aide": commande_aide,
    "/start": commande_aide,
}


def ecouter_commandes():
    """Boucle de polling : interroge Telegram toutes les 3 secondes pour
    voir s'il y a de nouveaux messages, et y repond si c'est une commande connue."""
    print("🤖 Bot Telegram démarré, en écoute des commandes...")
    print("   Commandes : /urgences /stats /aide\n")

    dernier_update_id = None

    while True:
        try:
            params = {"timeout": 20}
            if dernier_update_id is not None:
                params["offset"] = dernier_update_id + 1

            reponse = requests.get(f"{API_URL}/getUpdates", params=params, timeout=25)
            data = reponse.json()

            if not data.get("ok"):
                print(f"⚠️  Erreur API Telegram : {data}")
                time.sleep(5)
                continue

            for update in data.get("result", []):
                dernier_update_id = update["update_id"]
                message = update.get("message", {})
                texte = message.get("text", "").strip()
                chat_id = str(message.get("chat", {}).get("id", ""))

                if not texte or not chat_id:
                    continue

                commande = texte.split()[0].lower()
                if commande in COMMANDES:
                    print(f"📩 Commande reçue : {commande} (chat {chat_id})")
                    COMMANDES[commande](chat_id)
                else:
                    envoyer_message("Commande inconnue. Tape /aide pour voir les commandes disponibles.", chat_id)

        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            print(f"⚠️  Erreur dans la boucle d'écoute : {e}")
            time.sleep(5)


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquant dans le .env")
    else:
        ecouter_commandes()