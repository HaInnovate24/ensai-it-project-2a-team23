"""Mise en page des rapports PDF."""


class Pdf:
    """Met en page un rapport et produit le fichier PDF."""

    def construire(self, titre: str, sections: list) -> bytes:
        """Assemble les sections en un document PDF et renvoie son contenu."""
        ...
