"""Schémas Pydantic du journal d'activité."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JournalEntreeCreation(BaseModel):
    """Entrée de journal reçue en entrée (corps de requête)."""

    utilisateur_id: int
    action: str
    cible: str | None = None
    details: str | None = None


class JournalSortie(BaseModel):
    """Entrée de journal renvoyée au client (lecture du journal)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    utilisateur_id: int | None = None
    action: str
    cible: str | None = None
    details: str | None = None
    date_heure: datetime | None = None
