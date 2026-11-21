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
    "Les indicateurs du marché du travail dans le monde. Source : ILOSTAT.",
    eyebrow="Observatoire de l'emploi",
)

st.markdown(
    "<div class='ls-eyebrow plain' style='margin-top:0.4rem'>Espace d'analyse</div>",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    with st.container(border=True):
        carte_navigation(
            ICONE_TENDANCE, "Évolution temporelle",
            tag="Accès libre",
            aide_texte="Suivez l'évolution d'un indicateur pour un ou plusieurs pays, "
                       "année après année.",
        )
        st.page_link("vues/analyse_temporelle.py", label="Ouvrir",
                     icon=":material/arrow_forward:")

with col2:
    with st.container(border=True):
        carte_navigation(
            ICONE_GLOBE, "Comparaison pays",
            tag="Accès libre" if est_connecte() else "Connexion requise",
            verrou=not est_connecte(),
            aide_texte="Comparez un indicateur entre plusieurs pays sur une année commune.",
        )
        if est_connecte():
            st.page_link("vues/comparaison_pays.py", label="Ouvrir",
                         icon=":material/arrow_forward:")
        else:
            st.page_link("vues/login.py", label="Se connecter", icon=":material/lock:")

with col3:
    with st.container(border=True):
        carte_navigation(
            ICONE_COUCHES, "Multi-indicateurs",
            tag="Accès libre" if est_connecte() else "Connexion requise",
            verrou=not est_connecte(),
            aide_texte="Superposez plusieurs indicateurs pour un même pays.",
        )
        if est_connecte():
            st.page_link("vues/comparaison_multi.py", label="Ouvrir",
                         icon=":material/arrow_forward:")
        else:
            st.page_link("vues/login.py", label="Se connecter", icon=":material/lock:")

if est_admin():
    st.write("")
    with st.container(border=True):
        carte_navigation(
            ICONE_REGLAGES, "Administration",
            tag="Administrateur",
            aide_texte="Comptes, imports ILOSTAT et journal d'activité.",
        )
        st.page_link("vues/admin.py", label="Ouvrir", icon=":material/arrow_forward:")
