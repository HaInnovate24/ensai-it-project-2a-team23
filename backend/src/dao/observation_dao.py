"""Accès aux données des observations.

Point de coordination entre la collecte (P2), les analyses (P4) et
l'administration (P5) : les signatures ci-dessous doivent être validées
en commun avant implémentation.
"""

from business_object.enums import Sexe
from business_object.observation import Observation


class ObservationDao:
    """Lecture et écriture des observations en base."""

    def inserer_ou_mettre_a_jour_par_lot(self, observations: list[Observation]) -> int:
        """Insère ou met à jour un lot d'observations ; renvoie le nombre traité.

        S'appuie sur la contrainte d'unicité (indicateur, pays, période,
        sexe, classification) pour éviter les doublons.
        """
        ...

    def lire_serie(
        self,
        code_indicateur: str,
        code_pays: str,
        sexe: Sexe | None = None,
        code_classification: str | None = None,
    ) -> list[Observation]:
        """Renvoie la série temporelle correspondant aux filtres fournis."""
        ...

    def lire_par_periode(
        self,
        code_indicateur: str,
        periode: str,
        codes_pays: list[str] | None = None,
    ) -> list[Observation]:
        """Renvoie les observations d'une période donnée (comparaison, carte)."""
        ...

    def trouver_par_id(self, id: int) -> Observation | None:
        """Renvoie l'observation correspondant à l'identifiant, ou None."""
        ...

    def modifier(self, observation: Observation) -> bool:
        """Met à jour une observation existante ; renvoie True si succès."""
        ...

    def supprimer(self, id: int) -> bool:
        """Supprime une observation ; renvoie True si succès."""
        ...
