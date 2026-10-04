"""Objet métier représentant un rapport PDF."""

from datetime import datetime

from business_object.enums import StatutRapport


class Rapport:
    """Rapport PDF généré à la demande d'un utilisateur.

    Attributs :
        id : identifiant technique.
        utilisateur_id : auteur de la demande.
        titre : titre du rapport.
        description : description du contenu.
        date_creation : date de création.
        fichier_path : chemin du fichier PDF généré.
        statut : statut de génération.
    """

    def __init__(
        self,
        id: int | None = None,
        utilisateur_id: int | None = None,
        titre: str | None = None,
        description: str | None = None,
        date_creation: datetime | None = None,
        fichier_path: str | None = None,
        statut: StatutRapport | str = StatutRapport.EN_ATTENTE,
    ):
        """Initialise un rapport."""
        self.id = id
        self.utilisateur_id = utilisateur_id
        self.titre = titre
        self.description = description
        self.date_creation = date_creation
        self.fichier_path = fichier_path
        
        # Gère la conversion du texte PostgreSQL vers l'Enum
        if isinstance(statut, str):
            self.statut = StatutRapport(statut)
        else:
            self.statut = statut