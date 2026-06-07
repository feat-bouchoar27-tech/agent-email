import streamlit as st

EMAILS_DEMO = [
    {"sujet": "Relance facture 2024-087", "expediteur": "ahmed@client.com", "categorie": "recouvrement", "urgence": "haute", "resume": "Relance pour facture de 4500 EUR.", "reponse": "Bonjour, reglement sous 48h."},
    {"sujet": "Demande de conge", "expediteur": "sara@entreprise.com", "categorie": "RH", "urgence": "moyenne", "resume": "Demande 5 jours du 20 au 25 novembre.", "reponse": "Bonjour Sara, demande bien notee."},
    {"sujet": "Devis informatique", "expediteur": "contact@fournisseur.ma", "categorie": "fournisseur", "urgence": "faible", "resume": "Devis pour 10 ordinateurs.", "reponse": "Merci, nous allons etudier votre devis."},
    {"sujet": "Reunion direction", "expediteur": "direction@entreprise.com", "categorie": "direction", "urgence": "haute", "resume": "Reunion vendredi a 10h.", "reponse": "Je confirme ma presence."},
    {"sujet": "Releve bancaire", "expediteur": "banque@bmce.ma", "categorie": "banque", "urgence": "faible", "resume": "Releve octobre disponible.", "reponse": "Merci, bien note."},
]

st.set_page_config(page_title="Agent Email IA", page_icon="📧", layout="wide")
st.title("📧 Agent IA — Gestion des Emails")
st.markdown("---")

col1, col2, col3 = st.columns(3)
col1.metric("Emails non lus", len(EMAILS_DEMO))
col2.metric("Urgences", 2)
col3.metric("Categories", 7)
st.markdown("---")

categorie = st.selectbox("Filtrer par categorie", ["Toutes", "recouvrement", "RH", "fournisseur", "direction", "banque"])
urgence = st.selectbox("Filtrer par urgence", ["Toutes", "haute", "moyenne", "faible"])

emails = EMAILS_DEMO
if categorie != "Toutes":
    emails = [e for e in emails if e["categorie"] == categorie]
if urgence != "Toutes":
    emails = [e for e in emails if e["urgence"] == urgence]

st.markdown("---")
for email in emails:
    couleur = "🔴" if email["urgence"] == "haute" else "🟡" if email["urgence"] == "moyenne" else "🟢"
    with st.expander(f"{couleur} {email['sujet']} — {email['expediteur']}"):
        st.write(f"**Categorie :** {email['categorie']}")
        st.write(f"**Urgence :** {email['urgence']}")
        st.write(f"**Resume IA :** {email['resume']}")
        st.info(f"**Reponse proposee :** {email['reponse']}")
        st.button("Sauvegarder brouillon", key=email['sujet'])