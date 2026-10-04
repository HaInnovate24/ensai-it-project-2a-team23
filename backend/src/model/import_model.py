"""Schémas Pydantic des imports."""

from datetime import datetime

from pydantic import BaseModel

from business_object.enums import StatutImport


class ImportSortie(BaseModel):
    """Résultat d'un import en sortie."""

    id: int
    indicateur_code: str | None = None
    statut: StatutImport
    nombre_lignes: int
    date_debut: datetime | None = None
    date_fin: datetime | None = None
    message_erreur: str | None = None
