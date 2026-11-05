import pytest
from unittest.mock import MagicMock

from business_object.classification import Classification
from business_object.enums import TypeClassification
from business_object.indicateur import Indicateur
from business_object.pays import Pays
from service.referentiel_service import ReferentielService
from utils.exceptions import DonneesInvalides, RessourceIntrouvable


@pytest.fixture
def mock_indicateur_dao():
    return MagicMock()


@pytest.fixture
def mock_pays_dao():
    return MagicMock()


@pytest.fixture
def mock_classification_dao():
    return MagicMock()


@pytest.fixture
def service(mock_indicateur_dao, mock_pays_dao, mock_classification_dao):
    """Fournit une instance du service isolée avec de faux DAO."""
    return ReferentielService(
        indicateur_dao=mock_indicateur_dao,
        pays_dao=mock_pays_dao,
        classification_dao=mock_classification_dao,
    )


# ==============================================================================
# Tests pour Lister
# ==============================================================================

def test_lister_indicateurs_inactifs_exclus_par_defaut(service, mock_indicateur_dao):
    ind_actif = Indicateur(code_indicateur="I1", description="A", unite="U", source="S", actif=True)
    ind_inactif = Indicateur(code_indicateur="I2", description="B", unite="U", source="S", actif=False)
    
    mock_indicateur_dao.lister.return_value = [ind_actif, ind_inactif]
    
    # Par défaut, on ne doit récupérer que l'actif
    resultat = service.lister_indicateurs()
    assert len(resultat) == 1
    assert resultat[0].code_indicateur == "I1"


def test_lister_indicateurs_inclut_inactifs_si_demande(service, mock_indicateur_dao):
    ind_actif = Indicateur(code_indicateur="I1", description="A", unite="U", source="S", actif=True)
    ind_inactif = Indicateur(code_indicateur="I2", description="B", unite="U", source="S", actif=False)
    
    mock_indicateur_dao.lister.return_value = [ind_actif, ind_inactif]
    
    # Avec inclure_inactifs=True, on récupère tout
    resultat = service.lister_indicateurs(inclure_inactifs=True)
    assert len(resultat) == 2


def test_lister_pays(service, mock_pays_dao):
    mock_pays_dao.lister.return_value = [Pays(code_pays="FRA", nom_pays="France")]
    
    resultat = service.lister_pays()
    assert len(resultat) == 1
    assert resultat[0].code_pays == "FRA"


def test_lister_classifications_sans_filtre(service, mock_classification_dao):
    service.lister_classifications()
    mock_classification_dao.lister.assert_called_with(None)


def test_lister_classifications_avec_filtre_valide_chaine(service, mock_classification_dao):
    service.lister_classifications(type_classification="age")
    # L'enum est converti avant d'appeler le DAO
    mock_classification_dao.lister.assert_called_with(TypeClassification.AGE)


def test_lister_classifications_avec_filtre_valide_enum(service, mock_classification_dao):
    service.lister_classifications(type_classification=TypeClassification.OCCUPATION)
    mock_classification_dao.lister.assert_called_with(TypeClassification.OCCUPATION)


def test_lister_classifications_avec_filtre_invalide_leve_erreur(service):
    with pytest.raises(DonneesInvalides, match="Type de classification inconnu : type_bidon"):
        service.lister_classifications(type_classification="type_bidon")


# ==============================================================================
# Tests pour Trouver par Code (Indicateur)
# ==============================================================================

def test_trouver_indicateur_existant(service, mock_indicateur_dao):
    mock_indicateur_dao.trouver_par_code.return_value = Indicateur(
        code_indicateur="IND", description="D", unite="U", source="S", actif=True
    )
    
    ind = service.trouver_indicateur("IND")
    assert ind.code_indicateur == "IND"
    mock_indicateur_dao.trouver_par_code.assert_called_with("IND")


def test_trouver_indicateur_introuvable_leve_erreur(service, mock_indicateur_dao):
    mock_indicateur_dao.trouver_par_code.return_value = None
    with pytest.raises(RessourceIntrouvable, match="Indicateur inconnu : XXX"):
        service.trouver_indicateur("XXX")


def test_trouver_indicateur_code_vide_leve_erreur(service):
    with pytest.raises(DonneesInvalides, match="Le code indicateur est obligatoire"):
        service.trouver_indicateur("   ")


# ==============================================================================
# Tests pour Trouver par Code (Pays)
# ==============================================================================

def test_trouver_pays_existant(service, mock_pays_dao):
    mock_pays_dao.trouver_par_code.return_value = Pays(code_pays="FRA", nom_pays="France")
    
    pays = service.trouver_pays("FRA")
    assert pays.code_pays == "FRA"


def test_trouver_pays_introuvable_leve_erreur(service, mock_pays_dao):
    mock_pays_dao.trouver_par_code.return_value = None
    with pytest.raises(RessourceIntrouvable, match="Pays inconnu : ZZZ"):
        service.trouver_pays("ZZZ")


def test_trouver_pays_code_vide_leve_erreur(service):
    with pytest.raises(DonneesInvalides, match="Le code pays est obligatoire"):
        service.trouver_pays("")


# ==============================================================================
# Tests pour Trouver par Code (Classification)
# ==============================================================================

def test_trouver_classification_existant(service, mock_classification_dao):
    mock_classification_dao.trouver_par_code.return_value = Classification(
        code="AGE_TOTAL", libelle="Total", type="age"
    )
    
    classif = service.trouver_classification("AGE_TOTAL")
    assert classif.code == "AGE_TOTAL"


def test_trouver_classification_introuvable_leve_erreur(service, mock_classification_dao):
    mock_classification_dao.trouver_par_code.return_value = None
    with pytest.raises(RessourceIntrouvable, match="Classification inconnue : INCONNU"):
        service.trouver_classification("INCONNU")


def test_trouver_classification_code_vide_leve_erreur(service):
    with pytest.raises(DonneesInvalides, match="Le code classification est obligatoire"):
        service.trouver_classification(None)