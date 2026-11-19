"""Schéma Pydantic du journal d'activité (sortie)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JournalSortie(BaseModel):
    """Entrée du journal renvoyée au client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    utilisateur_id: int | None = None
    action: str
    cible: str | None = None
    details: str | None = None
    date_heure: datetime | None = None
