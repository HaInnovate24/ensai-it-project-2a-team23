"""Dépendances FastAPI : lecture du jeton et contrôle d'accès.

Le jeton est lu dans l'en-tête HTTP "Authorization: Bearer <jeton>" (et non dans l'URL).

Utilisation dans une route :
    utilisateur: Utilisateur = Depends(exiger_connexion)   # il faut être connecté
    utilisateur: Utilisateur = Depends(exiger_admin)       # il faut être administrateur
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from business_object.utilisateur import Utilisateur
from service.authentification_service import AuthentificationService

# Lit l'en-tête "Authorization: Bearer <jeton>". auto_error=False : si l'en-tête est
# absent, on laisse le service lever AuthentificationEchouee (réponse 401 uniforme).
schema_bearer = HTTPBearer(auto_error=False, description="Jeton obtenu avec /auth/connexion")


def get_authentification_service() -> AuthentificationService:
    """Fournit le service d'authentification aux routes (FastAPI l'appelle à chaque requête).

    On passe par une fonction pour ouvrir la connexion à la base seulement quand
    une route est appelée, et pour pouvoir remplacer le service dans les tests.
    """
    return AuthentificationService()


def utilisateur_courant(
    identifiants: HTTPAuthorizationCredentials | None = Depends(schema_bearer),
    service: AuthentificationService = Depends(get_authentification_service),
) -> Utilisateur:
    """Lit le jeton de l'en-tête Authorization et retrouve l'utilisateur courant.

    Réponse 401 si le jeton est absent, invalide ou expiré, 403 si le compte est désactivé.
    """
    jeton = identifiants.credentials if identifiants is not None else None
    return service.utilisateur_depuis_jeton(jeton)


def exiger_connexion(utilisateur: Utilisateur = Depends(utilisateur_courant)) -> Utilisateur:
    """Exige un utilisateur connecté (sinon la réponse est 401) et le renvoie."""
    return utilisateur


def exiger_admin(
    utilisateur: Utilisateur = Depends(exiger_connexion),
    service: AuthentificationService = Depends(get_authentification_service),
) -> Utilisateur:
    """Exige un utilisateur connecté possédant le rôle administrateur (sinon réponse 403)."""
    return service.exiger_admin(utilisateur)
