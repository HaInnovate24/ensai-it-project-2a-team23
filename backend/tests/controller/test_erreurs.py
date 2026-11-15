"""Tests du gestionnaire central de traduction erreur métier -> HTTP."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controller.erreurs import code_http, installer_gestionnaires_erreurs
from utils.exceptions import (
    AccesRefuse,
    AuthentificationEchouee,
    ConflitRessource,
    DonneesInvalides,
    ErreurMetier,
    RessourceIntrouvable,
)


@pytest.mark.parametrize(
    "erreur, code_attendu",
    [
        (AuthentificationEchouee("jeton invalide"), 401),
        (AccesRefuse("droits insuffisants"), 403),
        (RessourceIntrouvable("introuvable"), 404),
        (ConflitRessource("déjà pris"), 409),
        (DonneesInvalides("paramètre invalide"), 422),
        (ErreurMetier("erreur générique"), 422),
    ],
)
def test_code_http(erreur, code_attendu):
    """Chaque erreur métier est associée au bon code HTTP."""
    assert code_http(erreur) == code_attendu


def _toutes_les_sous_classes(classe: type) -> set[type]:
    """Renvoie récursivement toutes les sous-classes d'une classe."""
    sous_classes = set(classe.__subclasses__())
    for enfant in classe.__subclasses__():
        sous_classes |= _toutes_les_sous_classes(enfant)
    return sous_classes


def test_toute_erreur_metier_reste_une_erreur_client():
    """Garde-fou : toute sous-classe d'ErreurMetier (même future) donne un code 4xx.

    Si quelqu'un ajoute une exception métier sans l'intégrer au mapping, elle doit
    au pire retomber sur le 422 par défaut — jamais produire un 5xx.
    """
    for classe_erreur in {ErreurMetier, *_toutes_les_sous_classes(ErreurMetier)}:
        code = code_http(classe_erreur("message"))
        assert 400 <= code < 500, f"{classe_erreur.__name__} -> {code} (devrait être un 4xx)"


def _app_de_test() -> TestClient:
    """Construit une app minimale exposant une route par type d'erreur."""
    app = FastAPI()
    installer_gestionnaires_erreurs(app)

    @app.get("/auth")
    def _auth():
        raise AuthentificationEchouee("identifiants incorrects")

    @app.get("/acces")
    def _acces():
        raise AccesRefuse("droits insuffisants")

    @app.get("/introuvable")
    def _introuvable():
        raise RessourceIntrouvable("absent")

    @app.get("/conflit")
    def _conflit():
        raise ConflitRessource("déjà pris")

    @app.get("/invalide")
    def _invalide():
        raise DonneesInvalides("mauvais paramètre")

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "chemin, code_attendu, extrait_detail",
    [
        ("/auth", 401, "identifiants incorrects"),
        ("/acces", 403, "droits insuffisants"),
        ("/introuvable", 404, "absent"),
        ("/conflit", 409, "déjà pris"),
        ("/invalide", 422, "mauvais paramètre"),
    ],
)
def test_handler_central_traduit_les_erreurs(chemin, code_attendu, extrait_detail):
    """Une erreur métier non attrapée dans la route est traduite en code HTTP (pas de 500)."""
    client = _app_de_test()
    response = client.get(chemin)
    assert response.status_code == code_attendu
    assert extrait_detail in response.json()["detail"]
