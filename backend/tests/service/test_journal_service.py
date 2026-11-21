from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from business_object.enums import Role
from business_object.journal_activite import JournalActivite
from business_object.utilisateur import Utilisateur
from service.journal_service import (
    LIMITE_MAX,
    LONGUEUR_ACTION_MAX,
    LONGUEUR_CIBLE_MAX,
    JournalService,
)
from utils.exceptions import AccesRefuse, DonneesInvalides


def _admin():
    return Utilisateur(id=1, nom_utilisateur="admin", role=Role.ADMIN, actif=True)


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


# ---------------------------------------------------------------------------
# enregistrer : validations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("action", ["", "   ", None, 123])
def test_enregistrer_action_invalide_leve_donnees_invalides(action):
    service = JournalService(journal_dao=MagicMock())

    with pytest.raises(DonneesInvalides):
        service.enregistrer(utilisateur_id=1, action=action)


def test_enregistrer_action_trop_longue_leve_donnees_invalides():
    service = JournalService(journal_dao=MagicMock())

    with pytest.raises(DonneesInvalides):
        service.enregistrer(utilisateur_id=1, action="A" * (LONGUEUR_ACTION_MAX + 1))


def test_enregistrer_cible_trop_longue_leve_donnees_invalides():
    service = JournalService(journal_dao=MagicMock())

    with pytest.raises(DonneesInvalides):
        service.enregistrer(utilisateur_id=1, action="OK", cible="C" * (LONGUEUR_CIBLE_MAX + 1))


# ---------------------------------------------------------------------------
# lister : accès admin, validation de la limite et filtres
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "acteur",
    [
        None,
        Utilisateur(id=2, nom_utilisateur="u", role=Role.UTILISATEUR, actif=True),
        Utilisateur(id=3, nom_utilisateur="a", role=Role.ADMIN, actif=False),
    ],
)
def test_lister_refuse_si_non_admin(acteur):
    service = JournalService(journal_dao=MagicMock())

    with pytest.raises(AccesRefuse):
        service.lister(acteur)


@pytest.mark.parametrize("limite", [0, -1, LIMITE_MAX + 1, True, "10"])
def test_lister_limite_invalide_leve_donnees_invalides(limite):
    service = JournalService(journal_dao=MagicMock())

    with pytest.raises(DonneesInvalides):
        service.lister(_admin(), limite=limite)


def test_lister_filtre_par_utilisateur_et_action_et_respecte_la_limite():
    dao = MagicMock()
    dao.lister.return_value = [
        JournalActivite(id=1, utilisateur_id=42, action="CONNEXION"),
        JournalActivite(id=2, utilisateur_id=99, action="CONNEXION"),
        JournalActivite(id=3, utilisateur_id=42, action="SUPPRESSION"),
        JournalActivite(id=4, utilisateur_id=42, action="CONNEXION"),
    ]
    service = JournalService(journal_dao=dao)

    resultat = service.lister(_admin(), utilisateur_id=42, action="CONNEXION", limite=1)

    assert len(resultat) == 1
    assert resultat[0].id == 1


def test_lister_sans_filtre_renvoie_tout_dans_la_limite():
    dao = MagicMock()
    dao.lister.return_value = [JournalActivite(id=i) for i in range(5)]
    service = JournalService(journal_dao=dao)

    resultat = service.lister(_admin(), limite=3)

    assert len(resultat) == 3
