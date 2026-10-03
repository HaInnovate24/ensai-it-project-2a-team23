"""Accès aux données du référentiel des pays."""

from business_object.pays import Pays


class PaysDao:
    """Lecture et création des pays en base."""

    def lister(self) -> list[Pays]:
        """Renvoie tous les pays du référentiel."""
        ...

    def trouver_par_code(self, code_pays: str) -> Pays | None:
        """Renvoie le pays correspondant au code, ou None."""
        ...

    def creer(self, pays: Pays) -> Pays:
        """Insère un pays et renvoie l'objet créé."""
        ...
