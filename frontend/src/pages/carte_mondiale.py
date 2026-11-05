from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.api_client import api_client
from utils.centroides_pays import CENTROIDES
from utils.log_init import get_page_logger
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
    ICONE_CIBLE,
    ICONE_ECART,
    ICONE_GLOBE,
    afficher_graphique,
    carte_metrique,
    est_connecte,
    fmt_fr as format_fr,
    ligne_source,
    styliser_figure,
)

get_page_logger("Carte mondiale (F6)")

# Échelle de couleurs continue, dans l'esprit éditorial vert de LaborScope.
# Volontairement SOMBRE et saturée : même la valeur minimale est un vert franc
# (pas de teinte claire qui se noierait dans le crème), jusqu'à un vert forêt
# très profond pour les fortes valeurs. Contraste fort et lisible.
ECHELLE_VERTE = [
    [0.0, "#3FA06C"],
    [0.25, "#1F8A52"],
    [0.5, "#0F7040"],
    [0.75, "#08552F"],
    [1.0, "#063620"],
]


def annee(periode: str) -> str:
    """Renvoie l'année d'une période (4 premiers chiffres) ou la période brute."""
    p = str(periode)
    return p[:4] if len(p) >= 4 and p[:4].isdigit() else p


# --- En-tête éditorial (cohérent avec les autres pages d'analyse) ------------
_fil_g, _fil_d = st.columns([0.7, 0.3], vertical_alignment="center")
with _fil_g:
    st.markdown(
        "<div class='ls-meta'>Observatoire &nbsp;·&nbsp; Marché du travail</div>",
        unsafe_allow_html=True,
    )
with _fil_d:
    if est_connecte():
        st.markdown(
            "<div style='text-align:right'><span class='ls-chip'>"
            "<span class='dot' style='background:#2E7257'></span>Espace privé</span></div>",
            unsafe_allow_html=True,
        )

_col_titre, _col_action = st.columns([0.76, 0.24], vertical_alignment="center")
with _col_titre:
    st.markdown(
        "<div class='ls-eyebrow'>Explorateur de données · ILOSTAT</div>", unsafe_allow_html=True
    )
    st.markdown(
        "<div class='ls-serif ls-title'>Le monde du travail, d'un coup d'œil.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='ls-subtitle'>Une carte interactive. Un code couleur par pays. "
        "Repérez les contrastes en un instant.</p>",
        unsafe_allow_html=True,
    )
emplacement_export = _col_action.empty()
st.write("")

# Cette analyse exige une connexion (le backend attend un jeton).
if not est_connecte():
    st.info("Connectez-vous pour accéder à la carte mondiale.")
    st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")
    st.stop()

ligne_source(
    ["Données réelles", "OIT · diffusion ILOSTAT"],
    f"Extrait du {date.today():%d/%m/%Y}",
)

indicateurs = get_indicateurs()
pays_referentiel = get_pays()
# Nom de pays -> code ISO-3 (les codes du référentiel sont des ISO-3 : FRA, DEU…),
# nécessaire pour positionner les pays sur la carte Plotly.
code_par_nom = {nom: code for nom, code in pays_referentiel.items()}

# Sexe fixé à « Ensemble » (affiché dans la légende, pas en filtre).
sexe_backend = SEXES["Ensemble"]

# --- Carte de filtres : Indicateur · Population · Période --------------------
with st.container(border=True):
    col_indic, col_pop, col_periode = st.columns([1.5, 1.4, 1.2])

    with col_indic:
        st.markdown("<div class='ls-flabel'>Indicateur</div>", unsafe_allow_html=True)
        code_indicateur = st.selectbox(
            "Indicateur",
            options=list(indicateurs),
            format_func=lambda code: indicateurs[code],
            label_visibility="collapsed",
        )

    with col_pop:
        label_classif = libelle_type_classification(code_indicateur)
        st.markdown(f"<div class='ls-flabel'>{label_classif}</div>", unsafe_allow_html=True)
        classifications = get_classifications(code_indicateur)
        libelle_classification = st.selectbox(
            label_classif,
            list(classifications),
            index=index_defaut(classifications),
            label_visibility="collapsed",
        )

    code_classification = classifications[libelle_classification]

    # --- Périodes disponibles : lues sur un pays bien couvert ----------------
    # Les données ILOSTAT sont éparses ; on cherche la première série non vide
    # parmi quelques pays à large couverture pour peupler le sélecteur d'années.
    periodes: list[str] = []
    for nom_ref in ("France", "Allemagne", "Espagne", "Italie", "Royaume-Uni"):
        code_ref = pays_referentiel.get(nom_ref)
        if not code_ref:
            continue
        reponse_evo = api_client.get(
            "/analyses/evolution",
            params={
                "code_indicateur": code_indicateur,
                "code_pays": code_ref,
                "sexe": sexe_backend,
                "code_classification": code_classification,
            },
        )
        if reponse_evo["status_code"] == 200:
            periodes = [point["periode"] for point in reponse_evo["data"].get("points", [])]
            if periodes:
                break
    periodes = sorted(dict.fromkeys(periodes))

    with col_periode:
        st.markdown(
            "<div class='ls-flabel'>Période<span class='muted'>annuelle</span></div>",
            unsafe_allow_html=True,
        )
        if periodes:
            periode = st.selectbox(
                "Période",
                periodes,
                index=len(periodes) - 1,
                format_func=annee,
                label_visibility="collapsed",
            )
        else:
            periode = None
            st.selectbox(
                "Période", ["Aucune donnée"], disabled=True, label_visibility="collapsed"
            )

if not periode:
    st.warning("Aucune donnée disponible pour cette sélection (indicateur / population).")
    st.stop()

# --- Appel du backend : /analyses/carte --------------------------------------
with st.spinner("Chargement de la carte…"):
    reponse = api_client.get(
        "/analyses/carte",
        params={
            "jeton": st.session_state.get("access_token"),
            "code_indicateur": code_indicateur,
            "periode": periode,
            "sexe": sexe_backend,
            "code_classification": code_classification,
        },
    )

if reponse["status_code"] in (401, 403):
    st.error("Session expirée ou accès refusé. Reconnectez-vous pour continuer.")
    st.stop()
if reponse["status_code"] == 404:
    st.warning(f"Aucune donnée disponible pour l'année {annee(periode)} avec cette sélection.")
    st.stop()
if reponse["status_code"] != 200:
    st.error(message_erreur(reponse))
    st.stop()

lignes = [
    {
        "Pays": serie["libelle"],
        "Code": code_par_nom.get(serie["libelle"]),
        "Valeur": serie["points"][0]["valeur"],
    }
    for serie in reponse["data"]["series"]
    if serie["points"]
]
df = pd.DataFrame(lignes)
# On ne garde que les pays dont on connaît le code ISO-3 (positionnables sur la carte).
df = df.dropna(subset=["Code"])

if df.empty:
    st.warning("Aucune donnée localisable pour cette sélection.")
    st.stop()

unite = unite_indicateur(code_indicateur)
suffixe = f" {unite}" if unite else ""
annee_carte = annee(periode)
df["Étiquette"] = df["Valeur"].map(format_fr)

# Coloriage par RANG (quantile), pas par valeur brute : les indicateurs sont des
# effectifs absolus (milliers), très asymétriques — un gros pays écrase l'échelle
# linéaire et tasse tous les autres dans la même teinte. Le rang normalisé (0→1)
# répartit les pays sur toute l'échelle de couleurs : chaque pays prend une nuance
# distincte. L'infobulle et l'export gardent la valeur réelle.
_n = len(df)
if _n > 1 and df["Valeur"].nunique() > 1:
    df["Rang"] = (df["Valeur"].rank(method="average") - 1) / (_n - 1)
else:
    df["Rang"] = 0.5

# Légende (colorbar) en valeurs réelles, posée aux seuils de quantiles.
_quantiles = [0.0, 0.25, 0.5, 0.75, 1.0]
_cb_tickvals = _quantiles
_cb_ticktext = [format_fr(df["Valeur"].quantile(q)) for q in _quantiles]

haut = df.loc[df["Valeur"].idxmax()]
bas = df.loc[df["Valeur"].idxmin()]

# Bouton d'export, désormais que les données sont prêtes.
emplacement_export.download_button(
    "Exporter les données",
    data=df[["Pays", "Code", "Valeur"]].to_csv(index=False).encode("utf-8"),
    file_name=f"carte_{code_indicateur}_{annee_carte}.csv",
    mime="text/csv",
    icon=":material/download:",
    type="primary",
    use_container_width=True,
)

# --- Trois cartes métriques (couverture · plus haut · plus bas) --------------
m1, m2, m3 = st.columns(3)
with m1:
    carte_metrique(
        "Pays couverts",
        str(len(df)),
        "",
        f"Observations · {annee_carte}",
        icone_svg=ICONE_GLOBE,
    )
with m2:
    carte_metrique(
        f"Valeur la plus élevée · {haut['Pays']}",
        format_fr(haut["Valeur"]),
        unite,
        f"Maximum · {annee_carte}",
        icone_svg=ICONE_CIBLE,
    )
with m3:
    carte_metrique(
        f"Valeur la plus basse · {bas['Pays']}",
        format_fr(bas["Valeur"]),
        unite,
        f"Minimum · {annee_carte}",
        icone_svg=ICONE_ECART,
    )

st.write("")

# --- Carte choroplèthe interactive -------------------------------------------
with st.container(border=True):
    tete_g, tete_d = st.columns([0.7, 0.3], vertical_alignment="center")
    with tete_g:
        st.markdown(
            "<div class='ls-eyebrow plain'>Répartition mondiale</div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='ls-serif' style='font-size:1.5rem'>{indicateurs[code_indicateur]}</div>",
            unsafe_allow_html=True,
        )
    with tete_d:
        if unite:
            st.markdown(
                f"<div style='text-align:right;margin-bottom:0.3rem'>"
                f"<span class='ls-pill'>En {unite}</span></div>",
                unsafe_allow_html=True,
            )

    st.caption(f"{libelle_classification} · Ensemble des sexes · {annee_carte}")

    fig = px.choropleth(
        df,
        locations="Code",
        locationmode="ISO-3",
        color="Rang",
        range_color=[0, 1],
        hover_name="Pays",
        custom_data=["Étiquette"],
        color_continuous_scale=ECHELLE_VERTE,
    )
    fig.update_traces(
        marker_line_color="#FBFAF5",
        marker_line_width=0.7,
        hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}" + suffixe + "<extra></extra>",
    )

    # Couche d'étiquettes : nom du pays posé sur son centroïde (si connu).
    # Texte blanc (lisible sur les verts foncés) pour les pays qui ont une valeur.
    df_labels = df[df["Code"].isin(CENTROIDES)].copy()
    if not df_labels.empty:
        fig.add_trace(
            go.Scattergeo(
                lon=[CENTROIDES[c][1] for c in df_labels["Code"]],
                lat=[CENTROIDES[c][0] for c in df_labels["Code"]],
                text=df_labels["Pays"],
                mode="text",
                textfont=dict(family="Inter, sans-serif", size=10, color="#FFFFFF"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    styliser_figure(fig, hauteur=560)
    fig.update_geos(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#E2E0D5",
        coastlinewidth=0.6,
        showcountries=True,
        countrycolor="#ECEAE0",
        countrywidth=0.5,
        showland=True,
        landcolor="#EFEEE6",        # pays sans donnée : crème neutre
        showocean=False,            # océan transparent -> fond de la carte
        showlakes=False,
        lataxis_showgrid=False,
        lonaxis_showgrid=False,
        projection_type="natural earth",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=6, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        coloraxis_colorbar=dict(
            title=dict(text=unite or "", side="top", font=dict(size=11, color="#5B6B63")),
            thickness=10,
            len=0.62,
            yanchor="middle",
            y=0.5,
            outlinewidth=0,
            tickmode="array",
            tickvals=_cb_tickvals,
            ticktext=_cb_ticktext,
            ticks="outside",
            ticklen=3,
            tickcolor="#D8D6CC",
            tickfont=dict(size=11, color="#5B6B63"),
        ),
    )
    afficher_graphique(fig)

st.caption(
    f"L'intensité du vert reflète le **classement** des pays (quantiles) pour "
    f"« {indicateurs[code_indicateur]} » en {annee_carte} — ce rang évite qu'un pays "
    f"très peuplé n'écrase l'échelle. Survolez un pays pour lire sa valeur exacte "
    f"(la légende indique les seuils en {unite.lower() if unite else 'valeur'})."
)
