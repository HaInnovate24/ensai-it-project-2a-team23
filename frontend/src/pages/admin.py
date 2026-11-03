import pandas as pd
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import INDICATEURS, message_erreur

get_page_logger("Administration (F6)")

st.title("Espace Administration (F6) ⚙️")

# Garde-fou : la navigation masque déjà cette page, mais on protège l'accès
# direct par URL.
if st.session_state.get("role_utilisateur") != "Administrateur":
    st.warning("⚠️ Accès réservé aux administrateurs.")
    st.stop()

st.write("Gérez les accès utilisateurs et consultez le journal d'activité de la plateforme.")


def _corps(reponse: dict) -> dict:
    """Renvoie le corps JSON d'une réponse s'il s'agit d'un objet, sinon {}."""
    return reponse["data"] if isinstance(reponse["data"], dict) else {}


# --- Section 1 : utilisateurs ---
st.header("👥 Gestion des utilisateurs")

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
    st.error(f"❌ {message_erreur(reponse)}")

st.divider()

# --- Section 2 : imports ILOSTAT ---
st.header("📥 Imports de données")

col1, col2 = st.columns([3, 1])
with col1:
    code_indicateur = st.selectbox(
        "Indicateur à importer :",
        options=list(INDICATEURS),
        format_func=lambda code: INDICATEURS[code],
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
            f"✅ {corps.get('message', 'Import terminé')} — "
            f"statut : {corps.get('statut')}, lignes insérées : {corps.get('lignes_inserees')}"
        )
    else:
        st.error(f"❌ {message_erreur(reponse)}")

st.subheader("Historique des imports")
reponse = api_client.get("/admin/imports")
if reponse["status_code"] == 200:
    imports = _corps(reponse).get("data") or []
    if imports:
        st.dataframe(pd.DataFrame(imports), use_container_width=True, hide_index=True)
    else:
        st.info("Aucun import enregistré.")
else:
    st.error(f"❌ {message_erreur(reponse)}")

st.divider()

# --- Section 3 : journal d'activité ---
st.header("📋 Journal d'activité récent")

reponse = api_client.get("/admin/journal")
if reponse["status_code"] == 200:
    journal = _corps(reponse).get("data") or []
    if journal:
        st.dataframe(pd.DataFrame(journal), use_container_width=True, hide_index=True)
    else:
        st.info("Le journal d'activité n'est pas encore disponible.")
else:
    st.warning(f"Journal indisponible ({message_erreur(reponse)}).")
