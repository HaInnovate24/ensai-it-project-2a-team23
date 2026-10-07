import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

st.title("Espace Administration (F6) ⚙️")
st.write("Gérez les accès utilisateurs et consultez le journal d'activité de la plateforme.")

# --- Section 1 : Gestion des utilisateurs ---
st.header("👥 Gestion des utilisateurs")

# Fausse base de données des utilisateurs (Mock)
utilisateurs = pd.DataFrame({
    "ID": [101, 102, 103],
    "Nom d'utilisateur": ["admin_alice", "user_bob", "user_charlie"],
    "Rôle": ["Administrateur", "Utilisateur", "Utilisateur"],
    "Dernière connexion": ["Aujourd'hui", "Hier", "Il y a 10 jours"],
    "Statut": ["🟢 Actif", "🟢 Actif", "🔴 Inactif"]
})

# Affichage sous forme de tableau interactif
st.dataframe(utilisateurs, use_container_width=True, hide_index=True)

# Boutons d'action (visuels pour le moment)
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    st.button("➕ Nouvel utilisateur", type="primary")
with col2:
    st.button("🗑️ Supprimer")

st.divider()

# --- Section 2 : Journal d'activité (Logs) ---
st.header("📋 Journal d'activité récent")

# Création de faux historiques de navigation (Mock)
actions_possibles = ["Connexion", "Consultation F3", "Consultation F4", "Consultation F5", "Erreur 404", "Déconnexion"]
utilisateurs_possibles = ["admin_alice", "user_bob", "Visiteur Anonyme"]

logs = []
maintenant = datetime.now()

# On génère 15 fausses actions dans le passé
for _ in range(15):
    # On recule dans le temps de quelques minutes au hasard
    temps = maintenant - timedelta(minutes=random.randint(1, 300))
    logs.append({
        "Date et Heure": temps.strftime("%Y-%m-%d %H:%M:%S"),
        "Utilisateur": random.choice(utilisateurs_possibles),
        "Action": random.choice(actions_possibles)
    })

df_logs = pd.DataFrame(logs)
# On trie pour avoir les actions les plus récentes en haut
df_logs = df_logs.sort_values(by="Date et Heure", ascending=False)

st.dataframe(df_logs, use_container_width=True, hide_index=True)

if st.button("📥 Exporter les logs (CSV)"):
    st.success("Fonctionnalité d'export en cours de développement.")