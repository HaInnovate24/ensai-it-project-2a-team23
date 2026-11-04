"""Routes HTTP d'administration : imports, données, comptes, journal.

Le controller ne contient pas de logique métier : il lit les paramètres,
retrouve l'administrateur connecté à partir du jeton, appelle le service puis
transforme les erreurs métier en codes HTTP. La gestion des comptes s'appuie
sur ``UtilisateurService`` (lister / promouvoir / rétrograder / activer).
"""

import requests
from fastapi import APIRouter, HTTPException, Query

from business_object.enums import Role
from business_object.observation import Observation
from business_object.utilisateur import Utilisateur
from controller.dependances import utilisateur_courant
from model.donnees_model import ObservationCorrection
from service.collecte_service import CollecteService
from service.donnees_service import DonneesService
from service.utilisateur_service import UtilisateurService
from utils.exceptions import (
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
    DonneesInvalides,
    ErreurMetier,
    RessourceIntrouvable,
)

router = APIRouter()
collecte_service = CollecteService()
utilisateur_service = UtilisateurService()


def erreur_http(erreur: ErreurMetier) -> HTTPException:
    """Transforme une erreur métier en erreur HTTP.

    - AuthentificationEchouee -> 401 (jeton absent, invalide ou expiré)
    - AccesRefuse             -> 403 (droits insuffisants)
    - RessourceIntrouvable    -> 404 (compte ou observation inexistant)
    - ConflitRessource        -> 409 (état déjà atteint)
    - toute autre erreur      -> 422 (paramètres incorrects)
    """
    if isinstance(erreur, AuthentificationEchouee):
        code = 401
    elif isinstance(erreur, AccesRefuse):
        code = 403
    elif isinstance(erreur, RessourceIntrouvable):
        code = 404
    elif isinstance(erreur, ConflitRessource):
        code = 409
    else:  # DonneesInvalides et autres erreurs métier
        code = 422
    return HTTPException(status_code=code, detail=str(erreur))


def _utilisateur_public(utilisateur: Utilisateur) -> dict:
    """Représentation d'un compte sans l'empreinte du mot de passe."""
    return {
        "id": utilisateur.id,
        "nom_utilisateur": utilisateur.nom_utilisateur,
        "role": utilisateur.role,
        "actif": utilisateur.actif,
        "date_creation": utilisateur.date_creation,
        "derniere_connexion": utilisateur.derniere_connexion,
    }


# Imports ILOSTAT


@router.post("/imports/{indicator_id}")
def lancer_import(
    indicator_id: str,
    from_date: int = Query(default=2014, ge=2014, le=2026),
    to_date: int = Query(default=2026, ge=2014, le=2026),
):
    """Lance un import de données depuis ILOSTAT."""
    try:
        trace_import = collecte_service.collecter_indicateur(
            code_indicateur=indicator_id, from_date=from_date, to_date=to_date
        )
        return {
            "message": "Import terminé",
            "statut": trace_import.statut,
            "lignes_inserees": trace_import.nombre_lignes,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502, detail=f"Échec de la récupération ILOSTAT : {exc}"
        ) from exc


@router.get("/imports")
def lister_imports():
    """Renvoie l'historique des imports."""
    try:
        imports = collecte_service.lister_imports()
        return {"message": "Historique des imports", "statut": "succes", "data": imports}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502, detail=f"Échec de la récupération de la liste des données : {exc}"
        ) from exc


# Observations


@router.put("/observations/{observation_id}")
def corriger_observation(observation_id: int, observation: ObservationCorrection):
    """Corrige une observation."""
    try:
        DonneesService().corriger(Observation(**observation.model_dump()))
        return {"message": "Correction observation", "statut": "succes", "data": observation}
    except ErreurMetier as erreur:
        raise erreur_http(erreur) from erreur
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/observations/{observation_id}")
def supprimer_observation(observation_id: int):
    """Supprime une observation."""
    try:
        DonneesService().supprimer(observation_id)
        return {
            "message": "Suppression observation",
            "statut": "succes",
            "observation_id": observation_id,
        }
    except ErreurMetier as erreur:
        raise erreur_http(erreur) from erreur
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Comptes utilisateurs (administration — F6)


@router.get("/utilisateurs")
def lister_utilisateurs(jeton: str):
    """Renvoie la liste des comptes (administrateur uniquement)."""
    try:
        utilisateurs = UtilisateurService.lister_utilisateurs()
        return {"message": "Liste des utilisateurs", "statut": "succes", "data": utilisateurs}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec ILOSTAT : {exc}") from exc


@router.put("/utilisateurs/{utilisateur_id}")
def modifier_utilisateur(utilisateur_id: int, donnees: dict):
    """Gère un compte (promotion, désactivation)."""
    try:
        modification = Utilisateur(**donnees)
        if utilisateur_id != modification.id:
            raise ValueError("L'ID de l'URL ne correspond pas à l'ID de l'utilisateur fourni.")

        succes = UtilisateurService.modifier(modification)
        if succes:
            return {
                "message": "Utilisateur mis à jour avec succès",
                "statut": "succes",
                "utilisateur_id": utilisateur_id,
            }
        else:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(exc)}") from exc


@router.delete("/utilisateurs/{utilisateur_id}/supprimer")
def supprimer_utilisateur(utilisateur_id: int):
    """Supprime un compte utilisateur."""
    try:
        UtilisateurService.supprimer(utilisateur_id)
        return {"message": "Utilisateur supprimé avec succès", "statut": "succes", "utilisateur_id": utilisateur_id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec ILOSTAT : {exc}") from exc


@router.patch("/utilisateurs/{utilisateur_id}/role")
def modifier_role_utilisateur(utilisateur_id: int, role: str):
    """Modifie le role d'un compte utilisateur."""
    try:
        UtilisateurService.modifier_role(utilisateur_id, role)
        return {"message": "Utilisateur promu avec succès", "statut": "succes", "utilisateur_id": utilisateur_id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec ILOSTAT : {exc}") from exc

@router.patch("/utilisateurs/{utilisateur_id}/statut")
def statut_utilisateur(utilisateur_id: int, actif: bool):
    """Modifie le statut d'un compte utilisateur."""
    try:
        UtilisateurService.modifier_statut(utilisateur_id, actif)
        return {"message": "Statut Utilisateur modifié avec succès", "statut": "succes", "utilisateur_id": utilisateur_id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec ILOSTAT : {exc}") from exc
