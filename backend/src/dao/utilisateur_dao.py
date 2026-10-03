"""Accès aux données des comptes utilisateurs."""

from business_object.utilisateur import Utilisateur


class UtilisateurDao:
    """Création, recherche et modification des comptes."""

    def creer(self, utilisateur: Utilisateur) -> Utilisateur:
        """Insère un compte et renvoie l'objet créé."""
        ...

    def trouver_par_id(self, id: int) -> Utilisateur | None:
        """Renvoie le compte correspondant à l'identifiant, ou None."""
        ...

    def trouver_par_nom(self, nom_utilisateur: str) -> Utilisateur | None:
        """Renvoie le compte correspondant au nom d'utilisateur, ou None."""
        ...

    def lister(self) -> list[Utilisateur]:
        """Renvoie tous les comptes."""
        ...

    def modifier(self, utilisateur: Utilisateur) -> bool:
        """Met à jour un compte (rôle, activation, dernière connexion)."""
        ...
