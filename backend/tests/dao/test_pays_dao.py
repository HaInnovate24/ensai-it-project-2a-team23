import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from utils.config import load_environment_variables
load_environment_variables()

from business_object.pays import Pays
from dao.pays_dao import PaysDao

@pytest.fixture
def dao():
    """Fournit une instance du DAO pour les tests."""
    return PaysDao()

@pytest.fixture
def nettoyage_db(dao):
    """Nettoie la base de données après le test."""
    yield
    with dao.conn.cursor() as cursor:
        cursor.execute("DELETE FROM pays WHERE code_pays = 'ZZZ';")
    dao.conn.commit()

def test_trouver_par_code_existant(dao):
    """Vérifie qu'on peut récupérer la France."""
    pays = dao.trouver_par_code('FRA')
    assert pays is not None
    assert pays.code_pays == 'FRA'
    assert pays.nom_pays == 'France'

def test_trouver_par_code_inexistant(dao):
    """Vérifie le comportement si le pays n'existe pas."""
    pays = dao.trouver_par_code('XYZ')
    assert pays is None

def test_lister_pays(dao):
    """Vérifie que la liste contient bien des objets Pays."""
    pays_liste = dao.lister()
    assert len(pays_liste) >= 22
    assert isinstance(pays_liste[0], Pays)

def test_creer_pays(dao, nettoyage_db):
    """Vérifie l'insertion d'un nouveau pays et le nettoyage automatique."""
    nouveau_pays = Pays(code_pays='ZZZ', nom_pays='Pays de Test')
    
    pays_cree = dao.creer(nouveau_pays)
    assert pays_cree.code_pays == 'ZZZ'
    assert pays_cree.nom_pays == 'Pays de Test'
    
    pays_en_base = dao.trouver_par_code('ZZZ')
    assert pays_en_base is not None
    assert pays_en_base.nom_pays == 'Pays de Test'