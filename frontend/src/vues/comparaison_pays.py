from datetime import date

import pandas as pd
import plotly.express as px
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
    ICONE_CIBLE,
    ICONE_ECART,
    ICONE_TENDANCE,
    PALETTE_GRAPHIQUE,
    afficher_graphique,
    carte_a_retenir,
    carte_metrique,
    chip,
    est_connecte,
    ligne_source,
    notif,
    styliser_figure,
)
from utils.ui import (
    fmt_fr as format_fr,
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
    notif("Connectez-vous pour accéder à la comparaison entre pays.", "info")
    st.page_link("vues/login.py", label="Se connecter", icon=":material/lock:")
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
    notif("Sélectionnez au moins deux pays pour lancer la comparaison.", "info")
    st.stop()

if not periodes or p_fin is None:
    notif("Aucune donnée disponible pour cette sélection (indicateur / population).", "warn")
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
    notif("Session expirée ou accès refusé. Reconnectez-vous pour continuer.", "ko")
    st.stop()
if reponse["status_code"] == 0:
    notif(message_erreur(reponse), "ko")
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
    notif("Aucune donnée disponible pour cette sélection.", "warn")
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
    notif(
        f"Seul {df.iloc[0]['Pays']} dispose de données pour cette sélection "
        "(indicateur, population et période). Ajoutez un pays comparable ou changez "
        "de population pour visualiser un écart.",
        "info",
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
            textposition="outside", cliponaxis=False, marker_line_width=0,
            marker_cornerradius=0,  # barres à angles vifs (cohérent avec l'interface)
            textfont=dict(color="#1F2A26"),
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

# =====================================================================
# Taux d'emploi : évolution et variations entre pays
# =====================================================================
st.divider()
st.subheader("Taux d'emploi — comparaison entre pays")
st.caption("Taux d'emploi = Emploi (toutes professions) / Population (15 ans et plus) × 100")

col_t4a, col_t4b, col_t4c = st.columns([1.2, 1, 1])
with col_t4a:
    libelle_taux4 = st.selectbox(
        "Série à comparer",
        ["Taux total", "Hommes", "Femmes"],
        key="f4_taux_serie",
    )
with col_t4b:
    nb_periodes_taux4 = st.slider(
        "Nombre d'années", min_value=2, max_value=13, value=10, key="f4_taux_n"
    )
with col_t4c:
    sens_taux4 = st.segmented_control(
        "Affichage", ["Évolution", "Variations"], default="Évolution",
        key="f4_taux_sens",
        label_visibility="collapsed",
    )

st.write("")

_clé_taux = {"Taux total": "taux_total", "Hommes": "taux_homme", "Femmes": "taux_femme"}
_clé_var = {
    "Taux total": "variation_taux_total",
    "Hommes": "variation_taux_homme",
    "Femmes": "variation_taux_femme",
}
cle_taux = _clé_taux[libelle_taux4]
cle_var = _clé_var[libelle_taux4]

# Appel API pour chaque pays sélectionné
lignes_taux4 = []
pays_taux_sans = []
with st.spinner("Calcul des taux d'emploi…"):
    for nom in noms_pays:
        rep = api_client.get(
            "/analyses/taux-emploi",
            params={
                "code_pays": pays_referentiel[nom],
                "nb_periodes": nb_periodes_taux4,
            },
        )
        if rep["status_code"] in (401, 403):
            notif("Session expirée ou accès refusé. Reconnectez-vous pour continuer.", "ko")
            st.stop()
        if rep["status_code"] == 200:
            data = rep["data"]
            for pt in data[cle_taux]:
                lignes_taux4.append({"Période": pt["periode"], "Pays": nom, "Valeur": pt["taux"], "_type": "taux"})
            for pt in data[cle_var]:
                lignes_taux4.append({"Période": pt["periode"], "Pays": nom, "Valeur": pt["taux"], "_type": "var"})
        else:
            pays_taux_sans.append(nom)

if pays_taux_sans:
    notif("Taux non calculable pour : " + ", ".join(pays_taux_sans), "warn")

lignes_taux = [r for r in lignes_taux4 if r["_type"] == "taux"]
lignes_var = [r for r in lignes_taux4 if r["_type"] == "var"]

if not lignes_taux:
    notif("Aucun taux d'emploi calculable pour les pays sélectionnés.", "info")
    st.stop()

df_taux = pd.DataFrame(lignes_taux).sort_values("Période")
df_var = pd.DataFrame(lignes_var).sort_values("Période") if lignes_var else pd.DataFrame()

# --- Cartes métriques : dernière valeur par pays ---
dernieres = df_taux.groupby("Pays")["Valeur"].last().sort_values(ascending=False)
annee_derniere = df_taux["Période"].max()[:4] if not df_taux.empty else ""

cartes = st.columns(min(len(dernieres), 5))
for i, (nom_p, val_p) in enumerate(dernieres.items()):
    with cartes[i]:
        carte_metrique(
            nom_p,
            f"{val_p:.1f}",
            "%",
            f"{libelle_taux4} · {annee_derniere}",
            icone_svg=ICONE_CIBLE,
        )

st.write("")

# --- Graphique principal : évolution ou variations ---
with st.container(border=True):
    tete_g, tete_d = st.columns([0.62, 0.38], vertical_alignment="center")
    with tete_g:
        st.markdown("<div class='ls-eyebrow plain'>Taux d'emploi</div>", unsafe_allow_html=True)
        titre_graph = (
            f"Évolution — {libelle_taux4}" if sens_taux4 == "Évolution"
            else f"Variations annuelles — {libelle_taux4}"
        )
        st.markdown(
            f"<div class='ls-serif' style='font-size:1.5rem'>{titre_graph}</div>",
            unsafe_allow_html=True,
        )
    with tete_d:
        unite_aff = "En %" if sens_taux4 == "Évolution" else "En points"
        st.markdown(
            f"<div style='text-align:right;margin-bottom:0.3rem'><span class='ls-pill'>{unite_aff}</span></div>",
            unsafe_allow_html=True,
        )

    st.caption(f"{len(noms_pays)} pays · {nb_periodes_taux4} dernières années · Taux = Emploi / Population (15+) × 100")

    if sens_taux4 == "Évolution":
        fig_taux4 = px.line(
            df_taux,
            x="Période",
            y="Valeur",
            color="Pays",
            markers=True,
            labels={"Valeur": "Taux d'emploi (%)"},
            color_discrete_sequence=PALETTE_GRAPHIQUE,
        )
    else:
        if df_var.empty:
            st.info("Pas assez de périodes pour calculer les variations.")
            st.stop()
        fig_taux4 = px.line(
            df_var,
            x="Période",
            y="Valeur",
            color="Pays",
            markers=True,
            labels={"Valeur": "Variation (points)"},
            color_discrete_sequence=PALETTE_GRAPHIQUE,
        )
        fig_taux4.add_hline(y=0, line_dash="dash", line_color="#999", line_width=1)

    fig_taux4.update_xaxes(type="category")
    fig_taux4.update_traces(line=dict(width=2.5), marker=dict(size=7))
    styliser_figure(fig_taux4, hauteur=400)
    afficher_graphique(fig_taux4)

# --- Tableau détaillé ---
with st.expander("Voir les données brutes"):
    st.dataframe(
        df_taux.pivot_table(index="Période", columns="Pays", values="Valeur"),
        use_container_width=True,
    )
    if not df_var.empty:
        st.markdown("**Variations annuelles (points)**")
        st.dataframe(
            df_var.pivot_table(index="Période", columns="Pays", values="Valeur"),
            use_container_width=True,
        )

# --- Rapport PDF ---
st.write("")
if st.button("Rapport PDF (comparaison taux d'emploi)", icon=":material/picture_as_pdf:", key="f4_btn_pdf_taux"):
    chiffres_pdf4 = []
    for nom_p, val_p in dernieres.items():
        chiffres_pdf4.append((nom_p, f"{val_p:.1f}%"))

    lignes_pdf4 = []
    periodes4 = sorted(df_taux["Période"].unique())
    for per in periodes4:
        ligne = [per[:4]]
        for nom in noms_pays:
            val = df_taux[(df_taux["Période"] == per) & (df_taux["Pays"] == nom)]["Valeur"]
            ligne.append(f"{val.iloc[0]:.1f}%" if not val.empty else "—")
        lignes_pdf4.append(ligne)

    colonnes_pdf4 = ["Année"] + noms_pays

    if len(dernieres) >= 2:
        note4 = (
            f"Comparaison du taux d'emploi ({libelle_taux4}) entre {len(noms_pays)} pays. "
            f"En {annee_derniere}, le plus élevé est {dernieres.index[0]} ({dernieres.iloc[0]:.1f}%) "
            f"et le plus bas est {dernieres.index[-1]} ({dernieres.iloc[-1]:.1f}%)."
        )
    else:
        note4 = f"Taux d'emploi ({libelle_taux4}) pour {noms_pays[0]} en {annee_derniere} : {dernieres.iloc[0]:.1f}%."

    pdf4 = construire_rapport_pdf(
        titre="Taux d'emploi — comparaison",
        sous_titre=f"{libelle_taux4} · {annee_derniere}",
        contexte=[
            ("Série", libelle_taux4),
            ("Pays", ", ".join(noms_pays)),
            ("Période", f"{periodes4[0][:4]} - {periodes4[-1][:4]}" if periodes4 else "—"),
            ("Formule", "Emploi / Population (15+) x 100"),
            ("Source", "OIT - ILOSTAT"),
        ],
        colonnes=colonnes_pdf4,
        lignes=lignes_pdf4,
        chiffres=chiffres_pdf4[:4] or None,
        note=note4,
        image_png=figure_png(fig_taux4),
        legende_graphique=f"{libelle_taux4} · {len(noms_pays)} pays",
    )
    st.download_button(
        label="Télécharger le rapport PDF",
        data=pdf4,
        file_name=f"rapport_taux_comparaison_{libelle_taux4.replace(' ', '_')}.pdf",
        mime="application/pdf",
        icon=":material/download:",
        key="f4_dl_taux",
    )
