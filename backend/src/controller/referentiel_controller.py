"""Routes HTTP des référentiels : indicateurs, pays, classifications."""

from fastapi import APIRouter

from business_object.enums import TypeClassification
from service.referentiel_service import ReferentielService

router = APIRouter()


@router.get("/indicateurs")
def lister_indicateurs():
    """Renvoie la liste des indicateurs actifs."""
    service = ReferentielService()
    return service.lister_indicateurs()


@router.get("/pays")
def lister_pays():
    """Renvoie la liste des pays."""
    service = ReferentielService()
    return service.lister_pays()


@router.get("/classifications")
def lister_classifications(type: TypeClassification | None = None):
    """Renvoie la liste des classifications, éventuellement filtrées par type."""
    service = ReferentielService()
    return service.lister_classifications(type)
