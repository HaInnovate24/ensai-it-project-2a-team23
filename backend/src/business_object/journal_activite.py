"""Objet métier représentant une entrée du journal d'activité."""

from datetime import datetime


class JournalActivite:
    """Entrée du journal tracant une action sensible d'un utilisateur.

    Attributs :
        id : identifiant technique.
        utilisateur_id : auteur de l'action.
        action : type d'action réalisée.
        cible : objet visé par l'action.
        details : informations complémentaires.
        date_heure : horodatage de l'action.
    """

    def __init__(
        self,
        id: int | None = None,
        utilisateur_id: int | None = None,
        action: str | None = None,
        cible: str | None = None,
        details: str | None = None,
        date_heure: datetime | None = None,
    ):
        """Initialise une entrée de journal."""
        self.id = id
        self.utilisateur_id = utilisateur_id
        self.action = action
        self.cible = cible
        self.details = details
        self.date_heure = date_heure