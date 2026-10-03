"""Objet métier représentant un pays du référentiel ILOSTAT."""


class Pays:
    """Pays rattaché aux observations.

    Attributs :
        code_pays : code ISO du pays (clé du référentiel).
        nom_pays : nom du pays.
    """

    def __init__(
        self,
        code_pays: str | None = None,
        nom_pays: str | None = None,
    ):
        """Initialise un pays."""
        ...
