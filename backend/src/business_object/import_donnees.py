"""Objet métier représentant un import de données ILOSTAT."""

from datetime import datetime

from business_object.enums import StatutImport


class ImportDonnees:
    """Trace d'une opération de collecte et de chargement de données.

    Attributs :
        id : identifiant technique.
        indicateur_code : indicateur importé.
        utilisateur_id : utilisateur ayant déclenché l'import (si manuel).
        date_debut : horodatage de début.
        date_fin : horodatage de fin.
        statut : statut de l'import.
        nombre_lignes : nombre de lignes traitées.
        fichier_source : fichier ou URL source.
        message_erreur : message d'erreur en cas d'échec.
    """

    def __init__(
        self,
        id: int | None = None,
        indicateur_code: str | None = None,
        utilisateur_id: int | None = None,
        date_debut: datetime | None = None,
        date_fin: datetime | None = None,
        statut: StatutImport = StatutImport.EN_COURS,
        nombre_lignes: int = 0,
        fichier_source: str | None = None,
        message_erreur: str | None = None,
    ):
        """Initialise un import de données."""
        self.id = id
        self.indicateur_code = indicateur_code
        self.utilisateur_id = utilisateur_id
        self.date_debut = date_debut
        self.date_fin = date_fin

        # Conversion automatique du texte PostgreSQL vers l'Enum Python
        if isinstance(statut, str):
            self.statut = StatutImport(statut)
        else:
            self.statut = statut

        self.nombre_lignes = nombre_lignes
        self.fichier_source = fichier_source
        self.message_erreur = message_erreur
