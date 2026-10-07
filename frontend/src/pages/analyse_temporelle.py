import streamlit as st
import plotly.express as px
import pandas as pd
import random

st.title("Analyse temporelle de l'emploi (F3) 📈")
st.write("Visualisez l'évolution des indicateurs sur une période donnée.")

# --- Ligne 1 : Les filtres d'indicateurs ---
col1, col2 = st.columns(2)

with col1:
    indicateur = st.selectbox(
        "Choisissez l'indicateur :",
        ["Taux de chômage", "Taux d'activité", "Taux d'emploi"]
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

# --- Zone d'affichage du graphique Plotly ---
if pays:
    # 1. Création de fausses données pour simuler la réponse du Backend
    donnees_simulees = []
    noms_trimestres = [f"T{i}" for i in range(1, trimestres + 1)]
    
    for p in pays:
        # On génère une valeur de base différente selon le pays
        base = random.randint(40, 80)
        for t in noms_trimestres:
            valeur = base + random.uniform(-2, 2)
            donnees_simulees.append({"Trimestre": t, "Pays": p, "Valeur": valeur})
            
    df = pd.DataFrame(donnees_simulees)
    
    # 2. Création du graphique avec Plotly Express
    fig = px.line(
        df, 
        x="Trimestre", 
        y="Valeur", 
        color="Pays",
        title=f"Évolution : {indicateur} ({population})",
        markers=True
    )
    
    # 3. Affichage du graphique dans Streamlit
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Veuillez sélectionner au moins un pays pour afficher les données.")