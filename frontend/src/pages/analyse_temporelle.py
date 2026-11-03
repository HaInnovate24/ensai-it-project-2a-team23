import pandas as pd
import plotly.express as px
import streamlit as st
from utils.api_client import api_client

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

st.title("Analyse temporelle de l'emploi (F3) 📈")
st.write("Visualisez l'évolution des indicateurs sur une période donnée.")

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

st.divider()

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
