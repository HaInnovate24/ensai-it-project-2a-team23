"""F6 : journal des actions sensibles."""

from business_object.journal_activite import JournalActivite


class JournalService:
    """Enregistre chaque action sensible et permet de consulter le journal."""

    def enregistrer(
        self,
        utilisateur_id: int,
        action: str,
        cible: str | None = None,
        details: str | None = None,
    ) -> JournalActivite:
        """Enregistre une action sensible dans le journal."""
        ...

    def consulter(self) -> list[JournalActivite]:
        """Renvoie les entrées du journal."""
        ...
