import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Analyse Temporelle", page_icon="📈")

st.title("Analyse temporelle de l'emploi (F3) 📈")
st.write("Visualisez l'évolution des indicateurs sur une période donnée.")

# --- FILTRES DE RECHERCHE ---
with st.expander("🛠️ Filtres de recherche", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        # Correspondance exacte avec les codes présents dans votre base de données
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
# Remarque : Si le routeur backend utilise le préfixe /analyses, l'URL est http://localhost:5000/analyses/evolution
API_URL = "http://localhost:5000/analyses/evolution"

try:
    reponse = requests.get(
        API_URL,
        params={
            "code_indicateur": code_indicateur,
            "code_pays": code_pays,
            "nb_trimestres": nb_trimestres,
        },
        timeout=5,
    )

    # Si le préfixe /analyses n'est pas utilisé par le routeur, tente la route directe en secours
    if reponse.status_code == 404:
        reponse_secours = requests.get(
            "http://localhost:5000/evolution",
            params={
                "code_indicateur": code_indicateur,
                "code_pays": code_pays,
                "nb_trimestres": nb_trimestres,
            },
            timeout=5,
        )
        if reponse_secours.status_code != 404:
            reponse = reponse_secours

    # --- TRAITEMENT DE LA RÉPONSE ---
    if reponse.status_code == 200:
        donnees_api = reponse.json()
        points = donnees_api.get("points", [])

        if not points:
            st.info(
                "📊 L'indicateur existe en base mais aucune donnée trimestrielle n'est associée pour ce filtre."
            )
        else:
            df = pd.DataFrame(points)
            titre_graphique = donnees_api.get(
                "libelle", f"{nom_indicateur} - {nom_pays}"
            )

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

    elif reponse.status_code == 404:
        st.warning(
            "⚠️ Aucune donnée trouvée pour cette combinaison d'indicateur et de pays."
        )
    else:
        st.error(
            f"❌ Erreur du serveur backend ({reponse.status_code}) : {reponse.text}"
        )

except requests.exceptions.ConnectionError:
    st.error(
        "❌ Impossible de joindre le backend. Vérifiez qu'il tourne bien sur http://localhost:5000."
    )
