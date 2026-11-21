"""Tests du RapportService, isolés de la base (RapportDao mocké) et sur disque temporaire."""

from unittest.mock import MagicMock, patch

import pytest

from business_object.enums import StatutRapport
from business_object.rapport import Rapport


def _service_avec_dao_mock(tmp_path, dao_mock):
    """Construit un RapportService avec un RapportDao mocké et un stockage temporaire."""
    with patch("service.rapport_service.RapportDao", return_value=dao_mock):
        from service.rapport_service import RapportService

        service = RapportService()
    service.dossier_stockage = str(tmp_path)
    return service


def test_generer_cree_le_pdf_et_met_a_jour_le_statut(tmp_path):
    dao = MagicMock()
    # creer renvoie le rapport avec un id attribué par la "base"
    dao.creer.return_value = Rapport(
        id=7,
        utilisateur_id=1,
        titre="Mon analyse",
        description="Une description",
        statut=StatutRapport.EN_ATTENTE,
    )
    service = _service_avec_dao_mock(tmp_path, dao)

    rapport = service.generer(utilisateur_id=1, titre="Mon analyse", description="Une description")

    # Le PDF a été écrit sur disque
    assert rapport.fichier_path.endswith("rapport_7.pdf")
    import os

    assert os.path.exists(rapport.fichier_path)
    # Le statut final est PRET et la base a été mise à jour
    assert rapport.statut == StatutRapport.PRET
    dao.creer.assert_called_once()
    dao.mettre_a_jour.assert_called_once_with(rapport)


def test_generer_utilise_des_valeurs_par_defaut(tmp_path):
    dao = MagicMock()
    dao.creer.return_value = Rapport(id=3, utilisateur_id=9, titre="Analyse", description="")
    service = _service_avec_dao_mock(tmp_path, dao)

    service.generer(utilisateur_id=9)

    # Le rapport initial a été construit avec le titre par défaut "Analyse"
    rapport_initial = dao.creer.call_args.args[0]
    assert rapport_initial.titre == "Analyse"
    assert rapport_initial.statut == StatutRapport.EN_ATTENTE


def test_lister_delegue_au_dao(tmp_path):
    dao = MagicMock()
    rapports = [Rapport(id=1, utilisateur_id=4)]
    dao.lister.return_value = rapports
    service = _service_avec_dao_mock(tmp_path, dao)

    assert service.lister(4) == rapports
    dao.lister.assert_called_once_with(4)


def test_trouver_par_id_delegue_au_dao(tmp_path):
    dao = MagicMock()
    rapport = Rapport(id=5)
    dao.trouver_par_id.return_value = rapport
    service = _service_avec_dao_mock(tmp_path, dao)

    assert service.trouver_par_id(5) is rapport
    dao.trouver_par_id.assert_called_once_with(5)


def test_telecharger_renvoie_le_contenu_binaire(tmp_path):
    fichier = tmp_path / "rapport_1.pdf"
    fichier.write_bytes(b"%PDF-1.4 contenu")
    dao = MagicMock()
    dao.trouver_par_id.return_value = Rapport(id=1, fichier_path=str(fichier))
    service = _service_avec_dao_mock(tmp_path, dao)

    contenu = service.telecharger(1)

    assert contenu == b"%PDF-1.4 contenu"


def test_telecharger_rapport_absent_leve_file_not_found(tmp_path):
    dao = MagicMock()
    dao.trouver_par_id.return_value = None
    service = _service_avec_dao_mock(tmp_path, dao)

    with pytest.raises(FileNotFoundError):
        service.telecharger(999)


def test_telecharger_fichier_manquant_leve_file_not_found(tmp_path):
    dao = MagicMock()
    dao.trouver_par_id.return_value = Rapport(id=1, fichier_path=str(tmp_path / "absent.pdf"))
    service = _service_avec_dao_mock(tmp_path, dao)

    with pytest.raises(FileNotFoundError):
        service.telecharger(1)
