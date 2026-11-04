from datetime import date

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
from utils.ui import (
    PALETTE_GRAPHIQUE,
    carte_a_retenir,
    carte_metrique,
    chip,
    est_connecte,
    ligne_source,
    styliser_figure,
)

get_page_logger("Comparaison Pays (F4)")

# --- En-tête éditorial (constant sur les pages d'analyse) ---
# Le bouton d'export est placé dans un emplacement rempli une fois les données prêtes.
_col_titre, _col_action = st.columns([0.76, 0.24], vertical_alignment="center")
with _col_titre:
    st.markdown(
        "<div class='ls-eyebrow'>Explorateur de données · ILOSTAT</div>", unsafe_allow_html=True
    )
    st.markdown(
        "<div class='ls-serif ls-title'>Le travail, en perspective.</div>", unsafe_allow_html=True
    )
    st.markdown(
        "<p class='ls-subtitle'>Suivez les tendances. Comparez les pays. Comprenez les écarts.</p>",
        unsafe_allow_html=True,
    )
emplacement_export = _col_action.empty()
st.write("")

# Cette analyse exige une connexion (le backend attend un jeton).
if not est_connecte():
    st.info("Connectez-vous pour accéder à la comparaison entre pays.")
    st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")
    st.stop()

ligne_source(
    ["Données réelles", "OIT · diffusion ILOSTAT"],
    f"Consulté le {date.today():%d/%m/%Y}",
)

indicateurs = get_indicateurs()
pays_referentiel = get_pays()

# Liste de pays proposée : on privilégie une sélection lisible (pays réels),
# la recherche du multiselect donne accès à l'ensemble du référentiel.
_PAYS_SUGGERES = [
    n
    for n in (
        "France",
        "Maroc",
        "Guinée",
        "Sénégal",
        "Côte d'Ivoire",
        "Allemagne",
        "Espagne",
        "Italie",
        "Royaume-Uni",
        "Canada",
        "États-Unis",
        "Japon",
        "Brésil",
    )
    if n in pays_referentiel
]
_options_pays = _PAYS_SUGGERES + [n for n in pays_referentiel if n not in _PAYS_SUGGERES]
_defaut_pays = [n for n in ("France", "Maroc", "Guinée") if n in pays_referentiel]

# --- Carte de filtres ---
with st.container(border=True):
    col_pays, col_indic, col_sexe, col_cat = st.columns([1.4, 1.2, 1, 1.1])

    with col_pays:
        st.markdown("**Pays**")
        with st.popover(
            ", ".join(st.session_state.get("f4_pays", _defaut_pays)) or "Choisir des pays",
            use_container_width=True,
        ):
            st.caption("Sélectionnez de 1 à 5 pays")
            noms_pays = st.multiselect(
                "Pays",
                options=_options_pays,
                default=_defaut_pays,
                max_selections=5,
                key="f4_pays",
                label_visibility="collapsed",
                placeholder="Rechercher un pays…",
            )

    with col_indic:
        st.markdown("**Indicateur**")
        code_indicateur = st.selectbox(
            "Indicateur",
            options=list(indicateurs),
            format_func=lambda code: indicateurs[code],
            label_visibility="collapsed",
        )

    with col_sexe:
        st.markdown("**Sexe**")
        libelle_sexe = st.selectbox("Sexe", list(SEXES), label_visibility="collapsed")

    with col_cat:
        st.markdown("**Catégorie**")
        classifications = get_classifications(code_indicateur)
        libelle_classification = st.selectbox(
            "Catégorie",
            list(classifications),
            index=index_defaut(classifications),
            label_visibility="collapsed",
        )

noms_pays = st.session_state.get("f4_pays", _defaut_pays)

# Couleur stable par pays (réutilisée pour pastilles, graphique et « À retenir »).
couleur_par_pays = {
    nom: PALETTE_GRAPHIQUE[i % len(PALETTE_GRAPHIQUE)] for i, nom in enumerate(noms_pays)
}

# Pastilles de sélection + réinitialisation.
col_chips, col_reset = st.columns([0.8, 0.2], vertical_alignment="center")
with col_chips:
    if noms_pays:
        st.markdown(
            " ".join(chip(nom, couleur_par_pays[nom]) for nom in noms_pays),
            unsafe_allow_html=True,
        )
with col_reset:
    if st.button("Réinitialiser", icon=":material/restart_alt:", use_container_width=True):
        st.session_state["f4_pays"] = _defaut_pays
        st.rerun()

if len(noms_pays) < 2:
    st.info("Sélectionnez au moins deux pays pour lancer la comparaison.")
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
suffixe = f" {unite.lower()}" if unite else ""
periode = df["Période"].iloc[0]
haut, bas = df.iloc[0], df.iloc[-1]
ecart = haut["Valeur"] - bas["Valeur"]

# Bouton d'export dans l'en-tête, désormais que les données sont disponibles.
emplacement_export.download_button(
    "Exporter les données",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"comparaison_{code_indicateur}_{periode}.csv",
    mime="text/csv",
    icon=":material/download:",
    type="primary",
    use_container_width=True,
)

# --- Trois cartes métriques ---
m1, m2, m3 = st.columns(3)
with m1:
    carte_metrique("Le plus élevé", f"{haut['Valeur']:.1f}", unite, f"{haut['Pays']} · {periode}")
with m2:
    carte_metrique("Le plus bas", f"{bas['Valeur']:.1f}", unite, f"{bas['Pays']} · {periode}")
with m3:
    carte_metrique("Écart entre les pays", f"{ecart:.1f}", unite, f"Maximum − minimum · {periode}")

st.write("")

# --- Graphique + panneau « À retenir » ---
col_chart, col_aside = st.columns([0.68, 0.32])

with col_chart:
    with st.container(border=True):
        st.markdown(
            "<div class='ls-eyebrow plain'>Comparaison entre pays</div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='ls-serif' style='font-size:1.5rem'>{indicateurs[code_indicateur]}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{libelle_classification} · {libelle_sexe} · {periode} · année commune")

        df_graph = df.sort_values("Valeur")  # barres horizontales : plus haut en haut
        fig = px.bar(
            df_graph,
            x="Valeur",
            y="Pays",
            orientation="h",
            color="Pays",
            color_discrete_map=couleur_par_pays,
            text="Valeur",
            labels={"Valeur": f"Valeur ({unite})" if unite else "Valeur"},
        )
        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
            cliponaxis=False,
            marker_line_width=0,
        )
        fig.update_layout(showlegend=False)
        styliser_figure(fig, hauteur=360)
        st.plotly_chart(fig, use_container_width=True)

with col_aside:
    indic_court = indicateurs[code_indicateur].split()[0].capitalize()
    lignes_retenir = [
        (
            r["Pays"],
            f"{r['Valeur']:.1f}{suffixe}",
            couleur_par_pays.get(r["Pays"], PALETTE_GRAPHIQUE[0]),
        )
        for _, r in df.iterrows()
    ]
    note = (
        f"En {periode}, l'écart entre {haut['Pays']} et {bas['Pays']} atteint "
        f"{ecart:.1f}{suffixe} pour cet indicateur."
    )
    bas_note = (
        f"Les valeurs sont exprimées en {unite.lower()} et correspondent à la dernière "
        "période commune disponible."
        if unite
        else "Les valeurs correspondent à la dernière période commune disponible."
    )
    carte_a_retenir(f"{indic_court} · {periode}", lignes_retenir, note=note, bas=bas_note)
