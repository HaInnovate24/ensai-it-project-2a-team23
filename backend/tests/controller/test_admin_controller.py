import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app

client = TestClient(app)

@patch("controller.admin_controller.UtilisateurService.modifier")
def test_gerer_utilisateur_succes(mock_modifier):
    mock_modifier.return_value = True
    
    # On utilise "nom_utilisateur" au lieu de "nom" ou "email"
    payload = {
        "id": 10,
        "nom_utilisateur": "dupont_a",
        "role": "utilisateur",
        "actif": True
    }
    
    response = client.put("/admin/utilisateurs/10", json=payload)
    
    assert response.status_code == 200
    assert response.json()["statut"] == "succes"
    assert response.json()["utilisateur_id"] == 10

@patch("controller.admin_controller.UtilisateurService.modifier")
def test_gerer_utilisateur_id_incoherent(mock_modifier):
    # L'ID dans l'URL (10) ne correspond pas au JSON (99)
    payload = {
        "id": 99, 
        "nom_utilisateur": "erreur_user"
    }
    
    response = client.put("/admin/utilisateurs/10", json=payload)
    
    assert response.status_code == 400
    assert "ne correspond pas" in response.json()["detail"]

@patch("controller.admin_controller.DonneesService.supprimer")
def test_supprimer_observation_succes(mock_supprimer):
    # Le mock ne renvoie rien de spécial, il réussit juste silencieusement
    mock_supprimer.return_value = None
    
    response = client.delete("/admin/observations/456")
    
    assert response.status_code == 200
    assert response.json()["observation_id"] == 456
    mock_supprimer.assert_called_once_with(456)