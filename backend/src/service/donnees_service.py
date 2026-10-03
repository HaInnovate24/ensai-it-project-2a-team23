"""F6 : gestion des observations par l'administrateur."""

from business_object.observation import Observation


class DonneesService:
    """Recherche, correction et suppression d'observations par l'administrateur."""

    def rechercher(self, **filtres) -> list[Observation]:
        """Recherche des observations selon des filtres."""
        ...

    def corriger(self, observation: Observation) -> bool:
        """Corrige une observation existante."""
        ...

    def supprimer(self, observation_id: int) -> bool:
        """Supprime une observation."""
        ...
