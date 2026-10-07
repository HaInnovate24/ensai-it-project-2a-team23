import streamlit as st
import plotly.express as px
import pandas as pd
import random

st.title("Comparaison entre pays (F4) 🌍")
st.write("Comparez un indicateur entre plusieurs pays pour la période la plus récente.")

# --- Filtres ---
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

pays = st.multiselect(
    "Sélectionnez les pays à comparer :",
    ["France", "Allemagne", "États-Unis", "Sénégal", "Japon", "Canada", "Brésil"],
    default=["France", "Allemagne", "États-Unis"]
)

st.divider()

# --- Zone d'affichage ---
if len(pays) > 1:
    # 1. Création des fausses données (mock)
    donnees_simulees = []
    for p in pays:
        # On génère des valeurs cohérentes (chômage plus bas que l'activité)
        valeur = random.uniform(5.0, 15.0) if "chômage" in indicateur else random.uniform(60.0, 80.0)
        donnees_simulees.append({"Pays": p, "Valeur": round(valeur, 1)})
        
    df = pd.DataFrame(donnees_simulees)
    
    # On trie du plus grand au plus petit pour un joli graphique
    df = df.sort_values(by="Valeur", ascending=False)
    
    # 2. Mise en évidence des extrêmes (Demandé dans le cahier des charges)
    pays_max = df.iloc[0]["Pays"]
    val_max = df.iloc[0]["Valeur"]
    pays_min = df.iloc[-1]["Pays"]
    val_min = df.iloc[-1]["Valeur"]
    
    st.info(f"💡 **À retenir :** Le taux le plus élevé est en **{pays_max}** ({val_max}%) et le plus bas en **{pays_min}** ({val_min}%).")
    
    # 3. Création du graphique à barres avec Plotly
    fig = px.bar(
        df, 
        x="Pays", 
        y="Valeur", 
        color="Pays",
        title=f"Comparaison : {indicateur} ({population})",
        text="Valeur" # Affiche la valeur directement sur la barre
    )
    # Place le texte au-dessus de la barre
    fig.update_traces(textposition='outside')
    
    st.plotly_chart(fig, use_container_width=True)

elif len(pays) == 1:
    st.warning("⚠️ Veuillez sélectionner au moins deux pays pour faire une comparaison.")
else:
    st.warning("⚠️ Veuillez sélectionner des pays pour afficher les données.")