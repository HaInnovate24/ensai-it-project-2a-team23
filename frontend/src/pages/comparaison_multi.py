import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import (
    SEXES,
    get_classifications_toutes,
    get_indicateurs,
    get_pays,
    index_defaut,
    message_erreur,
)
from datetime import date

from utils.rapport_pdf import construire_rapport_pdf, figure_png
from utils.ui import (
    PALETTE_GRAPHIQUE,
    afficher_graphique,
    entete,
    entete_graphique,
    est_connecte,
    fmt_fr,
    ligne_source,
    styliser_figure,
)

get_page_logger("Multi-indicateurs (F5)")

entete(
    "Plusieurs indicateurs, un pays.",
    "Superposez plusieurs indicateurs sur un même graphique pour dégager "
    "visuellement des liens.",
    eyebrow="Explorateur de données · ILOSTAT",
)

# Cette analyse exige une connexion (le backend attend un jeton).
if not est_connecte():
    st.info("Connectez-vous pour accéder à la comparaison multi-indicateurs.")
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

    # L'API applique une seule classification à tous les indicateurs : chaque
    # indicateur n'apparaîtra que s'il possède des données pour cette catégorie.
    classifications = get_classifications_toutes()
    libelle_classification = st.selectbox(
        "Catégorie (âge ou profession)",
        list(classifications),
        index=index_defaut(classifications),
    )

st.write("")

if not codes_indicateur:
    st.warning("Sélectionnez au moins un indicateur pour générer le graphique.")
    st.stop()

# --- Appel du backend : /analyses/comparaison-indicateurs ---
with st.spinner("Chargement des données…"):
    reponse = api_client.get(
        "/analyses/comparaison-indicateurs",
        params={
            "jeton": st.session_state.get("access_token"),
            "codes_indicateur": codes_indicateur,
            "code_pays": pays_referentiel[nom_pays],
            "sexe": SEXES[libelle_sexe],
            "code_classification": classifications[libelle_classification],
        },
    )

if reponse["status_code"] == 404:
    st.warning("Aucune donnée disponible pour cette sélection.")
    st.stop()

if reponse["status_code"] in (401, 403):
    st.error("Session expirée ou accès refusé. Reconnectez-vous pour continuer.")
    st.stop()

if reponse["status_code"] != 200:
    st.error(message_erreur(reponse))
    st.stop()

lignes = []
for serie in reponse["data"]["series"]:
    for point in serie["points"]:
        lignes.append(
            {"Période": point["periode"], "Indicateur": serie["libelle"], "Valeur": point["valeur"]}
        )

if not lignes:
    st.info("Aucune donnée à afficher pour cette sélection.")
    st.stop()

df = pd.DataFrame(lignes).sort_values("Période")

with st.container(border=True):
    entete_graphique("Croisement d'indicateurs", nom_pays, f"{libelle_classification} · {libelle_sexe}")
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
        ("Catégorie", libelle_classification),
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
    legende_graphique=f"{libelle_classification} · {libelle_sexe}",
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
