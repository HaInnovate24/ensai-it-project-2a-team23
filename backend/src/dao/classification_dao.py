"""Accès aux données du référentiel des classifications."""

from business_object.classification import Classification
from business_object.enums import TypeClassification


class ClassificationDao:
    """Lecture et création des classifications (âge, occupation) en base."""

    def lister(self, type: TypeClassification | None = None) -> list[Classification]:
        """Renvoie les classifications, éventuellement filtrées par type."""
        ...

    def trouver_par_code(self, code: str) -> Classification | None:
        """Renvoie la classification correspondant au code, ou None."""
        ...

    def creer(self, classification: Classification) -> Classification:
        """Insère une classification et renvoie l'objet créé."""
        ...
