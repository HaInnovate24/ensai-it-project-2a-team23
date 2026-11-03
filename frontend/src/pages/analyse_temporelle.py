import pandas as pd
import plotly.express as px
import streamlit as st
from utils.api_client import api_client

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import (
    SEXES,
    get_classifications,
    get_indicateurs,
    get_pays,
    index_defaut,
    message_erreur,
    unite_indicateur,
)
from utils.ui import PALETTE_GRAPHIQUE, entete, styliser_figure

get_page_logger("Analyse Temporelle (F3)")

entete(
    "Analyse temporelle",
    "Visualisez l'évolution d'un indicateur sur plusieurs années.",
    eyebrow="Analyse",
)

indicateurs = get_indicateurs()
pays_referentiel = get_pays()

# --- Ligne 1 : indicateur et sexe ---
col1, col2 = st.columns(2)

with col1:
    code_indicateur = st.selectbox(
        "Indicateur :",
        options=list(indicateurs),
        format_func=lambda code: indicateurs[code],
    )

with col2:
    libelle_sexe = st.selectbox("Sexe :", list(SEXES))

# --- Ligne 2 : classification (âge ou profession selon l'indicateur) ---
classifications = get_classifications(code_indicateur)
libelle_classification = st.selectbox(
    "Catégorie :", list(classifications), index=index_defaut(classifications)
)

# --- Ligne 3 : pays et profondeur temporelle ---
col3, col4 = st.columns(2)

with col3:
    noms_pays = st.multiselect(
        "Pays :",
        options=list(pays_referentiel),
        default=["France"] if "France" in pays_referentiel else [],
    )

with col4:
    nb_periodes = st.slider(
        "Nombre d'années à afficher :", min_value=1, max_value=13, value=10
    )

st.divider()

if not noms_pays:
    st.warning("Sélectionnez au moins un pays pour afficher les données.")
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
        st.error(message_erreur(reponse))
        st.stop()
    else:
        st.error(f"{nom} : {message_erreur(reponse)}")

if pays_sans_donnees:
    st.warning("Aucune donnée disponible pour : " + ", ".join(pays_sans_donnees))

if lignes:
    unite = unite_indicateur(code_indicateur)
    df = pd.DataFrame(lignes).sort_values("Période")
    fig = px.line(
        df,
        x="Période",
        y="Valeur",
        color="Pays",
        title=f"Évolution : {indicateurs[code_indicateur]} ({libelle_sexe})",
        markers=True,
        labels={"Valeur": f"Valeur ({unite})" if unite else "Valeur"},
        color_discrete_sequence=PALETTE_GRAPHIQUE,
    )
    fig.update_xaxes(type="category")
    styliser_figure(fig)
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Voir les données"):
        st.dataframe(
            df.pivot_table(index="Période", columns="Pays", values="Valeur"),
            use_container_width=True,
        )
elif not pays_sans_donnees:
    st.info("Aucune donnée à afficher pour cette sélection.")
