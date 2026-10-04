"""FO3 : génération des rapports PDF."""

from business_object.rapport import Rapport


class RapportService:
    """Assemble séries, résumé statistique, graphiques et conclusion dans un PDF."""

    def generer(self, utilisateur_id: int, **parametres) -> Rapport:
        """Génère un rapport PDF à partir des paramètres d'analyse."""
        ...

    def lister(self, utilisateur_id: int) -> list[Rapport]:
        """Renvoie les rapports d'un utilisateur."""
        ...

    def telecharger(self, rapport_id: int) -> bytes:
        """Renvoie le contenu binaire du PDF d'un rapport."""
        ...
