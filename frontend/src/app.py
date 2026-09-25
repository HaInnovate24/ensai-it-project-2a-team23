import streamlit as st
from utils.env_variables import display_values, load_environment_variables
from utils.log_init import initialize_logs

# Initialisation
if "logs_initialized" not in st.session_state:
    initialize_logs("Streamlit App")
    load_environment_variables()
    display_values(include_prefix="BACKEND")
    st.session_state["logs_initialized"] = True

# --- DÉCLARATION DE TOUTES LES PAGES ---
page_accueil = st.Page("pages/home.py", title="Accueil", icon="🏠", default=True)
page_connexion = st.Page("pages/login.py", title="Connexion", icon="🔒")
page_analyse_f3 = st.Page("pages/analyse_temporelle.py", title="Analyse Temporelle (F3)", icon="📈")
page_comparaison_f4 = st.Page("pages/comparaison_pays.py", title="Comparaison Pays (F4)", icon="🌍")
page_multi_f5 = st.Page("pages/comparaison_multi.py", title="Multi-indicateurs (F5)", icon="📊")
page_admin = st.Page("pages/admin.py", title="Administration (F6)", icon="⚙️")

# --- LOGIQUE D'AFFICHAGE SELON LE RÔLE ---
if "role_utilisateur" not in st.session_state:
    # Mode "Sans connexion" : accès libre à l'accueil et à l'analyse temporelle (F3)
    pg = st.navigation({
        "LaborScope": [page_accueil, page_connexion],
        "Découverte (Accès libre)": [page_analyse_f3]
    })

elif st.session_state["role_utilisateur"] == "Utilisateur":
    # Mode "Utilisateur connecté" : accès à F3, F4, F5 (sans l'admin)
    pg = st.navigation({
        "LaborScope": [page_accueil],
        "Analyses Avancées": [page_analyse_f3, page_comparaison_f4, page_multi_f5]
    })

elif st.session_state["role_utilisateur"] == "Administrateur":
    # Mode "Administrateur" : accès total
    pg = st.navigation({
        "LaborScope": [page_accueil],
        "Analyses Avancées": [page_analyse_f3, page_comparaison_f4, page_multi_f5],
        "Espace Administration": [page_admin]
    })

pg.run()