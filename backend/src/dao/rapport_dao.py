"""Accès aux données des rapports."""

from business_object.rapport import Rapport


class RapportDao:
    """Enregistrement et consultation des rapports PDF."""

    def creer(self, rapport: Rapport) -> Rapport:
        """Enregistre un rapport et renvoie l'objet créé."""
        ...

    def mettre_a_jour(self, rapport: Rapport) -> bool:
        """Met à jour le statut et le chemin de fichier d'un rapport."""
        ...

    def trouver_par_id(self, id: int) -> Rapport | None:
        """Renvoie le rapport correspondant à l'identifiant, ou None."""
        ...

    def lister(self, utilisateur_id: int | None = None) -> list[Rapport]:
        """Renvoie les rapports, éventuellement filtrés par utilisateur."""
        ...
