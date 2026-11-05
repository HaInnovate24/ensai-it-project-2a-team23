"""Tests du controller des référentiels.

On utilise TestClient pour passer par les routes HTTP et monkeypatch
pour remplacer ReferentielService par un faux service.
"""

from fastapi.testclient import TestClient

from business_object.enums import TypeClassification
from controller import referentiel_controller
from main import app


class FauxService:
    """Faux service : renvoie des données fixes."""

    def lister_indicateurs(self):
        return [{"code_indicateur": "EMP", "libelle": "Emploi"}]

    def lister_pays(self):
        return [
            {"code_pays": "FR", "nom_pays": "France"},
            {"code_pays": "DE", "nom_pays": "Allemagne"},
        ]

    def lister_classifications(self, type=None):
        if type == TypeClassification.AGE:
            return [{"code_classification": "AGE_15_24", "libelle": "15-24 ans"}]
        return [
            {"code_classification": "AGE_15_24", "libelle": "15-24 ans"},
            {"code_classification": "NIVEAU_DIPLOME", "libelle": "Niveau de diplôme"},
        ]


def test_route_lister_pays(monkeypatch):
    """La route /pays renvoie la liste des pays du service."""
    monkeypatch.setattr(referentiel_controller, "ReferentielService", FauxService)
    client = TestClient(app)

    response = client.get("/referentiels/pays")

    assert response.status_code == 200
    assert response.json() == [
        {"code_pays": "FR", "nom_pays": "France"},
        {"code_pays": "DE", "nom_pays": "Allemagne"},
    ]


def test_route_lister_indicateurs(monkeypatch):
    """La route /indicateurs renvoie la liste des indicateurs du service."""
    monkeypatch.setattr(referentiel_controller, "ReferentielService", FauxService)
    client = TestClient(app)

    response = client.get("/referentiels/indicateurs")

    assert response.status_code == 200
    assert response.json() == [{"code_indicateur": "EMP", "libelle": "Emploi"}]


def test_route_lister_classifications_sans_type(monkeypatch):
    """La route /classifications sans paramètre renvoie toutes les classifications."""
    monkeypatch.setattr(referentiel_controller, "ReferentielService", FauxService)
    client = TestClient(app)

    response = client.get("/referentiels/classifications")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_route_lister_classifications_filtre_age(monkeypatch):
    """La route /classifications?type=AGE filtre par type."""
    monkeypatch.setattr(referentiel_controller, "ReferentielService", FauxService)
    client = TestClient(app)

    response = client.get("/referentiels/classifications", params={"type": TypeClassification.AGE})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["code_classification"] == "AGE_15_24"
