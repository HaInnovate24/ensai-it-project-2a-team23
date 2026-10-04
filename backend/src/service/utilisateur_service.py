"""F6 : gestion des comptes utilisateurs."""

from business_object.utilisateur import Utilisateur


class UtilisateurService:
    """Inscription, promotion en administrateur et désactivation des comptes."""

    def inscrire(self, nom_utilisateur: str, mot_de_passe: str) -> Utilisateur:
        """Crée un nouveau compte avec mot de passe haché."""
        ...

    def promouvoir_admin(self, utilisateur_id: int) -> bool:
        """Promeut un compte au rôle administrateur."""
        ...

    def desactiver(self, utilisateur_id: int) -> bool:
        """Désactive un compte."""
        ...
