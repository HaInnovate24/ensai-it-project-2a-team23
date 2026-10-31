"""Routes HTTP d'administration : imports, données, comptes, journal."""

import requests
from fastapi import APIRouter, HTTPException, Query

from service.collecte_service import CollecteService

router = APIRouter()
collecte_service = CollecteService()


@router.post("/imports/{indicator_id}")
def lancer_import(
    indicator_id: str,
    from_date: int = Query(default=2014, ge=1900, le=2100),
    to_date: int = Query(default=2026, ge=1900, le=2100),
):
    """Lance un import de données depuis ILOSTAT."""
    try:
        trace_import = collecte_service.collecter_indicateur(
            code_indicateur=indicator_id, 
            from_date=from_date, 
            to_date=to_date
        )
        return {
            "message": "Import terminé", 
            "statut": trace_import.statut,
            "lignes_inserees": trace_import.nombre_lignes
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec de la récupération ILOSTAT : {exc}") from exc


@router.get("/imports")
def lister_imports():
    """Renvoie l'historique des imports."""
    # TODO : Appeler self.import_dao.lister() via un ImportService (P5)
    ...


@router.put("/observations/{observation_id}")
def corriger_observation(observation_id: int):
    """Corrige une observation."""
    ...


@router.delete("/observations/{observation_id}")
def supprimer_observation(observation_id: int):
    """Supprime une observation."""
    ...


@router.get("/utilisateurs")
def lister_utilisateurs():
    """Renvoie la liste des comptes."""
    ...


@router.put("/utilisateurs/{utilisateur_id}")
def gerer_utilisateur(utilisateur_id: int):
    """Gère un compte (promotion, désactivation)."""
    ...


@router.get("/journal")
def consulter_journal():
    """Renvoie le journal des actions sensibles."""
    ...