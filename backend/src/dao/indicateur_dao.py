"""Accès aux données du référentiel des indicateurs."""

from business_object.indicateur import Indicateur


class IndicateurDao:
    """Lecture et création des indicateurs en base."""

    def lister(self) -> list[Indicateur]:
        """Renvoie tous les indicateurs du référentiel."""
        ...

    def trouver_par_code(self, code_indicateur: str) -> Indicateur | None:
        """Renvoie l'indicateur correspondant au code, ou None."""
        ...

    def creer(self, indicateur: Indicateur) -> Indicateur:
        """Insère un indicateur et renvoie l'objet créé."""
        ...
