import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from utils.config import load_environment_variables
load_environment_variables()

from business_object.classification import Classification
from dao.classification_dao import ClassificationDao

.
try:
    from business_object.enums import TypeClassification
except ImportError:
    TypeClassification = None

@pytest.fixture
def dao():
    """Fournit une instance du DAO pour les tests."""
    return ClassificationDao()

@pytest.fixture
def nettoyage_db(dao):
    """Nettoie la base de données après le test (Teardown)."""
    yield
    with dao.conn.cursor() as cursor:
        cursor.execute("DELETE FROM classification WHERE code = 'TEST_CLASS';")
    dao.conn.commit()

def test_trouver_par_code_existant(dao):
    """Vérifie qu'on peut récupérer une classification de base."""
    # 'AGE_AGGREGATE_TOTAL' est inséré par pop.referentiel.sql
    classif = dao.trouver_par_code('AGE_AGGREGATE_TOTAL')
    assert classif is not None
    assert classif.code == 'AGE_AGGREGATE_TOTAL'
    # Le DAO renvoie la chaîne ou l'Enum, on vérifie juste que c'est le bon type
    assert str(classif.type) == 'age' or getattr(classif.type, 'value', classif.type) == 'age'

def test_trouver_par_code_inexistant(dao):
    """Vérifie le comportement si la classification n'existe pas."""
    classif = dao.trouver_par_code('CODE_INEXISTANT')
    assert classif is None

def test_lister_sans_filtre(dao):
    """Vérifie que l'on récupère bien toutes les classifications (âges + occupations)."""
    liste = dao.lister()
    # pop.referentiel.sql contient 3 âges et 12 occupations = 15 lignes
    assert len(liste) >= 15
    assert isinstance(liste[0], Classification)

def test_lister_avec_filtre(dao):
    """Vérifie que le filtrage par type fonctionne bien."""
    # On peut passer l'Enum s'il existe, sinon on passe directement la chaîne 'age'
    filtre = TypeClassification.AGE if hasattr(TypeClassification, 'AGE') else 'age'
    
    liste = dao.lister(type=filtre)
    # Il n'y a que 3 tranches d'âge dans le référentiel de base
    assert len(liste) >= 3
    
    # On vérifie que toutes les lignes retournées sont bien du type 'age'
    for classif in liste:
        valeur_type = classif.type.value if hasattr(classif.type, 'value') else classif.type
        assert valeur_type == 'age'

def test_creer_classification(dao, nettoyage_db):
    """Vérifie l'insertion d'une nouvelle classification et le nettoyage."""
    nouvelle = Classification(
        code='TEST_CLASS',
        libelle='Classification de test automatisé',
        type='occupation'
    )
    
    classif_creee = dao.creer(nouvelle)
    assert classif_creee.code == 'TEST_CLASS'
    
    # Vérification en base
    classif_en_base = dao.trouver_par_code('TEST_CLASS')
    assert classif_en_base is not None
    assert classif_en_base.libelle == 'Classification de test automatisé'