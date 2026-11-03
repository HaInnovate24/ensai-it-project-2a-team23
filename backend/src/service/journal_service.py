"""F6 : journal des actions sensibles."""
from datetime import datetime
from business_object.journal_activite import JournalActivite
from dao.journal_dao import JournalDao

class JournalService:
    """Enregistre chaque action sensible et permet de consulter le journal."""

    def __init__(self):
        self.journal_dao = JournalDao()

    def enregistrer(
        self,
        utilisateur_id: int,
        action: str,
        cible: str | None = None,
        details: str | None = None,
    ) -> JournalActivite:
        """Enregistre une action sensible dans le journal."""
        # Création de l'objet métier
        nouvelle_entree = JournalActivite(
            utilisateur_id=utilisateur_id,
            action=action,
            cible=cible,
            details=details,
            date_action=datetime.now() # L'heure exacte de l'action
        )
        # Sauvegarde en base via le DAO
        return self.journal_dao.creer(nouvelle_entree)

    def consulter(self) -> list[JournalActivite]:
        """Renvoie les entrées du journal."""
        return self.journal_dao.lister()