from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.rapport_pdf import construire_rapport_pdf, figure_png
from utils.referentiels import (
    SEXES,
    get_indicateurs,
    get_pays,
    message_erreur,
    type_classification_de,
    unite_indicateur,
)
from utils.ui import (
    PALETTE_GRAPHIQUE,
    afficher_graphique,
    entete,
    entete_graphique,
    est_connecte,
    fmt_fr,
    ligne_source,
    notif,
    styliser_figure,
)

get_page_logger("Multi-indicateurs (F5)")

entete(
    "Plusieurs indicateurs, un pays.",
    "Superposez plusieurs indicateurs sur un même graphique pour dégager visuellement des liens.",
    eyebrow="Explorateur de données · ILOSTAT",
)

# Cette analyse exige une connexion (le backend attend un jeton).
if not est_connecte():
    notif("Connectez-vous pour accéder à la comparaison multi-indicateurs.", "info")
    st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")
    st.stop()

ligne_source(["Données réelles", "OIT · diffusion ILOSTAT"], f"Extrait du {date.today():%d/%m/%Y}")

indicateurs = get_indicateurs()
pays_referentiel = get_pays()

# --- Carte de filtres ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        nom_pays = st.selectbox("Pays cible", options=list(pays_referentiel))
    with col2:
        libelle_sexe = st.selectbox("Sexe", list(SEXES))

    codes_indicateur = st.multiselect(
        "Indicateurs à croiser",
        options=list(indicateurs),
        format_func=lambda code: indicateurs[code],
        default=list(indicateurs),
    )

st.write("")

if not codes_indicateur:
    notif("Sélectionnez au moins un indicateur pour générer le graphique.", "warn")
    st.stop()


def _classification_total(code: str) -> str:
    """Code de classification « total » adapté au type de l'indicateur.

    L'emploi se décline par profession, la population par âge : chaque
    indicateur est interrogé avec SON total agrégé (qui porte les données).
    """
    return (
        "AGE_AGGREGATE_TOTAL"
        if type_classification_de(code) == "age"
        else "OCU_ISCO08_TOTAL"
    )


# --- Données : une courbe par indicateur ------------------------------------
# L'endpoint /analyses/comparaison-indicateurs impose UNE classification unique
# pour tous les indicateurs — incompatible avec le fait que l'emploi se classe
# par profession et la population par âge (une des courbes disparaîtrait). On
# interroge donc /analyses/evolution indicateur par indicateur, chacun avec son
# total agrégé, pour que TOUTES les courbes s'affichent.
lignes: list[dict] = []
indic_sans_donnees: list[str] = []
with st.spinner("Chargement des données…"):
    for code in codes_indicateur:
        rep = api_client.get(
            "/analyses/evolution",
            params={
                "code_indicateur": code,
                "code_pays": pays_referentiel[nom_pays],
                "sexe": SEXES[libelle_sexe],
                "code_classification": _classification_total(code),
            },
        )
        if rep["status_code"] in (401, 403):
            notif("Session expirée ou accès refusé. Reconnectez-vous pour continuer.", "ko")
            st.stop()
        points = rep["data"].get("points", []) if rep["status_code"] == 200 else []
        if points:
            lignes.extend(
                {"Période": p["periode"], "Indicateur": indicateurs[code], "Valeur": p["valeur"]}
                for p in points
            )
        else:
            indic_sans_donnees.append(indicateurs[code])

if indic_sans_donnees:
    notif("Aucune donnée pour : " + ", ".join(indic_sans_donnees), "warn")

if not lignes:
    notif("Aucune donnée à afficher pour cette sélection.", "info")
    st.stop()

df = pd.DataFrame(lignes).sort_values("Période")
# Unités des indicateurs effectivement tracés (pour l'axe / la pastille).
unites_tracees = sorted({
    unite_indicateur(code) for code in codes_indicateur
    if indicateurs[code] in set(df["Indicateur"])
} - {""})

with st.container(border=True):
    tete_g, tete_d = st.columns([0.66, 0.34], vertical_alignment="center")
    with tete_g:
        entete_graphique("Croisement d'indicateurs", nom_pays, f"Totaux agrégés · {libelle_sexe}")
    with tete_d:
        if len(unites_tracees) == 1:
            st.markdown(
                f"<div style='text-align:right;margin-bottom:0.3rem'>"
                f"<span class='ls-pill'>En {unites_tracees[0]}</span></div>",
                unsafe_allow_html=True,
            )

    if len(unites_tracees) > 1:
        st.caption(
            "Les unités diffèrent d'un indicateur à l'autre : comparez les tendances "
            "plutôt que les niveaux absolus."
        )

    fig = px.line(
        df,
        x="Période",
        y="Valeur",
        color="Indicateur",
        markers=True,
        color_discrete_sequence=PALETTE_GRAPHIQUE,
    )
    fig.update_xaxes(type="category")
    fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
    styliser_figure(fig)
    fig.update_yaxes(title_text=unites_tracees[0] if len(unites_tracees) == 1 else "")
    # Légende sous le titre, horizontale, pour que les deux courbes soient
    # clairement identifiées sans empiéter sur le tracé.
    fig.update_layout(legend=dict(title_text=""))
    afficher_graphique(fig)

# --- Rapport PDF : chiffres de synthèse + détail de tous les points ---
chiffres_pdf = []
lignes_pdf = []
for indic, sous in df.groupby("Indicateur"):
    sous = sous.sort_values("Période")
    chiffres_pdf.append((indic, f"{fmt_fr(sous.iloc[-1]['Valeur'])} ({sous.iloc[-1]['Période']})"))
    for _, pt in sous.iterrows():
        lignes_pdf.append([indic, str(pt["Période"]), fmt_fr(pt["Valeur"])])
pdf_bytes = construire_rapport_pdf(
    titre="Multi-indicateurs",
    sous_titre=nom_pays,
    contexte=[
        ("Pays cible", nom_pays),
        ("Indicateurs", f"{df['Indicateur'].nunique()} croisé(s)"),
        ("Classification", "Totaux agrégés"),
        ("Sexe", libelle_sexe),
    ],
    colonnes=["Indicateur", "Période", "Valeur"],
    lignes=lignes_pdf,
    chiffres=chiffres_pdf[:3] or None,
    note=(
        f"Croisement de {df['Indicateur'].nunique()} indicateur(s) pour {nom_pays}. "
        "Les unités pouvant différer d'un indicateur à l'autre, comparez les tendances "
        "plutôt que les niveaux absolus."
    ),
    image_png=figure_png(fig),
    legende_graphique=f"Totaux agrégés · {libelle_sexe}",
)
_, col_pdf = st.columns([0.7, 0.3])
with col_pdf:
    st.download_button(
        "Rapport PDF",
        data=pdf_bytes,
        file_name=f"rapport_multi_{pays_referentiel[nom_pays]}.pdf",
        mime="application/pdf",
        icon=":material/picture_as_pdf:",
        use_container_width=True,
    )
