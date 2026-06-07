 import openai
import json
from config import *

CATEGORIES = ['banque', 'client', 'fournisseur', 'RH',
              'direction', 'recouvrement', 'comptabilite']

def analyser_email(sujet: str, corps: str, expediteur: str) -> dict:
    prompt = f"""Tu es un assistant pour un responsable d'entreprise.
Analyse cet email et reponds en JSON uniquement.

Email recu de : {expediteur}
Sujet : {sujet}
Corps : {corps[:1500]}

Reponds avec ce JSON exact :
{{
  "resume": "2-3 phrases resumant l'email",
  "categorie": "banque|client|fournisseur|RH|direction|recouvrement|comptabilite",
  "urgence": "haute|moyenne|faible",
  "type_action": "relance|paiement|document|information|autre",
  "reponse_proposee": "brouillon de reponse adapte"
}}"""

    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.2
    )
    return json.loads(response.choices[0].message.content)
