"""Routes HTTP des référentiels : indicateurs, pays, classifications."""

from fastapi import APIRouter

from service.referentiel_service import ReferentielService

router = APIRouter()


@router.get("/indicateurs")
def lister_indicateurs():
    """Renvoie la liste des indicateurs."""
    ...


@router.get("/pays")
def lister_pays():
    """Renvoie la liste des pays."""
    service = ReferentielService()
    return service.lister_pays()


@router.get("/classifications")
def lister_classifications():
    """Renvoie la liste des classifications."""
    ...
