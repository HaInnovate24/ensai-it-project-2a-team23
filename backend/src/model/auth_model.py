"""Schémas Pydantic de l'authentification."""

from pydantic import BaseModel


class Identifiants(BaseModel):
    """Identifiants de connexion en entrée."""

    nom_utilisateur: str
    mot_de_passe: str


class Jeton(BaseModel):
    """Jeton de session en sortie."""

    jeton: str
    type: str = "bearer"
