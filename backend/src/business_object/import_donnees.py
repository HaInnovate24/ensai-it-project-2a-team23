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
"""Tests unitaires pour ImportDao."""

from unittest.mock import MagicMock, patch
from datetime import datetime

from business_object.import_donnees import ImportDonnees
from business_object.enums import StatutImport
from dao.import_dao import ImportDao


@patch("dao.import_dao.DBConnection")
def test_creer_import_succes(mock_db_connection):
    """Vérifie que la création d'un import exécute la bonne requête SQL et renvoie l'objet avec son ID."""
    # 1. Préparation des Mocks (on simule la base de données)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # On simule ce que PostgreSQL renvoie via RETURNING (le dictionnaire row)
    mock_cursor.fetchone.return_value = {
        "id": 42,
        "indicateur_code": "UNE_123",
        "utilisateur_id": 1,
        "date_debut": datetime(2026, 11, 4, 10, 0),
        "date_fin": None,
        "statut": "en_cours",
        "nombre_lignes": 0,
        "fichier_source": "test.csv",
        "message_erreur": None
    }

    dao = ImportDao()

    # 2. Exécution de la méthode à tester
    import_a_creer = ImportDonnees(
        indicateur_code="UNE_123",
        utilisateur_id=1,
        statut=StatutImport.EN_COURS,
        fichier_source="test.csv"
    )
    resultat = dao.creer(import_a_creer)

    # 3. Vérifications (Asserts)
    # Vérifie que l'ID renvoyé par la fausse base a bien été assigné à l'objet
    assert resultat.id == 42
    assert resultat.indicateur_code == "UNE_123"
    
    # Vérifie que la requête a bien été exécutée 1 fois
    assert mock_cursor.execute.call_count == 1
    
    # On peut même vérifier les arguments passés à la requête SQL
    args, kwargs = mock_cursor.execute.call_args
    requete_sql = args[0]
    parametres = args[1]
    
    assert "INSERT INTO import_donnees" in requete_sql
    assert "RETURNING id" in requete_sql
    assert parametres[0] == "UNE_123"  # indicateur_code
    assert parametres[1] == 1          # utilisateur_id

@patch("dao.import_dao.DBConnection")
def test_lister_imports(mock_db_connection):
    """Vérifie que le DAO renvoie bien une liste d'objets ImportDonnees."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # On simule deux lignes renvoyées par le SELECT
    mock_cursor.fetchall.return_value = [
        {"id": 1, "indicateur_code": "IND_A", "statut": "termine"},
        {"id": 2, "indicateur_code": "IND_B", "statut": "en_erreur"}
    ]

    dao = ImportDao()
    resultats = dao.lister()

    assert len(resultats) == 2
    assert resultats[0].id == 1
    assert resultats[0].indicateur_code == "IND_A"
    assert resultats[1].statut == StatutImport.EN_ERREUR