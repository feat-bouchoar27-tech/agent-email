import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyser_email(sujet: str, corps: str, expediteur: str) -> dict:
    prompt = f"""Tu es un assistant expert en gestion d'emails professionnels.
Analyse cet email et reponds en JSON uniquement, sans texte avant ou apres.

Email recu de : {expediteur}
Sujet : {sujet}
Corps : {corps[:1500]}

Regles pour l'urgence :
- "haute" : delai mentionne (24h, urgent, immediat, aujourd'hui), montant > 10000 EUR, menace juridique, direction
- "moyenne" : relance, demande de validation, facture < 10000 EUR, fournisseur
- "faible" : information, newsletter, conge, devis sans deadline

Reponds avec ce JSON exact :
{{
    "resume": "2-3 phrases resumant l email",
    "categorie": "banque|client|fournisseur|RH|direction|recouvrement|comptabilite",
    "urgence": "haute|moyenne|faible",
    "type_action": "relance|paiement|document|information|autre",
    "reponse_proposee": "brouillon de reponse adapte et professionnel",
    "mots_cles": ["mot1", "mot2", "mot3"]
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    contenu = response.choices[0].message.content

    import json, re
    try:
        # Nettoyer si le modele ajoute des backticks
        contenu_clean = re.sub(r"```json|```", "", contenu).strip()
        return json.loads(contenu_clean)
    except:
        return {
            "resume": contenu[:200],
            "categorie": "autre",
            "urgence": "faible",
            "type_action": "autre",
            "reponse_proposee": "",
            "mots_cles": []
        }

def tester_ai():
    """Tests avec différents niveaux d'urgence"""
    tests = [
        {
            "sujet": "URGENT - Facture 15000 EUR impayée depuis 60 jours",
            "corps": "Bonjour, sans paiement sous 24h nous allons engager une procédure juridique.",
            "expediteur": "avocat@cabinet.ma"
        },
        {
            "sujet": "Relance facture 4500 EUR",
            "corps": "Bonjour, je relance pour ma facture de 4500 EUR.",
            "expediteur": "ahmed@client.com"
        },
        {
            "sujet": "Newsletter mensuelle",
            "corps": "Voici les actualités du mois de janvier.",
            "expediteur": "news@info.ma"
        }
    ]

    print("🧪 Test de détection des urgences :\n")
    for t in tests:
        result = analyser_email(t["sujet"], t["corps"], t["expediteur"])
        emoji = "🔴" if result["urgence"] == "haute" else "🟡" if result["urgence"] == "moyenne" else "🟢"
        print(f"{emoji} Urgence : {result['urgence']} | Catégorie : {result['categorie']}")
        print(f"   Sujet : {t['sujet'][:50]}")
        print(f"   Mots-clés : {result.get('mots_cles', [])}\n")

if __name__ == "__main__":
    tester_ai()