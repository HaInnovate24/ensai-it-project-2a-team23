"""F6 : gestion des comptes utilisateurs."""

from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDao


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

    @classmethod
    def lister_utilisateurs(cls) -> list[Utilisateur]:
        """Liste tous les comptes utilisateurs."""
        return UtilisateurDao().lister()

    @classmethod
    def modifier(cls, utilisateur: Utilisateur) -> bool:
        """Met à jour un compte utilisateur (rôle, activation)."""
        return UtilisateurDao().modifier(utilisateur)

