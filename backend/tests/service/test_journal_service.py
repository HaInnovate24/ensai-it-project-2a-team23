import pytest
from unittest.mock import MagicMock

from business_object.enums import Role
from business_object.journal_activite import JournalActivite
from business_object.utilisateur import Utilisateur
from service.journal_service import JournalService, LONGUEUR_ACTION_MAX, LONGUEUR_CIBLE_MAX
from utils.exceptions import AccesRefuse, DonneesInvalides


@pytest.fixture
def mock_journal_dao():
    return MagicMock()


@pytest.fixture
def service(mock_journal_dao):
    return JournalService(journal_dao=mock_journal_dao)


@pytest.fixture
def admin():
    return Utilisateur(id=1, nom_utilisateur="admin", role=Role.ADMIN, actif=True)


@pytest.fixture
def user_classique():
    return Utilisateur(id=2, nom_utilisateur="user", role=Role.UTILISATEUR, actif=True)


# ==============================================================================
# Tests pour Enregistrer
# ==============================================================================

def test_enregistrer_succes(service, mock_journal_dao):
    mock_journal_dao.creer.return_value = JournalActivite(id=1, action="TEST")
    
    resultat = service.enregistrer(
        utilisateur_id=42, action=" CONNEXION ", cible="Système", details="Détails"
    )
    
    assert resultat.id == 1
    mock_journal_dao.creer.assert_called_once()
    # Vérifie que les espaces autour de l'action ont été supprimés (.strip())
    assert mock_journal_dao.creer.call_args[0][0].action == "CONNEXION"


def test_enregistrer_action_vide_leve_erreur(service):
    with pytest.raises(DonneesInvalides, match="L'action du journal est obligatoire"):
        service.enregistrer(utilisateur_id=1, action="   ")


def test_enregistrer_action_non_string_leve_erreur(service):
    with pytest.raises(DonneesInvalides, match="L'action du journal est obligatoire"):
        service.enregistrer(utilisateur_id=1, action=None)


def test_enregistrer_action_trop_longue_leve_erreur(service):
    action_longue = "A" * (LONGUEUR_ACTION_MAX + 1)
    with pytest.raises(DonneesInvalides, match=f"ne peut pas dépasser {LONGUEUR_ACTION_MAX}"):
        service.enregistrer(utilisateur_id=1, action=action_longue)


def test_enregistrer_cible_trop_longue_leve_erreur(service):
    cible_longue = "B" * (LONGUEUR_CIBLE_MAX + 1)
    with pytest.raises(DonneesInvalides, match=f"ne peut pas dépasser {LONGUEUR_CIBLE_MAX}"):
        service.enregistrer(utilisateur_id=1, action="TEST", cible=cible_longue)


# ==============================================================================
# Tests pour Consulter
# ==============================================================================

def test_consulter(service, mock_journal_dao):
    mock_journal_dao.lister.return_value = [JournalActivite(id=1), JournalActivite(id=2)]
    
    resultat = service.consulter()
    
    assert len(resultat) == 2
    mock_journal_dao.lister.assert_called_once()


# ==============================================================================
# Tests pour Lister (Réservé Admin)
# ==============================================================================

def test_lister_sans_filtre(service, mock_journal_dao, admin):
    mock_journal_dao.lister.return_value = [
        JournalActivite(id=1, utilisateur_id=10, action="LOGIN"),
        JournalActivite(id=2, utilisateur_id=10, action="LOGOUT"),
        JournalActivite(id=3, utilisateur_id=20, action="LOGIN"),
    ]
    
    resultats = service.lister(acteur=admin)
    assert len(resultats) == 3


def test_lister_avec_filtre_utilisateur(service, mock_journal_dao, admin):
    mock_journal_dao.lister.return_value = [
        JournalActivite(id=1, utilisateur_id=10, action="LOGIN"),
        JournalActivite(id=2, utilisateur_id=20, action="LOGOUT"),
    ]
    
    resultats = service.lister(acteur=admin, utilisateur_id=10)
    assert len(resultats) == 1
    assert resultats[0].id == 1


def test_lister_avec_filtre_action(service, mock_journal_dao, admin):
    mock_journal_dao.lister.return_value = [
        JournalActivite(id=1, utilisateur_id=10, action="LOGIN"),
        JournalActivite(id=2, utilisateur_id=10, action="LOGOUT"),
    ]
    
    resultats = service.lister(acteur=admin, action="LOGOUT")
    assert len(resultats) == 1
    assert resultats[0].id == 2


def test_lister_avec_limite(service, mock_journal_dao, admin):
    mock_journal_dao.lister.return_value = [
        JournalActivite(id=1), JournalActivite(id=2), JournalActivite(id=3)
    ]
    
    resultats = service.lister(acteur=admin, limite=2)
    assert len(resultats) == 2


def test_lister_refuse_non_admin(service, user_classique):
    with pytest.raises(AccesRefuse, match="Droits d'administrateur requis"):
        service.lister(acteur=user_classique)


def test_lister_refuse_admin_inactif(service, admin):
    admin.actif = False
    with pytest.raises(AccesRefuse, match="Droits d'administrateur requis"):
        service.lister(acteur=admin)


def test_lister_refuse_acteur_none(service):
    with pytest.raises(AccesRefuse, match="Droits d'administrateur requis"):
        service.lister(acteur=None)


@pytest.mark.parametrize("mauvaise_limite", [-1, 0, 1001, "10", 10.5, True])
def test_lister_limite_invalide_leve_erreur(service, admin, mauvaise_limite):
    with pytest.raises(DonneesInvalides, match="La limite doit être un entier"):
        service.lister(acteur=admin, limite=mauvaise_limite)