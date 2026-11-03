import streamlit as st

from utils.env_variables import display_values, load_environment_variables
from utils.log_init import initialize_logs
from utils.ui import (
    ROLE_ADMIN,
    ROLE_UTILISATEUR,
    barre_laterale_bas,
    barre_laterale_haut,
    injecter_styles,
)

# La configuration de page doit être la toute première commande Streamlit.
st.set_page_config(
    page_title="LaborScope",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styles globaux (sobres, sans emoji) appliqués à chaque rerun.
injecter_styles()

# Initialisation (une seule fois par session)
if "logs_initialized" not in st.session_state:
    initialize_logs("Streamlit App")
    load_environment_variables()
    display_values(include_prefix="BACKEND")
    st.session_state["logs_initialized"] = True

# --- DÉCLARATION DE TOUTES LES PAGES ---
# Icônes Material (traits sobres, pas d'emoji) pour une navigation lisible.
page_accueil = st.Page("pages/home.py", title="Accueil", icon=":material/home:", default=True)
page_connexion = st.Page("pages/login.py", title="Connexion", icon=":material/lock:")
page_analyse_f3 = st.Page(
    "pages/analyse_temporelle.py", title="Évolution temporelle", icon=":material/trending_up:"
)
page_comparaison_f4 = st.Page(
    "pages/comparaison_pays.py", title="Comparaison pays", icon=":material/public:"
)
page_multi_f5 = st.Page(
    "pages/comparaison_multi.py", title="Multi-indicateurs", icon=":material/stacked_line_chart:"
)
page_admin = st.Page("pages/admin.py", title="Administration", icon=":material/settings:")

# --- BARRE LATÉRALE : branding (haut) ---
barre_laterale_haut()

# --- NAVIGATION SELON LE RÔLE ---
role = st.session_state.get("role_utilisateur")

if role == ROLE_ADMIN:
    pages = {
        "Espace d'analyse": [page_analyse_f3, page_comparaison_f4, page_multi_f5],
        "LaborScope": [page_accueil, page_connexion],
        "Administration": [page_admin],
    }
elif role == ROLE_UTILISATEUR:
    pages = {
        "Espace d'analyse": [page_analyse_f3, page_comparaison_f4, page_multi_f5],
        "LaborScope": [page_accueil, page_connexion],
    }
else:
    # Mode "sans connexion" : accueil, connexion et évolution temporelle (accès libre).
    pages = {
        "Espace d'analyse": [page_analyse_f3],
        "LaborScope": [page_accueil, page_connexion],
    }

pg = st.navigation(pages)

# --- BARRE LATÉRALE : promo + utilisateur (sous le menu) ---
barre_laterale_bas()

pg.run()
