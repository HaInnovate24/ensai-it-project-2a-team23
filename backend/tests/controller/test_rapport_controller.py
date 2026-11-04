"""Tests du controller de rapports PDF.

Le router n'est pas branché sur l'app principale (commenté dans main.py),
donc on crée une app de test dédiée. On patche get_rapport_service pour
éviter tout accès réel à la base ou au système de fichiers.
"""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from business_object.enums import StatutRapport
from business_object.rapport import Rapport
from controller.rapport_controller import router

app = FastAPI()
app.include_router(router, prefix="/rapports")
client = TestClient(app)


def _rapport(
    id=1,
    titre="Analyse France",
    description="Emploi par région",
    fichier_path=None,
    statut=StatutRapport.TERMINE,
):
    """Fabrique un objet Rapport pour les tests."""
    return Rapport(
        id=id,
        utilisateur_id=1,
        titre=titre,
        description=description,
        date_creation=datetime(2025, 1, 15, 10, 30),
        fichier_path=fichier_path,
        statut=statut,
    )


# ----------------------------------------------------------------------
# POST /rapports/ — Demande de génération
# ----------------------------------------------------------------------


@patch("controller.rapport_controller.get_rapport_service")
def test_demander_rapport_succes(mock_get_service):
    """Une demande valide renvoie 201 et les données du rapport."""
    rapport = _rapport(id=7, titre="Analyse France")
    service = MagicMock()
    service.generer_rapport.return_value = rapport
    mock_get_service.return_value = service

    response = client.post(
        "/rapports/",
        json={"titre": "Analyse France", "description": "Emploi par région", "code_indicateur": "EMP"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 7
    assert body["titre"] == "Analyse France"
    assert body["statut"] == "termine"
    service.generer_rapport.assert_called_once_with(
        utilisateur_id=1,
        titre="Analyse France",
        description="Emploi par region",
        code_indicateur="EMP",
    )


@patch("controller.rapport_controller.get_rapport_service")
def test_demander_rapport_transmet_les_parametres(mock_get_service):
    """Les champs du body sont bien transmis au service."""
    rapport = _rapport(id=3, titre="Taux chômage")
    service = MagicMock()
    service.generer_rapport.return_value = rapport
    mock_get_service.return_value = service

    client.post(
        "/rapports/",
        json={"titre": "Taux chômage", "description": None, "code_indicateur": "TAUX_CHOM"},
    )

    service.generer_rapport.assert_called_once_with(
        utilisateur_id=1,
        titre="Taux chômage",
        description=None,
        code_indicateur="TAUX_CHOM",
    )


@patch("controller.rapport_controller.get_rapport_service")
def test_demander_rapport_erreur_service_renvoie_500(mock_get_service):
    """Si le service lève une exception, FastAPI renvoie 500."""
    service = MagicMock()
    service.generer_rapport.side_effect = RuntimeError("Erreur inattendue.")
    mock_get_service.return_value = service

    response = client.post(
        "/rapports/",
        json={"titre": "Test", "code_indicateur": "EMP"},
    )

    assert response.status_code == 500


# ----------------------------------------------------------------------
# GET /rapports/ — Liste des rapports
# ----------------------------------------------------------------------


@patch("controller.rapport_controller.get_rapport_service")
def test_lister_rapports_succes(mock_get_service):
    """La liste renvoie 200 avec les rapports de l'utilisateur."""
    rapports = [
        _rapport(id=1, titre="Rapport A"),
        _rapport(id=2, titre="Rapport B"),
    ]
    service = MagicMock()
    service.lister.return_value = rapports
    mock_get_service.return_value = service

    response = client.get("/rapports/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["titre"] == "Rapport A"
    assert data[1]["titre"] == "Rapport B"
    service.lister.assert_called_once()


@patch("controller.rapport_controller.get_rapport_service")
def test_lister_rapports_vide(mock_get_service):
    """Aucun rapport renvoie une liste vide."""
    service = MagicMock()
    service.lister.return_value = []
    mock_get_service.return_value = service

    response = client.get("/rapports/")

    assert response.status_code == 200
    assert response.json() == []


# ----------------------------------------------------------------------
# GET /rapports/{id}/telecharger — Téléchargement PDF
# ----------------------------------------------------------------------


@patch("controller.rapport_controller.get_rapport_service")
def test_telecharger_pdf_succes(mock_get_service, tmp_path):
    """Un PDF existant est renvoyé avec le bon Content-Type."""
    pdf_fichier = tmp_path / "rapport_1.pdf"
    pdf_fichier.write_bytes(b"%PDF-1.4 fake content")

    rapport = _rapport(id=1, fichier_path=str(pdf_fichier))
    service = MagicMock()
    service.trouver_par_id.return_value = rapport
    mock_get_service.return_value = service

    response = client.get("/rapports/1/telecharger")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 fake content"
    service.trouver_par_id.assert_called_once_with(1)


@patch("controller.rapport_controller.get_rapport_service")
def test_telecharger_pdf_inconnu_renvoie_404(mock_get_service):
    """Un rapport inexistant renvoie 404."""
    service = MagicMock()
    service.trouver_par_id.return_value = None
    mock_get_service.return_value = service

    response = client.get("/rapports/999/telecharger")

    assert response.status_code == 404
    assert "introuvable" in response.json()["detail"].lower()


@patch("controller.rapport_controller.get_rapport_service")
def test_telecharger_pdf_fichier_manquant_renvoie_404(mock_get_service):
    """Le rapport existe mais le fichier PDF n'est pas sur le disque : 404."""
    rapport = _rapport(id=1, fichier_path="/chemin/inexistant/rapport.pdf")
    service = MagicMock()
    service.trouver_par_id.return_value = rapport
    mock_get_service.return_value = service

    response = client.get("/rapports/1/telecharger")

    assert response.status_code == 404


@patch("controller.rapport_controller.get_rapport_service")
def test_telecharger_pdf_sans_chemen_renvoie_404(mock_get_service):
    """Le rapport existe mais n'a pas de fichier_path : 404."""
    rapport = _rapport(id=1, fichier_path=None)
    service = MagicMock()
    service.trouver_par_id.return_value = rapport
    mock_get_service.return_value = service

    response = client.get("/rapports/1/telecharger")

    assert response.status_code == 404
