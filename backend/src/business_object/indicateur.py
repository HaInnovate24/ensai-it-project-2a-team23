"""Objet métier représentant un indicateur ILOSTAT."""


class Indicateur:
    """Indicateur statistique suivi par l'application.

    Attributs :
        code_indicateur : code ILOSTAT de l'indicateur (clé du référentiel).
        description : libellé de l'indicateur.
        unite : unité de mesure des valeurs.
        source : source des données.
        actif : indique si l'indicateur est collecté.
    """

    def __init__(
        self,
        code_indicateur: str | None = None,
        description: str | None = None,
        unite: str | None = None,
        source: str | None = None,
        actif: bool = True,
    ):
        """Initialise un indicateur."""
        self.code_indicateur = code_indicateur
        self.description = description
        self.unite = unite
        self.source = source
        self.actif = actif
