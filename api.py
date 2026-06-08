from flask import Flask, jsonify, send_file
from flask_cors import CORS
from database import get_tous_emails, marquer_traite
import subprocess

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return send_file("dashboard.html")

@app.route("/emails")
def emails():
    data = get_tous_emails()
    # Convertir les dates en string
    for e in data:
        if e.get("date_reception"):
            e["date_reception"] = str(e["date_reception"])
        if e.get("date_traitement"):
            e["date_traitement"] = str(e["date_traitement"])
        if e.get("created_at"):
            e["created_at"] = str(e["created_at"])
    return jsonify(data)

@app.route("/analyser", methods=["POST"])
def analyser():
    subprocess.Popen(["python", "agent.py"])
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(port=5000, debug=False)