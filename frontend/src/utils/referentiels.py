"""Référentiels et correspondances libellé -> code pour les pages d'analyse.

Ce module centralise ce dont les pages ont besoin pour parler au backend :
    - la correspondance entre les libellés affichés (en français) et les codes
      ILOSTAT attendus par l'API (indicateurs, sexe, classifications) ;
    - la récupération de la liste des pays via ``/referentiels/pays``.

Les codes utilisés ici correspondent au peuplement de ``data/pop_referentiels.sql``.
"""

import streamlit as st

from utils.api_client import api_client

# --- Indicateurs disponibles (code ILOSTAT -> libellé affiché) ---
INDICATEURS = {
    "POP_XWAP_SEX_AGE_NB": "Population en âge de travailler (par sexe et âge)",
    "EMP_TEMP_SEX_OCU_NB": "Emploi (par sexe et profession)",
}

# --- Sexe (libellé affiché -> valeur attendue par le backend, enum Sexe) ---
SEXES = {
    "Ensemble": "total",
    "Hommes": "homme",
    "Femmes": "femme",
}

# --- Classifications par âge (indicateurs ..._AGE_NB) ---
CLASSIFICATIONS_AGE = {
    "15 ans et plus": "AGE_AGGREGATE_TOTAL",
    "15 à 24 ans": "AGE_AGGREGATE_Y15-24",
    "25 ans et plus": "AGE_AGGREGATE_Y25-plus",
}

# --- Classifications par profession ISCO-08 (indicateurs ..._OCU_NB) ---
CLASSIFICATIONS_OCCUPATION = {
    "Toutes professions": "OCU_ISCO08_TOTAL",
    "Directeurs et cadres de direction": "OCU_ISCO08_1",
    "Professions intellectuelles et scientifiques": "OCU_ISCO08_2",
    "Professions intermédiaires": "OCU_ISCO08_3",
    "Employés de type administratif": "OCU_ISCO08_4",
    "Personnel des services et vendeurs": "OCU_ISCO08_5",
    "Agriculteurs et ouvriers qualifiés": "OCU_ISCO08_6",
    "Métiers de l'industrie et de l'artisanat": "OCU_ISCO08_7",
    "Conducteurs d'installations et de machines": "OCU_ISCO08_8",
    "Professions élémentaires": "OCU_ISCO08_9",
    "Professions militaires": "OCU_ISCO08_0",
}

# Repli statique (nom -> code ISO3) si le backend est injoignable.
_PAYS_FALLBACK = {
    "France": "FRA",
    "Allemagne": "DEU",
    "Royaume-Uni": "GBR",
    "Espagne": "ESP",
    "Italie": "ITA",
    "États-Unis": "USA",
    "Canada": "CAN",
    "Japon": "JPN",
    "Sénégal": "SEN",
    "Brésil": "BRA",
}


def classifications_pour(code_indicateur: str) -> dict[str, str]:
    """Renvoie les classifications adaptées à l'indicateur (âge ou profession)."""
    if code_indicateur.upper().endswith("_OCU_NB"):
        return CLASSIFICATIONS_OCCUPATION
    return CLASSIFICATIONS_AGE


def classifications_toutes() -> dict[str, str]:
    """Renvoie toutes les classifications, préfixées par leur type.

    Utile quand plusieurs indicateurs de types différents sont comparés sur un
    même écran (F5) : l'API n'accepte qu'une classification à la fois.
    """
    combinees = {f"Âge — {libelle}": code for libelle, code in CLASSIFICATIONS_AGE.items()}
    combinees.update(
        {f"Profession — {libelle}": code for libelle, code in CLASSIFICATIONS_OCCUPATION.items()}
    )
    return combinees


def get_pays() -> dict[str, str]:
    """Renvoie ``{nom_pays: code_pays}`` depuis le backend, avec repli statique.

    Le résultat est mémorisé dans la session dès qu'un appel aboutit, afin de ne
    pas réinterroger le backend à chaque interaction. En cas d'échec, on renvoie
    une liste de secours sans la mémoriser (le prochain appel réessaiera).
    """
    cache = st.session_state.get("referentiel_pays")
    if cache:
        return cache

    reponse = api_client.get("/referentiels/pays")
    if reponse["status_code"] == 200 and isinstance(reponse["data"], list):
        pays = {
            ligne["nom_pays"]: ligne["code_pays"]
            for ligne in reponse["data"]
            if ligne.get("nom_pays") and ligne.get("code_pays")
        }
        if pays:
            st.session_state["referentiel_pays"] = pays
            return pays

    return dict(_PAYS_FALLBACK)


def message_erreur(reponse: dict) -> str:
    """Transforme une réponse d'``api_client`` en message lisible.

    Gère les erreurs réseau (status_code 0) et extrait le champ ``detail`` des
    erreurs FastAPI quand il est présent.
    """
    if reponse["status_code"] == 0:
        return f"Backend injoignable ({reponse['data']})."

    detail = reponse["data"]
    if isinstance(detail, dict):
        detail = detail.get("detail", detail)
    return f"Erreur {reponse['status_code']} : {detail}"
