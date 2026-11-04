"""Tests du controller d'authentification.

On patche AuthentificationService pour éviter tout accès réel à la base ou à l'extérieur.
On vérifie que les paramètres sont bien transmis et que les erreurs métier sont
transformées en réponses HTTP appropriées.
"""

import requests
from unittest.mock import patch

from fastapi.testclient import TestClient

from business_object.utilisateur import Utilisateur
from main import app

client = TestClient(app)


# ----------------------------------------------------------------------
# Inscription
# ----------------------------------------------------------------------


@patch("controller.auth_controller.AuthentificationService")
def test_inscription_succes(mock_service_cls):
    """Une inscription réussie renvoie 200 et le message de confirmation."""
    utilisateur = Utilisateur(id=5, nom_utilisateur="nouveau", role=None, actif=True)
    mock_service_cls.return_value.inscrire.return_value = utilisateur

    response = client.post(
        "/auth/inscription",
        json={"nom_utilisateur": "nouveau", "mot_de_passe": "motdepasse123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["statut"] == "succes"
    assert body["message"] == "Utilisateur inscrit"
    assert body["data"]["nom_utilisateur"] == "nouveau"
    mock_service_cls.return_value.inscrire.assert_called_once_with("nouveau", "motdepasse123")


@patch("controller.auth_controller.AuthentificationService")
def test_inscription_utilisateur_existant_renvoie_400(mock_service_cls):
    """Un nom d'utilisateur déjà pris donne une erreur HTTP 400."""
    mock_service_cls.return_value.inscrire.side_effect = ValueError("Nom d'utilisateur déjà utilisé.")

    response = client.post(
        "/auth/inscription",
        json={"nom_utilisateur": "dupont", "mot_de_passe": "secret"},
    )

    assert response.status_code == 400
    assert "déjà utilisé" in response.json()["detail"]


@patch("controller.auth_controller.AuthentificationService")
def test_inscription_erreur_reseau_renvoie_502(mock_service_cls):
    """Une erreur réseau lors de la récupération ILOSTAT donne une erreur 502."""
    mock_service_cls.return_value.inscrire.side_effect = requests.RequestException("Connexion refusée.")

    response = client.post(
        "/auth/inscription",
        json={"nom_utilisateur": "nouveau", "mot_de_passe": "motdepasse123"},
    )

    assert response.status_code == 502
    assert "ILOSTAT" in response.json()["detail"]


# ----------------------------------------------------------------------
# Connexion
# ----------------------------------------------------------------------


@patch("controller.auth_controller.AuthentificationService")
def test_connexion_succes(mock_service_cls):
    """Une connexion réussie renvoie 200 et un jeton."""
    mock_service_cls.return_value.connecter.return_value = {"jeton": "abc123", "type": "bearer"}

    response = client.post(
        "/auth/connexion",
        json={"nom_utilisateur": "dupont", "mot_de_passe": "secret"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["statut"] == "succes"
    assert body["message"] == "Utilisateur connecté"
    assert body["data"]["jeton"] == "abc123"
    mock_service_cls.return_value.connecter.assert_called_once_with("dupont", "secret")


@patch("controller.auth_controller.AuthentificationService")
def test_connexion_identifiants_invalides_renvoie_400(mock_service_cls):
    """Des identifiants incorrects donnent une erreur HTTP 400."""
    mock_service_cls.return_value.connecter.side_effect = ValueError("Identifiants incorrects.")

    response = client.post(
        "/auth/connexion",
        json={"nom_utilisateur": "dupont", "mot_de_passe": "mauvais"},
    )

    assert response.status_code == 400
    assert "incorrects" in response.json()["detail"]


@patch("controller.auth_controller.AuthentificationService")
def test_connexion_erreur_reseau_renvoie_502(mock_service_cls):
    """Une erreur réseau lors de la récupération ILOSTAT donne une erreur 502."""
    mock_service_cls.return_value.connecter.side_effect = requests.RequestException("Timeout.")

    response = client.post(
        "/auth/connexion",
        json={"nom_utilisateur": "dupont", "mot_de_passe": "secret"},
    )

    assert response.status_code == 502
    assert "ILOSTAT" in response.json()["detail"]


# ----------------------------------------------------------------------
# Profil courant
# ----------------------------------------------------------------------


@patch("controller.auth_controller.AuthentificationService")
def test_profil_courant_succes(mock_service_cls):
    """Avec un jeton valide, renvoie 200 et le profil de l'utilisateur."""
    utilisateur = Utilisateur(id=1, nom_utilisateur="dupont", role=None, actif=True)
    mock_service_cls.return_value.utilisateur_depuis_jeton.return_value = utilisateur

    response = client.get("/auth/profil", params={"jeton": "abc123"})

    assert response.status_code == 200
    body = response.json()
    assert body["statut"] == "succes"
    assert body["message"] == "Profil de l'utilisateur"
    assert body["data"]["nom_utilisateur"] == "dupont"
    mock_service_cls.return_value.utilisateur_depuis_jeton.assert_called_once_with("abc123")


@patch("controller.auth_controller.AuthentificationService")
def test_profil_courant_jeton_invalide_renvoie_400(mock_service_cls):
    """Un jeton expiré ou invalide donne une erreur HTTP 400."""
    mock_service_cls.return_value.utilisateur_depuis_jeton.side_effect = ValueError("Jeton invalide.")

    response = client.get("/auth/profil", params={"jeton": "faux-jeton"})

    assert response.status_code == 400
    assert "invalide" in response.json()["detail"]


@patch("controller.auth_controller.AuthentificationService")
def test_profil_courant_erreur_reseau_renvoie_502(mock_service_cls):
    """Une erreur réseau lors de la récupération ILOSTAT donne une erreur 502."""
    mock_service_cls.return_value.utilisateur_depuis_jeton.side_effect = requests.RequestException("Indisponible.")

    response = client.get("/auth/profil", params={"jeton": "abc123"})

    assert response.status_code == 502
    assert "ILOSTAT" in response.json()["detail"]