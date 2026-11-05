import pytest
import requests
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from business_object.enums import Role, StatutImport
from business_object.import_donnees import ImportDonnees
from business_object.utilisateur import Utilisateur
from controller.admin_controller import erreur_http
from main import app
from utils.exceptions import (
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
    DonneesInvalides,
    RessourceIntrouvable,
)

client = TestClient(app)

ADMIN = Utilisateur(id=1, nom_utilisateur="admin", role=Role.ADMIN, actif=True)


def _cible(role=Role.UTILISATEUR, actif=True):
    return Utilisateur(
        id=10,
        nom_utilisateur="dupont_a",
        mot_de_passe_hash="secret-hash",
        role=role,
        actif=actif,
    )


# ==============================================================================
# Test de l'utilitaire d'erreurs HTTP
# ==============================================================================

def test_erreur_http_authentification_echouee():
    erreur = erreur_http(AuthentificationEchouee("Token expiré"))
    assert isinstance(erreur, HTTPException)
    assert erreur.status_code == 401


# ==============================================================================
# Tests Imports (Lancer & Lister)
# ==============================================================================

@patch("controller.admin_controller.collecte_service.collecter_indicateur")
def test_lancer_import_succes(mock_collecter):
    trace_simulee = ImportDonnees(statut=StatutImport.SUCCES, nombre_lignes=500)
    mock_collecter.return_value = trace_simulee

    response = client.post("/admin/imports/EMP_TEMP?from_date=2020&to_date=2025")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Import terminé"
    assert data["statut"] == "succes"
    assert data["lignes_inserees"] == 500
    mock_collecter.assert_called_once_with(code_indicateur="EMP_TEMP", from_date=2020, to_date=2025)


@patch("controller.admin_controller.collecte_service.collecter_indicateur")
def test_lancer_import_value_error(mock_collecter):
    mock_collecter.side_effect = ValueError("Code indicateur invalide")
    
    response = client.post("/admin/imports/INVALIDE")
    
    assert response.status_code == 400


@patch("controller.admin_controller.collecte_service.collecter_indicateur")
def test_lancer_import_request_exception(mock_collecter):
    mock_collecter.side_effect = requests.RequestException("Timeout")
    
    response = client.post("/admin/imports/EMP_TEMP")
    
    assert response.status_code == 502


@patch("controller.admin_controller.collecte_service.lister_imports")
def test_lister_imports_succes(mock_lister):
    mock_lister.return_value = [
        ImportDonnees(id=1, indicateur_code="EMP_TEMP"),
        ImportDonnees(id=2, indicateur_code="CHOMAGE")
    ]

    response = client.get("/admin/imports")

    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


@patch("controller.admin_controller.collecte_service.lister_imports")
def test_lister_imports_value_error(mock_lister):
    mock_lister.side_effect = ValueError("Erreur interne")
    
    response = client.get("/admin/imports")
    assert response.status_code == 400


@patch("controller.admin_controller.collecte_service.lister_imports")
def test_lister_imports_request_exception(mock_lister):
    mock_lister.side_effect = requests.RequestException("Erreur réseau")
    
    response = client.get("/admin/imports")
    assert response.status_code == 502


# ==============================================================================
# Tests Observations (Corriger & Supprimer)
# ==============================================================================

# ==============================================================================
# Tests Observations (Corriger & Supprimer)
# ==============================================================================

def payload_observation():
    """Génère un payload valide pour ObservationCorrection."""
    return {
        "id": 123,
        "code_indicateur": "EMP_TEMP",
        "code_pays": "FRA",
        "periode": "2024",
        "valeur": 42.5,
        "sexe": "total",
        "code_classification": "AGE_TOTAL",
        "source": "Correction manuelle"
    }


@patch("controller.admin_controller.DonneesService.corriger")
def test_corriger_observation_succes(mock_corriger):
    mock_corriger.return_value = None
    
    response = client.put("/admin/observations/123", json=payload_observation())
    
    assert response.status_code == 200
    assert response.json()["data"]["valeur"] == 42.5
    mock_corriger.assert_called_once()


@patch("controller.admin_controller.DonneesService.corriger")
def test_corriger_observation_erreur_metier(mock_corriger):
    mock_corriger.side_effect = RessourceIntrouvable("Observation introuvable")
    
    response = client.put("/admin/observations/999", json=payload_observation())
    assert response.status_code == 404


@patch("controller.admin_controller.DonneesService.corriger")
def test_corriger_observation_value_error(mock_corriger):
    mock_corriger.side_effect = ValueError("Format de valeur invalide")
    
    response = client.put("/admin/observations/123", json=payload_observation())
    assert response.status_code == 400


@patch("controller.admin_controller.DonneesService.supprimer")
def test_supprimer_observation_succes(mock_supprimer):
    mock_supprimer.return_value = None
    response = client.delete("/admin/observations/456")

    assert response.status_code == 200
    assert response.json()["observation_id"] == 456
    mock_supprimer.assert_called_once_with(456)


@patch("controller.admin_controller.DonneesService.supprimer")
def test_supprimer_observation_erreur_metier(mock_supprimer):
    mock_supprimer.side_effect = AccesRefuse("Droits insuffisants")
    
    response = client.delete("/admin/observations/456")
    assert response.status_code == 403


@patch("controller.admin_controller.DonneesService.supprimer")
def test_supprimer_observation_value_error(mock_supprimer):
    mock_supprimer.side_effect = ValueError("Impossible de supprimer")
    
    response = client.delete("/admin/observations/456")
    assert response.status_code == 400


# ==============================================================================
# Tests Comptes Utilisateurs (Listes & Rôles)
# ==============================================================================

@patch("controller.admin_controller.utilisateur_courant")
@patch("controller.admin_controller.utilisateur_service.lister_utilisateurs")
def test_lister_utilisateurs_succes(mock_lister, mock_courant):
    mock_courant.return_value = ADMIN
    mock_lister.return_value = [_cible()]

    response = client.get("/admin/utilisateurs", params={"jeton": "jwt"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data[0]["nom_utilisateur"] == "dupont_a"
    # L'empreinte du mot de passe ne doit jamais être exposée au client.
    assert "mot_de_passe_hash" not in data[0]
    mock_lister.assert_called_once_with(ADMIN)


@patch("controller.admin_controller.utilisateur_courant")
@patch("controller.admin_controller.utilisateur_service.lister_utilisateurs")
def test_lister_utilisateurs_refuse_si_non_admin(mock_lister, mock_courant):
    mock_courant.return_value = ADMIN
    mock_lister.side_effect = AccesRefuse("Droits d'administrateur requis.")

    response = client.get("/admin/utilisateurs", params={"jeton": "jwt"})
    assert response.status_code == 403


@patch("controller.admin_controller.utilisateur_courant")
@patch("controller.admin_controller.utilisateur_service.promouvoir_admin")
def test_promouvoir_admin_succes(mock_promouvoir, mock_courant):
    mock_courant.return_value = ADMIN
    mock_promouvoir.return_value = _cible(role=Role.ADMIN)

    response = client.patch(
        "/admin/utilisateurs/10/role", params={"jeton": "jwt", "role": "admin"}
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "admin"
    mock_promouvoir.assert_called_once_with(ADMIN, 10)


@patch("controller.admin_controller.utilisateur_courant")
@patch("controller.admin_controller.utilisateur_service.retrograder_admin")
def test_retrograder_admin_succes(mock_retrograder, mock_courant):
    mock_courant.return_value = ADMIN
    mock_retrograder.return_value = _cible(role=Role.UTILISATEUR)

    response = client.patch(
        "/admin/utilisateurs/10/role", params={"jeton": "jwt", "role": "utilisateur"}
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "utilisateur"
    mock_retrograder.assert_called_once_with(ADMIN, 10)


@patch("controller.admin_controller.utilisateur_courant")
def test_modifier_role_rejette_role_inconnu(mock_courant):
    mock_courant.return_value = ADMIN
    response = client.patch(
        "/admin/utilisateurs/10/role", params={"jeton": "jwt", "role": "roi"}
    )
    assert response.status_code == 422


@patch("controller.admin_controller.utilisateur_courant")
@patch("controller.admin_controller.utilisateur_service.promouvoir_admin")
def test_promouvoir_admin_erreur_metier(mock_promouvoir, mock_courant):
    mock_courant.return_value = ADMIN
    mock_promouvoir.side_effect = ConflitRessource("Cet utilisateur est déjà administrateur.")

    response = client.patch(
        "/admin/utilisateurs/10/role", params={"jeton": "jwt", "role": "admin"}
    )
    assert response.status_code == 409


@patch("controller.admin_controller.utilisateur_courant")
@patch("controller.admin_controller.utilisateur_service.definir_activation")
def test_modifier_statut_succes(mock_activation, mock_courant):
    mock_courant.return_value = ADMIN
    mock_activation.return_value = _cible(actif=False)

    response = client.patch(
        "/admin/utilisateurs/10/statut", params={"jeton": "jwt", "actif": False}
    )

    assert response.status_code == 200
    assert response.json()["data"]["actif"] is False
    mock_activation.assert_called_once_with(ADMIN, 10, False)


@patch("controller.admin_controller.utilisateur_courant")
@patch("controller.admin_controller.utilisateur_service.definir_activation")
def test_modifier_statut_erreur_metier(mock_activation, mock_courant):
    mock_courant.return_value = ADMIN
    mock_activation.side_effect = RessourceIntrouvable("Utilisateur inconnu : 10.")

    response = client.patch(
        "/admin/utilisateurs/10/statut", params={"jeton": "jwt", "actif": True}
    )
    assert response.status_code == 404