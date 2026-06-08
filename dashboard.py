import streamlit as st
from database import get_tous_emails, marquer_traite

st.set_page_config(page_title="Agent Email IA", page_icon="📧", layout="wide")
st.title("📧 Agent IA — Gestion des Emails")
st.markdown("---")

# Récupérer les vrais emails depuis PostgreSQL
emails = get_tous_emails()

# Statistiques
total = len(emails)
urgences = len([e for e in emails if e["urgence"] == "haute"])
categories = len(set(e["categorie"] for e in emails if e["categorie"]))

col1, col2, col3 = st.columns(3)
col1.metric("Emails traités", total)
col2.metric("Urgences hautes", urgences)
col3.metric("Catégories", 7)

st.markdown("---")

# Filtres
categorie = st.selectbox("Filtrer par catégorie", [
    "Toutes", "recouvrement", "RH", "fournisseur",
    "direction", "banque", "client", "comptabilite"
])
urgence = st.selectbox("Filtrer par urgence", ["Toutes", "haute", "moyenne", "faible"])

# Appliquer les filtres
if categorie != "Toutes":
    emails = [e for e in emails if e["categorie"] == categorie]
if urgence != "Toutes":
    emails = [e for e in emails if e["urgence"] == urgence]

st.markdown("---")

if not emails:
    st.info("Aucun email trouvé.")
else:
    for email in emails:
        couleur = "🔴" if email["urgence"] == "haute" else "🟡" if email["urgence"] == "moyenne" else "🟢"
        with st.expander(f"{couleur} {email['sujet']} — {email['expediteur']}"):
            col1, col2 = st.columns(2)
            col1.write(f"**Catégorie :** {email['categorie']}")
            col2.write(f"**Urgence :** {email['urgence']}")
            st.write(f"**Résumé IA :** {email['resume']}")
            st.write(f"**Action suggérée :** {email['type_action']}")
            st.info(f"**Réponse proposée :** {email['reponse_proposee']}")
            st.write(f"**Reçu le :** {email['date_reception']}")
            traite = email.get("traite", False)
            st.write(f"**Statut :** {'✅ Traité' if traite else '⏳ En attente'}")