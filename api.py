from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from database import get_tous_emails, marquer_traite, get_tokens_today, log_envoi, get_envois
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
load_dotenv()
from auth import requires_auth, register_auth_routes
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY manquant dans .env. "
        "Génère-le avec : python -c \"import secrets; print(secrets.token_hex(32))\""
    )
CORS(app)
register_auth_routes(app)
# Config SMTP OVH
SMTP_SERVER = "ssl0.ovh.net"
SMTP_PORT = 465
SMTP_USER = os.getenv("IMAP_USER")
SMTP_PASSWORD = os.getenv("IMAP_PASSWORD")
@app.route("/")
@requires_auth
def index():
    return send_file("dashboard.html")
@app.route("/emails")
@requires_auth
def emails():
    data = get_tous_emails()
    for e in data:
        if e.get("date_reception"):
            e["date_reception"] = str(e["date_reception"])
        if e.get("date_traitement"):
            e["date_traitement"] = str(e["date_traitement"])
        if e.get("created_at"):
            e["created_at"] = str(e["created_at"])
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response
@app.route("/analyser", methods=["POST"])
@requires_auth
def analyser():
    subprocess.Popen(["python", "agent.py"])
    return jsonify({"status": "ok"})
@app.route("/marquer/<int:email_id>", methods=["POST"])
@requires_auth
def marquer(email_id):
    marquer_traite(email_id)
    return jsonify({"status": "ok", "id": email_id})
@app.route("/repondre", methods=["POST"])
@requires_auth
def repondre():
    data = request.json
    destinataire = data.get("destinataire")
    sujet = data.get("sujet", "Re: ")
    corps = data.get("corps")
    email_id = data.get("email_id")
    if not destinataire or not corps:
        return jsonify({"status": "erreur", "message": "Destinataire et corps requis"}), 400
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = destinataire
        msg["Subject"] = sujet
        msg.attach(MIMEText(corps, "plain", "utf-8"))
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, destinataire, msg.as_string())
        try:
            log_envoi(destinataire, sujet, corps, email_id)
        except Exception as e:
            # On ne fait jamais echouer l'envoi reel a cause d'un souci de log.
            print(f"⚠️  Email envoyé mais non loggé dans l'historique : {e}")
        return jsonify({"status": "ok", "message": f"Email envoyé à {destinataire}"})
    except Exception as e:
        return jsonify({"status": "erreur", "message": str(e)}), 500
@app.route('/api/stats/tokens', methods=['GET'])
@requires_auth
def stats_tokens():
    limite = 100000
    # Lecture depuis la base de donnees (table tokens_usage), alimentee par
    # ai_processor.py a chaque appel Groq reel. Un compteur en memoire ici
    # ne fonctionnerait pas car agent.py tourne dans un processus separe.
    totaux = get_tokens_today()
    return jsonify({
        "success": True,
        "data": {
            "prompt": totaux["prompt"],
            "completion": totaux["completion"],
            "total": totaux["total"],
            "restants": max(limite - totaux["total"], 0),
            "limite": limite,
            "pourcentage": round(totaux["total"] / limite * 100, 1) if limite else 0
        }
    })
@app.route('/api/stats/emails-par-jour', methods=['GET'])
@requires_auth
def emails_par_jour():
    emails = get_tous_emails()
    counts = {}
    for e in emails:
        if e.get('date_reception'):
            jour = str(e['date_reception'])[:10]
            counts[jour] = counts.get(jour, 0) + 1
    data = [{"jour": k, "total": v} for k, v in sorted(counts.items())]
    return jsonify({"success": True, "data": data})
@app.route('/api/envois', methods=['GET'])
@requires_auth
def envois():
    data = get_envois()
    for e in data:
        if e.get("date_envoi"):
            e["date_envoi"] = str(e["date_envoi"])
    return jsonify({"success": True, "data": data})
if __name__ == "__main__":
    app.run(port=5000, debug=False)