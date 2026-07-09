import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from database import chercher_email_similaire, log_tokens

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyser_email(sujet: str, corps: str, expediteur: str) -> dict:

    # ETAPE 1 : Classification
    prompt_classif = (
        "Tu es un assistant expert en gestion d'emails professionnels pour l'entreprise Famasser (commerce et distribution, Maroc).\n"
        "Analyse cet email et reponds en JSON uniquement, sans texte avant ou apres.\n\n"
        f"Email recu de : {expediteur}\n"
        f"Sujet : {sujet}\n"
        f"Corps : {corps[:1500]}\n\n"
        "REGLES DE CLASSIFICATION (choisis UNE seule categorie) :\n"
        '- "banque" : releve de compte, virement, solde, operation bancaire, CIH, Attijariwafa, Banque Populaire, cheque, RIB\n'
        '- "client" : commande client, livraison, devis client, reclamation client, suivi commande, bon de livraison\n'
        '- "fournisseur" : facture RECUE d\'un fournisseur, bon de commande fournisseur, catalogue produits, offre commerciale\n'
        '- "RH" : conge, recrutement, contrat de travail, paie, salaire, absence, formation, employe\n'
        '- "direction" : reunion de direction, note interne, strategie, bilan trimestriel, objectifs, communication interne\n'
        '- "recouvrement" : facture EMISE non payee par un CLIENT, relance de paiement CLIENT, menace juridique pour impaye CLIENT\n'
        '- "comptabilite" : cloture comptable, bilan, justificatif de depense, TVA, declaration fiscale, releve comptable\n'
        '- "rejet" : spam, publicite, newsletter, message systeme automatique, email vide ou sans sens\n\n'
        "DISTINCTION IMPORTANTE :\n"
        "- fournisseur = ON RECOIT une facture (on doit payer)\n"
        "- recouvrement = ON RECLAME un paiement a un client (on attend d'etre paye)\n\n"
        "REGLES URGENCE :\n"
        '- "haute" : delai <= 48h, montant > 10000 MAD/EUR, menace juridique, convocation direction\n'
        '- "moyenne" : delai entre 3-15 jours, montant entre 1000-10000 MAD, relance fournisseur\n'
        '- "faible" : information, conge, newsletter interne, aucun delai mentionne\n\n'
        "Reponds avec ce JSON exact :\n"
        "{\n"
        '    "resume": "UNE SEULE phrase courte, 22 mots MAXIMUM, au format : [Expediteur/role] a [Famasser] : [demande principale tres resumee] + montant/delai si mentionne. Ex: Fournisseur X a Famasser : demande paiement 8000 MAD sous 15j. Pas de contexte, pas de details",\n'
        '    "categorie": "banque|client|fournisseur|RH|direction|recouvrement|comptabilite|rejet",\n'
        '    "urgence": "haute|moyenne|faible",\n'
        '    "raison_urgence": "explication courte et precise",\n'
        '    "type_action": "relance|paiement|document|information|autre|ignorer",\n'
        '    "mots_cles": ["mot1", "mot2", "mot3"]\n'
        "}"
    )

    response_classif = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_classif}],
        temperature=0.2
    )
    contenu_classif = response_classif.choices[0].message.content

    # Log des tokens consommes pour cet appel de classification.
    # getattr(..., 0) par securite : je ne suis pas certain a 100% que les noms
    # d'attributs prompt_tokens/completion_tokens soient exactement ceux renvoyes
    # par l'API Groq (compatibilite annoncee avec le format OpenAI, mais non testee
    # avec un vrai acces reseau) -> a verifier en conditions reelles.
    try:
        usage_classif = response_classif.usage
        log_tokens(
            getattr(usage_classif, "prompt_tokens", 0),
            getattr(usage_classif, "completion_tokens", 0)
        )
    except Exception as e:
        print(f"⚠️  Impossible de logger les tokens (classification) : {e}")

    try:
        contenu_clean = re.sub(r"```json|```", "", contenu_classif).strip()
        classif = json.loads(contenu_clean)
        classif["langue"] = "fr"
    except:
        classif = {
            "resume": contenu_classif[:200],
            "categorie": "autre",
            "urgence": "faible",
            "raison_urgence": "Impossible de determiner",
            "type_action": "autre",
            "mots_cles": [],
            "langue": "fr"
        }

    # ETAPE 2 : Email rejeté ? on arrete
    if classif.get("categorie") == "rejet":
        print("   Email rejete (spam/systeme) - sauvegarde sans reponse")
        classif["reponse_proposee"] = ""
        classif["source_reponse"] = "Rejeté"
        return classif

    # ETAPE 3 : Chercher email similaire en historique
    similaire = chercher_email_similaire(sujet, classif.get("categorie", "autre"))

    if similaire:
        print(f"   Email similaire trouve (score: {similaire['score']}) - reutilisation historique")
        classif["reponse_proposee"] = similaire["reponse"]
        classif["source_reponse"] = f"Historique (similarite: {similaire['score']*100:.0f}%)"
        return classif

    # ETAPE 4 : Generer reponse IA courte
    print("   Generation reponse IA concise")

    prompt_reponse = (
        "Tu es un assistant de Famasser (Maroc). Reponds en francais uniquement.\n\n"
        f"Email de : {expediteur}\n"
        f"Sujet : {sujet}\n"
        f"Corps : {corps[:800]}\n"
        f"Categorie : {classif.get('categorie')} | Urgence : {classif.get('urgence')} | Action : {classif.get('type_action')}\n\n"
        "INSTRUCTIONS STRICTES :\n"
        "- Exactement 2 phrases COURTES, pas plus, pas moins\n"
        "- Maximum 10 mots par phrase\n"
        "- Phrase 1 : accuse de reception + action concrete (fusionnees en une phrase)\n"
        "- Phrase 2 : formule de cloture courte (ex: 'Cordialement.')\n"
        "- Aucun detail, aucune reformulation, va droit au but\n"
        "- Reponds UNIQUEMENT avec les 2 phrases, rien de plus, aucune explication"
    )

    response_rep = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_reponse}],
        temperature=0.3
    )

    # Log des tokens consommes pour cet appel de generation de reponse.
    try:
        usage_rep = response_rep.usage
        log_tokens(
            getattr(usage_rep, "prompt_tokens", 0),
            getattr(usage_rep, "completion_tokens", 0)
        )
    except Exception as e:
        print(f"⚠️  Impossible de logger les tokens (reponse) : {e}")

    classif["reponse_proposee"] = response_rep.choices[0].message.content.strip()
    classif["source_reponse"] = "Générée par IA"
    return classif


def tester_ai():
    tests = [
        {
            "sujet": "URGENT - Facture 15000 MAD impayee depuis 60 jours",
            "corps": "Bonjour, sans paiement sous 24h nous allons engager une procedure juridique.",
            "expediteur": "avocat@cabinet.ma"
        },
        {
            "sujet": "Facture fournisseur F-2026-441",
            "corps": "Bonjour, veuillez trouver ci-joint notre facture de 8000 MAD pour les fournitures livrees.",
            "expediteur": "fournisseur@maroc.ma"
        },
        {
            "sujet": "Promotion speciale ce weekend !",
            "corps": "Profitez de -50% sur tous nos produits ce weekend seulement !",
            "expediteur": "promo@newsletter.com"
        }
    ]

    print("Test complet :\n")
    for t in tests:
        result = analyser_email(t["sujet"], t["corps"], t["expediteur"])
        emoji = "HAUTE" if result["urgence"] == "haute" else "MOYENNE" if result["urgence"] == "moyenne" else "FAIBLE"
        print(f"Urgence : {emoji}")
        print(f"   Raison    : {result.get('raison_urgence','')}")
        print(f"   Categorie : {result.get('categorie')}")
        print(f"   Source    : {result.get('source_reponse','IA')}")
        print(f"   Reponse   : {result.get('reponse_proposee','')}")
        print()

if __name__ == "__main__":
    tester_ai()
