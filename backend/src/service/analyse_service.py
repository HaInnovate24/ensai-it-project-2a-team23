"""F3, F4, F5 et carte : construction des séries et comparaisons."""

from business_object.enums import Sexe


class AnalyseService:
    """Construit les séries temporelles et les comparaisons pour les analyses."""

    def evolution(
        self,
        code_indicateur: str,
        code_pays: str,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
    ) -> list:
        """F3 : renvoie l'évolution temporelle d'un indicateur pour un pays."""
        ...

    def comparer_pays(
        self, code_indicateur: str, codes_pays: list[str], periode: str | None = None
    ) -> list:
        """F4 : compare un indicateur entre plusieurs pays."""
        ...

    def comparer_indicateurs(self, codes_indicateur: list[str], code_pays: str) -> list:
        """F5 : compare plusieurs indicateurs pour un même pays."""
        ...

    def carte(self, code_indicateur: str, periode: str) -> list:
        """Renvoie les valeurs par pays pour alimenter la carte."""
        ...
