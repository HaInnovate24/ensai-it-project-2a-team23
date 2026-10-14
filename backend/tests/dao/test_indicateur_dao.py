import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from utils.config import load_environment_variables
load_environment_variables()

from business_object.indicateur import Indicateur
from dao.indicateur_dao import IndicateurDao

@pytest.fixture
def dao():
    """Fournit une instance du DAO pour les tests."""
    return IndicateurDao()

@pytest.fixture
def nettoyage_db(dao):
    """Nettoie la base de données après le test (Teardown)."""
    yield
    with dao.conn.cursor() as cursor:
        cursor.execute("DELETE FROM indicateur WHERE code_indicateur = 'TEST_IND';")
    dao.conn.commit()

def test_trouver_par_code_existant(dao):
    """Vérifie qu'on peut récupérer un indicateur de base (EMP_TEMP_SEX_OCU_NB)."""
    indicateur = dao.trouver_par_code('EMP_TEMP_SEX_OCU_NB')
    assert indicateur is not None
    assert indicateur.code_indicateur == 'EMP_TEMP_SEX_OCU_NB'
    assert indicateur.source == 'ILOSTAT'
    assert indicateur.actif is True

def test_trouver_par_code_inexistant(dao):
    """Vérifie le comportement si l'indicateur n'existe pas."""
    indicateur = dao.trouver_par_code('CODE_BIDON')
    assert indicateur is None

def test_lister_indicateurs(dao):
    """Vérifie que la liste contient bien des objets Indicateur (dont les 2 de base)."""
    liste = dao.lister()
    assert len(liste) >= 2
    assert isinstance(liste[0], Indicateur)

def test_creer_indicateur(dao, nettoyage_db):
    """Vérifie l'insertion d'un nouvel indicateur et le nettoyage automatique."""
    nouvel_indicateur = Indicateur(
        code_indicateur='TEST_IND',
        description='Indicateur de test automatisé',
        unite='Pourcentage',
        source='TEST',
        actif=False
    )
    
    ind_cree = dao.creer(nouvel_indicateur)
    
    assert ind_cree.code_indicateur == 'TEST_IND'
    assert ind_cree.description == 'Indicateur de test automatisé'
    
    ind_en_base = dao.trouver_par_code('TEST_IND')
    assert ind_en_base is not None
    assert ind_en_base.unite == 'Pourcentage'
    assert ind_en_base.actif is False