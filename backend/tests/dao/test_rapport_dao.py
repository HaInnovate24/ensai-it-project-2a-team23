"""Tests unitaires pour RapportDao."""

from unittest.mock import MagicMock, patch
from datetime import datetime

from business_object.rapport import Rapport
from business_object.enums import StatutRapport
from dao.rapport_dao import RapportDao


@patch("dao.rapport_dao.DBConnection")
def test_creer_rapport(mock_db_connection):
    """Vérifie l'insertion d'un nouveau rapport."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = {
        "id": 100,
        "utilisateur_id": 1,
        "titre": "Analyse Chômage",
        "description": "Données 2026",
        "date_creation": datetime(2026, 11, 4, 16, 0),
        "fichier_path": None,
        "statut": "en_attente"
    }

    dao = RapportDao()
    nouveau_rapport = Rapport(
        utilisateur_id=1,
        titre="Analyse Chômage",
        description="Données 2026",
        statut=StatutRapport.EN_ATTENTE
    )
    
    resultat = dao.creer(nouveau_rapport)

    assert resultat.id == 100
    assert resultat.titre == "Analyse Chômage"
    
    args = mock_cursor.execute.call_args[0]
    assert "INSERT INTO rapport" in args[0]
    assert args[1][0] == 1  # utilisateur_id
    assert args[1][4] == "en_attente"  # statut

@patch("dao.rapport_dao.DBConnection")
def test_mettre_a_jour_rapport(mock_db_connection):
    """Vérifie la mise à jour du statut et du chemin du fichier."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    mock_cursor.rowcount = 1

    dao = RapportDao()
    rapport_a_maj = Rapport(
        id=100,
        statut=StatutRapport.PRET,
        fichier_path="/rapports_generes/rapport_100.pdf"
    )
    
    succes = dao.mettre_a_jour(rapport_a_maj)

    assert succes is True
    args = mock_cursor.execute.call_args[0]
    assert "UPDATE rapport" in args[0]
    assert args[1][0] == "pret"
    assert args[1][1] == "/rapports_generes/rapport_100.pdf"
    assert args[1][2] == 100

@patch("dao.rapport_dao.DBConnection")
def test_trouver_par_id(mock_db_connection):
    """Vérifie la récupération d'un rapport existant."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    mock_cursor.fetchone.return_value = {
        "id": 50,
        "utilisateur_id": 2,
        "titre": "Test",
        "description": None,
        "date_creation": None,
        "fichier_path": None,
        "statut": "echec"  # Correction : on utilise "echec" au lieu de "erreur"
    }

    dao = RapportDao()
    resultat = dao.trouver_par_id(50)

    assert resultat is not None
    assert resultat.statut == StatutRapport.ECHEC  # Correction ici aussi
    assert mock_cursor.execute.call_args[0][1][0] == 50

@patch("dao.rapport_dao.DBConnection")
def test_lister_rapports_avec_filtre(mock_db_connection):
    """Vérifie le listage des rapports filtré par utilisateur."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_connection.return_value.connection = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
    mock_cursor.fetchall.return_value = [
        {"id": 1, "utilisateur_id": 1, "titre": "R1", "description": "", "date_creation": None, "fichier_path": "", "statut": "pret"}  # Correction ici : "pret" au lieu de "termine"
        ]

    dao = RapportDao()
    resultats = dao.lister(utilisateur_id=1)

    assert len(resultats) == 1
    assert resultats[0].titre == "R1"
    assert resultats[0].statut == StatutRapport.PRET
        
    args = mock_cursor.execute.call_args[0]
    assert "WHERE utilisateur_id = %s" in args[0]
    assert args[1][0] == 1