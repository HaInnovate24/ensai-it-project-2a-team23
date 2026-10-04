"""Planificateur déclenchant la collecte périodique des données."""


class Planificateur:
    """Déclenche la collecte des indicateurs à intervalle régulier."""

    def demarrer(self) -> None:
        """Démarre la planification de la collecte périodique."""
        ...

    def arreter(self) -> None:
        """Arrête la planification."""
        ...
