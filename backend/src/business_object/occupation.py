"""Objet métier représentant une classification par catégorie d'occupation."""

from business_object.classification import Classification
from business_object.enums import TypeClassification


class Occupation(Classification):
    """Classification par catégorie d'occupation.

    Attributs supplémentaires :
        valeur : code de l'occupation dans la nomenclature source.
    """

    def __init__(
        self,
        code: str | None = None,
        libelle: str | None = None,
        valeur: str | None = None,
    ):
        """Initialise une occupation."""
        super().__init__(code=code, libelle=libelle, type=TypeClassification.OCCUPATION)
        self.valeur = valeur