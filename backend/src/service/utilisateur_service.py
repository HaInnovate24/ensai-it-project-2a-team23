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

    def lister_utilisateurs(
        self,
    ) -> list[Utilisateur]:
        """lister les utilisateurs."""
        ...
<<<<<<< HEAD


=======
    @classmethod
    def modifier(cls, utilisateur) -> bool:
        """Met à jour un compte utilisateur."""
        ...
>>>>>>> b6df9c9c686c31899b0a4a9e787d227ba5d1ba1e

