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
        self.id = id
        self.code_indicateur = code_indicateur
        self.code_pays = code_pays
        self.periode = periode
        self.valeur = valeur
        
        # Gère la conversion du type Sexe
        if isinstance(sexe, str):
            self.sexe = Sexe(sexe)
        else:
            self.sexe = sexe
            
        self.code_classification = code_classification
        self.import_id = import_id
        self.source = source
        self.date_import = date_import
