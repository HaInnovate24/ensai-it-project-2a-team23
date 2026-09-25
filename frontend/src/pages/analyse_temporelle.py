import streamlit as st

st.title("Analyse temporelle de l'emploi (F3) 📈")
st.write("Visualisez l'évolution des indicateurs sur une période donnée.")

# --- Ligne 1 : Les filtres d'indicateurs ---
col1, col2 = st.columns(2)

with col1:
    indicateur = st.selectbox(
        "Choisissez l'indicateur :",
        [
            "Taux de chômage",
            "Taux d'activité",
            "Taux d'emploi",
            "Comparaison des 3 indicateurs"
        ]
    )

with col2:
    population = st.selectbox(
        "Sélectionnez la tranche d'âge :",
        ["15 ans et plus", "15-24 ans"]
    )

# --- Ligne 2 : Les filtres géographiques et temporels ---
col3, col4 = st.columns(2)

with col3:
    pays = st.multiselect(
        "Sélectionnez le(s) pays :",
        ["France", "Allemagne", "États-Unis", "Sénégal", "Japon"],
        default=["France"]
    )

with col4:
    trimestres = st.slider("Période (derniers trimestres) :", min_value=4, max_value=20, value=8)

st.divider()

# --- Zone d'affichage ---
if pays:
    st.info(
        f"📊 Bientôt ici : Graphique pour la sélection '{indicateur}' \n\n"
        f"**Cible :** {population} \n\n"
        f"**Pays :** {', '.join(pays)} \n\n"
        f"**Période :** {trimestres} derniers trimestres."
    )
else:
    st.warning("⚠️ Veuillez sélectionner au moins un pays pour afficher les données.")