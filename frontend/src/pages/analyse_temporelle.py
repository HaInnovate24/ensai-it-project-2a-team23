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
from utils.ui import PALETTE_GRAPHIQUE, entete, ligne_source, styliser_figure

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
            lignes.append({"Période": point["periode"], "Pays": nom, "Valeur": point["valeur"]})
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
        st.markdown(
            "<div class='ls-eyebrow plain'>Évolution temporelle</div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='ls-serif' style='font-size:1.5rem'>{indicateurs[code_indicateur]}</div>",
            unsafe_allow_html=True,
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
                use_container_width=True,
            )

    # --- Rapport PDF : chiffres de synthèse + détail de toutes les valeurs ---
    suffixe = f" {unite}" if unite else ""
    chiffres_pdf = []
    for nom in noms_pays:
        sous = df[df["Pays"] == nom].sort_values("Période")
        if sous.empty:
            continue
        variation = sous.iloc[-1]["Valeur"] - sous.iloc[0]["Valeur"]
        chiffres_pdf.append((
            f"{nom} · variation",
            ("+" if variation > 0 else "") + f"{fmt_fr(variation)}{suffixe}",
        ))
    # Détail : toutes les valeurs, par période et par pays.
    pivot = df.pivot_table(index="Période", columns="Pays", values="Valeur").sort_index()
    colonnes_pdf = ["Période"] + [str(c) for c in pivot.columns]
    lignes_pdf = [
        [str(idx)] + [fmt_fr(v) if pd.notna(v) else "—" for v in row]
        for idx, row in pivot.iterrows()
    ]
    annees = sorted(df["Période"].unique())
    pdf_bytes = construire_rapport_pdf(
        titre="Évolution temporelle",
        sous_titre=indicateurs[code_indicateur],
        contexte=[
            ("Indicateur", indicateurs[code_indicateur]),
            ("Pays", ", ".join(noms_pays)),
            ("Période", f"{annees[0]} - {annees[-1]}" if annees else "—"),
            ("Catégorie", libelle_classification),
            ("Sexe", libelle_sexe),
        ],
        colonnes=colonnes_pdf,
        lignes=lignes_pdf,
        chiffres=chiffres_pdf[:3] or None,
        note=(
            f"Évolution de « {indicateurs[code_indicateur].lower()} » sur "
            f"{len(annees)} période(s) pour {len(noms_pays)} pays. "
            f"Valeurs exprimées en {unite.lower()}." if unite else
            f"Évolution sur {len(annees)} période(s) pour {len(noms_pays)} pays."
        ),
        image_png=figure_png(fig),
        legende_graphique=f"{libelle_classification} · {libelle_sexe} · {nb_periodes} dernières années",
    )
    _, col_pdf = st.columns([0.7, 0.3])
    with col_pdf:
        st.download_button(
            "Rapport PDF",
            data=pdf_bytes,
            file_name=f"rapport_evolution_{code_indicateur}.pdf",
            mime="application/pdf",
            icon=":material/picture_as_pdf:",
            use_container_width=True,
        )
elif not pays_sans_donnees:
    st.info("Aucune donnée à afficher pour cette sélection.")
