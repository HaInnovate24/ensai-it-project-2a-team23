from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import (
    SEXES,
    get_classifications,
    get_indicateurs,
    get_pays,
    index_defaut,
    libelle_type_classification,
    message_erreur,
    unite_indicateur,
)
from utils.ui import (
    PALETTE_GRAPHIQUE,
    afficher_graphique,
    entete,
    entete_graphique,
    fmt_fr,
    ligne_source,
    styliser_figure,
)

get_page_logger("Analyse Temporelle (F3)")

entete(
    "L'emploi au fil du temps.",
    "Visualisez l'évolution d'un indicateur sur plusieurs années.",
    eyebrow="Explorateur de données · ILOSTAT",
)

ligne_source(["Données réelles", "OIT · diffusion ILOSTAT"], f"Extrait du {date.today():%d/%m/%Y}")

indicateurs = get_indicateurs()
pays_referentiel = get_pays()

# --- Carte de filtres ---
with st.container(border=True):
    col1, col2, col3 = st.columns([1.2, 1, 1])
    with col1:
        code_indicateur = st.selectbox(
            "Indicateur",
            options=list(indicateurs),
            format_func=lambda code: indicateurs[code],
        )
    with col2:
        libelle_sexe = st.selectbox("Sexe", list(SEXES))
    with col3:
        label_classif = libelle_type_classification(code_indicateur)
        classifications = get_classifications(code_indicateur)
        libelle_classification = st.selectbox(
            label_classif, list(classifications), index=index_defaut(classifications)
        )

    col4, col5 = st.columns([1.5, 1])
    with col4:
        noms_pays = st.multiselect(
            "Pays",
            options=list(pays_referentiel),
            default=["France"] if "France" in pays_referentiel else [],
        )
    with col5:
        nb_periodes = st.slider("Nombre d'années", min_value=1, max_value=13, value=10)

st.write("")

if not noms_pays:
    st.warning("Sélectionnez au moins un pays pour afficher les données.")
    st.stop()

# --- Appel du backend : une série par pays via /analyses/evolution ---
lignes = []
pays_sans_donnees = []

with st.spinner("Chargement des données…"):
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
    with st.container(border=True):
        entete_graphique(
            "Évolution temporelle",
            indicateurs[code_indicateur],
            f"{libelle_classification} · {libelle_sexe} · {nb_periodes} dernières années",
        )
        fig = px.line(
            df,
            x="Période",
            y="Valeur",
            color="Pays",
            markers=True,
            labels={"Valeur": f"Valeur ({unite})" if unite else "Valeur"},
            color_discrete_sequence=PALETTE_GRAPHIQUE,
        )
        fig.update_xaxes(type="category")
        fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
        styliser_figure(fig)
        afficher_graphique(fig)
        with st.expander("Voir les données"):
            st.dataframe(
                df.pivot_table(index="Période", columns="Pays", values="Valeur"),
                use_container_width=