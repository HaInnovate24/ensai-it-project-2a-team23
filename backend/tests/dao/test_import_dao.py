from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch

from business_object.enums import StatutImport
from business_object.import_donnees import ImportDonnees
from dao.import_dao import ImportDao

@pytest.fixture(autouse=True)
def mock_db_cursor():
    """Mock la connexion à la base de données pour isoler le test sans toucher à la vraie DB."""
    with patch('dao.import_dao.DBConnection') as mock_db_class:
        mock_conn = MagicMock()
        mock_db_class.return_value.connection = mock_conn
        
        # Simule le comportement du "with self.conn.cursor() as cursor:"
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        yield mock_cursor


def test_creer_import(mock_db_cursor):
    # On simule ce que la base de données renverrait via la clause RETURNING
    mock_db_cursor.fetchone.return_value = {
        "id": 1,
        "indicateur_code": "EMP_TEMP",
        "utilisateur_id": 1,
        "date_debut": datetime.now(),
        "date_fin": None,
        "statut": "en_cours",
        "nombre_lignes": 0,
        "fichier_source": "API ILOSTAT",
        "message_erreur": None
    }
    
    dao = ImportDao()
    nouvel_import = ImportDonnees(
        indicateur_code="EMP_TEMP",
        utilisateur_id=1,
        date_debut=datetime.now(),
        statut=StatutImport.EN_COURS,
        fichier_source="API ILOSTAT"
    )
    
    import_cree = dao.creer(nouvel_import)
    
    assert import_cree.id == 1
    assert import_cree.indicateur_code == "EMP_TEMP"
    assert import_cree.statut == StatutImport.EN_COURS
    assert mock_db_cursor.execute.called


def test_mettre_a_jour_import(mock_db_cursor):
    # On simule que la ligne a bien été modifiée (1 ligne affectée)
    mock_db_cursor.rowcount = 1
    
    dao = ImportDao()
    import_existant = ImportDonnees(
        id=1,
        indicateur_code="CHOMAGE",
        utilisateur_id=1,
        date_debut=datetime.now(),
        statut=StatutImport.SUCCES,
        nombre_lignes=500
    )
    
    succes = dao.mettre_a_jour(import_existant)
    
    assert succes is True
    assert mock_db_cursor.execute.called


def test_mettre_a_jour_import_inexistant(mock_db_cursor):
    # On simule qu'aucune ligne n'a été modifiée
    mock_db_cursor.rowcount = 0
    
    dao = ImportDao()
    faux_import = ImportDonnees(
        id=9999,
        indicateur_code="TEST",
        utilisateur_id=1,
        date_debut=datetime.now(),
        statut=StatutImport.ECHEC
    )
    
    succes = dao.mettre_a_jour(faux_import)
    assert succes is False


def test_lister_imports(mock_db_cursor):
    # On simule la liste renvoyée par le SELECT
    mock_db_cursor.fetchall.return_value = [
        {
            "id": 2,
            "indicateur_code": "IND_2",
            "utilisateur_id": 1,
            "date_debut": datetime.now(),
            "date_fin": None,
            "statut": "succes",
            "nombre_lignes": 100,
            "fichier_source": "API",
            "message_erreur": None
        },
        {
            "id": 1,
            "indicateur_code": "IND_1",
            "utilisateur_id": 1,
            "date_debut": datetime.now(),
            "date_fin": None,
            "statut": "succes",
            "nombre_lignes": 100,
            "fichier_source": "API",
            "message_erreur": None
        }
    ]
    
    dao = ImportDao()
    imports = dao.lister()
    
    assert len(imports) == 2
    assert imports[0].indicateur_code == "IND_2"
    assert imports[1].indicateur_code == "IND_1"
    assert mock_db_cursor.execute.called