import streamlit as st

from utils.log_init import get_page_logger
from utils.ui import (
    ICONE_COUCHES,
    ICONE_GLOBE,
    ICONE_REGLAGES,
    ICONE_TENDANCE,
    carte_navigation,
    entete,
    est_admin,
    est_connecte,
)

get_page_logger("Accueil")

entete(
    "LaborScope",
    "Explorez et comparez les indicateurs du marché du travail dans le monde (source : ILOSTAT).",
    eyebrow="Observatoire de l'emploi",
)

# --- Bandeau selon l'état de connexion ---
if est_connecte():
    nom = st.session_state.get("nom_utilisateur", "")
    st.success(
        f"Vous êtes connecté{' en tant que ' + nom if nom else ''}. "
        "Toutes vos analyses sont débloquées."
    )
else:
    st.info(
        "Vous êtes en **mode découverte**. L'analyse temporelle est en accès libre ; "
        "connectez-vous pour débloquer les comparaisons entre pays et multi-indicateurs."
    )

st.markdown(
    "<div class='ls-eyebrow plain' style='margin-top:0.6rem'>Espace d'analyse</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='ls-serif' style='font-size:1.6rem;margin-bottom:0.8rem'>"
    "Que souhaitez-vous faire&nbsp;?</div>",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    with st.container(border=True):
        carte_navigation(
            ICONE_TENDANCE, "Évolution temporelle",
            "Suivez l'évolution d'un indicateur pour un ou plusieurs pays.",
            tag="Accès libre",
        )
        st.page_link("pages/analyse_temporelle.py", label="Ouvrir l'analyse",
                     icon=":material/arrow_forward:")

with col2:
    with st.container(border=True):
        carte_navigation(
            ICONE_GLOBE, "Comparaison pays",
            "Comparez un indicateur entre plusieurs pays sur une année commune.",
            tag="Accès libre" if est_connecte() else "Connexion requise",
            verrou=not est_connecte(),
        )
        if est_connecte():
            st.page_link("pages/comparaison_pays.py", label="Ouvrir la comparaison",
                         icon=":material/arrow_forward:")
        else:
            st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")

with col3:
    with st.container(border=True):
        carte_navigation(
            ICONE_COUCHES, "Multi-indicateurs",
            "Superposez plusieurs indicateurs pour un même pays.",
            tag="Accès libre" if est_connecte() else "Connexion requise",
            verrou=not est_connecte(),
        )
        if est_connecte():
            st.page_link("pages/comparaison_multi.py", label="Ouvrir le croisement",
                         icon=":material/arrow_forward:")
        else:
            st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")

if est_admin():
    st.write("")
    with st.container(border=True):
        carte_navigation(
            ICONE_REGLAGES, "Administration",
            "Gérez les comptes, lancez les imports ILOSTAT et suivez l'activité.",
            tag="Administrateur", verrou=False,
        )
        st.page_link("pages/admin.py", label="Ouvrir l'espace admin",
                     icon=":material/arrow_forward:")

st.divider()

with st.expander("Niveaux d'accès"):
    st.markdown(
        """
        | Fonctionnalité | Sans connexion | Utilisateur | Administrateur |
        |---|:---:|:---:|:---:|
        | Analyse temporelle | Oui | Oui | Oui |
        | Comparaison pays | — | Oui | Oui |
        | Multi-indicateurs | — | Oui | Oui |
        | Administration | — | — | Oui |
        """
    )
