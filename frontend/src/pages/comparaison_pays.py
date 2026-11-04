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
    libelle_type_classification,
    message_erreur,
    unite_indicateur,
)
from utils.rapport_pdf import construire_rapport_pdf, figure_png
from utils.ui import (
    ICONE_CIBLE,
    ICONE_ECART,
    ICONE_TENDANCE,
    PALETTE_GRAPHIQUE,
    afficher_graphique,
    carte_a_retenir,
    carte_metrique,
    chip,
    est_connecte,
    fmt_fr as format_fr,
    ligne_source,
    styliser_figure,
)

get_page_logger("Comparaison Pays (F4)")


# --- Petits utilitaires de présentation --------------------------------------

def annee(periode: str) -> str:
    """Renvoie l'année d'une période (4 premiers chiffres) ou la période brute."""
    p = str(periode)
    return p[:4] if len(p) >= 4 and p[:4].isdigit() else p


def nom_court_indicateur(description: str) -> str:
    """Nom court et lisible d'un indicateur, pour les cartes et « À retenir ».

    « Emploi par sexe et profession » -> « Emploi » ; « Population en âge de
    travailler… » -> « Population » ; « Taux de chômage » -> « Chômage ».
    """
    texte = description.strip()
    for prefixe in ("Taux de ", "Taux d'", "Taux ", "Nombre de ", "Nombre d'"):
        if texte.lower().startswith(prefixe.lower()):
            reste = texte[len(prefixe):]
            return reste[:1].upper() + reste[1:]
    base = texte.split(" par ")[0].strip()      # retire « … par sexe et âge »
    if len(base) > 22:                            # encore trop long -> 1er mot
        base = base.split()[0]
    return base[:1].upper() + base[1:]


# --- En-tête éditorial (constant sur les pages d'analyse) --------------------
# Fil d'Ariane discret repris des maquettes.
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
emplacement_pdf = _col_action.empty()
st.write("")

# Cette analyse exige une connexion (le backend attend un jeton).
if not est_connecte():
    st.info("Connectez-vous pour accéder à la comparaison entre pays.")
    st.page_link("pages/login.py", label="Se connecter", icon=":material/lock:")
    st.stop()

ligne_source(
    ["Données réelles", "OIT · diffusion ILOSTAT"],
    f"Extrait du {date.today():%d/%m/%Y}",
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
# Défaut : des pays couverts par les deux indicateurs (comparaison parlante d'emblée).
_defaut_pays = [n for n in ("France", "Allemagne", "Espagne") if n in pays_referentiel][:3] or _options_pays[:3]

# Sexe fixé à « Ensemble » (affiché dans le sous-titre du graphique, pas en filtre).
sexe_backend = SEXES["Ensemble"]

# --- Carte de filtres : Pays · Indicateur · Période · Population --------------
with st.container(border=True):
    col_pays, col_indic, col_periode, col_pop = st.columns([1.5, 1.3, 1.4, 1.2])

    with col_pays:
        noms_courants = st.session_state.get("f4_pays", _defaut_pays)
        st.markdown(
            "<div class='ls-flabel'>Pays"
            f"<span class='muted'>{len(noms_courants)} / 5</span></div>",
            unsafe_allow_html=True,
        )
        with st.popover(
            ", ".join(noms_courants) or "Choisir des pays",
            use_container_width=True,
        ):
            st.caption("Sélectionnez de 1 à 5 pays")
            st.multiselect(
                "Pays",
                options=_options_pays,
                default=_defaut_pays,
                max_selections=5,
                key="f4_pays",
                label_visibility="collapsed",
                placeholder="Rechercher un pays…",
            )

    with col_indic:
        st.markdown("<div class='ls-flabel'>Indicateur</div>", unsafe_allow_html=True)
        code_indicateur = st.selectbox(
            "Indicateur",
            options=list(indicateurs),
            format_func=lambda code: indicateurs[code],
            label_visibility="collapsed",
        )

    with col_pop:
        # Libellé cohérent avec l'indicateur : « Population » (âge) ou « Profession ».
        label_classif = libelle_type_classification(code_indicateur)
        st.markdown(f"<div class='ls-flabel'>{label_classif}</div>", unsafe_allow_html=True)
        classifications = get_classifications(code_indicateur)
        libelle_classification = st.selectbox(
            label_classif,
            list(classifications),
            index=index_defaut(classifications),
            label_visibility="collapsed",
        )

    noms_pays = st.session_state.get("f4_pays", _defaut_pays)
    code_classification = classifications[libelle_classification]

    # --- Périodes disponibles : lues sur l'évolution du 1er pays sélectionné ---
    # Ce même appel sert aussi à la carte « Évolution » (pays focus).
    periodes: list[str] = []
    evolution_focus: dict[str, float] = {}
    pays_focus = noms_pays[0] if noms_pays else None
    if pays_focus:
        reponse_evo = api_client.get(
            "/analyses/evolution",
            params={
                "code_indicateur": code_indicateur,
                "code_pays": pays_referentiel[pays_focus],
                "sexe": sexe_backend,
                "code_classification": code_classification,
            },
        )
        if reponse_evo["status_code"] == 200:
            for point in reponse_evo["data"].get("points", []):
                periodes.append(point["periode"])
                evolution_focus[point["periode"]] = point["valeur"]
    periodes = sorted(dict.fromkeys(periodes))

    with col_periode:
        st.markdown(
            "<div class='ls-flabel'>Période<span class='muted'>annuelle</span></div>",
            unsafe_allow_html=True,
        )
        if periodes:
            sc1, sc2 = st.columns(2)
            p_debut = sc1.selectbox(
                "Début", periodes, index=0, format_func=annee, label_visibility="collapsed"
            )
            p_fin = sc2.selectbox(
                "Fin", periodes, index=len(periodes) - 1, format_func=annee,
                label_visibility="collapsed",
            )
            if p_fin < p_debut:
                p_debut, p_fin = p_fin, p_debut
        else:
            p_debut = p_fin = None
            st.selectbox(
                "Période", ["Aucune donnée"], disabled=True, label_visibility="collapsed"
            )

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
    # Callback : on modifie la sélection AVANT que le multiselect ne soit réinstancié
    # (interdit de modifier la clé d'un widget après sa création dans le même run).
    def _reinitialiser_pays():
        st.session_state["f4_pays"] = _defaut_pays

    st.button("Réinitialiser", icon=":material/restart_alt:",
              use_container_width=True, on_click=_reinitialiser_pays)

if len(noms_pays) < 2:
    st.info("Sélectionnez au moins deux pays pour lancer la comparaison.")
    st.stop()

if not periodes or p_fin is None:
    st.warning("Aucune donnée disponible pour cette sélection (indicateur / population).")
    st.stop()

# --- Appel du backend : /analyses/comparaison-pays ---------------------------
# On vise l'année de fin (comparaison « à année commune »). Les données ILOSTAT
# étant éparses selon les pays, si moins de deux pays ont une valeur cette
# année-là, on bascule sur la dernière valeur disponible de chaque pays.
_codes_pays = [pays_referentiel[nom] for nom in noms_pays]


def _charger_comparaison(periode: str | None) -> dict:
    params = {
        "jeton": st.session_state.get("access_token"),
        "code_indicateur": code_indicateur,
        "codes_pays": _codes_pays,
        "sexe": sexe_backend,
        "code_classification": code_classification,
    }
    if periode is not None:
        params["periode"] = periode
    return api_client.get("/analyses/comparaison-pays", params=params)


def _lignes(reponse: dict) -> list[dict]:
    if reponse["status_code"] != 200:
        return []
    return [
        {
            "Pays": serie["libelle"],
            "Valeur": serie["points"][0]["valeur"],
            "Période": serie["points"][0]["periode"],
        }
        for serie in reponse["data"]["series"]
        if serie["points"]
    ]


with st.spinner("Chargement des données…"):
    reponse = _charger_comparaison(p_fin)
if reponse["status_code"] in (401, 403):
    st.error("Session expirée ou accès refusé. Reconnectez-vous pour continuer.")
    st.stop()
if reponse["status_code"] == 0:
    st.error(message_erreur(reponse))
    st.stop()

lignes = _lignes(reponse)
annee_commune = True
if len(lignes) < 2:
    with st.spinner("Chargement des données…"):
        reponse_repli = _charger_comparaison(None)
    lignes_repli = _lignes(reponse_repli)
    if len(lignes_repli) > len(lignes):
        lignes, annee_commune = lignes_repli, False

if not lignes:
    st.warning("Aucune donnée disponible pour cette sélection.")
    st.stop()

df = pd.DataFrame(lignes)
unite = unite_indicateur(code_indicateur)
# Pour un taux en %, l'écart se lit « en points » ; sinon on garde l'unité.
unite_ecart = "pts" if unite == "%" else unite
mot_variation = "écart en points" if unite == "%" else "variation"
indic_court = nom_court_indicateur(indicateurs[code_indicateur])
annee_fin = annee(p_fin)
annee_debut = annee(p_debut)

haut, bas = df.loc[df["Valeur"].idxmax()], df.loc[df["Valeur"].idxmin()]
ecart = haut["Valeur"] - bas["Valeur"]
# Un écart n'a de sens que si au moins deux pays ont une valeur pour la sélection.
comparaison_possible = len(df) >= 2
if not comparaison_possible:
    st.info(
        f"Seul **{df.iloc[0]['Pays']}** dispose de données pour cette sélection "
        "(indicateur, population et période). Ajoutez un pays comparable ou changez "
        "de population pour visualiser un écart."
    )

# Valeur et évolution du pays focus (1er sélectionné), calculées sur /evolution.
valeur_focus = evolution_focus.get(p_fin)
delta_focus = (
    evolution_focus.get(p_fin, 0) - evolution_focus.get(p_debut, 0)
    if p_debut in evolution_focus and p_fin in evolution_focus
    else None
)

# Bouton d'export dans l'en-tête, désormais que les données sont disponibles.
emplacement_export.download_button(
    "Exporter les données",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"comparaison_{code_indicateur}_{annee_fin}.csv",
    mime="text/csv",
    icon=":material/download:",
    type="primary",
    use_container_width=True,
)

# --- Trois cartes métriques (pays focus · évolution · écart) ---
m1, m2, m3 = st.columns(3)
with m1:
    carte_metrique(
        f"{indic_court} · {pays_focus}",
        format_fr(valeur_focus) if valeur_focus is not None else "—",
        unite,
        f"Dernière observation · {annee_fin}",
        icone_svg=ICONE_CIBLE,
    )
with m2:
    carte_metrique(
        f"Évolution · {pays_focus}",
        (("+" if delta_focus > 0 else "") + format_fr(delta_focus)) if delta_focus is not None else "—",
        unite_ecart if delta_focus is not None else "",
        f"{annee_debut} → {annee_fin} · {mot_variation}",
        icone_svg=ICONE_TENDANCE,
    )
with m3:
    carte_metrique(
        "Écart entre les pays",
        format_fr(ecart) if comparaison_possible else "—",
        unite_ecart if comparaison_possible else "",
        (f"Maximum − minimum · {annee_fin}" if annee_commune
         else "Maximum − minimum · dernières valeurs") if comparaison_possible
        else "un seul pays disponible",
        icone_svg=ICONE_ECART,
    )

st.write("")

# --- Graphique + panneau « À retenir » ---
col_chart, col_aside = st.columns([0.74, 0.26], gap="large")

with col_chart:
    with st.container(border=True):
<<<<<<< HEAD
        st.markdown(
            "<div class='ls-eyebrow plain'>Comparaison entre pays</div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='ls-serif' style='font-size:1.5rem'>{indicateurs[code_indicateur]}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{libelle_classification} · {libelle_sexe} · {periode} · année commune")
=======
        tete_g, tete_d = st.columns([0.62, 0.38], vertical_alignment="center")
        with tete_g:
            st.markdown("<div class='ls-eyebrow plain'>Comparaison entre pays</div>", unsafe_allow_html=True)
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
            sens = st.segmented_control(
                "Tri", ["Décroissant", "Croissant"], default="Décroissant",
                label_visibility="collapsed",
            )
>>>>>>> cee9590c5cf3aadc47445192cb78e59cee250a3c

        contexte_periode = (
            f"{annee_fin} · année commune" if annee_commune
            else "dernière année disponible par pays"
        )
        st.caption(
            f"{libelle_classification} · Ensemble des sexes · {contexte_periode}"
        )

        croissant = sens == "Croissant"
        # Barres horizontales : la plus longue en haut quand « Décroissant ».
        df_graph = df.sort_values("Valeur", ascending=croissant).copy()
        df_graph["Étiquette"] = df_graph["Valeur"].map(format_fr)  # virgule française
        fig = px.bar(
            df_graph,
            x="Valeur",
            y="Pays",
            orientation="h",
            color="Pays",
            color_discrete_map=couleur_par_pays,
            text="Étiquette",
            labels={"Valeur": f"Valeur ({unite})" if unite else "Valeur"},
        )
        fig.update_traces(
<<<<<<< HEAD
            texttemplate="%{text:.1f}",
            textposition="outside",
            cliponaxis=False,
            marker_line_width=0,
=======
            textposition="outside", cliponaxis=False, marker_line_width=0,
            marker_cornerradius=6,  # barres aux coins arrondis (plus « produit »)
            textfont=dict(color="#1F2A26"),
>>>>>>> cee9590c5cf3aadc47445192cb78e59cee250a3c
        )
        fig.update_layout(showlegend=False)
        styliser_figure(fig, hauteur=400)
        # Marge à droite pour que les étiquettes des barres ne soient pas coupées.
        fig.update_xaxes(showticklabels=False, range=[0, df["Valeur"].max() * 1.15])
        afficher_graphique(fig)

with col_aside:
    df_retenir = df.sort_values("Valeur", ascending=False)
    suffixe = f" {unite}" if unite else ""
    lignes_retenir = [
        (
            r["Pays"],
<<<<<<< HEAD
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
=======
            # En repli (années différentes), on précise l'année de chaque pays.
            f"{format_fr(r['Valeur'])}{suffixe}"
            + ("" if annee_commune else f" ({annee(r['Période'])})"),
            couleur_par_pays.get(r["Pays"], PALETTE_GRAPHIQUE[0]),
        )
        for _, r in df_retenir.iterrows()
    ]
    if not comparaison_possible:
        note = (
            f"Seul {df.iloc[0]['Pays']} dispose de données pour cette sélection. "
            "Ajoutez un pays comparable pour mesurer un écart."
        )
        bas_note = (
            f"Valeur exprimée en {unite.lower()}, pour l'ensemble des sexes."
            if unite else "Valeur pour l'ensemble des sexes."
        )
    elif annee_commune:
        note = (
            f"En {annee_fin}, {haut['Pays']} devance {bas['Pays']} de "
            f"{format_fr(ecart)} {unite_ecart}."
        )
        bas_note = (
            f"Valeurs exprimées en {unite.lower()}, à l'année commune {annee_fin}, "
            "pour l'ensemble des sexes."
            if unite else
            f"Valeurs à l'année commune {annee_fin}, pour l'ensemble des sexes."
        )
    else:
        note = (
            f"Dernières valeurs disponibles par pays : {haut['Pays']} devance "
            f"{bas['Pays']} de {format_fr(ecart)} {unite_ecart}."
        )
        bas_note = (
            f"Les années diffèrent selon les pays (donnée {indicateurs[code_indicateur].lower()} "
            "éparse) ; chaque valeur indique son année entre parenthèses."
        )
    entete_retenir = f"{indic_court.upper()} · {annee_fin if annee_commune else 'DERNIÈRES VALEURS'}"
    carte_a_retenir(entete_retenir, lignes_retenir, note=note, bas=bas_note)

# --- Rapport PDF (généré côté front à partir des données affichées) ---
periode_txt = annee_fin if annee_debut == annee_fin else f"{annee_debut} - {annee_fin}"
chiffres_pdf = [
    (f"{indic_court} · {pays_focus}",
     f"{format_fr(valeur_focus)} {unite}".strip() if valeur_focus is not None else "—"),
    (f"Évolution · {pays_focus}",
     (("+" if delta_focus > 0 else "") + f"{format_fr(delta_focus)} {unite_ecart}").strip()
     if delta_focus is not None else "—"),
    ("Écart entre les pays",
     f"{format_fr(ecart)} {unite_ecart}".strip() if comparaison_possible else "—"),
]
lignes_pdf = [
    [r["Pays"], format_fr(r["Valeur"]), annee(r["Période"])]
    for _, r in df_retenir.iterrows()
]
pdf_bytes = construire_rapport_pdf(
    titre="Comparaison entre pays",
    sous_titre=indicateurs[code_indicateur],
    contexte=[
        ("Indicateur", indicateurs[code_indicateur]),
        ("Pays", ", ".join(noms_pays)),
        ("Période", periode_txt),
        (libelle_type_classification(code_indicateur), libelle_classification),
        ("Sexe", "Ensemble des sexes"),
    ],
    colonnes=["Pays", f"Valeur ({unite})" if unite else "Valeur", "Année"],
    lignes=lignes_pdf,
    chiffres=chiffres_pdf,
    note=f"{note} {bas_note}".strip(),
    image_png=figure_png(fig),
    legende_graphique=f"{libelle_classification} · Ensemble des sexes · {contexte_periode}",
)
emplacement_pdf.download_button(
    "Rapport PDF",
    data=pdf_bytes,
    file_name=f"rapport_comparaison_{code_indicateur}_{annee_fin}.pdf",
    mime="application/pdf",
    icon=":material/picture_as_pdf:",
    use_container_width=True,
)
>>>>>>> cee9590c5cf3aadc47445192cb78e59cee250a3c
