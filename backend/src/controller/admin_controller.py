"""Routes HTTP d'administration : imports, données, comptes, journal."""

import requests
from fastapi import APIRouter, HTTPException, Query

from service.collecte_service import CollecteService
from service.donnees_service import DonneesService
from service.utilisateur_service import UtilisateurService

from business_object.observation import Observation


router = APIRouter()
collecte_service = CollecteService()


@router.post("/imports/{indicator_id}")
def lancer_import(
    indicator_id: str,
    from_date: int = Query(default=2014, ge=2014, le=2026),
    to_date: int = Query(default=2026, ge=2014, le=2026),
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
    try:
        imports = collecte_service.lister_imports(
           )
        return {
            "message": "Historique des imports",
            "statut": "succes",
            "data": imports
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec de la récupération de la liste des données : {exc}") from exc



@router.put("/observations/{observation_id}")
def corriger_observation(observation_id: int, observation:Observation):
    """Corrige une observation."""
    try:
        observation = DonneesService.corriger(observation)
        return {
            "message": "Correction observation",
            "statut": "succes",
            "data": observation
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec de la récupération ILOSTAT : {exc}") from exc




@router.delete("/observations/{observation_id}")
def supprimer_observation(observation_id: int):
    """Supprime une observation."""
    try:
        observation = DonneesService.supprimer(observation_id)
        return {
            "message": "Suppression observation",
            "statut": "succes",
            "observation_id": observation_id
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec de la récupération ILOSTAT : {exc}") from exc



@router.get("/utilisateurs")
def lister_utilisateurs():
    """Renvoie la liste des comptes."""
    try:
        utilisateurs = UtilisateurService.lister_utilisateurs()
        return {
            "message": "Liste des utilisateurs",
            "statut": "succes",
            "data": utilisateurs
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec de la récupération ILOSTAT : {exc}") from exc



@router.put("/utilisateurs/{utilisateur_id}")
def gerer_utilisateur(utilisateur_id: int):
    """Gère un compte (promotion, désactivation)."""
    ...


@router.get("/journal")
def consulter_journal():
    """Renvoie le journal des actions sensibles."""
    ...
