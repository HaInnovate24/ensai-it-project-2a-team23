import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
<<<<<<< HEAD

get_page_logger("Multi-indicateurs (F5)")

st.set_page_config(page_title="Comparaison Multi-indicateurs", page_icon="📊")

st.title("Comparaison Multi-indicateurs (F5) 📊")
st.write(
=======
from utils.referentiels import (
    SEXES,
    get_classifications_toutes,
    get_indicateurs,
    get_pays,
    index_defaut,
    message_erreur,
)
from utils.ui import PALETTE_GRAPHIQUE, entete, est_connecte, styliser_figure

get_page_logger("Multi-indicateurs (F5)")

entete(
    "Comparaison multi-indicateurs",
>>>>>>> f4d753ee7f00cfbed40afdc2538dda2d69849181
    "Superposez plusieurs indicateurs sur un même graphique pour dégager "
    "visuellement des liens.",
    eyebrow="Analyse",
)

# Cette analyse exige une connexion (le backend attend un jeton).
if not est_connecte():
    st.info("Connectez-vous pour accéder à la comparaison multi-indicateurs.")
    st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")
    st.stop()

indicateurs = get_indicateurs()
pays_referentiel = get_pays()

# --- Filtres de recherche ---
with st.expander("🛠️ Filtres de recherche", expanded=True):
    col1, col2 = st.columns(2)

with col1:
    nom_pays = st.selectbox("Pays cible :", options=list(pays_referentiel))

with col2:
    libelle_sexe = st.selectbox("Sexe :", list(SEXES))

codes_indicateur = st.multiselect(
    "Indicateurs à croiser :",
    options=list(indicateurs),
    format_func=lambda code: indicateurs[code],
    default=list(indicateurs),
)

# L'API applique une seule classification à tous les indicateurs : chaque
# indicateur n'apparaîtra que s'il possède des données pour cette catégorie.
classifications = get_classifications_toutes()
libelle_classification = st.selectbox(
    "Catégorie (âge ou profession) :",
    list(classifications),
    index=index_defaut(classifications),
)

st.divider()

if not codes_indicateur:
    st.warning("Sélectionnez au moins un indicateur pour générer le graphique.")
    st.stop()

# --- Appel du backend ---
reponse = api_client.get(
    "/analyses/comparaison-indicateurs",
    params={
        "jeton": st.session_state.get("access_token"),
        "codes_indicateur": codes_indicateur,
        "code_pays": code_pays,
        "sexe": code_sexe,
        "code_classification": code_classification,
    },
)

<<<<<<< HEAD
status_code = reponse.get("status_code", 0)
donnees = reponse.get("data", {})

if status_code == 404:
    st.warning("⚠️ Aucune donnée disponible pour cette sélection.")
    st.stop()

if status_code != 200:
    # Si 'donnees' est un dict et contient un message d'erreur spécifique, on l'affiche
    msg = donnees.get("detail", donnees) if isinstance(donnees, dict) else donnees
    st.error(f"❌ Erreur du serveur backend ({status_code}) : {msg}")
=======
if reponse["status_code"] == 404:
    st.warning("Aucune donnée disponible pour cette sélection.")
    st.stop()

if reponse["status_code"] in (401, 403):
    st.error("Session expirée ou accès refusé. Reconnectez-vous pour continuer.")
    st.stop()

if reponse["status_code"] != 200:
    st.error(message_erreur(reponse))
>>>>>>> f4d753ee7f00cfbed40afdc2538dda2d69849181
    st.stop()

# --- Traitement des données ---
lignes = []
for serie in donnees.get("series", []):
    for point in serie.get("points", []):
        lignes.append(
            {
                "Période": point["periode"],
                "Indicateur": serie["libelle"],
                "Valeur": point["valeur"]
            }
        )

if not lignes:
    st.info("📊 Aucune donnée à afficher pour cette sélection.")
    st.stop()

df = pd.DataFrame(lignes).sort_values("Période")

fig = px.line(
    df,
    x="Période",
    y="Valeur",
    color="Indicateur",
    title=f"Croisement des indicateurs pour : {nom_pays}",
    markers=True,
    color_discrete_sequence=PALETTE_GRAPHIQUE,
)
fig.update_xaxes(type="category")
styliser_figure(fig)

st.plotly_chart(fig, use_container_width=True)
