"""Schémas Pydantic des comptes utilisateurs.

UtilisateurSortie ne contient aucun champ pour l'empreinte du mot
de passe, même si l'objet reçu la contient, elle n'est jamais renvoyée au client.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, StrictBool

from business_object.enums import Role


class UtilisateurCreation(BaseModel):
    """Données d'inscription. Aucun autre champ n'est accepté (on ne peut pas choisir son rôle)."""

    model_config = ConfigDict(extra="forbid")

    nom_utilisateur: str
    mot_de_passe: str


class UtilisateurSortie(BaseModel):
    """Compte renvoyé au client, sans mot de passe ni empreinte."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nom_utilisateur: str
    role: Role
    actif: bool
    date_creation: datetime | None = None
    derniere_connexion: datetime | None = None


class ChangementRole(BaseModel):
    """Demande de changement de rôle. "admin" pour promouvoir, "utilisateur" pour rétrograder."""

    model_config = ConfigDict(extra="forbid")

    role: Role


class ChangementActivation(BaseModel):
    """Demande d'activation (true) ou de désactivation (false) d'un compte.

    StrictBool refuse les valeurs ambiguës comme "false", 0 ou 1.
    """

    model_config = ConfigDict(extra="forbid")

    actif: StrictBool
