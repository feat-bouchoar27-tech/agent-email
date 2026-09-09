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
        '- "client" : une entreprise EXTERNE (grossiste, distributeur, magasin) demande un devis, un catalogue, une remise, ou signale un probleme SUR UNE COMMANDE QU\'ELLE A PASSEE A FAMASSER (Famasser lui vend des produits)\n'
        '- "fournisseur" : une entreprise EXTERNE qui VEND des matieres premieres ou produits A Famasser envoie une facture, un catalogue, une confirmation de livraison, ou une offre commerciale (Famasser leur achete des produits)\n'
        '- "RH" : conge, recrutement, contrat de travail, paie, salaire, absence, formation, employe, accident de travail\n'
        '- "direction" : reunion de direction, note interne, strategie, bilan trimestriel, objectifs, communication interne, VALIDATION DE BUDGET par la direction generale\n'
        '- "recouvrement" : TOUT email envoye par le service recouvrement de Famasser (souvent recouvrement@famasser.ma) concernant un client : relance de paiement, echeancier, mise en demeure, suivi de factures impayees, cloture de dossier apres paiement recu, surveillance du risque d\'un client\n'
        '- "comptabilite" : tache comptable INTERNE (validation de facture fournisseur AVANT paiement, cloture comptable, TVA, note de frais, rapprochement bancaire), typiquement envoyee par compta.interne@famasser.ma\n'
        '- "rejet" : spam, publicite, newsletter, message systeme automatique, email vide ou sans sens\n\n'
        "INDICE IMPORTANT — L'ADRESSE DE L'EXPEDITEUR :\n"
        "Si l'expediteur se termine par @famasser.ma (email INTERNE), la categorie est presque toujours "
        "recouvrement, comptabilite, RH ou direction — PAS fournisseur/client/banque (qui viennent normalement "
        "d'une adresse EXTERNE a famasser.ma). Un email interne qui PARLE d'un fournisseur ou d'un client "
        "reste une tache interne (comptabilite ou recouvrement), pas une communication directe du fournisseur/client.\n\n"
        "DISTINCTION IMPORTANTE :\n"
        "- fournisseur = communication DIRECTE et EXTERNE d'un fournisseur (facture qu'IL envoie, IL confirme une livraison)\n"
        "- comptabilite = un COLLEGUE Famasser demande une action comptable, meme si ca concerne un fournisseur (ex: 'merci de valider cette facture fournisseur' envoye par compta.interne@famasser.ma = comptabilite, pas fournisseur)\n"
        "- recouvrement = un COLLEGUE Famasser (service recouvrement) parle d'un client qui doit de l'argent, y compris pour signaler qu'il a paye ou pour evaluer son risque\n"
        "- client = le client EXTERNE ecrit LUI-MEME a Famasser\n\n"
        "REGLES URGENCE — IMPORTANT, LIS ATTENTIVEMENT :\n"
        "Un email peut etre urgent meme SANS chiffre precis (delai ou montant). Detecte aussi l'urgence IMPLICITE :\n"
        "signaux forts d'urgence dans le ton ou le vocabulaire : 'urgent', 'urgence', 'immediatement', 'des que possible', "
        "'au plus vite', 'bloque', 'bloquee', 'arret', 'stopper', 'en panne', 'sans attendre', 'des maintenant', "
        "menace juridique, procedure legale, accident, securite, systeme a l'arret, production arretee, chantier bloque.\n\n"
        '- "haute" : au moins UN des cas suivants -> delai <= 48h explicite, OU montant > 10000 MAD/EUR, OU menace juridique, '
        "OU convocation direction urgente, OU un signal fort d'urgence implicite ci-dessus (meme sans chiffre), "
        "OU une activite/production/chantier a l'arret ou bloque(e), OU un accident/incident de securite\n"
        '- "moyenne" : delai entre 3-15 jours, OU montant entre 1000-10000 MAD, OU relance simple sans blocage total, '
        "OU demande d'action attendue prochainement sans caractere critique immediat\n"
        '- "faible" : simple information, conge standard, newsletter interne, aucun delai ni signal d\'urgence mentionne\n\n'
        "Ne classe JAMAIS un email en 'faible' par defaut simplement parce qu'aucun chiffre exact n'est donne : "
        "cherche d'abord un signal d'urgence implicite dans le ton du message avant de conclure a une urgence faible.\n\n"
        "Exemples :\n"
        "- 'Nous devons stopper l'installation en urgence' -> haute (activite bloquee + mot urgence), meme sans montant\n"
        "- 'Le chantier est a l'arret' -> haute (activite bloquee)\n"
        "- 'Merci de traiter cela des que possible' -> moyenne au minimum (signal de priorite sans blocage total)\n"
        "- 'Pour information, voici le compte-rendu' -> faible (aucun signal d'urgence)\n"
        "- Email de recouvrement@famasser.ma disant qu'un client a regle sa dette -> categorie recouvrement (pas comptabilite)\n"
        "- Email de recouvrement@famasser.ma evaluant le risque d'un nouveau client -> categorie recouvrement (pas direction)\n"
        "- Email de compta.interne@famasser.ma demandant de valider une facture fournisseur ou de regulariser un retard "
        "de paiement fournisseur -> categorie comptabilite (pas fournisseur)\n"
        "- Un fournisseur externe qui confirme la livraison d'une commande passee par Famasser -> categorie fournisseur (pas client)\n"
        "- La direction generale (dg@famasser.ma) qui demande de valider un budget -> categorie direction (pas comptabilite)\n\n"
        "Reponds avec ce JSON exact :\n"
        "{\n"
        '    "resume": "UNE SEULE phrase courte, 22 mots MAXIMUM, au format : [Expediteur/role] a [Famasser] : [demande principale tres resumee] + montant/delai si mentionne. Ex: Fournisseur X a Famasser : demande paiement 8000 MAD sous 15j. Pas de contexte, pas de details",\n'
        '    "categorie": "banque|client|fournisseur|RH|direction|recouvrement|comptabilite|rejet",\n'
        '    "urgence": "haute|moyenne|faible",\n'
        '    "raison_urgence": "explication courte et precise, cite le signal detecte (chiffre OU mot-cle d\'urgence implicite)",\n'
        '    "type_action": "relance|paiement|document|information|autre|ignorer",\n'
        '    "mots_cles": ["mot1", "mot2", "mot3"]\n'
        "}"
    )

    response_classif = client.chat.completions.create(
        model="openai/gpt-oss-20b",
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
        model="openai/gpt-oss-20b",
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