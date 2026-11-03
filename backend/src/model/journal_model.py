"""Schémas Pydantic du journal d'activité."""

from pydantic import BaseModel


class JournalEntreeCreation(BaseModel):
    """Entrée de journal reçue en entrée (corps de requête)."""

    utilisateur_id: int
    action: str
    cible: str | None = None
    details: str | None = None
