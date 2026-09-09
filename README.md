# Agent IA — Gestion intelligente des emails

Agent IA connecté à la messagerie Outlook/IMAP de Famasser (marque CLEDOR), qui classe automatiquement les emails reçus, détecte leur niveau d'urgence, génère un résumé et propose une réponse — sans jamais envoyer automatiquement quoi que ce soit.

Projet réalisé dans le cadre d'un stage élève-ingénieur EIGSI Casablanca (spécialité AIBD), sujet principal.

## Fonctionnalités

- **Classification automatique** en 7 catégories métier (recouvrement, RH, fournisseur, direction, banque, client, comptabilité) + détection du spam/rejet
- **Détection d'urgence** (haute / moyenne / faible) avec raison explicite, y compris détection de signaux d'urgence implicites (pas seulement des critères chiffrés)
- **Résumé enrichi** (format court, avec expéditeur) et **proposition de réponse** (2 phrases courtes), jamais envoyée automatiquement
- **Économie de tokens** : réutilisation des réponses historiques similaires (similarité de Jaccard)
- **Dashboard web** (5 pages) : Dashboard, Emails, Urgences, Statistiques, Configuration
- **Notifications multicanal** : email HTML automatique + bot Telegram interactif (`@FamasserAgentBot`, commandes `/urgences`, `/stats`, `/aide`)
- **Mode automatique** : vérification en boucle toutes les 5 minutes (`python agent.py --auto`)

## Stack technique

- Python + Flask
- PostgreSQL
- API Groq (modèle `openai/gpt-oss-20b`)
- IMAP/SMTP OVH (SSL)
- HTML/CSS/JavaScript (dashboard, Chart.js, jsPDF)

## Installation

```bash
pip install -r requirements.txt
```

Copier `.env.example` en `.env` et remplir les identifiants (IMAP, Groq, Telegram, base de données).

## Lancement

```bash
# Traitement ponctuel (vérifie une fois, puis s'arrête)
python api.py          # dashboard web, http://127.0.0.1:5000
python agent.py         # traite les emails non lus une fois

# Mode automatique (vérifie en boucle toutes les 5 min)
python agent.py --auto
```

## Résultats de test

Un script de test (`tests_50_emails.py`) évalue la précision de l'agent sur 50 emails représentatifs, annotés manuellement (catégorie et urgence attendues) :

| Métrique | Résultat |
|---|---|
| Précision classification | 82.0% (41/50) |
| Précision détection urgence | 77.6% (38/49) |

Ces résultats s'appuient sur une seconde itération du prompt de détection d'urgence, après une première version limitée à des critères chiffrés stricts (57.1% de précision initiale).

```bash
python tests_50_emails.py
```

Génère un résumé dans le terminal et un export détaillé (`resultats_test_50_emails.csv`).

## Sécurité

Les identifiants (clé API Groq, mot de passe IMAP, token Telegram) sont stockés exclusivement dans `.env`, exclu du dépôt Git (`.gitignore`). Ne jamais committer ce fichier.

## Auteure

AIT BOUCHOAR Fatima Ezzahra — EIGSI Casablanca, 4ème année AIBD
Stage élève-ingénieur — Famasser (CLEDOR), 2026