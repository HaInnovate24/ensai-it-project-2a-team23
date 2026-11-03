import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import get_indicateurs, message_erreur
from utils.ui import entete, est_admin

get_page_logger("Administration (F6)")

# Garde-fou : la navigation masque déjà cette page, mais on protège l'accès
# direct par URL.
if not est_admin():
    st.title("Administration")
    st.warning("Accès réservé aux administrateurs.")
    st.stop()

entete(
    "Administration",
    "Gérez les accès utilisateurs, lancez des imports et consultez le journal.",
    eyebrow="Espace réservé",
)


def _corps(reponse: dict) -> dict:
    """Renvoie le corps JSON d'une réponse s'il s'agit d'un objet, sinon {}."""
    return reponse["data"] if isinstance(reponse["data"], dict) else {}


# --- Section 1 : utilisateurs ---
st.subheader("Gestion des utilisateurs")

reponse = api_client.get("/admin/utilisateurs")
if reponse["status_code"] == 200:
    utilisateurs = _corps(reponse).get("data") or []
    if utilisateurs:
        df = pd.DataFrame(utilisateurs)
        # On masque le hash du mot de passe s'il est présent dans la réponse.
        df = df.drop(columns=["mot_de_passe_hash"], errors="ignore")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun utilisateur à afficher.")
else:
    st.error(message_erreur(reponse))

st.divider()

# --- Section 2 : imports ILOSTAT ---
st.subheader("Imports de données")

indicateurs = get_indicateurs()
col1, col2 = st.columns([3, 1])
with col1:
    code_indicateur = st.selectbox(
        "Indicateur à importer :",
        options=list(indicateurs),
        format_func=lambda code: indicateurs[code],
    )
with col2:
    st.write("")
    st.write("")
    lancer = st.button("Lancer l'import", type="primary")

if lancer:
    with st.spinner("Import en cours (téléchargement ILOSTAT)…"):
        reponse = api_client.post(f"/admin/imports/{code_indicateur}", timeout=120)
    if reponse["status_code"] == 200:
        corps = _corps(reponse)
        st.success(
            f"{corps.get('message', 'Import terminé')} — "
            f"statut : {corps.get('statut')}, lignes insérées : {corps.get('lignes_inserees')}"
        )
    else:
        st.error(message_erreur(reponse))

st.subheader("Historique des imports")
reponse = api_client.get("/admin/imports")
if reponse["status_code"] == 200:
    imports = _corps(reponse).get("data") or []
    if imports:
        st.dataframe(pd.DataFrame(imports), use_container_width=True, hide_index=True)
    else:
        st.info("Aucun import enregistré.")
else:
    st.error(message_erreur(reponse))

st.divider()

# --- Section 3 : journal d'activité ---
st.subheader("Journal d'activité récent")

reponse = api_client.get("/admin/journal")
if reponse["status_code"] == 200:
    journal = _corps(reponse).get("data") or []
    if journal:
        st.dataframe(pd.DataFrame(journal), use_container_width=True, hide_index=True)
    else:
        st.info("Le journal d'activité n'est pas encore disponible.")
else:
    st.warning(f"Journal indisponible ({message_erreur(reponse)}).")
