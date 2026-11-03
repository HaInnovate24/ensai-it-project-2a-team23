"""Routes HTTP pour le journal d'activité."""

from fastapi import APIRouter, HTTPException
from service.journal_service import JournalService

router = APIRouter()
journal_service = JournalService()

@router.get("/")
def consulter_journal():
    """Renvoie le journal des actions sensibles."""
    try:
        entrees = journal_service.consulter()
        return {
            "message": "Journal d'activité récupéré avec succès",
            "statut": "succes",
            "data": entrees
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération du journal : {str(exc)}"
        ) from exc