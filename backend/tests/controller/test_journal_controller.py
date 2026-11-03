import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from business_object.journal_activite import JournalActivite

client = TestClient(app)

@patch("controller.journal_controller.journal_service.consulter")
def test_consulter_journal_succes(mock_consulter):
    # On simule le retour du service (on utilise des dicts car FastAPI les sérialise facilement en JSON)
    mock_consulter.return_value = [
        {"id": 1, "utilisateur_id": 42, "action": "LOGIN", "cible": "App", "details": None}
    ]
    
    # On attaque directement la route branchée dans main.py
    response = client.get("/journal/")
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["statut"] == "succes"
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["action"] == "LOGIN"

@patch("controller.journal_controller.journal_service.consulter")
def test_consulter_journal_erreur_interne(mock_consulter):
    # Simulation d'une erreur (ex: base de données injoignable)
    mock_consulter.side_effect = Exception("Erreur DB")
    
    response = client.get("/journal/")
    
    assert response.status_code == 500
    assert "Erreur lors de la récupération" in response.json()["detail"]