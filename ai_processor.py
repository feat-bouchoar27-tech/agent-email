import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CATEGORIES = ['banque', 'client', 'fournisseur', 'RH',
              'direction', 'recouvrement', 'comptabilite']

def analyser_email(sujet: str, corps: str, expediteur: str) -> dict:
    prompt = f"""Tu es un assistant pour un responsable d'entreprise.
Analyse cet email et reponds en JSON uniquement, sans texte avant ou apres.

Email recu de : {expediteur}
Sujet : {sujet}
Corps : {corps[:1500]}

Reponds avec ce JSON exact :
{{
  "resume": "2-3 phrases resumant l email",
  "categorie": "banque|client|fournisseur|RH|direction|recouvrement|comptabilite",
  "urgence": "haute|moyenne|faible",
  "type_action": "relance|paiement|document|information|autre",
  "reponse_proposee": "brouillon de reponse adapte"
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    
    contenu = response.choices[0].message.content
    return json.loads(contenu)