"""Routes HTTP des analyses : évolution, comparaisons, carte.

Le controller ne calcule rien, il reçoit les paramètres, appelle le service,
puis transforme les erreurs métier en codes HTTP.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from business_object.enums import Sexe
from controller.dependances import exiger_connexion
from controller.erreurs_http import erreur_http
from model.analyse_model import Comparaison, ResumeSerie, Serie
from service.analyse_service import AnalyseService
from utils.exceptions import ErreurMetier

router = APIRouter()


def get_analyse_service() -> AnalyseService:
    """Fournit le service d'analyse aux routes (FastAPI l'appelle à chaque requête).

    On passe par une fonction plutôt que de créer le service en haut du fichier.
    la connexion à la base n'est ainsi ouverte que lorsqu'une route est appelée,
    et les tests peuvent remplacer le service par un faux.
    """
    return AnalyseService()


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


@router.get("/resume-evolution", response_model=ResumeSerie)
def resume_evolution(
    code_indicateur: str,
    code_pays: str,
    sexe: Sexe | None = None,
    code_classification: str | None = None,
    nb_periodes: int | None = None,
    service: AnalyseService = Depends(get_analyse_service),
) -> ResumeSerie:
    """Renvoie le résumé de l'évolution : minimum, maximum, moyenne et variation (accès libre)."""
    try:
        return service.resumer_evolution(
            code_indicateur=code_indicateur,
            code_pays=code_pays,
            sexe=sexe,
            code_classification=code_classification,
            nb_periodes=nb_periodes,
        )
    except ErreurMetier as erreur:
        raise erreur_http(erreur) from erreur


@router.get(
    "/comparaison-pays", response_model=Comparaison, dependencies=[Depends(exiger_connexion)]
)
def comparaison_pays(
    code_indicateur: str,
    codes_pays: Annotated[list[str], Query()],
    periode: str | None = None,
    sexe: Sexe | None = None,
    code_classification: str | None = None,
    service: AnalyseService = Depends(get_analyse_service),
) -> Comparaison:
    """Compare un indicateur entre plusieurs pays, du plus haut au plus bas (connexion exigée)."""
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


@router.get(
    "/comparaison-indicateurs", response_model=Comparaison, dependencies=[Depends(exiger_connexion)]
)
def comparaison_indicateurs(
    codes_indicateur: Annotated[list[str], Query()],
    code_pays: str,
    sexe: Sexe | None = None,
    code_classification: str | None = None,
    base_100: bool = False,
    service: AnalyseService = Depends(get_analyse_service),
) -> Comparaison:
    """Compare plusieurs indicateurs pour un même pays (connexion exigée).

    Avec base_100=true, les séries sont ramenées à 100 à la première période commune.
    """
    try:
        return service.comparer_indicateurs(
            codes_indicateur=codes_indicateur,
            code_pays=code_pays,
            sexe=sexe,
            code_classification=code_classification,
            base_100=base_100,
        )
    except ErreurMetier as erreur:
        raise erreur_http(erreur) from erreur


@router.get("/carte", response_model=Comparaison, dependencies=[Depends(exiger_connexion)])
def carte(
    code_indicateur: str,
    periode: str,
    sexe: Sexe | None = None,
    code_classification: str | None = None,
    service: AnalyseService = Depends(get_analyse_service),
) -> Comparaison:
    """Renvoie les valeurs par pays pour la carte (connexion exigée)."""
    try:
        return service.carte(
            code_indicateur=code_indicateur,
            periode=periode,
            sexe=sexe,
            code_classification=code_classification,
        )
    except ErreurMetier as erreur:
        raise erreur_http(erreur) from erreur
