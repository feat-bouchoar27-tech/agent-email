from ai_processor import analyser_email
from database import init_db, email_existe, sauvegarder_email
from outlook_connector import get_emails_non_lus, marquer_lu
from datetime import datetime
import time
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()

INTERVALLE = int(os.getenv("INTERVALLE_MINUTES", 5)) * 60

# =================== NOTIFICATION URGENCE (EMAIL) ===================
SMTP_SERVER   = "ssl0.ovh.net"
SMTP_PORT     = 465
SMTP_USER     = os.getenv("IMAP_USER")
SMTP_PASSWORD = os.getenv("IMAP_PASSWORD")

# Email qui recoit les alertes urgences (M. Mohim ou toi)
ALERTE_DESTINATAIRE = os.getenv("ALERTE_EMAIL", SMTP_USER)

# =================== NOTIFICATION URGENCE (TELEGRAM) ===================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

def envoyer_telegram(message: str):
    """Envoie une notification via le bot Telegram. Ne bloque jamais le
    traitement d'un email si l'envoi echoue (reseau, token invalide, etc.)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("   ⚠️  Telegram non configure (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID manquant)")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        reponse = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        if reponse.status_code == 200:
            print("   📲 Notification Telegram envoyée")
        else:
            print(f"   ⚠️  Telegram a répondu avec une erreur : {reponse.status_code} - {reponse.text}")
    except Exception as e:
        print(f"   ⚠️  Impossible d'envoyer la notification Telegram : {e}")

# ============================================================

def envoyer_alerte_urgence(sujet_email, expediteur, resume, raison_urgence, categorie):
    """Envoie un email d'alerte quand une urgence haute est détectée."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = SMTP_USER
        msg["To"]      = ALERTE_DESTINATAIRE
        msg["Subject"] = f"🔴 ALERTE URGENCE — {sujet_email}"

        corps_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
          <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            
            <div style="background: #EF4444; padding: 24px 30px;">
              <h1 style="color: #fff; margin: 0; font-size: 20px;">🔴 Email Urgent Détecté</h1>
              <p style="color: rgba(255,255,255,0.85); margin: 6px 0 0; font-size: 13px;">Agent IA — Famasser / CLEDOR</p>
            </div>

            <div style="padding: 28px 30px;">
              <table style="width: 100%; border-collapse: collapse;">
                <tr>
                  <td style="padding: 10px 0; font-size: 13px; color: #6B7280; width: 130px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Sujet</td>
                  <td style="padding: 10px 0; font-size: 14px; color: #111827; font-weight: 600;">{sujet_email}</td>
                </tr>
                <tr style="border-top: 1px solid #F3F4F6;">
                  <td style="padding: 10px 0; font-size: 13px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Expéditeur</td>
                  <td style="padding: 10px 0; font-size: 14px; color: #111827;">{expediteur}</td>
                </tr>
                <tr style="border-top: 1px solid #F3F4F6;">
                  <td style="padding: 10px 0; font-size: 13px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Catégorie</td>
                  <td style="padding: 10px 0;"><span style="background: #EEF1FE; color: #4F6EF7; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;">{categorie}</span></td>
                </tr>
                <tr style="border-top: 1px solid #F3F4F6;">
                  <td style="padding: 10px 0; font-size: 13px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Urgence</td>
                  <td style="padding: 10px 0;"><span style="background: #FEF2F2; color: #EF4444; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 700;">🔴 HAUTE</span></td>
                </tr>
              </table>

              <div style="margin-top: 20px; background: #FFFBEB; border-left: 4px solid #F59E0B; border-radius: 8px; padding: 14px 16px;">
                <p style="margin: 0 0 6px; font-size: 11px; font-weight: 700; color: #92400E; text-transform: uppercase; letter-spacing: 0.5px;">⚠️ Raison de l'urgence</p>
                <p style="margin: 0; font-size: 13px; color: #111827;">{raison_urgence}</p>
              </div>

              <div style="margin-top: 16px; background: #EEF1FE; border-left: 4px solid #4F6EF7; border-radius: 8px; padding: 14px 16px;">
                <p style="margin: 0 0 6px; font-size: 11px; font-weight: 700; color: #4F6EF7; text-transform: uppercase; letter-spacing: 0.5px;">📋 Résumé IA</p>
                <p style="margin: 0; font-size: 13px; color: #111827; line-height: 1.6;">{resume}</p>
              </div>

              <div style="margin-top: 24px; text-align: center;">
                <p style="font-size: 13px; color: #6B7280; margin: 0;">Connectez-vous au dashboard pour traiter cet email</p>
                <p style="font-size: 12px; color: #9CA3AF; margin: 8px 0 0;">Agent IA — {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>
              </div>
            </div>

          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(corps_html, "html", "utf-8"))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, ALERTE_DESTINATAIRE, msg.as_string())

        print(f"   🔔 Alerte urgence envoyée à {ALERTE_DESTINATAIRE}")
    except Exception as e:
        print(f"   ⚠️  Impossible d'envoyer l'alerte : {e}")

# ============================================================

def traiter_emails():
    print("📬 Vérification des nouveaux emails...\n")
    emails = get_emails_non_lus(top=20)
    if not emails:
        print("📭 Aucun nouvel email.")
        return

    nouveaux = 0
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

        try:
            date_reception = datetime.strptime(
                date[:31].strip(), "%a, %d %b %Y %H:%M:%S %z"
            ) if date else datetime.now()
        except:
            date_reception = datetime.now()

        # Sauvegarder les emails rejetés aussi
        if analyse.get("categorie") == "rejet":
            print(f"   🚫 Email rejeté (spam/système) — sauvegardé\n")
            sauvegarder_email({
                "message_id"      : message_id,
                "expediteur"      : expediteur,
                "sujet"           : sujet,
                "corps"           : corps,
                "date_reception"  : date_reception,
                "resume"          : analyse.get("resume", "Email rejeté automatiquement"),
                "categorie"       : "rejet",
                "urgence"         : "faible",
                "type_action"     : "ignorer",
                "reponse_proposee": "",
                "langue"          : analyse.get("langue", "fr"),
                "raison_urgence"  : "Email rejeté : spam, publicité ou message système",
                "source_reponse"  : "Rejeté"
            })

            try:
                marquer_lu(email["uid_imap"])
            except Exception as e:
                print(f"   ⚠️  Impossible de marquer comme lu : {e}")

            nouveaux += 1
            continue

        emoji = "🔴" if analyse.get("urgence") == "haute" else "🟡" if analyse.get("urgence") == "moyenne" else "🟢"
        print(f"   📁 Catégorie     : {analyse.get('categorie')}")
        print(f"   {emoji} Urgence  : {analyse.get('urgence')} — {analyse.get('raison_urgence','')}")
        print(f"   💡 Action        : {analyse.get('type_action')}")
        print(f"   🌍 Langue        : {analyse.get('langue','fr').upper()}")
        print(f"   📝 Source réponse: {analyse.get('source_reponse','IA')}")

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
            "reponse_proposee": analyse.get("reponse_proposee", ""),
            "langue"          : analyse.get("langue", "fr"),
            "raison_urgence"  : analyse.get("raison_urgence", ""),
            "source_reponse"  : analyse.get("source_reponse", "IA")
        })

        # =================== ALERTE URGENCE HAUTE ===================
        if analyse.get("urgence") == "haute":
            envoyer_alerte_urgence(
                sujet_email    = sujet,
                expediteur     = expediteur,
                resume         = analyse.get("resume", ""),
                raison_urgence = analyse.get("raison_urgence", ""),
                categorie      = analyse.get("categorie", "autre")
            )
            envoyer_telegram(
                f"🔴 URGENCE — {sujet}\n"
                f"De : {expediteur}\n"
                f"Catégorie : {analyse.get('categorie', 'autre')}\n"
                f"Raison : {analyse.get('raison_urgence', '')}"
            )
        # ============================================================

        try:
            marquer_lu(email["uid_imap"])
        except Exception as e:
            print(f"   ⚠️  Impossible de marquer comme lu : {e}")

        print(f"   ✅ Sauvegardé !\n")
        nouveaux += 1
        time.sleep(1)

    print(f"✅ Traitement terminé ! ({nouveaux} nouveau(x))\n")

def mode_automatique():
    print("🤖 Mode automatique démarré")
    print(f"⏱️  Vérification toutes les {INTERVALLE//60} minute(s)\n")
    init_db()
    while True:
        maintenant = datetime.now().strftime("%H:%M:%S")
        print(f"🕐 [{maintenant}] Cycle en cours...")
        try:
            traiter_emails()
        except Exception as e:
            print(f"❌ Erreur cycle : {e}")
        print(f"😴 Prochain cycle dans {INTERVALLE//60} minute(s)...\n")
        time.sleep(INTERVALLE)

if __name__ == "__main__":
    import sys
    if "--auto" in sys.argv:
        mode_automatique()
    else:
        print("🚀 Démarrage agent (mode réel)...\n")
        init_db()
        traiter_emails()