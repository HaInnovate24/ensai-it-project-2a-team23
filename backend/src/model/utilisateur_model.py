"""Schémas Pydantic des comptes utilisateurs (sans mot de passe en sortie)."""

from datetime import datetime

from pydantic import BaseModel

from business_object.enums import Role


class UtilisateurCreation(BaseModel):
    """Compte à créer, en entrée."""

    nom_utilisateur: str
    mot_de_passe: str


class UtilisateurSortie(BaseModel):
    """Compte renvoyé à l'API, sans le mot de passe."""

    id: int
    nom_utilisateur: str
    role: Role
    actif: bool
    date_creation: datetime | None = None
    derniere_connexion: datetime | None = None
