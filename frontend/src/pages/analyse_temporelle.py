import pandas as pd
import plotly.express as px
import requests
import streamlit as st

<<<<<<< HEAD
from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import (
    INDICATEURS,
    SEXES,
    classifications_pour,
    get_pays,
    message_erreur,
)

get_page_logger("Analyse Temporelle (F3)")
=======
st.set_page_config(page_title="Analyse Temporelle", page_icon="📈")
>>>>>>> a7af81dcebcc3df8d50b14074d100037988a73e0

st.title("Analyse temporelle de l'emploi (F3) 📈")
st.write("Visualisez l'évolution des indicateurs sur une période donnée.")

<<<<<<< HEAD
pays_referentiel = get_pays()

# --- Ligne 1 : indicateur et sexe ---
col1, col2 = st.columns(2)

with col1:
    code_indicateur = st.selectbox(
        "Choisissez l'indicateur :",
        options=list(INDICATEURS),
        format_func=lambda code: INDICATEURS[code],
    )

with col2:
    libelle_sexe = st.selectbox("Sexe :", list(SEXES))

# --- Ligne 2 : classification (âge ou profession selon l'indicateur) ---
classifications = classifications_pour(code_indicateur)
libelle_classification = st.selectbox("Catégorie :", list(classifications))

# --- Ligne 3 : pays et profondeur temporelle ---
col3, col4 = st.columns(2)

with col3:
    noms_pays = st.multiselect(
        "Sélectionnez le(s) pays :",
        options=list(pays_referentiel),
        default=["France"] if "France" in pays_referentiel else [],
    )

with col4:
    nb_periodes = st.slider(
        "Période (dernières périodes) :", min_value=4, max_value=20, value=8
    )
=======
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
>>>>>>> a7af81dcebcc3df8d50b14074d100037988a73e0

    # --- TRAITEMENT DE LA RÉPONSE ---
    if reponse.status_code == 200:
        donnees_api = reponse.json()
        points = donnees_api.get("points", [])

<<<<<<< HEAD
if not noms_pays:
    st.warning("⚠️ Veuillez sélectionner au moins un pays pour afficher les données.")
    st.stop()

# --- Appel du backend : une série par pays via /analyses/evolution ---
lignes = []
pays_sans_donnees = []

for nom in noms_pays:
    reponse = api_client.get(
        "/analyses/evolution",
        params={
            "code_indicateur": code_indicateur,
            "code_pays": pays_referentiel[nom],
            "sexe": SEXES[libelle_sexe],
            "code_classification": classifications[libelle_classification],
            "nb_periodes": nb_periodes,
        },
    )

    if reponse["status_code"] == 200:
        for point in reponse["data"]["points"]:
            lignes.append(
                {"Période": point["periode"], "Pays": nom, "Valeur": point["valeur"]}
            )
    elif reponse["status_code"] == 404:
        pays_sans_donnees.append(nom)
    elif reponse["status_code"] == 0:
        st.error(f"❌ {message_erreur(reponse)}")
        st.stop()
    else:
        st.error(f"❌ {nom} : {message_erreur(reponse)}")

if pays_sans_donnees:
    st.warning("⚠️ Aucune donnée disponible pour : " + ", ".join(pays_sans_donnees))

if lignes:
    df = pd.DataFrame(lignes)
    fig = px.line(
        df,
        x="Période",
        y="Valeur",
        color="Pays",
        title=f"Évolution : {INDICATEURS[code_indicateur]} ({libelle_sexe})",
        markers=True,
    )
    st.plotly_chart(fig, use_container_width=True)
elif not pays_sans_donnees:
    st.info("Aucune donnée à afficher pour cette sélection.")
=======
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
>>>>>>> a7af81dcebcc3df8d50b14074d100037988a73e0
