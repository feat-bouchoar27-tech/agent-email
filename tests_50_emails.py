# -*- coding: utf-8 -*-
"""
Script de test — évaluation de l'agent IA sur 50 emails annotés manuellement.

Principe : plutôt que d'envoyer 50 emails réels un par un (lent, dépend de la
réception IMAP), ce script appelle directement la fonction analyser_email()
utilisée par l'agent, avec 50 exemples réalistes déjà annotés (catégorie et
urgence attendues). Ça teste exactement le même moteur d'analyse IA, juste
sans passer par la boîte email — plus rapide et 100% reproductible.

Usage : à placer dans le dossier agent-email, puis lancer :
    python tests_50_emails.py

Résultat : un résumé de précision affiché dans le terminal, et un fichier
resultats_test_50_emails.csv généré (à insérer dans le rapport, section 3.9).
"""

import csv
import time
from ai_processor import analyser_email

# ============================================================
# 50 CAS DE TEST — (sujet, corps, expediteur, categorie_attendue, urgence_attendue)
# urgence_attendue peut être None si le cas est volontairement ambigu (on ne
# compare alors que la catégorie, pas l'urgence).
# ============================================================

CAS_DE_TEST = [
    # ---- FOURNISSEUR (7) ----
    ("Devis serrures TG-55", "Bonjour, pourriez-vous nous envoyer un devis pour 200 targettes modèle TG-55 ? Merci.", "achats@quincaillerie-ndm.ma", "fournisseur", "faible"),
    ("Rupture de stock urgente", "Nous ne pourrons pas livrer les 500 unités commandées avant 3 semaines suite à une rupture de matière première. Merci de nous confirmer si un délai supplémentaire est acceptable.", "commercial@metalcast.ma", "fournisseur", "moyenne"),
    ("Confirmation de commande N°4521", "Votre commande N°4521 a bien été enregistrée et sera livrée le 15 du mois. Cordialement.", "logistique@acierpro.ma", "fournisseur", "faible"),
    ("Hausse tarifaire matières premières", "Suite à la hausse du cours de l'acier, nos tarifs seront révisés de 8% à partir du mois prochain.", "direction@sideracier.ma", "fournisseur", "moyenne"),
    ("Problème qualité livraison N°3390", "Une partie du lot livré hier présente des défauts de finition. Nous devons bloquer la production concernée en urgence.", "qualite@fournimetal.ma", "fournisseur", "haute"),
    ("Facture en pièce jointe", "Veuillez trouver ci-joint la facture N°2026-887 relative à notre dernière livraison.", "compta@ferronnerie-atlas.ma", "fournisseur", "faible"),
    ("Renouvellement contrat cadre", "Notre contrat cadre arrive à échéance le mois prochain. Pouvons-nous convenir d'un rendez-vous pour le renouveler ?", "partenariats@metaux-maroc.ma", "fournisseur", "moyenne"),

    # ---- CLIENT (7) ----
    ("Réclamation produit défectueux", "Le lot de serrures CLEDOR livré la semaine dernière présente un défaut de verrouillage sur plusieurs unités. Nous devons stopper l'installation chez notre client final immédiatement.", "sav@quincaillerie-fes.ma", "client", "haute"),
    ("Demande de catalogue produits", "Bonjour, pourriez-vous nous faire parvenir votre catalogue produits 2026 ? Merci d'avance.", "contact@bricomarrakech.ma", "client", "faible"),
    ("Retard de livraison signalé", "Notre commande devait arriver hier, elle n'est toujours pas là. Pouvez-vous nous donner une estimation ?", "achats@habitatplus.ma", "client", "moyenne"),
    ("Demande de remise quantité", "Pour une commande de plus de 1000 unités, proposez-vous une remise sur le tarif catalogue ?", "b.hassani@grossiste-quincaillerie.ma", "client", "faible"),
    ("Litige facturation", "Nous avons constaté un écart entre le devis initial et la facture reçue. Merci de clarifier rapidement, le règlement est en attente.", "compta@distribmaroc.ma", "client", "moyenne"),
    ("Remerciements et fidélité", "Merci pour la qualité constante de vos produits, nous restons fidèles à CLEDOR pour tous nos chantiers.", "direction@batimax.ma", "client", "faible"),
    ("Urgence chantier bloqué", "Le chantier de l'hôtel Atlas est actuellement à l'arrêt faute de réception des serrures anti-panique commandées il y a 10 jours. Merci de traiter en priorité absolue.", "chef.projet@constructma.ma", "client", "haute"),

    # ---- RH (6) ----
    ("Demande de congé", "Bonjour, je souhaiterais poser 3 jours de congé la semaine du 20. Merci de valider.", "k.amrani@famasser.ma", "RH", "faible"),
    ("Convocation entretien annuel", "Votre entretien annuel d'évaluation est fixé au 12 du mois à 10h en salle de réunion.", "rh@famasser.ma", "RH", "moyenne"),
    ("Arrêt maladie", "Je vous informe que je suis en arrêt maladie à partir d'aujourd'hui, certificat médical joint.", "j.tazi@famasser.ma", "RH", "moyenne"),
    ("Candidature spontanée", "Bonjour, je vous transmets ma candidature pour un poste de technicien de production. CV en pièce jointe.", "yassine.b@gmail.com", "RH", "faible"),
    ("Question sur bulletin de paie", "J'ai une question concernant une ligne sur mon dernier bulletin de paie, pouvez-vous m'éclairer ?", "m.idrissi@famasser.ma", "RH", "faible"),
    ("Accident de travail à déclarer", "Un incident est survenu ce matin sur la chaîne de production, un employé légèrement blessé à la main. Déclaration à faire dans les 48h.", "securite@famasser.ma", "RH", "haute"),

    # ---- BANQUE (6) ----
    ("Relevé de compte mensuel", "Veuillez trouver ci-joint votre relevé de compte du mois en cours.", "notifications@banquepopulaire.ma", "banque", "faible"),
    ("Échéance de crédit à venir", "Nous vous rappelons que l'échéance de votre crédit équipement est prévue dans 5 jours.", "credit@attijariwafabank.ma", "banque", "moyenne"),
    ("Rejet de virement", "Le virement N°88213 n'a pas pu être exécuté faute de provision suffisante. Merci de régulariser rapidement.", "operations@bmcebank.ma", "banque", "haute"),
    ("Proposition de placement", "Notre conseiller souhaite vous présenter une offre de placement de trésorerie adaptée à votre profil.", "conseiller@cih.ma", "banque", "faible"),
    ("Mise à jour dossier KYC", "Dans le cadre de la réglementation, merci de nous transmettre vos documents actualisés sous 15 jours.", "conformite@bankofafrica.ma", "banque", "moyenne"),
    ("Alerte solde bas", "Le solde de votre compte professionnel est en dessous du seuil habituel, merci de vérifier.", "alertes@attijariwafabank.ma", "banque", "moyenne"),

    # ---- DIRECTION (6) ----
    ("Réunion stratégique lundi", "Merci de préparer un point sur l'avancement des projets IT pour la réunion de direction de lundi 9h.", "direction.generale@famasser.ma", "direction", "moyenne"),
    ("Validation budget projet", "Merci de valider en urgence le budget révisé du projet avant la clôture comptable de vendredi.", "dg@famasser.ma", "direction", "haute"),
    ("Note d'information générale", "Veuillez prendre connaissance de la nouvelle organisation des équipes, effective à partir du mois prochain.", "direction.generale@famasser.ma", "direction", "faible"),
    ("Demande de reporting mensuel", "Merci de me faire parvenir le reporting d'activité du mois avant la fin de semaine.", "dg@famasser.ma", "direction", "moyenne"),
    ("Visite client important prévue", "Un client stratégique visite nos locaux jeudi matin, merci de préparer une présentation courte.", "direction.generale@famasser.ma", "direction", "moyenne"),
    ("Décision arrêt ligne de production", "Suite à un incident technique majeur, la ligne 2 doit être arrêtée immédiatement dans l'attente d'une inspection.", "dg@famasser.ma", "direction", "haute"),

    # ---- COMPTABILITÉ (6) ----
    ("Facture à valider", "Merci de valider la facture fournisseur N°7742 avant son règlement prévu la semaine prochaine.", "compta.interne@famasser.ma", "comptabilite", "moyenne"),
    ("Rapprochement bancaire mensuel", "Le rapprochement bancaire du mois est disponible pour vérification.", "compta.interne@famasser.ma", "comptabilite", "faible"),
    ("Retard de paiement fournisseur signalé", "Un fournisseur nous relance pour un paiement en retard de 15 jours, merci de régulariser rapidement.", "compta.interne@famasser.ma", "comptabilite", "haute"),
    ("Clôture comptable annuelle", "Merci de transmettre l'ensemble des justificatifs manquants avant la clôture de l'exercice, délai serré.", "compta.interne@famasser.ma", "comptabilite", "haute"),
    ("Note de frais à traiter", "Voici mes notes de frais du mois de déplacement, merci de les traiter pour remboursement.", "commercial1@famasser.ma", "comptabilite", "faible"),
    ("Question TVA", "J'ai une question sur le taux de TVA applicable à une commande export, pouvez-vous confirmer ?", "compta.interne@famasser.ma", "comptabilite", "faible"),

    # ---- RECOUVREMENT (6) ----
    ("Relance client impayé", "Le client Distrimétal n'a toujours pas réglé la facture échue depuis 45 jours, merci d'engager une relance.", "recouvrement@famasser.ma", "recouvrement", "haute"),
    ("Échéancier de paiement proposé", "Le client souhaite un échéancier sur 3 mois pour régler sa dette. Merci de valider.", "recouvrement@famasser.ma", "recouvrement", "moyenne"),
    ("Mise en demeure à envoyer", "Aucune réponse du client malgré 3 relances. Merci de préparer une mise en demeure.", "recouvrement@famasser.ma", "recouvrement", "haute"),
    ("Suivi factures en attente", "Voici le point hebdomadaire des factures en attente de règlement, rien d'urgent cette semaine.", "recouvrement@famasser.ma", "recouvrement", "faible"),
    ("Client règle sa dette", "Le client Ferronor a réglé l'intégralité de sa dette ce jour, dossier à clôturer.", "recouvrement@famasser.ma", "recouvrement", "faible"),
    ("Risque client à surveiller", "Ce nouveau client présente un profil de risque élevé selon notre analyse, à surveiller de près sur les prochaines commandes.", "recouvrement@famasser.ma", "recouvrement", "moyenne"),

    # ---- REJET / SPAM (6) ----
    ("Vous avez gagné un iPhone !", "Félicitations, cliquez ici pour récupérer votre cadeau exclusif dès maintenant !", "no-reply@promo-cadeaux.xyz", "rejet", "faible"),
    ("Newsletter hebdomadaire", "Découvrez les actualités de la semaine dans notre secteur.", "newsletter@salon-industrie.com", "rejet", "faible"),
    ("Notification système automatique", "Ceci est un message automatique généré par le système de sauvegarde. Aucune action requise.", "system@backup-service.local", "rejet", "faible"),
    ("Offre publicitaire agressive", "Boostez votre visibilité en ligne dès aujourd'hui avec notre offre exceptionnelle à -70% !", "marketing@webagency-promo.com", "rejet", "faible"),
    ("Test envoyé par erreur", "test test", "collegue@famasser.ma", "rejet", "faible"),
    ("Message vide", "", "inconnu@mailtest.com", "rejet", "faible"),
]


def executer_tests():
    resultats = []
    correct_categorie = 0
    correct_urgence = 0
    total_urgence_evaluee = 0

    print(f"🧪 Lancement du test sur {len(CAS_DE_TEST)} emails...\n")

    for i, (sujet, corps, expediteur, categorie_attendue, urgence_attendue) in enumerate(CAS_DE_TEST, 1):
        print(f"[{i}/{len(CAS_DE_TEST)}] {sujet[:50]}...")

        try:
            analyse = analyser_email(sujet, corps, expediteur)
        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            resultats.append({
                "sujet": sujet, "categorie_attendue": categorie_attendue, "categorie_obtenue": "ERREUR",
                "urgence_attendue": urgence_attendue, "urgence_obtenue": "ERREUR",
                "categorie_correcte": False, "urgence_correcte": False,
            })
            continue

        categorie_obtenue = analyse.get("categorie", "")
        urgence_obtenue = analyse.get("urgence", "")

        cat_ok = (categorie_obtenue == categorie_attendue)
        if cat_ok:
            correct_categorie += 1

        urg_ok = None
        if urgence_attendue is not None:
            total_urgence_evaluee += 1
            urg_ok = (urgence_obtenue == urgence_attendue)
            if urg_ok:
                correct_urgence += 1

        symbole = "✅" if cat_ok else "❌"
        print(f"   {symbole} Catégorie : attendu={categorie_attendue} / obtenu={categorie_obtenue}")
        if urgence_attendue is not None:
            symbole_u = "✅" if urg_ok else "❌"
            print(f"   {symbole_u} Urgence   : attendu={urgence_attendue} / obtenu={urgence_obtenue}")

        resultats.append({
            "sujet": sujet, "categorie_attendue": categorie_attendue, "categorie_obtenue": categorie_obtenue,
            "urgence_attendue": urgence_attendue or "-", "urgence_obtenue": urgence_obtenue,
            "categorie_correcte": cat_ok, "urgence_correcte": urg_ok,
        })

        time.sleep(1)  # évite de saturer le quota API

    # ---- Résumé final ----
    total = len(CAS_DE_TEST)
    precision_categorie = (correct_categorie / total) * 100
    precision_urgence = (correct_urgence / total_urgence_evaluee) * 100 if total_urgence_evaluee else 0

    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DU TEST")
    print("=" * 50)
    print(f"Emails testés               : {total}")
    print(f"Précision classification    : {correct_categorie}/{total} ({precision_categorie:.1f}%)")
    print(f"Précision détection urgence : {correct_urgence}/{total_urgence_evaluee} ({precision_urgence:.1f}%)")
    print("=" * 50)

    # ---- Export CSV pour le rapport ----
    with open("resultats_test_50_emails.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sujet", "categorie_attendue", "categorie_obtenue", "categorie_correcte",
            "urgence_attendue", "urgence_obtenue", "urgence_correcte"
        ])
        writer.writeheader()
        writer.writerows(resultats)

    print("\n✅ Résultats détaillés exportés dans resultats_test_50_emails.csv")
    print("   (à ouvrir dans Excel, et à résumer dans la section 3.9 de ton rapport)")


if __name__ == "__main__":
    executer_tests()