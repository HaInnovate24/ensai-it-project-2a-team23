"""Accès aux données des imports."""

from business_object.import_donnees import ImportDonnees


class ImportDao:
    """Enregistrement et consultation des imports de données."""

    def creer(self, import_donnees: ImportDonnees) -> ImportDonnees:
        """Enregistre un import et renvoie l'objet créé."""
        ...

    def mettre_a_jour(self, import_donnees: ImportDonnees) -> bool:
        """Met à jour le statut et les compteurs d'un import."""
        ...

    def lister(self) -> list[ImportDonnees]:
        """Renvoie l'historique des imports."""
        ...
