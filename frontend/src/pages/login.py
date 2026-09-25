import streamlit as st

st.title("Connexion à LaborScope 🔒")

# Faux système de connexion pour tester le menu
col1, col2 = st.columns(2)

with col1:
    if st.button("Se connecter en Utilisateur"):
        st.session_state["role_utilisateur"] = "Utilisateur"
        st.rerun()

with col2:
    if st.button("Se connecter en Administrateur"):
        st.session_state["role_utilisateur"] = "Administrateur"
        st.rerun()

# Bouton de déconnexion si déjà connecté
if "role_utilisateur" in st.session_state:
    st.success(f"Vous êtes connecté en tant que : {st.session_state['role_utilisateur']}")
    if st.button("Se déconnecter"):
        del st.session_state["role_utilisateur"]
        st.rerun()