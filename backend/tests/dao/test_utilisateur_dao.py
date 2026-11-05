from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDao

@pytest.fixture(autouse=True)
def mock_db_cursor():
    """Mock la connexion à la base de données pour isoler le test."""
    with patch('dao.utilisateur_dao.DBConnection') as mock_db_class:
        mock_conn = MagicMock()
        mock_db_class.return_value.connection = mock_conn
        
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        yield mock_cursor


def test_creer_utilisateur(mock_db_cursor):
    # On simule le retour du RETURNING de la base de données
    mock_db_cursor.fetchone.return_value = {
        "id": 1,
        "nom_utilisateur": "test_pytest_nouveau",
        "mot_de_passe_hash": "hash_456",
        "role": "admin",
        "actif": True,
        "date_creation": datetime.now(),
        "derniere_connexion": None
    }
    
    dao = UtilisateurDao()
    nouveau = Utilisateur(
        nom_utilisateur="test_pytest_nouveau",
        mot_de_passe_hash="hash_456",
        role=Role.ADMIN,
        actif=True,
    )
    
    cree = dao.creer(nouveau)
    
    assert cree.id == 1
    assert cree.nom_utilisateur == "test_pytest_nouveau"
    assert cree.date_creation is not None
    assert mock_db_cursor.execute.called


def test_trouver_par_id(mock_db_cursor):
    # On simule le retour d'une ligne
    mock_db_cursor.fetchone.return_value = {
        "id": 1,
        "nom_utilisateur": "test_pytest_base",
        "mot_de_passe_hash": "hash_secret",
        "role": "utilisateur",
        "actif": True,
        "date_creation": datetime.now(),
        "derniere_connexion": None
    }
    
    dao = UtilisateurDao()
    trouve = dao.trouver_par_id(1)
    
    assert trouve is not None
    assert trouve.nom_utilisateur == "test_pytest_base"
    assert mock_db_cursor.execute.called


def test_trouver_par_nom(mock_db_cursor):
    # On simule le retour d'une ligne
    mock_db_cursor.fetchone.return_value = {
        "id": 1,
        "nom_utilisateur": "test_pytest_base",
        "mot_de_passe_hash": "hash_secret",
        "role": "utilisateur",
        "actif": True,
        "date_creation": datetime.now(),
        "derniere_connexion": None
    }
    
    dao = UtilisateurDao()
    trouve = dao.trouver_par_nom("test_pytest_base")
    
    assert trouve is not None
    assert trouve.id == 1
    assert mock_db_cursor.execute.called


def test_lister(mock_db_cursor):
    # On simule le retour d'un fetchall()
    mock_db_cursor.fetchall.return_value = [
        {
            "id": 1,
            "nom_utilisateur": "admin",
            "mot_de_passe_hash": "hash",
            "role": "admin",
            "actif": True,
            "date_creation": datetime.now(),
            "derniere_connexion": None
        },
        {
            "id": 2,
            "nom_utilisateur": "user",
            "mot_de_passe_hash": "hash",
            "role": "utilisateur",
            "actif": True,
            "date_creation": datetime.now(),
            "derniere_connexion": None
        }
    ]
    
    dao = UtilisateurDao()
    liste = dao.lister()
    
    assert len(liste) == 2
    assert isinstance(liste[0], Utilisateur)
    assert mock_db_cursor.execute.called


def test_modifier_utilisateur(mock_db_cursor):
    # On simule qu'une ligne a été modifiée
    mock_db_cursor.rowcount = 1
    
    dao = UtilisateurDao()
    utilisateur = Utilisateur(
        id=1,
        nom_utilisateur="test_pytest_base",
        mot_de_passe_hash="hash_secret",
        role=Role.UTILISATEUR,
        actif=False,  # On le désactive
        derniere_connexion=datetime.now()
    )

    succes = dao.modifier(utilisateur)
    
    assert succes is True
    assert mock_db_cursor.execute.called