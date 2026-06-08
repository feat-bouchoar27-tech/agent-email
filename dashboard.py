import streamlit as st
import pandas as pd
from database import get_tous_emails, marquer_traite

st.set_page_config(page_title="Agent Email IA", page_icon="📧", layout="wide")
st.title("📧 Agent IA — Gestion des Emails")
st.markdown("---")

# Données
emails = get_tous_emails()
df = pd.DataFrame(emails) if emails else pd.DataFrame()

# Statistiques
total = len(emails)
urgences_hautes = len([e for e in emails if e["urgence"] == "haute"])

col1, col2, col3 = st.columns(3)
col1.metric("📬 Emails traités", total)
col2.metric("🔴 Urgences hautes", urgences_hautes)
col3.metric("📁 Catégories", 7)

st.markdown("---")

# Graphiques
if not df.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Emails par catégorie")
        cat_counts = df["categorie"].value_counts().reset_index()
        cat_counts.columns = ["Catégorie", "Nombre"]
        st.bar_chart(cat_counts.set_index("Catégorie"))

    with col2:
        st.subheader("🚨 Emails par urgence")
        urg_counts = df["urgence"].value_counts().reset_index()
        urg_counts.columns = ["Urgence", "Nombre"]
        st.bar_chart(urg_counts.set_index("Urgence"))

st.markdown("---")

# Filtres
col1, col2 = st.columns(2)
with col1:
    categorie = st.selectbox("Filtrer par catégorie", [
        "Toutes", "recouvrement", "RH", "fournisseur",
        "direction", "banque", "client", "comptabilite"
    ])
with col2:
    urgence = st.selectbox("Filtrer par urgence", [
        "Toutes", "haute", "moyenne", "faible"
    ])

# Appliquer filtres
emails_filtres = emails
if categorie != "Toutes":
    emails_filtres = [e for e in emails_filtres if e["categorie"] == categorie]
if urgence != "Toutes":
    emails_filtres = [e for e in emails_filtres if e["urgence"] == urgence]

st.markdown("---")
st.subheader(f"📋 Emails ({len(emails_filtres)})")

if not emails_filtres:
    st.info("Aucun email trouvé.")
else:
    for email in emails_filtres:
        couleur = "🔴" if email["urgence"] == "haute" else "🟡" if email["urgence"] == "moyenne" else "🟢"
        with st.expander(f"{couleur} {email['sujet']} — {email['expediteur']}"):
            col1, col2 = st.columns(2)
            col1.write(f"**Catégorie :** {email['categorie']}")
            col2.write(f"**Urgence :** {email['urgence']}")
            st.write(f"**Résumé IA :** {email['resume']}")
            st.write(f"**Action suggérée :** {email['type_action']}")
            st.info(f"**Réponse proposée :** {email['reponse_proposee']}")
            st.write(f"**Reçu le :** {email['date_reception']}")
            statut = "✅ Traité" if email.get("traite") else "⏳ En attente"
            st.write(f"**Statut :** {statut}")
            if not email.get("traite"):
                if st.button("✅ Marquer comme traité", key=f"btn_{email['id']}"):
                    marquer_traite(email["id"])
                    st.success("Marqué comme traité !")
                    st.rerun()