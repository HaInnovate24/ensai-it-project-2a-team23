"""Tests unitaires pour ImportDao."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from business_object.enums import StatutImport
from business_object.import_donnees import ImportDonnees
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
        "message_erreur": None,
    }

    dao = ImportDao()

    # 2. Exécution de la méthode à tester
    import_a_creer = ImportDonnees(
        indicateur_code="UNE_123",
        utilisateur_id=1,
        statut=StatutImport.EN_COURS,
        fichier_source="test.csv",
    )
    resultat = dao.creer(import_a_creer)

    # 3. Vérifications (Asserts)
    # Vérifie que l'ID renvoyé par la fausse base a bien été assigné à l'objet
    assert resultat.id == 42
    assert resultat.indicateur_code == "UNE_123"

    # Vérifie que la requête a bien été exécutée 1 fois
    assert mock_cursor.execute.call_count == 1

    # On peut même vérifier les arguments passés à la requête SQL
    args, _kwargs = mock_cursor.execute.call_args
    requete_sql = args[0]
    parametres = args[1]

    assert "INSERT INTO import_donnees" in requete_sql
    assert "RETURNING id" in requete_sql
    assert parametres[0] == "UNE_123"  # indicateur_code
    assert parametres[1] == 1  # utilisateur_id


@patch("dao.import_dao.DBConnection")
def test_lister_imports(mock_db_connection):
    """Vérifie que le DAO renvoie bien une liste d'objets ImportDonnees."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # On simule deux lignes renvoyées par le SELECT
    mock_cursor.fetchall.return_value = [
        {"id": 1, "indicateur_code": "IND_A", "statut": "succes"},
        {"id": 2, "indicateur_code": "IND_B", "statut": "echec"},
    ]

    dao = ImportDao()
    resultats = dao.lister()

    assert len(resultats) == 2
    assert resultats[0].id == 1
    assert resultats[0].indicateur_code == "IND_A"
    assert resultats[0].statut == StatutImport.SUCCES
    assert resultats[1].statut == StatutImport.ECHEC


@patch("dao.import_dao.DBConnection")
def test_mettre_a_jour_import(mock_db_connection):
    """Vérifie que la mise à jour exécute l'UPDATE et renvoie True si une ligne est modifiée."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.rowcount = 1

    dao = ImportDao()
    import_a_jour = ImportDonnees(
        id=7,
        indicateur_code="IND_A",
        statut=StatutImport.SUCCES,
        nombre_lignes=120,
    )
    resultat = dao.mettre_a_jour(import_a_jour)

    assert resultat is True
    args, _kwargs = mock_cursor.execute.call_args
    requete_sql = args[0]
    assert "UPDATE import_donnees" in requete_sql
