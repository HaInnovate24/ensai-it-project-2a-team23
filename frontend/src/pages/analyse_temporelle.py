import pandas as pd
import plotly.express as px
import streamlit as st
from utils.api_client import api_client

st.set_page_config(page_title="Analyse Temporelle", page_icon="📈")

st.title("Analyse temporelle de l'emploi (F3) 📈")
st.write("Visualisez l'évolution des indicateurs sur une période donnée.")

# --- FILTRES DE RECHERCHE ---
with st.expander("🛠️ Filtres de recherche", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        dict_indicateurs = {
            "Emploi par sexe et profession": "EMP_TEMP_SEX_OCU_NB",
            "Population en âge de travailler": "POP_XWAP_SEX_AGE_NB",
        }
        nom_indicateur = st.selectbox(
            "Choisissez l'indicateur :", options=list(dict_indicateurs.keys())
        )
        code_indicateur = dict_indicateurs[nom_indicateur]

    with col2:
        dict_pays = {
            "France": "FRA",
            "Allemagne": "DEU",
            "Espagne": "ESP",
            "Italie": "ITA",
        }
        nom_pays = st.selectbox(
            "Sélectionnez le pays :", options=list(dict_pays.keys())
        )
        code_pays = dict_pays[nom_pays]

    nb_trimestres = st.slider(
        "Période (derniers trimestres) :",
        min_value=1,
        max_value=40,
        value=8,
    )

st.markdown("---")

# --- APPEL API BACKEND ---
reponse = api_client.get(
    "/analyses/evolution",
    params={
        "code_indicateur": code_indicateur,
        "code_pays": code_pays,
        "nb_trimestres": nb_trimestres,
    },
)

status_code = reponse.get("status_code", 0)
donnees_api = reponse.get("data")

# --- TRAITEMENT DE LA RÉPONSE ---
if status_code == 200 and isinstance(donnees_api, dict):
    points = donnees_api.get("points", [])

    if not points:
        st.info("📊 L'indicateur existe en base mais aucune donnée trimestrielle n'est associée pour ce filtre.")
    else:
        df = pd.DataFrame(points)
        titre_graphique = donnees_api.get("libelle", f"{nom_indicateur} - {nom_pays}")

        col_x = "periode" if "periode" in df.columns else df.columns[0]
        col_y = "valeur" if "valeur" in df.columns else df.columns[1]

        fig = px.line(
            df,
            x=col_x,
            y=col_y,
            markers=True,
            title=titre_graphique,
            labels={col_x: "Période", col_y: "Valeur"},
        )
        st.plotly_chart(fig, use_container_width=True)

elif status_code == 404:
    st.warning("⚠️ Aucune donnée trouvée pour cette combinaison d'indicateur et de pays.")
elif status_code == 0:
    st.error(f"❌ Impossible de joindre le backend : {donnees_api}")
else:
    st.error(f"❌ Erreur du serveur backend ({status_code}) : {donnees_api}")