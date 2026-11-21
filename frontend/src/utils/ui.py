"""Système de design partagé par toutes les pages.

Identité : sobre et professionnelle. Fond crème, barre latérale vert forêt,
un seul accent vert, cartes blanches à angles vifs (aucun arrondi), police
unique Schibsted Grotesk (les titres se distinguent par le poids et
l'interlettrage). Aucun emoji ; les icônes sont des traits Material
(:material/...:) ou des SVG inline. Les explications passent par des bulles
d'aide « ? » (``aide``) plutôt que par du texte permanent.

Ce module centralise l'injection CSS, la barre latérale, les en-têtes et les
composants (cartes, métriques, pastilles, « À retenir ») pour éviter toute
duplication.
"""

import html

import streamlit as st

# Libellés de rôle utilisés par la navigation (cf. app.py et login.py).
ROLE_ADMIN = "Administrateur"
ROLE_UTILISATEUR = "Utilisateur"

# --- Palette ----------------------------------------------------------------
VERT = "#2E7257"  # accent principal (boutons, pastilles, liens)
VERT_FONCE = "#215540"  # survol / variantes foncées
ENCRE = "#1F2A26"  # titres
TEXTE = "#39443F"  # corps de texte
TEXTE_DOUX = "#8A938D"  # légendes, libellés discrets
CREME = "#F4F3EE"  # fond principal
BORDURE = "#E7E6DD"  # bordures de cartes
SIDEBAR = "#143529"  # fond barre latérale

# Séquence de couleurs des graphiques : palette sobre et désaturée, menée par le
# vert, de teintes feutrées (data-journalisme) pour distinguer les séries sans
# surcharge chromatique.
PALETTE_GRAPHIQUE = [
    "#2E7257",  # vert (teinte principale)
    "#9C6B4A",  # terre sourde
    "#4E7C8C",  # bleu ardoise
    "#857A98",  # violet feutré
    "#94803F",  # ocre discret
    "#5C6862",  # ardoise neutre
    "#71905E",  # olive doux
    "#7E564A",  # brun sobre
]


def est_connecte() -> bool:
    """Indique si un utilisateur est connecté (jeton présent en session)."""
    return bool(st.session_state.get("access_token"))


def est_admin() -> bool:
    """Indique si l'utilisateur connecté est administrateur."""
    return st.session_state.get("role_utilisateur") == ROLE_ADMIN


def deconnexion() -> None:
    """Purge la session de connexion et recharge l'application."""
    for cle in ("access_token", "role_utilisateur", "nom_utilisateur"):
        st.session_state.pop(cle, None)
    st.rerun()


# --- Styles globaux ---------------------------------------------------------


def injecter_styles() -> None:
    """Injecte les polices et les styles globaux. À appeler une fois par rerun."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Schibsted+Grotesk:wght@500;600;700;800&display=swap');

        /* Appairage : Inter pour le texte courant, Schibsted Grotesk pour
           l'affichage (titres, chiffres, marque) — défini plus bas. */
        html, body, .stApp, button, input, select, textarea,
        [data-testid="stMarkdownContainer"] {
            font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
        }
        /* Restaure la police des icônes Material (sinon elles s'affichent en texte). */
        span[data-testid="stIconMaterial"], .material-symbols-rounded,
        [class*="material-symbols"], i.material-icons {
            font-family: 'Material Symbols Rounded', 'Material Icons' !important;
        }

        /* Fond crème + zone de travail large (place aux graphiques). */
        .stApp { background: #F4F3EE; }
        .block-container {
            max-width: 1480px; padding-top: 2.6rem; padding-bottom: 4rem;
            padding-left: 3rem; padding-right: 3rem;
        }

        /* Titres : même police, poids fort + interlettrage resserré (effet display). */
        h1, h2, h3, h4,
        .ls-serif { font-family: 'Schibsted Grotesk', sans-serif !important; color: #1F2A26;
            font-weight: 700; letter-spacing: -0.018em; }
        h1 { font-weight: 800; letter-spacing: -0.022em; }

        /* Sur-titre « eyebrow » : petite capitale verte espacée. */
        .ls-eyebrow {
            display: flex; align-items: center; gap: 0.5rem;
            font-size: 0.72rem; font-weight: 700; letter-spacing: 0.13em;
            text-transform: uppercase; color: #2E7257; margin-bottom: 0.5rem;
        }
        .ls-eyebrow::before {
            content: ""; width: 7px; height: 7px; border-radius: 50%;
            background: #2E7257; display: inline-block;
        }
        .ls-eyebrow.plain::before { display: none; }

        .ls-title { font-size: 2.9rem; line-height: 1.05; margin: 0 0 0.3rem 0; }
        .ls-subtitle { color: #8A938D; font-size: 1.05rem; margin: 0; }

        /* Barre de contexte (sources, date d'extraction). */
        .ls-meta { color: #8A938D; font-size: 0.85rem; }
        .ls-meta .dot { color: #2E7257; }

        /* Cartes blanches, angles vifs (sobre, architectural). */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF; border: 1px solid #E7E6DD; border-radius: 0;
            box-shadow: 0 1px 2px rgba(31,42,38,0.03);
        }

        /* Boutons : vert plein pour l'action primaire, discret sinon. Angles vifs. */
        .stButton > button[kind="primary"],
        .stForm [data-testid="stFormSubmitButton"] button[kind="primary"] {
            background: #2E7257; border: 1px solid #2E7257; color: #fff;
            border-radius: 0; font-weight: 600;
        }
        .stButton > button[kind="primary"]:hover { background: #215540; border-color: #215540; }
        .stButton > button[kind="secondary"] {
            background: #fff; border: 1px solid #E7E6DD; color: #1F2A26;
            border-radius: 0; font-weight: 600;
        }
        .stButton > button[kind="secondary"]:hover { border-color: #2E7257; color: #215540; }

        /* Champs et menus : bordure nette, angles vifs. */
        [data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {
            border-radius: 0; border-color: #E7E6DD;
        }
        /* Libellés de champs (au-dessus des selects) : petite capitale. */
        .stSelectbox label p, .stMultiSelect label p, .stTextInput label p,
        .stSlider label p, .stNumberInput label p {
            font-weight: 600; color: #39443F;
        }
        /* Libellé de filtre personnalisé (avec compteur / unité à droite). */
        .ls-flabel {
            display:flex; align-items:baseline; justify-content:space-between;
            font-weight:600; color:#39443F; font-size:0.92rem; margin-bottom:0.35rem;
        }
        .ls-flabel .muted { color:#A7AEA8; font-weight:500; font-size:0.78rem; }
        /* Pastille d'unité (« En % ») au-dessus du graphique. */
        .ls-pill {
            display:inline-block; background:#F4F3EE; border:1px solid #E7E6DD;
            border-radius:0; padding:0.15rem 0.6rem; font-size:0.78rem;
            font-weight:600; color:#5C6862;
        }
        /* Marqueur d'aide « ? » (bulle au survol) : remplace le texte permanent. */
        .ls-help {
            display:inline-flex; align-items:center; justify-content:center;
            width:15px; height:15px; margin-left:0.35rem; border:1px solid #CBD3CC;
            color:#8A938D; font-size:0.66rem; font-weight:700; line-height:1;
            cursor:help; vertical-align:middle;
        }
        .ls-help:hover { border-color:#2E7257; color:#2E7257; }

        /* Notifications à plat, couleur sémantique nette (bord gauche marqué). */
        .ls-notif {
            display:flex; gap:0.6rem; align-items:flex-start; padding:0.7rem 0.9rem;
            border:1px solid; border-left-width:4px; font-size:0.92rem; line-height:1.45;
            margin:0.3rem 0 0.6rem; font-weight:500;
        }
        .ls-notif .ic { flex:0 0 auto; line-height:0; margin-top:1px; }
        .ls-notif .msg { color:inherit; }
        .ls-notif.ok   { background:#EBF4EE; border-color:#2E7257; color:#1C5540; }
        .ls-notif.ko   { background:#FBEBE8; border-color:#C0392B; color:#8E2A1E; }
        .ls-notif.warn { background:#FAF2DC; border-color:#B07D16; color:#6B5210; }
        .ls-notif.info { background:#EEF1EF; border-color:#5C6862; color:#39443F; }

        /* Métriques natives (st.metric) : chiffre en serif. */
        [data-testid="stMetricValue"] { font-family: 'Schibsted Grotesk', sans-serif;
            font-weight: 700; color: #1F2A26; }
        [data-testid="stMetricLabel"] p { color: #8A938D; font-weight: 600; }

        /* ---- Barre latérale sombre ---- */
        [data-testid="stSidebar"] { border-right: none; }
        [data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }

        /* Navigation (st.navigation) stylée en « pills » soignées. */
        [data-testid="stSidebarNav"] { margin-top: 0.2rem; }
        [data-testid="stSidebarNav"] ul { gap: 3px; }
        [data-testid="stSidebarNav"] a {
            position: relative; border-radius: 0; padding: 0.5rem 0.8rem 0.5rem 0.95rem;
            color: #9DB3A6 !important; font-weight: 500; font-size: 0.93rem;
        }
        [data-testid="stSidebarNav"] a:hover {
            background: rgba(255,255,255,0.04); color: #EAF2EC !important;
        }
        /* Icône de menu : vert discret, blanc-vert quand actif. */
        [data-testid="stSidebarNav"] a span[data-testid="stIconMaterial"] { color: #7FA592; }
        [data-testid="stSidebarNav"] a:hover span[data-testid="stIconMaterial"] { color: #BFE8D3; }
        /* Actif : pas de pavé plein — simple repère vert + texte blanc (sobre). */
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: transparent; color: #FFFFFF !important; font-weight: 700;
        }
        /* Repère vertical vert pleine hauteur sur l'élément actif. */
        [data-testid="stSidebarNav"] a[aria-current="page"]::before {
            content: ""; position: absolute; left: 0; top: 6px; bottom: 6px;
            width: 3px; border-radius: 0; background: #8FE3B8;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] span { color: #FFFFFF !important; }
        [data-testid="stSidebarNav"] a[aria-current="page"] span[data-testid="stIconMaterial"] {
            color: #8FE3B8 !important;
        }
        /* Intitulés de groupes (« Espace d'analyse », etc.) : petites capitales. */
        [data-testid="stSidebarNav"] ul + div,
        [data-testid="stNavSectionHeader"] {
            font-size: 0.66rem !important; font-weight: 700 !important; letter-spacing: 0.14em;
            text-transform: uppercase; color: #6E8578 !important;
            margin: 0.9rem 0 0.3rem 0.2rem;
        }

        /* Marque (haut de barre latérale) : wordmark sobre + filet de séparation. */
        .ls-logo { display:flex; align-items:center; gap:0.5rem; margin: 0.1rem 0 0 0.1rem; }
        .ls-logo .name { font-family:'Schibsted Grotesk',sans-serif; font-weight:800;
            font-size:1.35rem; letter-spacing:-0.02em; color:#fff; }
        .ls-rule { height:1px; background:rgba(255,255,255,0.09); margin:0.9rem 0 0.2rem; }

        /* Pied : utilisateur. */
        .ls-user { display:flex; align-items:center; gap:0.6rem; padding:0.2rem; }
        .ls-user .av {
            width:34px; height:34px; border-radius:0; background:#1C4435; color:#8FE3B8;
            display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.8rem;
        }
        .ls-user .n { color:#EAF2EC; font-weight:600; font-size:0.86rem; line-height:1.1; }
        .ls-user .r { color:#8AA194; font-size:0.74rem; }

        /* Carte métrique personnalisée. */
        .ls-metric {
            background:#fff; border:1px solid #E7E6DD; border-radius:0; padding:1.1rem 1.2rem;
            box-shadow:0 1px 2px rgba(31,42,38,0.03); height:100%;
        }
        .ls-metric .top { display:flex; align-items:flex-start; justify-content:space-between; gap:0.5rem; }
        .ls-metric .ic { color:#C5CEC8; flex:0 0 auto; line-height:0; margin-top:1px; }
        .ls-metric .lab { color:#8A938D; font-size:0.9rem; font-weight:600; }
        .ls-metric .val { font-family:'Schibsted Grotesk',sans-serif; font-weight:700; color:#1F2A26;
            font-size:2.4rem; line-height:1; letter-spacing:-0.02em; margin:0.6rem 0 0.2rem; }
        .ls-metric .val .u { font-size:1rem; font-weight:500; color:#8A938D; margin-left:2px; }
        .ls-metric .cap { color:#9AA39E; font-size:0.8rem; }

        /* Carte « À retenir ». */
        .ls-aside { background:#fff; border:1px solid #E7E6DD; border-radius:0; padding:1.2rem; }
        /* Filet de séparation horizontal (sections de cartes, admin). */
        .ls-divider { height:0; border-top:1px solid #E7E6DD; margin:0.55rem 0 0.8rem; }
        .ls-aside .hd { display:flex; align-items:center; gap:0.4rem;
            font-family:'Schibsted Grotesk',sans-serif; font-weight:700;
            letter-spacing:-0.015em; font-size:1.15rem; color:#1F2A26; margin-bottom:0.8rem; }
        .ls-aside .k { font-size:0.68rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase;
            color:#8A938D; margin-bottom:0.5rem; }
        .ls-aside .row { display:flex; align-items:center; justify-content:space-between;
            padding:0.33rem 0; border-top:1px solid #F0EFE8; }
        .ls-aside .row:first-of-type { border-top:none; }
        .ls-aside .row .lft { display:flex; align-items:center; gap:0.5rem; color:#39443F; font-size:0.92rem; }
        .ls-aside .row .dot { width:9px; height:9px; border-radius:50%; display:inline-block; }
        .ls-aside .row .v { font-weight:600; color:#1F2A26; }
        .ls-aside .note { color:#5C6862; font-size:0.9rem; line-height:1.5; margin-top:0.9rem; }

        /* Pastille (chip) de sélection. */
        .ls-chip { display:inline-flex; align-items:center; gap:0.4rem; background:#fff;
            border:1px solid #E7E6DD; border-radius:0; padding:0.25rem 0.7rem; font-size:0.85rem;
            color:#39443F; margin-right:0.4rem; }
        .ls-chip .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }

        /* ============ Finitions « produit » (sobre, pro, UX) ============ */
        /* Transitions douces sur les éléments interactifs. */
        .stButton > button, .stDownloadButton > button, [data-baseweb="select"] > div,
        .stTextInput input, .stNumberInput input, [data-testid="stPopover"] button,
        [data-testid="stVerticalBlockBorderWrapper"], a, .ls-metric, .ls-chip {
            transition: border-color .15s ease, box-shadow .15s ease,
                        background-color .15s ease, color .15s ease, transform .15s ease;
        }
        /* Anneau de focus accessible (vert discret) plutôt que le contour par défaut. */
        button:focus-visible, a:focus-visible, input:focus-visible,
        [role="button"]:focus-visible, [data-baseweb="select"] > div:focus-within {
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(46,114,87,0.20) !important;
        }
        ::selection { background: rgba(46,114,87,0.16); }

        /* Barre de défilement sobre. */
        * { scrollbar-width: thin; scrollbar-color: #D6D9CF transparent; }
        ::-webkit-scrollbar { width: 11px; height: 11px; }
        ::-webkit-scrollbar-thumb {
            background: #D6D9CF; border-radius: 0; border: 3px solid #F4F3EE;
        }
        ::-webkit-scrollbar-thumb:hover { background: #C3C8BB; }

        /* Champs : fond blanc, hauteur confortable, focus net. */
        [data-baseweb="select"] > div { background:#fff; min-height:42px; }
        [data-baseweb="select"] > div:hover { border-color:#CFD4C9; }
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color:#2E7257 !important; box-shadow:0 0 0 3px rgba(46,114,87,0.14) !important;
        }

        /* Déclencheur de popover : allure d'un select (texte à gauche, cadre doux). */
        [data-testid="stPopover"] > div > button {
            justify-content:space-between; background:#fff; border:1px solid #E7E6DD;
            border-radius:0; color:#1F2A26; font-weight:500; min-height:42px;
        }
        [data-testid="stPopover"] > div > button:hover { border-color:#2E7257; color:#215540; }

        /* Cartes : survol subtil (cadre teinté + ombre portée). */
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color:#DADFD3; box-shadow:0 8px 24px rgba(31,42,38,0.06);
        }
        .ls-metric:hover {
            border-color:#DADFD3; box-shadow:0 8px 24px rgba(31,42,38,0.06);
            transform:translateY(-1px);
        }

        /* Chiffres alignés verticalement (tabular figures). */
        .ls-metric .val, [data-testid="stMetricValue"], .ls-aside .v, .ls-aside .row {
            font-variant-numeric: tabular-nums; font-feature-settings:"tnum" 1;
        }

        /* Contrôle segmenté : segments à angles vifs, sélection verte. */
        [data-testid="stSegmentedControl"] button { border-radius:0 !important; font-weight:600; }
        [data-testid="stSegmentedControl"] button[aria-checked="true"],
        [data-testid="stSegmentedControl"] button[kind="segmented_controlActive"] {
            background:#2E7257 !important; color:#fff !important; border-color:#2E7257 !important;
        }

        /* Légendes et expander. */
        [data-testid="stCaptionContainer"] p { color:#9AA39E; }
        [data-testid="stExpander"] { border:1px solid #E7E6DD !important; border-radius:0; background:#fff; }
        [data-testid="stExpander"] summary:hover { color:#215540; }

        /* Spinner teinté accent. */
        .stSpinner > div { border-top-color:#2E7257 !important; }

        /* Info/warning : angles vifs, ton feutré. */
        [data-testid="stAlert"] { border-radius:0; }

        /* Cartes de navigation (accueil) : badge d'icône, titre, description, tag. */
        .ls-nav-ic {
            width:42px; height:42px; border-radius:0; background:#EAF1EC; color:#2E7257;
            display:flex; align-items:center; justify-content:center; line-height:0;
        }
        .ls-nav-d { color:#5C6862; font-size:0.93rem; line-height:1.5; margin:0.5rem 0 0.7rem;
            min-height:2.8em; }
        .ls-tag { display:inline-block; font-size:0.68rem; font-weight:700; letter-spacing:0.09em;
            text-transform:uppercase; padding:0.22rem 0.6rem; border-radius:0; }
        .ls-tag.libre { background:#EAF1EC; color:#2E7257; }
        .ls-tag.verrou { background:#F1EFE8; color:#9AA39E; }

        /* Lien de page (st.page_link) présenté comme une action discrète. */
        [data-testid="stPageLink"] a {
            color:#2E7257 !important; font-weight:600; border-radius:0;
            padding:0.3rem 0.1rem; margin-top:0.2rem;
        }
        [data-testid="stPageLink"] a:hover { color:#215540 !important; transform:translateX(2px); }
        [data-testid="stPageLink"] a span[data-testid="stIconMaterial"] { color:#2E7257; }

        /* Tableaux sobres (admin) avec badges de statut. */
        .ls-table { width:100%; border-collapse:collapse; font-size:0.9rem;
            font-variant-numeric:tabular-nums; }
        .ls-table th { text-align:left; font-weight:700; color:#8A938D; font-size:0.68rem;
            letter-spacing:0.07em; text-transform:uppercase; padding:0.5rem 0.65rem;
            border-bottom:1px solid #E7E6DD; }
        .ls-table td { padding:0.55rem 0.65rem; border-bottom:1px solid #F0EFE8; color:#39443F;
            vertical-align:middle; }
        .ls-table tr:last-child td { border-bottom:none; }
        .ls-table tbody tr:hover td { background:#FAFAF7; }
        .ls-table td.num { text-align:right; }
        /* Conteneur de classement défilant, en-tête collant. */
        .ls-scroll { max-height:430px; overflow-y:auto; border-top:1px solid #F0EFE8; }
        .ls-scroll .ls-table th {
            position:sticky; top:0; background:#FFFFFF; z-index:1;
            box-shadow:inset 0 -1px 0 #E7E6DD; border-bottom:none;
        }
        .ls-rank-no { color:#8A938D; font-variant-numeric:tabular-nums; font-weight:600; }
        .ls-bar { background:#EFEEE6; height:7px; width:120px; display:inline-block; vertical-align:middle; }
        .ls-bar > span { display:block; height:7px; background:#2E7257; }
        .ls-badge { display:inline-block; font-size:0.72rem; font-weight:700;
            padding:0.16rem 0.55rem; border-radius:0; white-space:nowrap; }
        .ls-badge.ok { background:#E4F0E8; color:#2E7257; }
        .ls-badge.ko { background:#F6E6E3; color:#B4532E; }
        .ls-badge.warn { background:#F6EFDD; color:#8A6D22; }
        .ls-badge.neutre { background:#F1EFE8; color:#6B736D; }

        /* Rendu épuré : on masque les actions superflues de l'en-tête (Deploy,
           menu) MAIS on garde la barre d'outils, car elle contient le bouton de
           ré-affichage de la barre latérale quand elle est repliée. */
        footer { display:none; }
        [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"],
        #MainMenu, [data-testid="stMainMenu"] { display:none !important; }
        [data-testid="stDecoration"] { display:none; }
        [data-testid="stHeader"] { background:transparent; }

        /* Bouton de ré-affichage de la barre latérale quand elle est masquée.
           Streamlit le rend en 0×0 sur notre thème : on le force visible, carré,
           épinglé en haut à gauche (cadre blanc + icône encre sur le crème). */
        [data-testid="stExpandSidebarButton"] {
            position:fixed !important; top:0.7rem; left:0.7rem; z-index:1000;
            width:2.2rem !important; height:2.2rem !important; min-width:2.2rem !important;
            display:flex !important; align-items:center; justify-content:center;
            background:#FFFFFF !important; border:1px solid #E7E6DD !important;
            border-radius:0 !important; color:#1F2A26 !important;
            box-shadow:0 1px 3px rgba(31,42,38,0.12); opacity:1 !important; visibility:visible !important;
        }
        [data-testid="stExpandSidebarButton"]:hover {
            border-color:#2E7257 !important; color:#215540 !important;
        }
        [data-testid="stExpandSidebarButton"] span[data-testid="stIconMaterial"] {
            color:inherit !important; font-size:1.25rem; line-height:1;
        }
        /* Bouton « masquer » dans la barre latérale : icône claire, bien visible. */
        [data-testid="stSidebarCollapseButton"] button { color:#AFC4B8 !important; }
        [data-testid="stSidebarCollapseButton"] button:hover { color:#FFFFFF !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --- Barre latérale ---------------------------------------------------------

_LOGO_SVG = (
    "<svg width='26' height='26' viewBox='0 0 24 24' fill='none' "
    "xmlns='http://www.w3.org/2000/svg'>"
    "<rect x='2' y='13' width='4' height='8' rx='1' fill='#8FE3B8'/>"
    "<rect x='9' y='8' width='4' height='13' rx='1' fill='#FFFFFF'/>"
    "<rect x='16' y='4' width='4' height='17' rx='1' fill='#8FE3B8'/>"
    "</svg>"
)


def barre_laterale_haut() -> None:
    """Marque sobre en haut de la barre latérale (wordmark + filet)."""
    with st.sidebar:
        st.markdown(
            f"<div class='ls-logo'>{_LOGO_SVG}<span class='name'>LaborScope</span></div>"
            f"<div class='ls-rule'></div>",
            unsafe_allow_html=True,
        )


def barre_laterale_bas() -> None:
    """Pied de barre latérale : identité de l'utilisateur connecté.

    À appeler après ``st.navigation`` pour apparaître sous le menu.
    """
    with st.sidebar:
        st.markdown("<div class='ls-rule'></div>", unsafe_allow_html=True)
        if est_connecte():
            nom = st.session_state.get("nom_utilisateur") or "Utilisateur"
            role = st.session_state.get("role_utilisateur", ROLE_UTILISATEUR)
            initiales = "".join(mot[0] for mot in nom.split()[:2]).upper() or "U"
            st.markdown(
                f"<div class='ls-user'><div class='av'>{html.escape(initiales)}</div>"
                f"<div><div class='n'>{html.escape(nom)}</div>"
                f"<div class='r'>{html.escape(role)}</div></div></div>",
                unsafe_allow_html=True,
            )
            if st.button("Se déconnecter", use_container_width=True):
                deconnexion()
        else:
            st.markdown(
                "<div class='ls-user'><div class='av'>LS</div>"
                "<div><div class='n'>Projet LaborScope</div>"
                "<div class='r'>Observatoire du marché du travail</div></div></div>",
                unsafe_allow_html=True,
            )


# --- En-têtes et composants de page ----------------------------------------


def entete(
    titre: str,
    description: str = "",
    eyebrow: str = "",
    action_label: str | None = None,
    action_icon: str = ":material/download:",
) -> bool:
    """En-tête éditorial : sur-titre, grand titre serif, sous-titre, action.

    Renvoie True si le bouton d'action (optionnel) a été cliqué.
    """
    col_titre, col_action = st.columns([0.78, 0.22], vertical_alignment="center")
    with col_titre:
        if eyebrow:
            st.markdown(
                f"<div class='ls-eyebrow'>{html.escape(eyebrow)}</div>", unsafe_allow_html=True
            )
        st.markdown(
            f"<div class='ls-serif ls-title'>{html.escape(titre)}</div>", unsafe_allow_html=True
        )
        if description:
            st.markdown(
                f"<p class='ls-subtitle'>{html.escape(description)}</p>", unsafe_allow_html=True
            )
    clique = False
    with col_action:
        if action_label:
            clique = st.button(
                action_label, icon=action_icon, type="primary", use_container_width=True
            )
    st.write("")
    return clique


def ligne_source(gauche: list[str], droite: str = "") -> None:
    """Affiche la petite ligne de contexte (source des données, date d'extrait)."""
    morceaux = [f"<span class='dot'>●</span> {html.escape(gauche[0])}"] if gauche else []
    morceaux += [html.escape(x) for x in gauche[1:]]
    gauche_html = " &nbsp;·&nbsp; ".join(morceaux)
    droite_html = f"<span style='float:right'>{html.escape(droite)}</span>" if droite else ""
    st.markdown(f"<div class='ls-meta'>{gauche_html}{droite_html}</div>", unsafe_allow_html=True)


def carte_metrique(
    label: str, valeur: str, unite: str = "", caption: str = "", icone_svg: str = ""
) -> None:
    """Carte métrique (label, grande valeur serif + unité, légende).

    ``icone_svg`` : SVG inline optionnel affiché en haut à droite (trait discret).
    """
    u = f"<span class='u'>{html.escape(unite)}</span>" if unite else ""
    ic = f"<span class='ic'>{icone_svg}</span>" if icone_svg else ""
    st.markdown(
        f"<div class='ls-metric'><div class='top'><div class='lab'>{html.escape(label)}</div>{ic}</div>"
        f"<div class='val'>{html.escape(valeur)}{u}</div>"
        f"<div class='cap'>{html.escape(caption)}</div></div>",
        unsafe_allow_html=True,
    )


# SVG d'angle (traits sobres) pour les cartes métriques, repris des maquettes.
ICONE_CIBLE = (
    "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
    "stroke-width='1.6' stroke-linecap='round'><circle cx='12' cy='12' r='8'/>"
    "<circle cx='12' cy='12' r='3.2'/></svg>"
)
ICONE_TENDANCE = (
    "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
    "stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>"
    "<path d='M3 17l6-6 4 4 7-7'/><path d='M17 5h4v4'/></svg>"
)
ICONE_ECART = (
    "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
    "stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>"
    "<path d='M8 7L4 11l4 4'/><path d='M16 7l4 4-4 4'/><path d='M4 11h16'/></svg>"
)
# Icônes de badge pour les cartes de navigation (accueil).
ICONE_GLOBE = (
    "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
    "stroke-width='1.6' stroke-linecap='round'><circle cx='12' cy='12' r='9'/>"
    "<path d='M3 12h18'/><path d='M12 3c2.5 2.6 2.5 15.4 0 18M12 3c-2.5 2.6-2.5 15.4 0 18'/></svg>"
)
ICONE_COUCHES = (
    "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
    "stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>"
    "<path d='M12 3l9 5-9 5-9-5 9-5z'/><path d='M3 13l9 5 9-5'/></svg>"
)
ICONE_REGLAGES = (
    "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
    "stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>"
    "<circle cx='12' cy='12' r='3'/><path d='M19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.4 1a7 7 0 0 0-2-1.2"
    "l-.4-2.6H9.9l-.4 2.6a7 7 0 0 0-2 1.2l-2.4-1-2 3.4 2 1.6A7 7 0 0 0 5 12a7 7 0 0 0 .1 1.2l-2 1.6 "
    "2 3.4 2.4-1a7 7 0 0 0 2 1.2l.4 2.6h4.2l.4-2.6a7 7 0 0 0 2-1.2l2.4 1 2-3.4-2-1.6A7 7 0 0 0 19 12z'/></svg>"
)


def badge(texte: str, variante: str = "neutre") -> str:
    """Renvoie le HTML d'un badge de statut (``ok``, ``ko``, ``warn``, ``neutre``)."""
    return f"<span class='ls-badge {variante}'>{html.escape(str(texte))}</span>"


def aide(texte: str) -> str:
    """Renvoie un petit marqueur « ? » porteur d'une bulle d'aide au survol.

    À concaténer dans un markdown HTML (``unsafe_allow_html=True``) pour déporter
    une explication hors du texte permanent (interface plus sobre).
    """
    return f"<span class='ls-help' title='{html.escape(texte)}'>?</span>"


# Icônes de notification (traits sobres, héritent de la couleur sémantique).
_NOTIF_ICONES = {
    "ok": "<svg width='17' height='17' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
          "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
          "<circle cx='12' cy='12' r='9'/><path d='M8.5 12.5l2.5 2.5 4.5-5'/></svg>",
    "ko": "<svg width='17' height='17' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
          "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
          "<circle cx='12' cy='12' r='9'/><path d='M9 9l6 6M15 9l-6 6'/></svg>",
    "warn": "<svg width='17' height='17' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
            "<path d='M12 3l9 16H3z'/><path d='M12 10v4'/><path d='M12 17.5v.01'/></svg>",
    "info": "<svg width='17' height='17' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
            "<circle cx='12' cy='12' r='9'/><path d='M12 11v5'/><path d='M12 8v.01'/></svg>",
}


def notif(message: str, type: str = "info") -> None:
    """Notification à plat, couleur sémantique : ``ok`` (vert), ``ko`` (rouge),
    ``warn`` (ambre) ou ``info`` (neutre). Remplace ``st.success``/``error`` etc.
    pour un retour visuel net et cohérent avec le reste de l'interface.
    """
    variante = type if type in _NOTIF_ICONES else "info"
    corps = html.escape(str(message)).replace("**", "")
    st.markdown(
        f"<div class='ls-notif {variante}'><span class='ic'>{_NOTIF_ICONES[variante]}</span>"
        f"<span class='msg'>{corps}</span></div>",
        unsafe_allow_html=True,
    )


def tableau(entetes: list[str], lignes: list[list[str]], aligns: list[str] | None = None) -> None:
    """Rend un tableau HTML sobre.

    ``lignes`` contient des cellules déjà prêtes (texte échappé par l'appelant ou
    HTML de badge). ``aligns`` optionnel : liste de "" ou "num" par colonne.
    """
    aligns = aligns or [""] * len(entetes)
    thead = "".join(f"<th>{html.escape(str(col))}</th>" for col in entetes)
    corps = ""
    for ligne in lignes:
        cells = "".join(
            f"<td class='{aligns[i] if i < len(aligns) else ''}'>{cell}</td>"
            for i, cell in enumerate(ligne)
        )
        corps += f"<tr>{cells}</tr>"
    st.markdown(
        f"<table class='ls-table'><thead><tr>{thead}</tr></thead><tbody>{corps}</tbody></table>",
        unsafe_allow_html=True,
    )


def carte_navigation(icone_svg: str, titre: str, description: str = "",
                     tag: str = "", verrou: bool = False, aide_texte: str = "") -> None:
    """Entête d'une carte de navigation (badge, titre, tag, « ? » d'aide).

    À appeler dans un ``st.container(border=True)`` ; le ``st.page_link`` est
    ajouté juste après par l'appelant. ``description`` est optionnelle (interface
    sobre) ; ``aide_texte`` alimente une bulle « ? » à côté du titre.
    """
    marge_tag = "0.5rem" if description else "0.8rem"
    tag_html = (
        f"<div style='margin-top:{marge_tag}'>"
        f"<span class='ls-tag {'verrou' if verrou else 'libre'}'>{html.escape(tag)}</span></div>"
        if tag else ""
    )
    aide_html = aide(aide_texte) if aide_texte else ""
    desc_html = f"<p class='ls-nav-d'>{html.escape(description)}</p>" if description else ""
    st.markdown(
        f"<div class='ls-nav-ic'>{icone_svg}</div>"
        f"<div class='ls-serif' style='font-size:1.2rem;margin-top:0.55rem'>"
        f"{html.escape(titre)}{aide_html}</div>{desc_html}{tag_html}",
        unsafe_allow_html=True,
    )


def chip(libelle: str, couleur: str) -> str:
    """Renvoie le HTML d'une pastille colorée (pour un conteneur markdown)."""
    return (
        f"<span class='ls-chip'><span class='dot' style='background:{couleur}'></span>"
        f"{html.escape(libelle)}</span>"
    )


def carte_a_retenir(titre_section: str, lignes: list[tuple], note: str = "", bas: str = "") -> None:
    """Carte latérale « À retenir » : liste pays/valeur + note explicative.

    ``lignes`` : liste de tuples (libellé, valeur_affichée, couleur).
    """
    lignes_html = "".join(
        f"<div class='row'><span class='lft'>"
        f"<span class='dot' style='background:{coul}'></span>{html.escape(lib)}</span>"
        f"<span class='v'>{html.escape(val)}</span></div>"
        for lib, val, coul in lignes
    )
    note_html = f"<div class='note'>{html.escape(note)}</div>" if note else ""
    bas_html = (
        f"<div class='k' style='margin-top:1rem'>Bien lire les chiffres</div>"
        f"<div class='note' style='margin-top:0.2rem'>{html.escape(bas)}</div>"
        if bas
        else ""
    )
    st.markdown(
        f"<div class='ls-aside'><div class='hd'>À retenir</div>"
        f"<div class='k'>{html.escape(titre_section)}</div>{lignes_html}{note_html}{bas_html}</div>",
        unsafe_allow_html=True,
    )


# --- Format & en-têtes de graphique ----------------------------------------

def fmt_fr(valeur: float, decimales: int = 1) -> str:
    """Formate un nombre avec la virgule décimale française (ex. 7,5)."""
    return f"{valeur:.{decimales}f}".replace(".", ",")


def entete_graphique(eyebrow: str, titre: str, sous_titre: str = "") -> None:
    """En-tête standard d'une carte graphique : sur-titre, titre serif, légende."""
    st.markdown(f"<div class='ls-eyebrow plain'>{html.escape(eyebrow)}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='ls-serif' style='font-size:1.5rem'>{html.escape(titre)}</div>",
                unsafe_allow_html=True)
    if sous_titre:
        st.caption(sous_titre)


# --- Graphiques -------------------------------------------------------------


def styliser_figure(fig, hauteur: int = 430):
    """Applique une mise en forme sobre et éditoriale à une figure Plotly.

    ``separators=", "`` impose le format français (virgule décimale, espace
    comme séparateur de milliers) sur les axes et les infobulles.
    """
    fig.update_layout(
        template="plotly_white",
        colorway=PALETTE_GRAPHIQUE,
        font=dict(family="Inter, sans-serif", size=13, color=TEXTE),
        title=dict(text="", font=dict(family="Schibsted Grotesk, sans-serif", size=18, color=ENCRE),
                   x=0, xanchor="left", y=0.98),
        margin=dict(l=8, r=16, t=40, b=8),
        height=hauteur,
        separators=", ",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title="",
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12.5)),
        hoverlabel=dict(bgcolor="white", bordercolor=BORDURE, font_size=12.5,
                        font_family="Inter, sans-serif"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F0EFE8", griddash="dot", showline=False,
                     zeroline=False, ticksuffix="  ", tickfont=dict(color=TEXTE_DOUX))
    fig.update_yaxes(showgrid=False, showline=False, zeroline=False,
                     tickfont=dict(color=ENCRE))
    return fig


def afficher_graphique(fig) -> None:
    """Affiche une figure Plotly sans barre d'outils (rendu épuré)."""
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def couleur_serie(index: int) -> str:
    """Renvoie la couleur de la palette pour la n-ième série (cyclique)."""
    return PALETTE_GRAPHIQUE[index % len(PALETTE_GRAPHIQUE)]
