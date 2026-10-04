"""Fourniture des listes de référentiels."""

from business_object.classification import Classification
from business_object.enums import TypeClassification
from business_object.indicateur import Indicateur
from business_object.pays import Pays


class ReferentielService:
    """Fournit les listes d'indicateurs, de pays et de classifications."""

    def lister_indicateurs(self) -> list[Indicateur]:
        """Renvoie la liste des indicateurs."""
        ...

    def lister_pays(self) -> list[Pays]:
        """Renvoie la liste des pays."""
        ...

    def lister_classifications(
        self, type: TypeClassification | None = None
    ) -> list[Classification]:
        """Renvoie la liste des classifications, éventuellement filtrées par type."""
        ...
