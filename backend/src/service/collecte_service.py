"""F1 : collecte des données ILOSTAT."""

from business_object.import_donnees import ImportDonnees


class CollecteService:
    """Télécharge un indicateur, le fait parser, l'enregistre et trace l'import."""

    def collecter_indicateur(
        self, code_indicateur: str, utilisateur_id: int | None = None
    ) -> ImportDonnees:
        """Collecte un indicateur de bout en bout et renvoie la trace d'import."""
        ...
