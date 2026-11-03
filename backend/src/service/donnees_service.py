"""F6 : gestion des observations par l'administrateur."""

from business_object.observation import Observation
from dao.observation_dao import ObservationDao


class DonneesService:
    """Recherche, correction et suppression d'observations par l'administrateur."""

    def __init__(self, observation_dao: ObservationDao | None = None):
        """Initialise le service, avec possibilité d'injecter un DAO de test."""
        self.observation_dao = (
            observation_dao if observation_dao is not None else ObservationDao()
        )

    def rechercher(self, **filtres: object) -> list[Observation]:
        """Recherche des observations selon les filtres fournis.

        Filtres disponibles : id, code_indicateur, code_pays, periode, valeur,
        sexe, code_classification, import_id et source.
        """
        return self.observation_dao.rechercher(**filtres)

    def corriger(self, observation: Observation) -> bool:
        """Corrige une observation existante."""
        if observation.id is None:
            return False
        return self.observation_dao.modifier(observation)

    def supprimer(self, observation_id: int) -> bool:
        """Supprime une observation."""
        return self.observation_dao.supprimer(observation_id)
