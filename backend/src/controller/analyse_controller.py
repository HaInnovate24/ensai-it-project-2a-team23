"""Routes HTTP des analyses : évolution, comparaisons, carte."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/evolution")
def evolution():
    """Renvoie l'évolution temporelle d'un indicateur (accès libre)."""
    ...


@router.get("/comparaison-pays")
def comparaison_pays():
    """Compare un indicateur entre plusieurs pays."""
    ...


@router.get("/comparaison-indicateurs")
def comparaison_indicateurs():
    """Compare plusieurs indicateurs pour un même pays."""
    ...


@router.get("/carte")
def carte():
    """Renvoie les valeurs par pays pour la carte (connexion exigée)."""
    ...
