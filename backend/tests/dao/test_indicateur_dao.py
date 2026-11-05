import pytest
from unittest.mock import MagicMock, patch

from business_object.indicateur import Indicateur
from dao.indicateur_dao import IndicateurDao

@pytest.fixture(autouse=True)
def mock_db_cursor():
    """Mock la connexion à la base de données pour isoler le test."""
    with patch('dao.indicateur_dao.DBConnection') as mock_db_class:
        mock_conn = MagicMock()
        mock_db_class.return_value.connection = mock_conn
        
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        yield mock_cursor


def test_trouver_par_code_existant(mock_db_cursor):
    """Vérifie qu'on peut récupérer un indicateur de base (EMP_TEMP_SEX_OCU_NB)."""
    # On simule ce que PostgreSQL renverrait
    mock_db_cursor.fetchone.return_value = {
        "code_indicateur": "EMP_TEMP_SEX_OCU_NB",
        "description": "Emploi temporaire par sexe et occupation",
        "unite": "Milliers",
        "source": "ILOSTAT",
        "actif": True
    }
    
    dao = IndicateurDao()
    indicateur = dao.trouver_par_code("EMP_TEMP_SEX_OCU_NB")
    
    assert indicateur is not None
    assert indicateur.code_indicateur == "EMP_TEMP_SEX_OCU_NB"
    assert indicateur.source == "ILOSTAT"
    assert indicateur.actif is True
    assert mock_db_cursor.execute.called


def test_trouver_par_code_inexistant(mock_db_cursor):
    """Vérifie le comportement si l'indicateur n'existe pas."""
    # On simule une réponse vide de la BDD
    mock_db_cursor.fetchone.return_value = None
    
    dao = IndicateurDao()
    indicateur = dao.trouver_par_code("CODE_BIDON")
    
    assert indicateur is None
    assert mock_db_cursor.execute.called


def test_lister_indicateurs(mock_db_cursor):
    """Vérifie que la liste contient bien des objets Indicateur (dont les 2 de base)."""
    # On simule le retour d'un fetchall()
    mock_db_cursor.fetchall.return_value = [
        {
            "code_indicateur": "IND_1",
            "description": "Indicateur 1",
            "unite": "%",
            "source": "ILOSTAT",
            "actif": True
        },
        {
            "code_indicateur": "IND_2",
            "description": "Indicateur 2",
            "unite": "Milliers",
            "source": "ILOSTAT",
            "actif": False
        }
    ]
    
    dao = IndicateurDao()
    liste = dao.lister()
    
    assert len(liste) >= 2
    assert isinstance(liste[0], Indicateur)
    assert mock_db_cursor.execute.called


def test_creer_indicateur(mock_db_cursor):
    """Vérifie l'insertion d'un nouvel indicateur simulée."""
    # On simule le retour du RETURNING de la base de données
    donnees_simulees = {
        "code_indicateur": "TEST_IND",
        "description": "Indicateur de test automatisé",
        "unite": "Pourcentage",
        "source": "TEST",
        "actif": False
    }
    mock_db_cursor.fetchone.return_value = donnees_simulees
    
    nouvel_indicateur = Indicateur(
        code_indicateur="TEST_IND",
        description="Indicateur de test automatisé",
        unite="Pourcentage",
        source="TEST",
        actif=False,
    )

    dao = IndicateurDao()
    ind_cree = dao.creer(nouvel_indicateur)

    assert ind_cree.code_indicateur == "TEST_IND"
    assert ind_cree.description == "Indicateur de test automatisé"
    
    # On simule le trouver_par_code qui suit dans ton test d'origine
    mock_db_cursor.fetchone.return_value = donnees_simulees
    ind_en_base = dao.trouver_par_code("TEST_IND")
    
    assert ind_en_base is not None
    assert ind_en_base.unite == "Pourcentage"
    assert ind_en_base.actif is False
    assert mock_db_cursor.execute.called