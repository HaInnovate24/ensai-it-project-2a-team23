"""Client HTTP vers l'API ILOSTAT (seul point d'appel externe)."""


class IlostatClient:
    """Appelle l'API ILOSTAT et renvoie le contenu brut (CSV ou JSON)."""

    def telecharger_indicateur(self, code_indicateur: str) -> str:
        """Télécharge les données brutes d'un indicateur et les renvoie telles quelles."""
        ...
