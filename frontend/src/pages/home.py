import streamlit as st

from utils.log_init import get_page_logger
from utils.ui import entete, est_admin, est_connecte

get_page_logger("Accueil")

entete(
    "LaborScope",
    "Explorez et comparez les indicateurs du marché du travail dans le monde "
    "(source : ILOSTAT).",
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

st.subheader("Que souhaitez-vous faire ?")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("#### Évolution temporelle")
        st.write("Suivez l'évolution d'un indicateur pour un ou plusieurs pays.")
        st.caption("Accès libre")
        st.page_link(
            "pages/analyse_temporelle.py", label="Ouvrir", icon=":material/trending_up:"
        )

with col2:
    with st.container(border=True):
        st.markdown("#### Comparaison pays")
        st.write("Comparez un indicateur entre plusieurs pays sur la dernière période.")
        st.caption("Connexion requise")
        if est_connecte():
            st.page_link(
                "pages/comparaison_pays.py", label="Ouvrir", icon=":material/public:"
            )
        else:
            st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")

with col3:
    with st.container(border=True):
        st.markdown("#### Multi-indicateurs")
        st.write("Superposez plusieurs indicateurs pour un même pays.")
        st.caption("Connexion requise")
        if est_connecte():
            st.page_link(
                "pages/comparaison_multi.py",
                label="Ouvrir",
                icon=":material/stacked_line_chart:",
            )
        else:
            st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")

if est_admin():
    st.write("")
    with st.container(border=True):
        st.markdown("#### Administration")
        st.write(
            "Gérez les utilisateurs, lancez des imports ILOSTAT et consultez le journal."
        )
        st.page_link(
            "pages/admin.py", label="Ouvrir l'espace admin", icon=":material/settings:"
        )

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
