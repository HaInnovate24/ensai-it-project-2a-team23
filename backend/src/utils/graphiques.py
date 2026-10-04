"""Génération des graphiques insérés dans les rapports PDF."""


class Graphiques:
    """Trace les courbes et barres destinées aux rapports."""

    def courbe(self, serie) -> bytes:
        """Trace une courbe à partir d'une série et renvoie l'image."""
        ...

    def barres(self, donnees) -> bytes:
        """Trace un diagramme en barres et renvoie l'image."""
        ...
