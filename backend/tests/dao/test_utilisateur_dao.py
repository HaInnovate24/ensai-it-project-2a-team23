import sys
import os
import pytest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from utils.config import load_environment_variables
load_environment_variables()

from business_object.utilisateur import Utilisateur
from dao.utilisateur_dao import UtilisateurDao
from business_object.enums import Role 

@pytest.fixture
def dao():
    return UtilisateurDao()

@pytest.fixture
def nettoyage_db(dao):
    yield
    with dao.conn.cursor() as cursor:
        cursor.execute("DELETE FROM utilisateur WHERE nom_utilisateur LIKE 'test_pytest_%';")
    dao.conn.commit()

@pytest.fixture
def utilisateur_test(dao, nettoyage_db):
    u = Utilisateur(
        nom_utilisateur='test_pytest_base',
        mot_de_passe_hash='hash_secret_123',
        role=Role.UTILISATEUR,  # Utilisation de l'Enum
        actif=True
    )
    return dao.creer(u)

def test_creer_utilisateur(dao, nettoyage_db):
    nouveau = Utilisateur(
        nom_utilisateur='test_pytest_nouveau',
        mot_de_passe_hash='hash_456',
        role=Role.ADMIN,  # Utilisation de l'Enum
        actif=True
    )
    cree = dao.creer(nouveau)
    assert cree.id is not None
    assert cree.nom_utilisateur == 'test_pytest_nouveau'
    assert cree.date_creation is not None

def test_trouver_par_id(dao, utilisateur_test):
    trouve = dao.trouver_par_id(utilisateur_test.id)
    assert trouve is not None
    assert trouve.nom_utilisateur == 'test_pytest_base'

def test_trouver_par_nom(dao, utilisateur_test):
    trouve = dao.trouver_par_nom('test_pytest_base')
    assert trouve is not None
    assert trouve.id == utilisateur_test.id

def test_lister(dao, utilisateur_test):
    liste = dao.lister()
    assert len(liste) >= 1
    assert isinstance(liste[0], Utilisateur)

def test_modifier_utilisateur(dao, utilisateur_test):
    utilisateur_test.actif = False
    utilisateur_test.derniere_connexion = datetime.now()
    
    succes = dao.modifier(utilisateur_test)
    assert succes is True
    
    en_base = dao.trouver_par_id(utilisateur_test.id)
    assert en_base.actif is False
    assert en_base.derniere_connexion is not None