"""Objet métier représentant une classification par catégorie d'occupation."""

from business_object.classification import Classification


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
        ...
