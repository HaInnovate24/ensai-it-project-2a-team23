"""Système d'interface partagé par toutes les pages.

Objectif : une présentation homogène, sobre et professionnelle (styles globaux,
en-têtes, barre latérale, graphiques) sans dupliquer le code dans chaque page.
Aucun emoji, une palette restreinte et un accent unique.
"""

import streamlit as st

# Libellés de rôle utilisés par la navigation (cf. app.py et login.py).
ROLE_ADMIN = "Administrateur"
ROLE_UTILISATEUR = "Utilisateur"

# --- Palette ----------------------------------------------------------------
# Accent unique + nuances d'ardoise. Les couleurs ne servent qu'à hiérarchiser.
ACCENT = "#2563EB"
ENCRE = "#0F172A"
TEXTE = "#1E293B"
TEXTE_DOUX = "#64748B"
BORDURE = "#E2E8F0"
SURFACE = "#F8FAFC"

# Séquence de couleurs sobre et lisible pour les graphiques multi-séries.
PALETTE_GRAPHIQUE = [
    "#2563EB",  # bleu
    "#0F766E",  # sarcelle
    "#B45309",  # ambre foncé
    "#7C3AED",  # violet
    "#475569",  # ardoise
    "#BE123C",  # framboise
    "#0891B2",  # cyan
    "#4D7C0F",  # olive
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


def injecter_styles() -> None:
    """Injecte les styles globaux (typographie, espacements, cartes, boutons).

    À appeler une fois par rerun, avant toute autre sortie, depuis app.py.
    """
    st.markdown(
        f"""
        <style>
        /* Largeur de lecture confortable et respiration en haut de page. */
        .block-container {{
            max-width: 1180px;
            padding-top: 2.6rem;
            padding-bottom: 4rem;
        }}

        /* Titres : plus affirmés, sans espacement relâché. */
        h1 {{ font-weight: 700; letter-spacing: -0.021em; color: {ENCRE}; }}
        h2, h3 {{ font-weight: 650; letter-spacing: -0.012em; color: {TEXTE}; }}
        h1, h2, h3 {{ margin-bottom: 0.2rem; }}

        /* Cartes (st.container(border=True)) : coins doux, bordure discrète. */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 12px;
            border: 1px solid {BORDURE};
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }}
        [data-testid="stVerticalBlockBorderWrapper"] > div {{ padding: 0.35rem 0.25rem; }}

        /* Boutons : coins arrondis, graisse lisible. */
        .stButton > button, .stForm [data-testid="stFormSubmitButton"] button {{
            border-radius: 9px;
            font-weight: 600;
            border: 1px solid {BORDURE};
            transition: border-color .15s ease, box-shadow .15s ease;
        }}
        .stButton > button:hover,
        .stForm [data-testid="stFormSubmitButton"] button:hover {{
            border-color: {ACCENT};
            box-shadow: 0 1px 3px rgba(37, 99, 235, 0.15);
        }}

        /* Champs de saisie et menus : bordure nette au repos. */
        [data-baseweb="select"] > div,
        .stTextInput input, .stNumberInput input {{
            border-radius: 9px;
        }}

        /* Barre latérale : séparée du contenu par une fine bordure. */
        [data-testid="stSidebar"] {{
            background: {SURFACE};
            border-right: 1px solid {BORDURE};
        }}

        /* Liens de page (st.page_link) : aspect bouton léger. */
        [data-testid="stPageLink-NavLink"] {{
            border-radius: 9px;
            padding: 0.35rem 0.5rem;
        }}

        /* Onglets : indicateur plus net. */
        .stTabs [data-baseweb="tab-list"] {{ gap: 1.4rem; }}
        .stTabs [data-baseweb="tab"] {{ font-weight: 600; }}

        /* Masque le bandeau « Deploy » et le menu par défaut pour un rendu épuré. */
        [data-testid="stToolbar"] {{ display: none; }}
        footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def entete(titre: str, description: str = "", eyebrow: str = "") -> None:
    """Affiche un en-tête de page cohérent : sur-titre optionnel, titre, description.

    Args:
        titre: Titre principal de la page.
        description: Phrase de contexte affichée sous le titre.
        eyebrow: Petit libellé de section au-dessus du titre (ex. « Analyse »).
    """
    if eyebrow:
        st.markdown(
            f"<div style='font-size:0.8rem; font-weight:700; letter-spacing:0.08em; "
            f"text-transform:uppercase; color:{ACCENT};'>{eyebrow}</div>",
            unsafe_allow_html=True,
        )
    st.title(titre)
    if description:
        st.markdown(
            f"<p style='color:{TEXTE_DOUX}; font-size:1.02rem; margin-top:-0.2rem;'>"
            f"{description}</p>",
            unsafe_allow_html=True,
        )
    st.divider()


def styliser_figure(fig, hauteur: int = 430):
    """Applique une mise en forme sobre et homogène à une figure Plotly.

    Centralise le template, la typographie, les marges, la légende et la grille
    pour que tous les graphiques partagent la même identité visuelle.
    """
    fig.update_layout(
        template="plotly_white",
        colorway=PALETTE_GRAPHIQUE,
        font=dict(family="sans-serif", size=13, color=TEXTE),
        title=dict(font=dict(size=17, color=ENCRE), x=0, xanchor="left", y=0.97),
        margin=dict(l=8, r=8, t=64, b=8),
        height=hauteur,
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.0,
            xanchor="left",
            x=0,
            title="",
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="white", bordercolor=BORDURE, font_size=12),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=BORDURE, ticks="outside",
                     tickcolor=BORDURE)
    fig.update_yaxes(showgrid=True, gridcolor="#EEF2F7", zeroline=False)
    return fig


def barre_laterale() -> None:
    """Affiche dans la barre latérale le branding et l'état de connexion.

    À appeler depuis app.py avant ``st.navigation`` pour que le bloc apparaisse
    au-dessus du menu de navigation.
    """
    with st.sidebar:
        st.markdown(
            f"<div style='font-size:1.35rem; font-weight:800; letter-spacing:-0.02em; "
            f"color:{ENCRE};'>LaborScope</div>"
            f"<div style='font-size:0.82rem; color:{TEXTE_DOUX}; margin-bottom:0.4rem;'>"
            f"Observatoire de l'emploi — données ILOSTAT</div>",
            unsafe_allow_html=True,
        )

        if est_connecte():
            nom = st.session_state.get("nom_utilisateur", "?")
            role = st.session_state.get("role_utilisateur", ROLE_UTILISATEUR)
            st.markdown(
                f"<div style='background:#ECFDF5; border:1px solid #A7F3D0; "
                f"border-radius:9px; padding:0.5rem 0.7rem; font-size:0.9rem;'>"
                f"<span style='color:#047857; font-weight:600;'>Connecté</span><br>"
                f"<strong>{nom}</strong> · {role}</div>",
                unsafe_allow_html=True,
            )
            if st.button("Se déconnecter", use_container_width=True):
                deconnexion()
        else:
            st.markdown(
                f"<div style='background:#EFF6FF; border:1px solid #BFDBFE; "
                f"border-radius:9px; padding:0.5rem 0.7rem; font-size:0.9rem; "
                f"color:{TEXTE};'>Mode découverte — non connecté</div>",
                unsafe_allow_html=True,
            )

        st.divider()
