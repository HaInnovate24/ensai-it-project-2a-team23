"""Objet métier représentant une classification."""

from business_object.enums import TypeClassification


class Classification:
    """Dimension de ventilation d'une observation (âge ou occupation).

    Attributs :
        code : code de la classification (clé du référentiel).
        libelle : libellé lisible.
        type : type de classification (âge ou occupation).
    """

    def __init__(
        self,
        code: str | None = None,
        libelle: str | None = None,
        type: TypeClassification | None = None,
    ):
        """Initialise une classification."""
        ...
