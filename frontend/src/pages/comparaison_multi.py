import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.referentiels import (
    INDICATEURS,
    SEXES,
    classifications_toutes,
    get_pays,
    message_erreur,
)

get_page_logger("Multi-indicateurs (F5)")

st.title("Comparaison Multi-indicateurs (F5) 📊")
st.write(
<<<<<<< HEAD
    "Superposez plusieurs indicateurs sur un même graphique pour dégager visuellement des liens."
)
=======
    "Superposez plusieurs indicateurs sur un même graphique pour dégager "
    "visuellement des liens."
)

pays_referentiel = get_pays()
>>>>>>> 459404f89f84fa83d33a4c449b0b4e2eb08b53ba

# --- Filtres ---
col1, col2 = st.columns(2)

with col1:
<<<<<<< HEAD
    pays = st.selectbox(
        "Sélectionnez un pays cible :", ["France", "Allemagne", "États-Unis", "Sénégal", "Japon"]
    )
=======
    nom_pays = st.selectbox("Sélectionnez un pays cible :", options=list(pays_referentiel))
>>>>>>> 459404f89f84fa83d33a4c449b0b4e2eb08b53ba

with col2:
    libelle_sexe = st.selectbox("Sexe :", list(SEXES))

codes_indicateur = st.multiselect(
    "Sélectionnez les indicateurs à croiser :",
<<<<<<< HEAD
    ["Taux de chômage", "Taux d'activité", "Taux d'emploi"],
    default=["Taux de chômage", "Taux d'activité"],  # Deux courbes affichées par défaut
=======
    options=list(INDICATEURS),
    format_func=lambda code: INDICATEURS[code],
    default=list(INDICATEURS),
>>>>>>> 459404f89f84fa83d33a4c449b0b4e2eb08b53ba
)

# L'API applique une seule classification à tous les indicateurs : chaque
# indicateur n'apparaîtra que s'il possède des données pour cette catégorie.
classifications = classifications_toutes()
libelle_classification = st.selectbox("Catégorie (âge ou profession) :", list(classifications))

st.divider()

<<<<<<< HEAD
# --- Zone d'affichage ---
if len(indicateurs) > 0:
    # 1. Création des fausses données (mock)
    donnees_simulees = []
    noms_trimestres = [f"T{i}" for i in range(1, trimestres + 1)]

    for ind in indicateurs:
        # On ajuste les valeurs de base pour que les courbes ne se superposent pas bêtement
        if "chômage" in ind:
            base = random.randint(5, 12)
        elif "activité" in ind:
            base = random.randint(65, 75)
        else:  # Taux d'emploi
            base = random.randint(60, 70)

        for t in noms_trimestres:
            valeur = base + random.uniform(-1.5, 1.5)
            donnees_simulees.append({"Trimestre": t, "Indicateur": ind, "Valeur": round(valeur, 1)})

    df = pd.DataFrame(donnees_simulees)

    # 2. Création du graphique Plotly (courbes multiples)
    fig = px.line(
        df,
        x="Trimestre",
        y="Valeur",
        color="Indicateur",  # Une couleur différente par indicateur
        title=f"Croisement des indicateurs pour : {pays}",
        markers=True,
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Veuillez sélectionner au moins un indicateur pour générer le graphique.")
=======
if not codes_indicateur:
    st.warning("⚠️ Veuillez sélectionner au moins un indicateur pour générer le graphique.")
    st.stop()

# --- Appel du backend : /analyses/comparaison-indicateurs ---
reponse = api_client.get(
    "/analyses/comparaison-indicateurs",
    params={
        "codes_indicateur": codes_indicateur,
        "code_pays": pays_referentiel[nom_pays],
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

lignes = []
for serie in reponse["data"]["series"]:
    for point in serie["points"]:
        lignes.append(
            {"Période": point["periode"], "Indicateur": serie["libelle"], "Valeur": point["valeur"]}
        )

if not lignes:
    st.info("Aucune donnée à afficher pour cette sélection.")
    st.stop()

df = pd.DataFrame(lignes)

fig = px.line(
    df,
    x="Période",
    y="Valeur",
    color="Indicateur",
    title=f"Croisement des indicateurs pour : {nom_pays}",
    markers=True,
)

st.plotly_chart(fig, use_container_width=True)
>>>>>>> 459404f89f84fa83d33a4c449b0b4e2eb08b53ba
