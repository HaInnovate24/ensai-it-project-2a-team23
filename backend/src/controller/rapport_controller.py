"""Routes de l'API pour les rapports PDF."""

import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from model.rapport_model import RapportDemande, RapportSortie 
from service.rapport_service import RapportService

router = APIRouter()

def get_rapport_service() -> RapportService:
    return RapportService()

@router.post("/", response_model=RapportSortie, status_code=status.HTTP_201_CREATED)
def demander_rapport(
    demande: RapportDemande,
    service: RapportService = Depends(get_rapport_service)
):
    """Déclenche la génération d'un nouveau rapport PDF."""
    # TODO: Remplacer par l'ID réel extrait du jeton d'authentification
    utilisateur_id = 1 
    
    return service.generer_rapport(
        utilisateur_id=utilisateur_id,
        titre=demande.titre,
        description=demande.description,
        code_indicateur=demande.code_indicateur
    )

@router.get("/", response_model=list[RapportSortie])
def lister_rapports(service: RapportService = Depends(get_rapport_service)):
    """Liste l'historique des rapports."""
    return service.lister()

@router.get("/{rapport_id}/telecharger")
def telecharger_pdf(
    rapport_id: int, 
    service: RapportService = Depends(get_rapport_service)
):
    """Renvoie le fichier PDF physique pour téléchargement."""
    rapport = service.trouver_par_id(rapport_id)
    
    if not rapport or not rapport.fichier_path or not os.path.exists(rapport.fichier_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Fichier PDF introuvable ou non généré."
        )
        
    return FileResponse(
        path=rapport.fichier_path,
        filename=f"analyse_{rapport_id}.pdf",
        media_type="application/pdf"
    )