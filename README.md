# 📧 Agent IA — Gestion des Emails

## 📌 Description
Agent intelligent connecté à Outlook qui aide un responsable à gérer sa boîte mail automatiquement grâce à l'intelligence artificielle.

## 🎯 Fonctionnalités
- 📖 Lecture automatique des emails entrants
- 📝 Résumé rapide de chaque email
- 📁 Classification en 7 catégories : banque, client, fournisseur, RH, direction, recouvrement, comptabilité
- 🚨 Détection des urgences (haute / moyenne / faible)
- 💡 Détection des actions : relance, paiement, document, information
- ✉️ Proposition de brouillons de réponse (sans envoi automatique)
- 📊 Dashboard interactif avec graphiques

## 🛠️ Technologies utilisées
| Technologie | Rôle |
|---|---|
| Python 3.14 | Langage principal |
| Groq LLaMA 3.3 70B | Analyse IA des emails |
| PostgreSQL | Base de données |
| Streamlit | Dashboard interactif |
| Microsoft Graph API | Connexion Outlook |

## 📁 Structure du projet
agent-email/
├── agent.py              # Pipeline principal
├── ai_processor.py       # Analyse IA avec Groq
├── outlook_connector.py  # Connexion Outlook
├── database.py           # Gestion PostgreSQL
├── dashboard.py          # Interface Streamlit
├── .env                  # Variables d'environnement
└── README.md             # Documentation

## ⚙️ Installation

### 1. Cloner le projet
git clone https://github.com/feat-bouchoar27-tech/agent-email.git
cd agent-email

### 2. Installer les dépendances
pip install groq psycopg2 streamlit python-dotenv msal requests pandas

### 3. Configurer le fichier .env
GROQ_API_KEY=votre_clé_groq
DATABASE_URL=postgresql://postgres:motdepasse@localhost:5432/agent_email
USER_EMAIL=votre_email@outlook.com

### 4. Initialiser la base de données
python database.py

### 5. Lancer l'agent
python agent.py

### 6. Lancer le dashboard
streamlit run dashboard.py

## 🔄 Pipeline de traitement
Boîte Outlook
     ↓
agent.py lit les emails non lus
     ↓
ai_processor.py analyse avec Groq LLM
     ↓
Résumé + Catégorie + Urgence + Réponse proposée
     ↓
database.py sauvegarde dans PostgreSQL
     ↓
dashboard.py affiche les résultats

## 📊 Exemple de résultat
| Email | Catégorie | Urgence | Action |
|---|---|---|---|
| Facture 15000 EUR impayée | recouvrement | haute | relance |
| Demande de congé | RH | moyenne | document |
| Devis fournisseur | fournisseur | moyenne | information |
| Relevé bancaire | banque | faible | information |

## 👩‍💻 Auteur
Fatima Ezzahra Aït Bouchoar
Étudiante ingénieure 4A — Dominante AIBD
Stage entreprise — 2026