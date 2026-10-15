"""Routes HTTP des analyses : évolution, comparaisons, carte.

Le controller ne calcule rien : il reçoit les paramètres, appelle le service,
puis transforme les erreurs métier en codes HTTP.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from business_object.enums import Sexe
from model.analyse_model import Comparaison, Serie
from service.analyse_service import AnalyseService
from utils.exceptions import ErreurMetier, RessourceIntrouvable

router = APIRouter()


def get_analyse_service() -> AnalyseService:
    """Fournit le service d'analyse aux routes (FastAPI l'appelle à chaque requête).

    On passe par une fonction plutôt que de créer le service en haut du fichier :
    la connexion à la base n'est ainsi ouverte que lorsqu'une route est appelée.
    """
    return AnalyseService()


def erreur_http(erreur: ErreurMetier) -> HTTPException:
    """Transforme une erreur métier en erreur HTTP.

    - RessourceIntrouvable -> 404 (élément ou donnée inexistante)
    - toute autre erreur métier (DonneesInvalides, ...) -> 422 (paramètres incorrects)
    """
    if isinstance(erreur, RessourceIntrouvable):
        return HTTPException(status_code=404, detail=str(erreur))
    return HTTPException(status_code=422, detail=str(erreur))


@router.get("/evolution", response_model=Serie)
def evolution(
    code_indicateur: str,
    code_pays: str,
    sexe: Sexe | None = None,
    code_classification: str | None = None,
    nb_periodes: int | None = None,
    service: AnalyseService = Depends(get_analyse_service),
) -> Serie:
    """Renvoie l'évolution temporelle d'un indicateur (accès libre)."""
    try:
        return service.evolution(
            code_indicateur=code_indicateur,
            code_pays=code_pays,
            sexe=sexe,
            code_classification=code_classification,
            nb_periodes=nb_periodes,
        )
    except ErreurMetier as erreur:
        raise erreur_http(erreur) from erreur


@router.get("/comparaison-pays", response_model=Comparaison)
def comparaison_pays(
    code_indicateur: str,
    codes_pays: Annotated[list[str], Query()],
    periode: str | None = None,
    sexe: Sexe | None = None,
    code_classification: str | None = None,
    service: AnalyseService = Depends(get_analyse_service),
) -> Comparaison:
    """Compare un indicateur entre plusieurs pays (du plus haut au plus bas)."""
    # TODO : exiger la connexion (dépendance de controller/dependances.py).
    try:
        return service.comparer_pays(
            code_indicateur=code_indicateur,
            codes_pays=codes_pays,
            periode=periode,
            sexe=sexe,
            code_classification=code_classification,
        )
    except ErreurMetier as erreur:
        raise erreur_http(erreur) from erreur


@router.get("/comparaison-indicateurs", response_model=Comparaison)
def comparaison_indicateurs(
    codes_indicateur: Annotated[list[str], Query()],
    code_pays: str,
    sexe: Sexe | None = None,
    code_classification: str | None = None,
    service: AnalyseService = Depends(get_analyse_service),
) -> Comparaison:
    """Compare plusieurs indicateurs pour un même pays."""
    # TODO : exiger la connexion (dépendance de controller/dependances.py).
    try:
        return service.comparer_indicateurs(
            codes_indicateur=codes_indicateur,
            code_pays=code_pays,
            sexe=sexe,
            code_classification=code_classification,
        )
    except ErreurMetier as erreur:
        raise erreur_http(erreur) from erreur


@router.get("/carte", response_model=Comparaison)
def carte(
    code_indicateur: str,
    periode: str,
    sexe: Sexe | None = None,
    code_classification: str | None = None,
    service: AnalyseService = Depends(get_analyse_service),
) -> Comparaison:
    """Renvoie les valeurs par pays pour la carte."""
    # TODO : exiger la connexion (dépendance de controller/dependances.py).
    try:
        return service.carte(
            code_indicateur=code_indicateur,
            periode=periode,
            sexe=sexe,
            code_classification=code_classification,
        )
    except ErreurMetier as erreur:
        raise erreur_http(erreur) from erreur
