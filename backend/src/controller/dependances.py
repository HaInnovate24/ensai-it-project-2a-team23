"""Dépendances FastAPI : lecture du jeton et contrôle d'accès."""

from business_object.utilisateur import Utilisateur
from service.authentification_service import AuthentificationService


def utilisateur_courant(jeton: str) -> Utilisateur:
    """Lit le jeton et retrouve l'utilisateur courant."""
    return AuthentificationService().utilisateur_depuis_jeton(jeton)


def exiger_connexion(jeton: str) -> Utilisateur:
    """Exige un utilisateur connecté."""
    return AuthentificationService().exiger_connexion(jeton)


def exiger_admin(utilisateur: Utilisateur) -> Utilisateur:
    """Exige un utilisateur connecté possédant le rôle administrateur."""
    return AuthentificationService().exiger_admin(utilisateur)
