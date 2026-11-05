import pytest
from unittest.mock import MagicMock
from datetime import datetime

from business_object.enums import Sexe, StatutImport
from business_object.import_donnees import ImportDonnees
from business_object.observation import Observation
from business_object.pays import Pays
from business_object.classification import Classification
from service.collecte_service import CollecteService


@pytest.fixture
def mock_ilostat_client():
    return MagicMock()


@pytest.fixture
def mock_import_dao():
    dao = MagicMock()
    # On simule le retour de creer() pour avoir la trace d'import (id=42)
    dao.creer.side_effect = lambda trace: trace
    # On donne l'ID après création
    return dao


@pytest.fixture
def mock_observation_dao():
    dao = MagicMock()
    # On simule le retour du nombre de lignes insérées (len observations)
    dao.inserer_ou_mettre_a_jour_par_lot.side_effect = lambda obs: len(obs)
    return dao


@pytest.fixture
def mock_pays_dao():
    dao = MagicMock()
    dao.lister.return_value = [Pays(code_pays="FRA", nom_pays="France")]
    return dao


@pytest.fixture
def mock_classification_dao():
    dao = MagicMock()
    dao.lister.return_value = [Classification(code="AGE", libelle="Age", type="age")]
    return dao


@pytest.fixture
def mock_indicateur_dao():
    return MagicMock()


@pytest.fixture
def mock_parser_service():
    service = MagicMock()
    # Par défaut, le parser renvoie une observation valide
    service.parser.return_value = [
        Observation(
            id=1,
            code_indicateur="EMP",
            code_pays="FRA",
            periode="2020",
            valeur=10.0,
            sexe=Sexe.TOTAL,
            code_classification="AGE",
            source="ILOSTAT"
        )
    ]
    return service


@pytest.fixture
def service(
    mock_ilostat_client,
    mock_import_dao,
    mock_observation_dao,
    mock_pays_dao,
    mock_classification_dao,
    mock_indicateur_dao,
    mock_parser_service
):
    return CollecteService(
        ilostat_client=mock_ilostat_client,
        import_dao=mock_import_dao,
        observation_dao=mock_observation_dao,
        pays_dao=mock_pays_dao,
        classification_dao=mock_classification_dao,
        indicateur_dao=mock_indicateur_dao,
        parser_service=mock_parser_service
    )


# ==============================================================================
# Tests Validation des Paramètres
# ==============================================================================

def test_collecter_indicateur_code_vide_leve_erreur(service):
    with pytest.raises(ValueError, match="Le code de l'indicateur est obligatoire"):
        service.collecter_indicateur("   ")


def test_collecter_indicateur_dates_invalides_leve_erreur(service):
    with pytest.raises(ValueError, match="doit être inférieure ou égale"):
        service.collecter_indicateur("EMP", from_date=2025, to_date=2020)


# ==============================================================================
# Tests Scénario Nominal
# ==============================================================================

def test_collecter_indicateur_succes(service, mock_ilostat_client, mock_import_dao, mock_observation_dao, mock_parser_service):
    # La trace a besoin d'un ID
    mock_import_dao.creer.side_effect = lambda t: type("T", (), {"__dict__": t.__dict__, "id": 42})()
    
    mock_ilostat_client.telecharger_indicateur.return_value = "header\ndata"
    
    trace = service.collecter_indicateur("EMP", 2020, 2025, utilisateur_id=1)
    
    assert trace.statut == StatutImport.SUCCES
    assert trace.nombre_lignes == 1
    assert trace.message_erreur is None
    assert mock_ilostat_client.telecharger_indicateur.called
    assert mock_parser_service.parser.called
    assert mock_observation_dao.inserer_ou_mettre_a_jour_par_lot.called
    assert mock_import_dao.mettre_a_jour.called


# ==============================================================================
# Tests Scénarios Alternatifs
# ==============================================================================

def test_collecter_csv_vide_ne_parse_pas(service, mock_ilostat_client, mock_parser_service, mock_import_dao):
    mock_import_dao.creer.side_effect = lambda t: type("T", (), {"__dict__": t.__dict__, "id": 42})()
    mock_ilostat_client.telecharger_indicateur.return_value = "   "  # csv vide
    
    trace = service.collecter_indicateur("EMP", 2020, 2020)
    
    assert trace.statut == StatutImport.SUCCES
    assert trace.nombre_lignes == 0
    mock_parser_service.parser.assert_not_called()


def test_collecter_aucune_observation_renvoyee_par_parser(service, mock_ilostat_client, mock_parser_service, mock_import_dao):
    mock_import_dao.creer.side_effect = lambda t: type("T", (), {"__dict__": t.__dict__, "id": 42})()
    mock_ilostat_client.telecharger_indicateur.return_value = "header\n"
    # Le parser renvoie une liste vide
    mock_parser_service.parser.return_value = []
    
    trace = service.collecter_indicateur("EMP")
    
    # Doit attraper l'exception ValueError et mettre la trace en échec
    assert trace.statut == StatutImport.ECHEC
    assert "Aucune observation exploitable" in trace.message_erreur


# ==============================================================================
# Tests Déduplication et Filtrage (Referentiel)
# ==============================================================================

def test_collecter_deduplication(service, mock_ilostat_client, mock_parser_service, mock_import_dao, mock_observation_dao):
    mock_import_dao.creer.side_effect = lambda t: type("T", (), {"__dict__": t.__dict__, "id": 42})()
    mock_ilostat_client.telecharger_indicateur.return_value = "header\ndata"
    
    # On renvoie 2 observations avec EXACTEMENT la même clé métier, mais des valeurs différentes
    obs1 = Observation(code_indicateur="EMP", code_pays="FRA", periode="2020", valeur=10.0, sexe=Sexe.TOTAL, code_classification="AGE", source="ILO")
    obs2 = Observation(code_indicateur="EMP", code_pays="FRA", periode="2020", valeur=20.0, sexe=Sexe.TOTAL, code_classification="AGE", source="ILO")
    mock_parser_service.parser.return_value = [obs1, obs2]
    
    trace = service.collecter_indicateur("EMP")
    
    assert trace.statut == StatutImport.SUCCES
    # Il ne doit rester qu'une seule ligne (obs2 car elle écrase obs1 dans le dictionnaire)
    assert trace.nombre_lignes == 1
    # On vérifie que la ligne gardée est bien passée au DAO
    args = mock_observation_dao.inserer_ou_mettre_a_jour_par_lot.call_args[0][0]
    assert len(args) == 1
    assert args[0].valeur == 20.0


def test_collecter_filtrage_referentiels(service, mock_ilostat_client, mock_parser_service, mock_import_dao, mock_observation_dao):
    mock_import_dao.creer.side_effect = lambda t: type("T", (), {"__dict__": t.__dict__, "id": 42})()
    mock_ilostat_client.telecharger_indicateur.return_value = "header\ndata"
    
    # 1 obs valide, 1 obs pays inconnu (XYZ), 1 obs classif inconnue (BAD)
    obs_valide = Observation(code_indicateur="EMP", code_pays="FRA", periode="2020", valeur=10.0, sexe="total", code_classification="AGE")
    obs_bad_pays = Observation(code_indicateur="EMP", code_pays="XYZ", periode="2020", valeur=10.0, sexe="total")
    obs_bad_classif = Observation(code_indicateur="EMP", code_pays="FRA", periode="2020", valeur=10.0, sexe="total", code_classification="BAD")
    
    mock_parser_service.parser.return_value = [obs_valide, obs_bad_pays, obs_bad_classif]
    
    trace = service.collecter_indicateur("EMP")
    
    assert trace.statut == StatutImport.SUCCES
    assert trace.nombre_lignes == 1 # Seule l'obs valide a survécu


# ==============================================================================
# Tests Gestion des Erreurs Globales
# ==============================================================================

def test_collecter_gere_erreur_execution(service, mock_ilostat_client, mock_import_dao, mock_observation_dao):
    mock_import_dao.creer.side_effect = lambda t: type("T", (), {"__dict__": t.__dict__, "id": 42})()
    
    # On force le client à déclencher une exception non gérée
    mock_ilostat_client.telecharger_indicateur.side_effect = RuntimeError("Crash du réseau ILOSTAT")
    
    trace = service.collecter_indicateur("EMP")
    
    assert trace.statut == StatutImport.ECHEC
    assert "Crash du réseau" in trace.message_erreur
    assert mock_observation_dao.conn.rollback.called
    assert mock_import_dao.mettre_a_jour.called


# ==============================================================================
# Tests Lister Imports
# ==============================================================================

def test_lister_imports(service, mock_import_dao):
    mock_import_dao.lister.return_value = [ImportDonnees(id=1), ImportDonnees(id=2)]
    
    imports = service.lister_imports()
    
    assert len(imports) == 2
    assert mock_import_dao.lister.called