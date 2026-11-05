import pytest
from unittest.mock import MagicMock, patch

from business_object.enums import Sexe
from business_object.observation import Observation
from dao.observation_dao import ObservationDao


@pytest.fixture(autouse=True)
def mock_db_cursor():
    """Mock standard de la connexion PostgreSQL."""
    with patch('dao.observation_dao.DBConnection') as mock_db_class:
        mock_conn = MagicMock()
        mock_db_class.return_value.connection = mock_conn
        
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        yield mock_cursor


def fausse_observation_dict():
    """Helper pour générer un dictionnaire d'observation."""
    return {
        "id": 1,
        "code_indicateur": "EMP_TEMP",
        "code_pays": "FRA",
        "periode": "2024",
        "valeur": 12.5,
        "sexe": "total",
        "code_classification": "AGE_TOTAL",
        "import_id": 10,
        "source": "ILOSTAT",
        "date_import": None,
    }


@patch('dao.observation_dao.execute_values')
def test_inserer_ou_mettre_a_jour_par_lot(mock_execute_values, mock_db_cursor):
    """Vérifie l'insertion en lot."""
    dao = ObservationDao()
    
    obs1 = Observation(**fausse_observation_dict())
    obs2 = Observation(**fausse_observation_dict())
    obs2.sexe = Sexe.FEMME  # Pour tester la conversion de l'Enum
    
    nb_traites = dao.inserer_ou_mettre_a_jour_par_lot([obs1, obs2])
    
    assert nb_traites == 2
    assert mock_execute_values.called
    
    # Vérifie que les données ont bien été formatées pour execute_values
    args = mock_execute_values.call_args[0]
    valeurs_inserees = args[2]  # Le 3ème argument d'execute_values est la liste des valeurs
    assert valeurs_inserees[0][4] == "total"
    assert valeurs_inserees[1][4] == "femme"  # L'Enum Sexe.FEMME a bien été converti


def test_lire_serie_sans_filtres_optionnels(mock_db_cursor):
    mock_db_cursor.fetchall.return_value = [fausse_observation_dict()]
    
    dao = ObservationDao()
    resultats = dao.lire_serie("EMP", "FRA")
    
    assert len(resultats) == 1
    args = mock_db_cursor.execute.call_args[0]
    assert "sexe =" not in args[0]


def test_lire_serie_avec_filtres_optionnels(mock_db_cursor):
    mock_db_cursor.fetchall.return_value = []
    
    dao = ObservationDao()
    dao.lire_serie("EMP", "FRA", sexe=Sexe.HOMME, code_classification="AGE")
    
    args = mock_db_cursor.execute.call_args[0]
    requete, parametres = args[0], args[1]
    
    assert "AND sexe = %s" in requete
    assert "AND code_classification = %s" in requete
    assert "homme" in parametres
    assert "AGE" in parametres


def test_lire_par_periode_sans_pays(mock_db_cursor):
    mock_db_cursor.fetchall.return_value = []
    
    dao = ObservationDao()
    dao.lire_par_periode("EMP", "2024")
    
    args = mock_db_cursor.execute.call_args[0]
    assert "ANY(%s)" not in args[0]


def test_lire_par_periode_avec_pays(mock_db_cursor):
    mock_db_cursor.fetchall.return_value = []
    
    dao = ObservationDao()
    dao.lire_par_periode("EMP", "2024", codes_pays=["FRA", "ESP"])
    
    args = mock_db_cursor.execute.call_args[0]
    assert "code_pays = ANY(%s)" in args[0]
    assert ["FRA", "ESP"] in args[1]


def test_rechercher_valide(mock_db_cursor):
    mock_db_cursor.fetchall.return_value = [fausse_observation_dict()]
    
    dao = ObservationDao()
    resultat = dao.rechercher(code_pays="FRA", sexe=Sexe.FEMME)
    
    assert len(resultat) == 1
    args = mock_db_cursor.execute.call_args[0]
    assert "code_pays = %s" in args[0]
    assert "sexe = %s" in args[0]
    assert ("FRA", "femme") == args[1]


def test_rechercher_none_comme_is_null(mock_db_cursor):
    mock_db_cursor.fetchall.return_value = []
    
    dao = ObservationDao()
    dao.rechercher(code_classification=None)
    
    args = mock_db_cursor.execute.call_args[0]
    assert "code_classification IS NULL" in args[0]


def test_rechercher_sans_filtre(mock_db_cursor):
    mock_db_cursor.fetchall.return_value = []
    
    dao = ObservationDao()
    dao.rechercher()
    
    args = mock_db_cursor.execute.call_args[0]
    assert " WHERE " not in args[0]


def test_rechercher_refuse_filtre_inconnu():
    dao = ObservationDao()
    with pytest.raises(ValueError, match="Filtre\\(s\\) de recherche inconnu\\(s\\)"):
        dao.rechercher(colonne_dangereuse="FRA")


def test_trouver_par_id(mock_db_cursor):
    mock_db_cursor.fetchone.return_value = fausse_observation_dict()
    
    dao = ObservationDao()
    obs = dao.trouver_par_id(1)
    
    assert obs is not None
    assert obs.id == 1


def test_trouver_par_id_inexistant(mock_db_cursor):
    mock_db_cursor.fetchone.return_value = None
    
    dao = ObservationDao()
    assert dao.trouver_par_id(99) is None


def test_modifier_succes(mock_db_cursor):
    mock_db_cursor.rowcount = 1
    
    dao = ObservationDao()
    obs = Observation(**fausse_observation_dict())
    
    assert dao.modifier(obs) is True
    assert mock_db_cursor.execute.called


def test_modifier_echec(mock_db_cursor):
    mock_db_cursor.rowcount = 0
    
    dao = ObservationDao()
    obs = Observation(**fausse_observation_dict())
    
    assert dao.modifier(obs) is False


def test_supprimer_succes(mock_db_cursor):
    mock_db_cursor.rowcount = 1
    dao = ObservationDao()
    assert dao.supprimer(1) is True


def test_supprimer_echec(mock_db_cursor):
    mock_db_cursor.rowcount = 0
    dao = ObservationDao()
    assert dao.supprimer(99) is False