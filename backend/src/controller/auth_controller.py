"""Routes HTTP d'authentification : inscription, connexion, profil courant.

Les routes ne contiennent aucun try/except. les erreurs (identifiants
incorrects, nom déjà pris) sont transformées en codes HTTP par le gestionnaire
global (controller/erreurs_http.py, branché dans main.py).
"""

from fastapi import APIRouter, Depends

from business_object.utilisateur import Utilisateur
from controller.dependances import exiger_connexion, get_authentification_service
from model.auth_model import Identifiants
from model.utilisateur_model import UtilisateurSortie
from service.authentification_service import AuthentificationService

router = APIRouter()


@router.post("/inscription")
def inscription(
    identifiants: Identifiants,
    service: AuthentificationService = Depends(get_authentification_service),
):
    """Inscrit un nouvel utilisateur (accès libre).

    Réponses : 200 compte créé, 409 nom déjà pris, 422 nom ou mot de passe invalide.
    """
    utilisateur = service.inscrire(identifiants.nom_utilisateur, identifiants.mot_de_passe)
    return {
        "message": "Utilisateur inscrit",
        "statut": "succes",
        "data": UtilisateurSortie.model_validate(utilisateur),
    }


@router.post("/connexion")
def connexion(
    identifiants: Identifiants,
    service: AuthentificationService = Depends(get_authentification_service),
):
    """Authentifie un utilisateur et renvoie un jeton (accès libre).

    Le jeton est à envoyer ensuite dans l'en-tête "Authorization: Bearer <jeton>".
    Réponses : 200 jeton, 401 identifiants incorrects, 403 compte désactivé.
    """
    jeton = service.connecter(identifiants.nom_utilisateur, identifiants.mot_de_passe)
    return {"message": "Utilisateur connecté", "statut": "succes", "data": jeton}


@router.get("/profil")
def profil_courant(utilisateur: Utilisateur = Depends(exiger_connexion)):
    """Renvoie le profil de l'utilisateur connecté (jeton exigé dans l'en-tête Authorization)."""
    return {
        "message": "Profil de l'utilisateur",
        "statut": "succes",
        "data": UtilisateurSortie.model_validate(utilisateur),
    }
