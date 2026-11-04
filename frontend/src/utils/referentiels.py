"""Référentiels consommés par les pages d'analyse.

Les listes (indicateurs, pays, classifications) sont récupérées depuis le
backend (``/referentiels/...``) et mémorisées en session pour éviter de
réinterroger l'API à chaque interaction. En cas d'indisponibilité du backend,
un repli statique minimal permet à l'interface de rester utilisable.
"""

import streamlit as st

from utils.api_client import api_client

# --- Sexe (libellé affiché -> valeur attendue par le backend, enum Sexe) ---
SEXES = {
    "Ensemble": "total",
    "Hommes": "homme",
    "Femmes": "femme",
}

# --- Replis statiques (uniquement si le backend est injoignable) ---
_INDICATEURS_FALLBACK = {
    "POP_XWAP_SEX_AGE_NB": "Population en âge de travailler (par sexe et âge)",
    "EMP_TEMP_SEX_OCU_NB": "Emploi (par sexe et profession)",
}
_UNITES_FALLBACK = {
    "POP_XWAP_SEX_AGE_NB": "Milliers",
    "EMP_TEMP_SEX_OCU_NB": "Milliers",
}
_CLASSIF_AGE_FALLBACK = {
    "Tous âges (15 ans et plus)": "AGE_AGGREGATE_TOTAL",
    "15 à 24 ans": "AGE_AGGREGATE_Y15-24",
    "25 ans et plus": "AGE_AGGREGATE_Y25-plus",
}
_CLASSIF_OCC_FALLBACK = {
    "Toutes professions": "OCU_ISCO08_TOTAL",
    "Niveau de compétence : total": "OCU_SKILL_TOTAL",
}
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


def type_classification_de(code_indicateur: str) -> str:
    """Déduit le type de classification pertinent pour un indicateur.

    Les indicateurs d'occupation (``..._OCU_NB``) utilisent les classifications
    de profession ; les autres utilisent les classifications d'âge.
    """
    return "occupation" if code_indicateur.upper().endswith("_OCU_NB") else "age"


def libelle_type_classification(code_indicateur: str) -> str:
    """Libellé du filtre de classification selon l'indicateur.

    Les indicateurs d'âge se déclinent par « Population », ceux d'occupation
    par « Profession ». Garde l'interface cohérente avec les données du backend.
    """
    return "Population" if type_classification_de(code_indicateur) == "age" else "Profession"


def get_indicateurs() -> dict[str, str]:
    """Renvoie ``{code_indicateur: description}`` depuis le backend (repli statique)."""
    cache = st.session_state.get("ref_indicateurs")
    if cache:
        return cache

    reponse = api_client.get("/referentiels/indicateurs")
    if reponse["status_code"] == 200 and isinstance(reponse["data"], list) and reponse["data"]:
        indicateurs: dict[str, str] = {}
        meta: dict[str, dict] = {}
        for ligne in reponse["data"]:
            code = ligne.get("code_indicateur")
            if not code:
                continue
            indicateurs[code] = ligne.get("description") or code
            meta[code] = {"unite": ligne.get("unite")}
        if indicateurs:
            st.session_state["ref_indicateurs"] = indicateurs
            st.session_state["ref_indicateurs_meta"] = meta
            return indicateurs

    return dict(_INDICATEURS_FALLBACK)


def unite_indicateur(code_indicateur: str) -> str:
    """Renvoie l'unité d'un indicateur (ex. « Milliers »), vide si inconnue."""
    meta = st.session_state.get("ref_indicateurs_meta") or {}
    unite = meta.get(code_indicateur, {}).get("unite")
    return unite or _UNITES_FALLBACK.get(code_indicateur, "")


def _get_classifications_par_type(type_classif: str) -> dict[str, str]:
    """Renvoie ``{libelle: code}`` pour un type de classification donné."""
    cle = f"ref_classif_{type_classif}"
    cache = st.session_state.get(cle)
    if cache:
        return cache

    reponse = api_client.get("/referentiels/classifications", params={"type": type_classif})
    if reponse["status_code"] == 200 and isinstance(reponse["data"], list) and reponse["data"]:
        classifs = {
            ligne["libelle"]: ligne["code"]
            for ligne in reponse["data"]
            if ligne.get("libelle") and ligne.get("code")
        }
        if classifs:
            st.session_state[cle] = classifs
            return classifs

    return dict(_CLASSIF_OCC_FALLBACK if type_classif == "occupation" else _CLASSIF_AGE_FALLBACK)


def get_classifications(code_indicateur: str) -> dict[str, str]:
    """Renvoie les classifications adaptées à l'indicateur (âge ou profession)."""
    return _get_classifications_par_type(type_classification_de(code_indicateur))


def get_classifications_toutes() -> dict[str, str]:
    """Renvoie toutes les classifications, préfixées par leur type.

    Utile quand plusieurs indicateurs de types différents coexistent (F5) :
    l'API n'accepte qu'une classification à la fois.
    """
    combinees = {
        f"Âge — {libelle}": code for libelle, code in _get_classifications_par_type("age").items()
    }
    combinees.update(
        {
            f"Profession — {libelle}": code
            for libelle, code in _get_classifications_par_type("occupation").items()
        }
    )
    return combinees


def index_defaut(libelle_to_code: dict[str, str]) -> int:
    """Index de la classification agrégée à présélectionner.

    On vise l'agrégat « total » qui porte réellement des données dans le
    backend : ``AGE_AGGREGATE_TOTAL`` (âge) et ``OCU_ISCO08_TOTAL`` (professions,
    norme ISCO-08). On évite les totaux de normes anciennes (ISCO-88) qui sont
    vides, pour ne pas afficher « aucune donnée » par défaut.
    """
    codes = list(libelle_to_code.values())

    for prefere in ("AGE_AGGREGATE_TOTAL", "OCU_ISCO08_TOTAL"):
        if prefere in codes:
            return codes.index(prefere)

    for i, code in enumerate(codes):
        if code and code.upper().endswith("TOTAL") and "ISCO88" not in code.upper():
            return i
    for i, code in enumerate(codes):
        if code and code.upper().endswith("TOTAL"):
            return i
    return 0


def get_pays() -> dict[str, str]:
    """Renvoie ``{nom_pays: code_pays}`` depuis le backend, avec repli statique."""
    cache = st.session_state.get("ref_pays")
    if cache:
        return cache

    reponse = api_client.get("/referentiels/pays")
    if reponse["status_code"] == 200 and isinstance(reponse["data"], list) and reponse["data"]:
        pays = {
            ligne["nom_pays"]: ligne["code_pays"]
            for ligne in reponse["data"]
            if ligne.get("nom_pays") and ligne.get("code_pays")
        }
        if pays:
            st.session_state["ref_pays"] = pays
            return pays

    return dict(_PAYS_FALLBACK)


def message_erreur(reponse: dict) -> str:
    """Transforme une réponse d'``api_client`` en message lisible."""
    if reponse["status_code"] == 0:
        return f"Backend injoignable ({reponse['data']})."

    detail = reponse["data"]
    if isinstance(detail, dict):
        detail = detail.get("detail", detail)
    return f"Erreur {reponse['status_code']} : {detail}"
