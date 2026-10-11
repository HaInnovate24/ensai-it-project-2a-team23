from fastapi.testclient import TestClient

from controller import referentiel_controller
from main import app


def test_route_lister_pays(monkeypatch):
    class FauxService:
        def lister_pays(self):
            return [
                {"code_pays": "FR", "nom_pays": "France"},
                {"code_pays": "DE", "nom_pays": "Allemagne"},
            ]

    monkeypatch.setattr(referentiel_controller, "ReferentielService", FauxService)

    client = TestClient(app)

    response = client.get("/referentiels/pays")

    assert response.status_code == 200
    assert response.json() == [
        {"code_pays": "FR", "nom_pays": "France"},
        {"code_pays": "DE", "nom_pays": "Allemagne"},
    ]
