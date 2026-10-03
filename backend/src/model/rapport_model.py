"""Schémas Pydantic des rapports."""

from datetime import datetime

from pydantic import BaseModel

from business_object.enums import StatutRapport


class RapportDemande(BaseModel):
    """Demande de génération d'un rapport en entrée."""

    titre: str
    description: str | None = None
    code_indicateur: str
    code_pays: str | None = None
    codes_pays: list[str] | None = None


class RapportSortie(BaseModel):
    """Rapport renvoyé à l'API."""

    id: int
    titre: str
    description: str | None = None
    date_creation: datetime | None = None
    statut: StatutRapport
