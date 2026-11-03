"""Routes HTTP d'authentification : inscription, connexion, profil courant."""

from fastapi import APIRouter, HTTPException
import requests
from model.auth_model import Identifiants
from service.authentification_service import AuthentificationService

router = APIRouter()


@router.post("/inscription")
def inscription(identifiants: Identifiants):
    """Inscrit un nouvel utilisateur."""
    try:
        utilisateur = AuthentificationService().inscrire(identifiants.nom_utilisateur, identifiants.mot_de_passe)
        return {
            "message": "Utilisateur inscrit",
            "statut": "succes",
            "data": utilisateur
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec de la récupération ILOSTAT : {exc}") from exc


@router.post("/connexion")
def connexion(identifiants: Identifiants):
    """Authentifie un utilisateur et renvoie un jeton."""
    try:
        jeton = AuthentificationService().connecter(identifiants.nom_utilisateur, identifiants.mot_de_passe)
        return {
            "message": "Utilisateur connecté",
            "statut": "succes",
            "data": jeton
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec de la récupération ILOSTAT : {exc}") from exc


@router.get("/profil")
def profil_courant(jeton: str):
    """Renvoie le profil de l'utilisateur connecté."""
    try:
        utilisateur = AuthentificationService().utilisateur_depuis_jeton(jeton)
        return {
            "message": "Profil de l'utilisateur",
            "statut": "succes",
            "data": utilisateur
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Échec de la récupération ILOSTAT : {exc}") from exc
