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
    message_erreur,
    unite_indicateur,
)
from utils.ui import ACCENT, entete, est_connecte, styliser_figure

get_page_logger("Comparaison Pays (F4)")

entete(
    "Comparaison entre pays",
    "Comparez un indicateur entre plusieurs pays pour la période la plus récente.",
    eyebrow="Analyse",
)

# Cette analyse exige une connexion (le backend attend un jeton).
if not est_connecte():
    st.info("Connectez-vous pour accéder à la comparaison entre pays.")
    st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")
    st.stop()

indicateurs = get_indicateurs()
pays_referentiel = get_pays()

# --- Filtres ---
col1, col2 = st.columns(2)

with col1:
    code_indicateur = st.selectbox(
        "Indicateur :",
        options=list(indicateurs),
        format_func=lambda code: indicateurs[code],
    )

with col2:
    libelle_sexe = st.selectbox("Sexe :", list(SEXES))

classifications = get_classifications(code_indicateur)
libelle_classification = st.selectbox(
    "Catégorie :", list(classifications), index=index_defaut(classifications)
)

noms_pays = st.multiselect(
    "Pays à comparer :",
    options=list(pays_referentiel),
    default=[n for n in ("France", "Allemagne", "États-Unis") if n in pays_referentiel],
)

st.divider()

if len(noms_pays) < 2:
    st.warning("Sélectionnez au moins deux pays pour faire une comparaison.")
    st.stop()

# --- Appel du backend : /analyses/comparaison-pays ---
reponse = api_client.get(
    "/analyses/comparaison-pays",
    params={
        "jeton": st.session_state.get("access_token"),
        "code_indicateur": code_indicateur,
        "codes_pays": [pays_referentiel[nom] for nom in noms_pays],
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

# Le backend renvoie une série d'un seul point par pays, déjà triée de la valeur
# la plus haute à la plus basse.
lignes = [
    {
        "Pays": serie["libelle"],
        "Valeur": serie["points"][0]["valeur"],
        "Période": serie["points"][0]["periode"],
    }
    for serie in reponse["data"]["series"]
    if serie["points"]
]

if not lignes:
    st.info("Aucune donnée à afficher pour cette sélection.")
    st.stop()

df = pd.DataFrame(lignes)
unite = unite_indicateur(code_indicateur)

# --- Mise en évidence des extrêmes ---
suffixe = f" {unite.lower()}" if unite else ""
haut = df.iloc[0]
bas = df.iloc[-1]
col_haut, col_bas = st.columns(2)
col_haut.metric(
    "Valeur la plus élevée", f"{haut['Valeur']:.1f}{suffixe}", haut["Pays"], delta_color="off"
)
col_bas.metric(
    "Valeur la plus basse", f"{bas['Valeur']:.1f}{suffixe}", bas["Pays"], delta_color="off"
)

st.write("")

# Une seule teinte : les pays sont déjà distingués par l'axe des abscisses.
fig = px.bar(
    df,
    x="Pays",
    y="Valeur",
    title=f"Comparaison : {indicateurs[code_indicateur]} ({libelle_sexe})",
    text="Valeur",
    hover_data=["Période"],
    labels={"Valeur": f"Valeur ({unite})" if unite else "Valeur"},
)
fig.update_traces(
    textposition="outside", texttemplate="%{text:.1f}", marker_color=ACCENT
)
styliser_figure(fig)

st.plotly_chart(fig, use_container_width=True)
