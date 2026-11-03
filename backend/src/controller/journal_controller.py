"""Routes HTTP pour le journal d'activité."""

from fastapi import APIRouter, HTTPException
from model.journal_model import JournalEntreeCreation
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
        # On capture toute erreur inattendue pour ne pas faire crasher l'API
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la récupération du journal : {str(exc)}"
        ) from exc


@router.post("/")
def enregistrer_journal(journal: JournalEntreeCreation):
    """Enregistre une action dans le journal."""
    try:
        entree = journal_service.enregistrer(
            utilisateur_id=journal.utilisateur_id,
            action=journal.action,
            cible=journal.cible,
            details=journal.details,
        )
        return {
            "message": "Action enregistrée avec succès",
            "statut": "succes",
            "data": entree
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement : {str(exc)}") from exc