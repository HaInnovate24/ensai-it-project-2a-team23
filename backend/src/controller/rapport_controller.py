"""Routes HTTP des rapports PDF : demande, liste, téléchargement."""

from fastapi import APIRouter

router = APIRouter()


@router.post("")
def demander_rapport():
    """Demande la génération d'un rapport PDF."""
    ...


@router.get("")
def lister_rapports():
    """Renvoie les rapports de l'utilisateur connecté."""
    ...


@router.get("/{rapport_id}")
def telecharger_rapport(rapport_id: int):
    """Télécharge le fichier PDF d'un rapport."""
    ...
