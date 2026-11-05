from unittest.mock import patch

from fastapi.testclient import TestClient

from business_object.enums import Role
from business_object.utilisateur import Utilisateur
from main import app
from utils.exceptions import AccesRefuse, ConflitRessource, RessourceIntrouvable

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
def test_promouvoir_admin_deja_admin(mock_promouvoir, mock_courant):
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
def test_modifier_statut_utilisateur_inconnu(mock_activation, mock_courant):
    mock_courant.return_value = ADMIN
    mock_activation.side_effect = RessourceIntrouvable("Utilisateur inconnu : 10.")

    response = client.patch(
        "/admin/utilisateurs/10/statut", params={"jeton": "jwt", "actif": True}
    )

    assert response.status_code == 404


@patch("controller.admin_controller.DonneesService.supprimer")
def test_supprimer_observation_succes(mock_supprimer):
    # Le mock ne renvoie rien de spécial, il réussit juste silencieusement
    mock_supprimer.return_value = None

    response = client.delete("/admin/observations/456")

    assert response.status_code == 200
    assert response.json()["observation_id"] == 456
    mock_supprimer.assert_called_once_with(456)
