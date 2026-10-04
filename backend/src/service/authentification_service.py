"""F6 : authentification et contrôle des rôles."""

from business_object.enums import Role
from business_object.utilisateur import Utilisateur


class AuthentificationService:
    """Vérifie le mot de passe, crée et contrôle le jeton, vérifie le rôle."""

    def se_connecter(self, nom_utilisateur: str, mot_de_passe: str) -> str:
        """Vérifie les identifiants et renvoie un jeton de session."""
        ...

    def utilisateur_courant(self, jeton: str) -> Utilisateur:
        """Retrouve l'utilisateur associé à un jeton valide."""
        ...

    def verifier_role(self, utilisateur: Utilisateur, role_requis: Role) -> bool:
        """Vérifie que l'utilisateur possède le rôle requis."""
        ...
