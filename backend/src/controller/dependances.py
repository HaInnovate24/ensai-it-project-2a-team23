"""Dépendances FastAPI : lecture du jeton et contrôle d'accès."""

from business_object.utilisateur import Utilisateur


def utilisateur_courant() -> Utilisateur:
    """Lit le jeton et retrouve l'utilisateur courant."""
    ...


def exiger_connexion() -> Utilisateur:
    """Exige un utilisateur connecté."""
    ...


def exiger_admin() -> Utilisateur:
    """Exige un utilisateur connecté possédant le rôle administrateur."""
    ...
