from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger
from utils.rapport_pdf import construire_rapport_pdf, figure_png
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
from utils.ui import (
    PALETTE_GRAPHIQUE,
    afficher_graphique,
    entete,
    entete_graphique,
    ligne_source,
    notif,
    styliser_figure,
)

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
    notif("Sélectionnez au moins un pays pour afficher les données.", "warn")
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
                lignes.append(
                    {"Période": point["periode"], "Pays": nom, "Valeur": point["valeur"]}
                )
        elif reponse["status_code"] == 404:
            pays_sans_donnees.append(nom)
        elif reponse["status_code"] == 0:
            notif(message_erreur(reponse), "ko")
            st.stop()
        else:
            notif(f"{nom} : {message_erreur(reponse)}", "ko")

if pays_sans_donnees:
    notif("Aucune donnée disponible pour : " + ", ".join(pays_sans_donnees), "warn")

if lignes:
    unite = unite_indicateur(code_indicateur)
    df = pd.DataFrame(lignes).sort_values("Période")
    with st.container(border=True):
        entete_graphique(
            "Évolution temporelle",
            indicateurs[code_indicateur],
            f"{libelle_classification} · {libelle_sexe} · {nb_periodes} dernières années",
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

    # --- Génération du Rapport PDF via le Backend ---
    st.divider()
    st.subheader("Générer le rapport PDF complet")
    st.write("Demandez au serveur de générer une analyse au format PDF (incluant ce graphique et les tables).")

    # On utilise un bouton d'action pour déclencher la requête POST
    if st.button("Demander la génération du PDF", icon="📄", type="primary"):
        with st.spinner("Génération du rapport côté serveur en cours..."):

            # 1. Demande de création du rapport au backend
            payload = {
                "titre": "Évolution temporelle",
                "description": f"{indicateurs[code_indicateur]} - {libelle_sexe} - {libelle_classification}",
                "code_indicateur": code_indicateur,
                "codes_pays": noms_pays
            }

            reponse_creation = api_client.post("/rapports/", json=payload)

            if reponse_creation["status_code"] == 201:
                rapport_id = reponse_creation["data"]["id"]

                # 2. Téléchargement du fichier binaire généré via le GET
                reponse_telechargement = api_client.download_file(f"/rapports/{rapport_id}/telecharger")

                if reponse_telechargement["status_code"] == 200:
                    pdf_bytes = reponse_telechargement["content"]
                    notif("Rapport généré avec succès.", "ok")

                    # 3. Affichage du bouton natif Streamlit pour sauvegarder le fichier
                    st.download_button(
                        label="Télécharger le fichier PDF",
                        data=pdf_bytes,
                        file_name=f"rapport_evolution_{code_indicateur}.pdf",
                        mime="application/pdf",
                        icon=":material/download:",
                    )
                else:
                    notif(f"Erreur lors du téléchargement : {message_erreur(reponse_telechargement)}", "ko")
            else:
                notif(f"Erreur lors de la création en base : {message_erreur(reponse_creation)}", "ko")

elif not pays_sans_donnees:
    notif("Aucune donnée à afficher pour cette sélection.", "info")

# =====================================================================
# Taux d'emploi (calculé : Emploi / Population * 100)
# =====================================================================
st.divider()
st.subheader("Taux d'emploi")
st.caption("Taux d'emploi = Emploi (toutes professions) / Population (15 ans et plus) × 100")

col_tx, col_ty = st.columns([1, 1])
with col_tx:
    nom_pays_taux = st.selectbox(
        "Pays (taux d'emploi)",
        options=list(pays_referentiel),
        key="f3_taux_pays",
    )
with col_ty:
    nb_periodes_taux = st.slider(
        "Nombre d'années (taux)", min_value=2, max_value=13, value=10, key="f3_taux_n"
    )

st.write("")

with st.spinner("Calcul des taux d'emploi…"):
    rep_taux = api_client.get(
        "/analyses/taux-emploi",
        params={"code_pays": pays_referentiel[nom_pays_taux], "nb_periodes": nb_periodes_taux},
    )

if rep_taux["status_code"] == 0:
    notif(message_erreur(rep_taux), "ko")
elif rep_taux["status_code"] != 200:
    notif(f"Erreur lors du calcul des taux : {message_erreur(rep_taux)}", "ko")
else:
    data_taux = rep_taux["data"]

    lignes_taux = []
    for pt in data_taux["taux_total"]:
        lignes_taux.append({"Période": pt["periode"], "Série": "Taux total", "Valeur": pt["taux"]})
    for pt in data_taux["taux_homme"]:
        lignes_taux.append({"Période": pt["periode"], "Série": "Hommes", "Valeur": pt["taux"]})
    for pt in data_taux["taux_femme"]:
        lignes_taux.append({"Période": pt["periode"], "Série": "Femmes", "Valeur": pt["taux"]})

    if lignes_taux:
        df_taux = pd.DataFrame(lignes_taux).sort_values("Période")

        with st.container(border=True):
            entete_graphique(
                "Taux d'emploi",
                nom_pays_taux,
                f"{nb_periodes_taux} dernières années · %",
            )
            df_taux["Année"] = df_taux["Période"].str[:4].astype(int)
            fig_taux = go.Figure()
            for i, (serie, sous_df) in enumerate(df_taux.groupby("Série", sort=False)):
                sous_df = sous_df.sort_values("Année")
                annees = sous_df["Année"].tolist()
                valeurs = sous_df["Valeur"].tolist()
                gaps = [annees[j + 1] - annees[j] for j in range(len(annees) - 1)]
                max_gap = max(gaps) if gaps else 0
                connecter = max_gap < 3
                fig_taux.add_trace(go.Scatter(
                    x=annees,
                    y=valeurs,
                    mode="lines+markers",
                    name=serie,
                    line=dict(width=2.5, color=PALETTE_GRAPHIQUE[i % len(PALETTE_GRAPHIQUE)]),
                    marker=dict(size=7, color=PALETTE_GRAPHIQUE[i % len(PALETTE_GRAPHIQUE)]),
                    connectgaps=connecter,
                ))
            fig_taux.update_layout(yaxis_title="Taux d'emploi (%)")
            fig_taux.update_xaxes(type="linear", dtick=1, tickformat=".0f", title="Année")
            styliser_figure(fig_taux)
            afficher_graphique(fig_taux)

        st.subheader("Variations annuelles du taux d'emploi (en points)")

        lignes_var = []
        for pt in data_taux["variation_taux_total"]:
            lignes_var.append({"Période": pt["periode"], "Série": "Total", "Valeur": pt["taux"]})
        for pt in data_taux["variation_taux_homme"]:
            lignes_var.append({"Période": pt["periode"], "Série": "Hommes", "Valeur": pt["taux"]})
        for pt in data_taux["variation_taux_femme"]:
            lignes_var.append({"Période": pt["periode"], "Série": "Femmes", "Valeur": pt["taux"]})

        if lignes_var:
            df_var = pd.DataFrame(lignes_var).sort_values("Période")

            with st.container(border=True):
                entete_graphique(
                    "Variations annuelles",
                    nom_pays_taux,
                    "En points (différence entre deux années consécutives)",
                )
                df_var["Année"] = df_var["Période"].str[:4].astype(int)
                fig_var = go.Figure()
                for i, (serie, sous_df) in enumerate(df_var.groupby("Série", sort=False)):
                    sous_df = sous_df.sort_values("Année")
                    annees = sous_df["Année"].tolist()
                    valeurs = sous_df["Valeur"].tolist()
                    gaps = [annees[j + 1] - annees[j] for j in range(len(annees) - 1)]
                    max_gap = max(gaps) if gaps else 0
                    connecter = max_gap < 3
                    fig_var.add_trace(go.Scatter(
                        x=annees,
                        y=valeurs,
                        mode="lines+markers",
                        name=serie,
                        line=dict(width=2.5, color=PALETTE_GRAPHIQUE[i % len(PALETTE_GRAPHIQUE)]),
                        marker=dict(size=7, color=PALETTE_GRAPHIQUE[i % len(PALETTE_GRAPHIQUE)]),
                        connectgaps=connecter,
                    ))
                fig_var.update_layout(yaxis_title="Variation (points)")
                fig_var.update_xaxes(type="linear", dtick=1, tickformat=".0f", title="Année")
                fig_var.add_hline(y=0, line_dash="dash", line_color="#999", line_width=1)
                styliser_figure(fig_var)
                afficher_graphique(fig_var)

        st.subheader("Détail des taux")
        df_detail = pd.DataFrame(lignes_taux)
        st.dataframe(
            df_detail.pivot_table(index="Période", columns="Série", values="Valeur"),
            use_container_width=True,
        )

        st.write("")
        if st.button("Générer le rapport PDF (taux + évolutions)", icon=":material/description:", type="primary"):
            derniers_total = data_taux["taux_total"][-1]["taux"] if data_taux["taux_total"] else 0
            derniers_homme = data_taux["taux_homme"][-1]["taux"] if data_taux["taux_homme"] else 0
            derniers_femme = data_taux["taux_femme"][-1]["taux"] if data_taux["taux_femme"] else 0
            annee_derniere = data_taux["taux_total"][-1]["periode"][:4] if data_taux["taux_total"] else ""
            ecart_genre = abs(derniers_homme - derniers_femme)
            derniere_var = data_taux["variation_taux_total"][-1]["taux"] if data_taux["variation_taux_total"] else 0

            chiffres_pdf = [
                ("Taux total", f"{derniers_total:.1f}%"),
                ("Hommes", f"{derniers_homme:.1f}%"),
                ("Femmes", f"{derniers_femme:.1f}%"),
                ("Écart genre", f"{ecart_genre:.1f} pts"),
            ]

            lignes_pdf = []
            periodes_emploi = sorted(set(p["periode"] for p in data_taux["taux_total"]))
            for periode in periodes_emploi:
                tt = next((p["taux"] for p in data_taux["taux_total"] if p["periode"] == periode), None)
                th = next((p["taux"] for p in data_taux["taux_homme"] if p["periode"] == periode), None)
                tf = next((p["taux"] for p in data_taux["taux_femme"] if p["periode"] == periode), None)
                vt = next((p["taux"] for p in data_taux["variation_taux_total"] if p["periode"] == periode), None)
                lignes_pdf.append([
                    periode[:4],
                    f"{tt:.1f}%" if tt is not None else "—",
                    f"{th:.1f}%" if th is not None else "—",
                    f"{tf:.1f}%" if tf is not None else "—",
                    f"{vt:+.1f} pts" if vt is not None else "—",
                ])

            pdf_bytes = construire_rapport_pdf(
                titre="Taux d'emploi et évolutions",
                sous_titre=f"{nom_pays_taux} — {annee_derniere}",
                contexte=[
                    ("Pays", nom_pays_taux),
                    ("Période", f"{periodes_emploi[0][:4]} - {periodes_emploi[-1][:4]}" if periodes_emploi else "—"),
                    ("Formule", "Emploi / Population (15+) x 100"),
                    ("Source", "OIT - ILOSTAT"),
                ],
                colonnes=["Année", "Taux total", "Hommes", "Femmes", "Variation"],
                lignes=lignes_pdf,
                chiffres=chiffres_pdf,
                note=(
                    f"En {annee_derniere}, le taux d'emploi global est de {derniers_total:.1f}% "
                    f"(variation de {derniere_var:+.1f} pts). "
                    f"L'écart entre les taux masculin et féminin est de {ecart_genre:.1f} points."
                ),
                image_png=figure_png(fig_taux),
                legende_graphique=f"Taux d'emploi par sexe — {nom_pays_taux}",
            )
            st.download_button(
                label="Télécharger le rapport PDF",
                data=pdf_bytes,
                file_name=f"rapport_taux_emploi_{nom_pays_taux}.pdf",
                mime="application/pdf",
                icon=":material/download:",
            )
    else:
        notif("Aucun taux calculable (données emploi ou population manquantes).", "warn")
