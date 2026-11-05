import pytest
from unittest.mock import MagicMock, patch

from business_object.pays import Pays
from dao.pays_dao import PaysDao


@pytest.fixture(autouse=True)
def mock_db_cursor():
    """Mock la connexion à la base de données pour isoler le test."""
    with patch('dao.pays_dao.DBConnection') as mock_db_class:
        mock_conn = MagicMock()
        mock_db_class.return_value.connection = mock_conn
        
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        yield mock_cursor


def test_trouver_par_code_existant(mock_db_cursor):
    """Vérifie qu'on peut récupérer la France."""
    # On simule ce que PostgreSQL renverrait
    mock_db_cursor.fetchone.return_value = {
        "code_pays": "FRA",
        "nom_pays": "France"
    }
    
    dao = PaysDao()
    pays = dao.trouver_par_code("FRA")
    
    assert pays is not None
    assert pays.code_pays == "FRA"
    assert pays.nom_pays == "France"
    assert mock_db_cursor.execute.called


def test_trouver_par_code_inexistant(mock_db_cursor):
    """Vérifie le comportement si le pays n'existe pas."""
    # On simule une réponse vide
    mock_db_cursor.fetchone.return_value = None
    
    dao = PaysDao()
    pays = dao.trouver_par_code("XYZ")
    
    assert pays is None
    assert mock_db_cursor.execute.called


def test_lister_pays(mock_db_cursor):
    """Vérifie que la liste contient bien des objets Pays."""
    # On simule le retour d'un fetchall() avec 22 pays fictifs
    mock_db_cursor.fetchall.return_value = [
        {"code_pays": f"P{i:02d}", "nom_pays": f"Pays {i}"} for i in range(22)
    ]
    
    dao = PaysDao()
    pays_liste = dao.lister()
    
    assert len(pays_liste) >= 22
    assert isinstance(pays_liste[0], Pays)
    assert mock_db_cursor.execute.called


def test_creer_pays(mock_db_cursor):
    """Vérifie l'insertion d'un nouveau pays simulée."""
    # On simule le retour du RETURNING de la base de données
    donnees_simulees = {
        "code_pays": "ZZZ",
        "nom_pays": "Pays de Test"
    }
    mock_db_cursor.fetchone.return_value = donnees_simulees
    
    nouveau_pays = Pays(code_pays="ZZZ", nom_pays="Pays de Test")
    dao = PaysDao()
    
    # 1. Test de la création
    pays_cree = dao.creer(nouveau_pays)
    assert pays_cree.code_pays == "ZZZ"
    assert pays_cree.nom_pays == "Pays de Test"
    
    # 2. Test de la récupération (on simule que trouver_par_code marche juste après)
    mock_db_cursor.fetchone.return_value = donnees_simulees
    pays_en_base = dao.trouver_par_code("ZZZ")
    
    assert pays_en_base is not None
    assert pays_en_base.nom_pays == "Pays de Test"
    assert mock_db_cursor.execute.called