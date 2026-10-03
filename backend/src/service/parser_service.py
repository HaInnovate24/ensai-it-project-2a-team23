"""F2 : transformation des données brutes en observations."""

from business_object.observation import Observation


class ParserService:
    """Transforme le CSV ou JSON ILOSTAT en objets Observation."""

    def parser(self, contenu_brut: str, code_indicateur: str) -> list[Observation]:
        """Parse le contenu brut en observations, en rejetant les lignes invalides."""
        ...
