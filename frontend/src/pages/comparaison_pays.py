import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import (
    INDICATEURS,
    SEXES,
    classifications_pour,
    get_pays,
    message_erreur,
)

get_page_logger("Comparaison Pays (F4)")

st.title("Comparaison entre pays (F4) 🌍")
st.write("Comparez un indicateur entre plusieurs pays pour la période la plus récente.")

pays_referentiel = get_pays()

# --- Filtres ---
col1, col2 = st.columns(2)

with col1:
<<<<<<< HEAD
    indicateur = st.selectbox(
        "Choisissez l'indicateur :", ["Taux de chômage", "Taux d'activité", "Taux d'emploi"]
    )

with col2:
    population = st.selectbox("Sélectionnez la tranche d'âge :", ["15 ans et plus", "15-24 ans"])
=======
    code_indicateur = st.selectbox(
        "Choisissez l'indicateur :",
        options=list(INDICATEURS),
        format_func=lambda code: INDICATEURS[code],
    )

with col2:
    libelle_sexe = st.selectbox("Sexe :", list(SEXES))
>>>>>>> 459404f89f84fa83d33a4c449b0b4e2eb08b53ba

classifications = classifications_pour(code_indicateur)
libelle_classification = st.selectbox("Catégorie :", list(classifications))

noms_pays = st.multiselect(
    "Sélectionnez les pays à comparer :",
<<<<<<< HEAD
    ["France", "Allemagne", "États-Unis", "Sénégal", "Japon", "Canada", "Brésil"],
    default=["France", "Allemagne", "États-Unis"],
=======
    options=list(pays_referentiel),
    default=[n for n in ("France", "Allemagne", "États-Unis") if n in pays_referentiel],
>>>>>>> 459404f89f84fa83d33a4c449b0b4e2eb08b53ba
)

st.divider()

<<<<<<< HEAD
# --- Zone d'affichage ---
if len(pays) > 1:
    # 1. Création des fausses données (mock)
    donnees_simulees = []
    for p in pays:
        # On génère des valeurs cohérentes (chômage plus bas que l'activité)
        valeur = (
            random.uniform(5.0, 15.0) if "chômage" in indicateur else random.uniform(60.0, 80.0)
        )
        donnees_simulees.append({"Pays": p, "Valeur": round(valeur, 1)})

    df = pd.DataFrame(donnees_simulees)

    # On trie du plus grand au plus petit pour un joli graphique
    df = df.sort_values(by="Valeur", ascending=False)

    # 2. Mise en évidence des extrêmes (Demandé dans le cahier des charges)
    pays_max = df.iloc[0]["Pays"]
    val_max = df.iloc[0]["Valeur"]
    pays_min = df.iloc[-1]["Pays"]
    val_min = df.iloc[-1]["Valeur"]

    st.info(
        f"💡 **À retenir :** Le taux le plus élevé est en **{pays_max}** ({val_max}%) et le plus bas en **{pays_min}** ({val_min}%)."
    )

    # 3. Création du graphique à barres avec Plotly
    fig = px.bar(
        df,
        x="Pays",
        y="Valeur",
        color="Pays",
        title=f"Comparaison : {indicateur} ({population})",
        text="Valeur",  # Affiche la valeur directement sur la barre
    )
    # Place le texte au-dessus de la barre
    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

elif len(pays) == 1:
=======
if len(noms_pays) < 2:
>>>>>>> 459404f89f84fa83d33a4c449b0b4e2eb08b53ba
    st.warning("⚠️ Veuillez sélectionner au moins deux pays pour faire une comparaison.")
    st.stop()

# --- Appel du backend : /analyses/comparaison-pays ---
reponse = api_client.get(
    "/analyses/comparaison-pays",
    params={
        "code_indicateur": code_indicateur,
        "codes_pays": [pays_referentiel[nom] for nom in noms_pays],
        "sexe": SEXES[libelle_sexe],
        "code_classification": classifications[libelle_classification],
    },
)

if reponse["status_code"] == 404:
    st.warning("⚠️ Aucune donnée disponible pour cette sélection.")
    st.stop()

if reponse["status_code"] != 200:
    st.error(f"❌ {message_erreur(reponse)}")
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

# --- Mise en évidence des extrêmes ---
haut = df.iloc[0]
bas = df.iloc[-1]
st.info(
    f"💡 **À retenir :** valeur la plus élevée en **{haut['Pays']}** "
    f"({haut['Valeur']:.1f}) et la plus basse en **{bas['Pays']}** ({bas['Valeur']:.1f})."
)

fig = px.bar(
    df,
    x="Pays",
    y="Valeur",
    color="Pays",
    title=f"Comparaison : {INDICATEURS[code_indicateur]} ({libelle_sexe})",
    text="Valeur",
    hover_data=["Période"],
)
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)
