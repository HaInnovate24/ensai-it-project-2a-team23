"""Accès aux données du journal d'activité."""

from business_object.journal_activite import JournalActivite


class JournalDao:
    """Écriture et lecture des entrées du journal."""

    def creer(self, entree: JournalActivite) -> JournalActivite:
        """Enregistre une entrée de journal et renvoie l'objet créé."""
        ...

    def lister(self) -> list[JournalActivite]:
        """Renvoie les entrées du journal, de la plus récente à la plus ancienne."""
        ...
