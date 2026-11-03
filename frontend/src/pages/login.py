import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import message_erreur
from utils.ui import deconnexion, entete

get_page_logger("Connexion")

entete(
    "Connexion",
    "Connectez-vous ou créez un compte pour accéder aux analyses avancées.",
    eyebrow="Votre espace",
)

# Correspondance rôle renvoyé par le backend -> libellé attendu par la
# navigation (app.py).
_ROLES = {"admin": "Administrateur", "utilisateur": "Utilisateur"}


def _corps(reponse: dict) -> dict:
    """Renvoie le corps JSON d'une réponse s'il s'agit d'un objet, sinon {}."""
    return reponse["data"] if isinstance(reponse["data"], dict) else {}


def _charger_profil(jeton: str) -> bool:
    """Alimente la session à partir du profil associé au jeton.

    Renvoie True si le profil a pu être récupéré.
    """
    reponse = api_client.get("/auth/profil", params={"jeton": jeton})
    if reponse["status_code"] != 200:
        return False

    utilisateur = _corps(reponse).get("data") or {}
    st.session_state["role_utilisateur"] = _ROLES.get(utilisateur.get("role"), "Utilisateur")
    st.session_state["nom_utilisateur"] = utilisateur.get("nom_utilisateur")
    return True


# --- Déjà connecté : on affiche le statut et la déconnexion ---
if st.session_state.get("access_token"):
    st.success(
        f"Vous êtes connecté en tant que **{st.session_state.get('nom_utilisateur', '?')}** "
        f"({st.session_state.get('role_utilisateur', 'Utilisateur')})."
    )
    if st.button("Se déconnecter"):
        deconnexion()
    st.stop()

# --- Non connecté : connexion ou création de compte ---
onglet_connexion, onglet_inscription = st.tabs(["Se connecter", "Créer un compte"])

with onglet_connexion:
    with st.form("connexion"):
        nom = st.text_input("Nom d'utilisateur")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        valider = st.form_submit_button("Se connecter")

    if valider:
        reponse = api_client.post(
            "/auth/connexion",
            json={"nom_utilisateur": nom, "mot_de_passe": mot_de_passe},
        )
        if reponse["status_code"] == 200:
            data = _corps(reponse).get("data")
            jeton = data.get("jeton") if isinstance(data, dict) else data
            if not jeton:
                st.error("Jeton de connexion introuvable dans la réponse.")
            else:
                # La connexion a réussi : on est authentifié.
                st.session_state["access_token"] = jeton
                if not _charger_profil(jeton):
                    # Profil illisible (ex. endpoint /auth/profil indisponible) :
                    # on ouvre une session en rôle standard par défaut.
                    st.session_state["role_utilisateur"] = "Utilisateur"
                    st.session_state["nom_utilisateur"] = nom
                st.rerun()
        else:
            st.error(message_erreur(reponse))

with onglet_inscription:
    with st.form("inscription"):
        nouveau_nom = st.text_input("Nom d'utilisateur", key="inscription_nom")
        nouveau_mdp = st.text_input("Mot de passe", type="password", key="inscription_mdp")
        st.caption("8 à 128 caractères, au moins une lettre et un chiffre.")
        creer = st.form_submit_button("Créer le compte")

    if creer:
        reponse = api_client.post(
            "/auth/inscription",
            json={"nom_utilisateur": nouveau_nom, "mot_de_passe": nouveau_mdp},
        )
        if reponse["status_code"] == 200:
            st.success("Compte créé. Vous pouvez maintenant vous connecter.")
        else:
            st.error(message_erreur(reponse))
