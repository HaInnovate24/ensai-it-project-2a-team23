"""Tests unitaires pour JournalDao."""

from unittest.mock import MagicMock, patch
from datetime import datetime

from business_object.journal_activite import JournalActivite
from dao.journal_dao import JournalDao


@patch("dao.journal_dao.DBConnection")
def test_creer_journal_succes(mock_db_connection):
    """Vérifie que la création d'une entrée de journal exécute la bonne requête SQL."""
    # 1. Préparation des Mocks
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # On simule le retour de PostgreSQL (le dictionnaire row)
    date_simulee = datetime(2026, 11, 4, 15, 0)
    mock_cursor.fetchone.return_value = {
        "id": 10,
        "utilisateur_id": 42,
        "action": "CONNEXION",
        "cible": "app",
        "details": "Connexion réussie",
        "date_heure": date_simulee
    }

    dao = JournalDao()

    # 2. Exécution de la méthode
    entree_a_creer = JournalActivite(
        utilisateur_id=42,
        action="CONNEXION",
        cible="app",
        details="Connexion réussie"
    )
    resultat = dao.creer(entree_a_creer)

    # 3. Vérifications
    assert resultat.id == 10
    assert resultat.date_heure == date_simulee
    
    # Vérifie que la requête a bien été exécutée 1 fois
    assert mock_cursor.execute.call_count == 1
    
    # Vérifie le contenu de la requête SQL et les paramètres
    args, kwargs = mock_cursor.execute.call_args
    requete_sql = args[0]
    parametres = args[1]
    
    assert "INSERT INTO journal_activite" in requete_sql
    assert parametres[0] == 42           # utilisateur_id
    assert parametres[1] == "CONNEXION"  # action

@patch("dao.journal_dao.DBConnection")
def test_lister_journal(mock_db_connection):
    """Vérifie que le DAO renvoie bien une liste d'objets JournalActivite."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # On simule plusieurs lignes renvoyées par la base
    mock_cursor.fetchall.return_value = [
        {"id": 1, "utilisateur_id": 42, "action": "CONNEXION", "cible": "app", "details": None, "date_heure": datetime(2026, 11, 4, 10, 0)},
        {"id": 2, "utilisateur_id": 42, "action": "DECONNEXION", "cible": "app", "details": None, "date_heure": datetime(2026, 11, 4, 11, 0)}
    ]

    dao = JournalDao()
    resultats = dao.lister()

    assert len(resultats) == 2
    assert resultats[0].id == 1
    assert resultats[1].action == "DECONNEXION"