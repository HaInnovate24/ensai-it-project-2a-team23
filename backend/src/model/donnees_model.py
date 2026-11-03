"""Schémas Pydantic des observations manipulées par l'administrateur."""

from datetime import datetime

from pydantic import BaseModel

from business_object.enums import Sexe


class ObservationCorrection(BaseModel):
    """Observation à corriger, en entrée de l'API."""

    id: int
    code_indicateur: str | None = None
    code_pays: str | None = None
    periode: str | None = None
    valeur: float | None = None
    sexe: Sexe | None = None
    code_classification: str | None = None
    import_id: int | None = None
    source: str | None = None
    date_import: datetime | None = None
