"""Objet métier représentant une observation statistique."""

from datetime import datetime

from business_object.enums import Sexe


class Observation:
    """Valeur mesurée pour un indicateur, un pays, une période et une ventilation.

    Attributs :
        id : identifiant technique.
        code_indicateur : indicateur concerné.
        code_pays : pays concerné.
        periode : période de la mesure (ex. une année).
        valeur : valeur numérique mesurée.
        sexe : sexe associé à l'observation.
        code_classification : classification (âge ou occupation) associée.
        import_id : import à l'origine de l'enregistrement.
        source : source de la donnée.
        date_import : date d'enregistrement.
    """

    def __init__(
        self,
        id: int | None = None,
        code_indicateur: str | None = None,
        code_pays: str | None = None,
        periode: str | None = None,
        valeur: float | None = None,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
        import_id: int | None = None,
        source: str | None = None,
        date_import: datetime | None = None,
    ):
        """Initialise une observation."""
        ...
