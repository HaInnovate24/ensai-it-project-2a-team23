import streamlit as st
import plotly.express as px
import pandas as pd
import random

st.title("Comparaison Multi-indicateurs (F5) 📊")
st.write("Superposez plusieurs indicateurs sur un même graphique pour dégager visuellement des liens.")

# --- Filtres ---
col1, col2 = st.columns(2)

with col1:
    pays = st.selectbox(
        "Sélectionnez un pays cible :",
        ["France", "Allemagne", "États-Unis", "Sénégal", "Japon"]
    )

with col2:
    trimestres = st.slider("Période (derniers trimestres) :", min_value=4, max_value=20, value=8)

indicateurs = st.multiselect(
    "Sélectionnez les indicateurs à croiser :",
    ["Taux de chômage", "Taux d'activité", "Taux d'emploi"],
    default=["Taux de chômage", "Taux d'activité"] # Deux courbes affichées par défaut
)

st.divider()

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
        else: # Taux d'emploi
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
        color="Indicateur", # Une couleur différente par indicateur
        title=f"Croisement des indicateurs pour : {pays}",
        markers=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Veuillez sélectionner au moins un indicateur pour générer le graphique.")