from datetime import datetime
from unittest.mock import patch

from business_object.journal_activite import JournalActivite
from service.journal_service import JournalService


@patch("service.journal_service.JournalDao")
def test_enregistrer_succes(MockJournalDao):
    # Configuration du mock
    mock_dao = MockJournalDao.return_value
    entree_simulee = JournalActivite(
        id=1, utilisateur_id=42, action="CONNEXION", date_heure=datetime.now()
    )
    mock_dao.creer.return_value = entree_simulee

    # Exécution
    service = JournalService()
    resultat = service.enregistrer(
        utilisateur_id=42, action="CONNEXION", cible="Système", details="Test"
    )

    # Vérifications
    assert resultat.id == 1
    assert resultat.action == "CONNEXION"
    mock_dao.creer.assert_called_once()

    # Vérification des paramètres envoyés au DAO
    args, _ = mock_dao.creer.call_args
    objet_envoye = args[0]
    assert objet_envoye.utilisateur_id == 42
    assert objet_envoye.details == "Test"


@patch("service.journal_service.JournalDao")
def test_consulter_succes(MockJournalDao):
    mock_dao = MockJournalDao.return_value
    mock_dao.lister.return_value = [JournalActivite(id=1), JournalActivite(id=2)]

    service = JournalService()
    resultat = service.consulter()

    assert len(resultat) == 2
    mock_dao.lister.assert_called_once()
