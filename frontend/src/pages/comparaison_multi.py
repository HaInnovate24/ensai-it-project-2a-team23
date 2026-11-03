import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger

get_page_logger("Multi-indicateurs (F5)")

st.set_page_config(page_title="Comparaison Multi-indicateurs", page_icon="📊")

st.title("Comparaison Multi-indicateurs (F5) 📊")
st.write(
    "Superposez plusieurs indicateurs sur un même graphique pour dégager visuellement des liens."
)

# --- Filtres de recherche ---
with st.expander("🛠️ Filtres de recherche", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        dict_pays = {
            "France": "FRA",
            "Allemagne": "DEU",
            "Espagne": "ESP",
            "Italie": "ITA",
        }
        nom_pays = st.selectbox("Sélectionnez un pays cible :", options=list(dict_pays.keys()))
        code_pays = dict_pays[nom_pays]

        dict_sexes = {
            "Total": "total",
            "Hommes": "homme",
            "Femmes": "femme",
        }
        nom_sexe = st.selectbox("Sexe :", options=list(dict_sexes.keys()))
        code_sexe = dict_sexes[nom_sexe]

    with col2:
        dict_indicateurs = {
            "Emploi par sexe et profession": "EMP_TEMP_SEX_OCU_NB",
            "Population en âge de travailler": "POP_XWAP_SEX_AGE_NB",
        }
        noms_indicateurs = st.multiselect(
            "Sélectionnez les indicateurs à croiser :",
            options=list(dict_indicateurs.keys()),
            default=list(dict_indicateurs.keys()),
        )
        codes_indicateur = [dict_indicateurs[nom] for nom in noms_indicateurs]

        dict_classifications = {
            "Total": "TOTAL",
        }
        nom_classification = st.selectbox("Catégorie :", options=list(dict_classifications.keys()))
        code_classification = dict_classifications[nom_classification]

st.divider()

if not codes_indicateur:
    st.warning("⚠️ Veuillez sélectionner au moins un indicateur pour générer le graphique.")
    st.stop()

# --- Appel du backend ---
reponse = api_client.get(
    "/analyses/comparaison-indicateurs",
    params={
        "codes_indicateur": codes_indicateur,
        "code_pays": code_pays,
        "sexe": code_sexe,
        "code_classification": code_classification,
    },
)

status_code = reponse.get("status_code", 0)
donnees = reponse.get("data", {})

if status_code == 404:
    st.warning("⚠️ Aucune donnée disponible pour cette sélection.")
    st.stop()

if status_code != 200:
    # Si 'donnees' est un dict et contient un message d'erreur spécifique, on l'affiche
    msg = donnees.get("detail", donnees) if isinstance(donnees, dict) else donnees
    st.error(f"❌ Erreur du serveur backend ({status_code}) : {msg}")
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

df = pd.DataFrame(lignes)

fig = px.line(
    df,
    x="Période",
    y="Valeur",
    color="Indicateur",
    title=f"Croisement des indicateurs pour : {nom_pays}",
    markers=True,
)

st.plotly_chart(fig, use_container_width=True)