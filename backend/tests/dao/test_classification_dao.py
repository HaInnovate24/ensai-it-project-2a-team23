import pytest
from unittest.mock import MagicMock, patch

from business_object.classification import Classification
from dao.classification_dao import ClassificationDao

@pytest.fixture(autouse=True)
def mock_db_cursor():
    """Mock la connexion à la base de données pour isoler le test."""
    with patch('dao.classification_dao.DBConnection') as mock_db_class:
        mock_conn = MagicMock()
        mock_db_class.return_value.connection = mock_conn
        
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        yield mock_cursor


def test_trouver_par_code_existant(mock_db_cursor):
    """Vérifie qu'on peut récupérer une classification de base."""
    # On simule ce que PostgreSQL renverrait
    mock_db_cursor.fetchone.return_value = {
        "code": "AGE_AGGREGATE_TOTAL",
        "libelle": "Total (tous âges)",
        "type": "age"
    }
    
    dao = ClassificationDao()
    classif = dao.trouver_par_code("AGE_AGGREGATE_TOTAL")
    
    assert classif is not None
    assert classif.code == "AGE_AGGREGATE_TOTAL"
    assert classif.libelle == "Total (tous âges)"
    assert classif.type == "age"
    assert mock_db_cursor.execute.called


def test_trouver_par_code_inexistant(mock_db_cursor):
    """Vérifie le comportement si le code n'existe pas."""
    # On simule une réponse vide
    mock_db_cursor.fetchone.return_value = None
    
    dao = ClassificationDao()
    classif = dao.trouver_par_code("INCONNU")
    
    assert classif is None
    assert mock_db_cursor.execute.called


def test_lister_sans_filtre(mock_db_cursor):
    """Vérifie la récupération de la liste complète des classifications."""
    # On simule le retour d'un fetchall()
    mock_db_cursor.fetchall.return_value = [
        {"code": "AGE_15_24", "libelle": "15-24 ans", "type": "age"},
        {"code": "OCU_MANAGER", "libelle": "Managers", "type": "occupation"}
    ]
    
    dao = ClassificationDao()
    liste = dao.lister()
    
    assert len(liste) == 2
    assert liste[0].code == "AGE_15_24"
    assert mock_db_cursor.execute.called


def test_lister_avec_filtre(mock_db_cursor):
    """Vérifie que le filtrage par type fonctionne bien."""
    # On simule le retour d'un fetchall() filtré sur 'age'
    mock_db_cursor.fetchall.return_value = [
        {"code": "AGE_15_24", "libelle": "15-24 ans", "type": "age"}
    ]
    
    dao = ClassificationDao()
    liste = dao.lister(type="age")
    
    assert len(liste) == 1
    assert liste[0].type == "age"
    
    # On vérifie que la requête envoyée contenait bien un paramètre (le filtre)
    # arg = (requete, variables)
    args, kwargs = mock_db_cursor.execute.call_args
    assert args[1] == ("age",) # Les variables de la requête SQL


def test_creer_classification(mock_db_cursor):
    """Vérifie l'insertion d'une nouvelle classification."""
    # On simule le retour du RETURNING
    mock_db_cursor.fetchone.return_value = {
        "code": "TEST_CLASS",
        "libelle": "Classification de test",
        "type": "occupation"
    }
    
    nouvelle = Classification(
        code="TEST_CLASS", libelle="Classification de test", type="occupation"
    )
    
    dao = ClassificationDao()
    classif_creee = dao.creer(nouvelle)
    
    assert classif_creee.code == "TEST_CLASS"
    assert classif_creee.libelle == "Classification de test"
    assert mock_db_cursor.execute.called