"""Objet métier représentant un compte utilisateur."""

from datetime import datetime

from business_object.enums import Role


class Utilisateur:
    """Compte permettant l'accès à l'application.

    Attributs :
        id : identifiant technique.
        nom_utilisateur : identifiant de connexion.
        mot_de_passe_hash : empreinte du mot de passe (jamais en clair).
        role : rôle de l'utilisateur (standard ou administrateur).
        actif : indique si le compte peut se connecter.
        date_creation : date de création du compte.
        derniere_connexion : date de la dernière connexion réussie.
    """

    def __init__(
        self,
        id: int | None = None,
        nom_utilisateur: str | None = None,
        mot_de_passe_hash: str | None = None,
        role: Role = Role.UTILISATEUR,
        actif: bool = True,
        date_creation: datetime | None = None,
        derniere_connexion: datetime | None = None,
    ):
        """Initialise un utilisateur."""
        self.id = id
        self.nom_utilisateur = nom_utilisateur
        self.mot_de_passe_hash = mot_de_passe_hash
        
        # Gère la conversion si PostgreSQL renvoie une chaîne de caractères
        if isinstance(role, str):
            self.role = Role(role)
        else:
            self.role = role
            
        self.actif = actif
        self.date_creation = date_creation
        self.derniere_connexion = derniere_connexion
