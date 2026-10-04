"""Objet métier représentant une classification par tranche d'âge."""

from business_object.classification import Classification
from business_object.enums import TypeClassification

class Age(Classification):
    """Classification par tranche d'âge.

    Attributs supplémentaires :
        age_min : borne inférieure de la tranche.
        age_max : borne supérieure de la tranche.
    """

    def __init__(
        self,
        code: str | None = None,
        libelle: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
    ):
        """Initialise une tranche d'âge."""
        super().__init__(code=code, libelle=libelle, type=TypeClassification.AGE)
        self.age_min = age_min
        self.age_max = age_max
